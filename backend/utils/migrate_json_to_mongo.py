"""One-time JSON -> MongoDB migration.

Called automatically on startup when MongoDB collections are empty.
Preserves all existing data from output/ JSON files.
"""

import json
import logging
import os
from datetime import datetime, timezone
from hashlib import sha256
from mimetypes import guess_type
from pathlib import Path
from typing import Any

from bson.binary import Binary

logger = logging.getLogger(__name__)

_DEFAULT_SETTINGS_PAYLOAD = {
    "schedule_times": ["08:00", "20:00"],
    "exit_after_run": False,
    "open_web_ui": True,
    "hide_browser": False,
    "run_task": True,
    "gather_shopping_data": True,
    "exchange_good": False,
    "buy_all": False,
    "draw_item": False,
    "enable_hunt_mode": False,
    "stop_on_failed_exchange": False,
    "theme": "purple",
    "sentry_dsn": "",
    "sentry_send_test_event": False,
    "sentry_traces_sample_rate": 1.0,
    "sentry_profiles_sample_rate": 1.0,
    "mongodb_uri": "",
}


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    """Deduplicate paths while preserving input order."""
    unique_paths: list[Path] = []
    seen: set[str] = set()
    for raw_path in paths:
        try:
            normalized = str(raw_path.expanduser().resolve(strict=False)).lower()
        except (OSError, RuntimeError):
            normalized = str(raw_path).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(raw_path)
    return unique_paths


def _resolve_output_dirs(output_dir: str) -> list[Path]:
    """Return primary output dir plus legacy fallback locations."""
    candidates = [Path(output_dir)]

    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        local_path = Path(local_app_data)
        candidates.extend(
            [
                local_path / "zzz-bot" / "output",
                local_path / "ZZZ Bot" / "output",
                local_path / "Programs" / "zzz-bot" / "output",
                local_path / "Programs" / "ZZZ Bot" / "output",
            ]
        )

    custom_legacy_dirs = os.getenv("ZZZ_LEGACY_OUTPUT_DIRS", "").strip()
    if custom_legacy_dirs:
        for raw_path in custom_legacy_dirs.split(";"):
            cleaned = raw_path.strip()
            if cleaned:
                candidates.append(Path(cleaned))

    return _dedupe_paths(candidates)


def _resolve_artifact_path(filename: str, output_dirs: list[Path]) -> str:
    """Pick the first existing artifact path from configured output directories."""
    if not output_dirs:
        return filename

    for directory in output_dirs:
        candidate = directory / filename
        if candidate.is_file():
            return str(candidate)

    return str(output_dirs[0] / filename)


def _is_default_settings_payload(data: Any) -> bool:
    """Return True when settings payload matches app defaults."""
    if not isinstance(data, dict):
        return False
    return all(data.get(key) == value for key, value in _DEFAULT_SETTINGS_PAYLOAD.items())


def _is_blank_account_payload(data: Any) -> bool:
    """Return True when account payload has no credentials."""
    if not isinstance(data, dict):
        return True
    fields = ("username", "password", "app_password")
    return not any(str(data.get(field, "")).strip() for field in fields)


def _read_json_with_error(path: str) -> tuple[Any, str | None]:
    """Read a JSON file and return payload + parse/read error."""
    try:
        json_path = Path(path)
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as file:
                return json.load(file), None
        return None, None
    except Exception as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None, str(exc)


def _build_artifact_status(path: str, before_count: int) -> dict[str, Any]:
    """Build default migration status metadata for one JSON artifact."""
    return {
        "path": path,
        "read_ok": False,
        "parse_error": None,
        "collection_before_count": before_count,
        "collection_after_count": before_count,
        "action": "skipped_missing",
        "safe_to_delete": False,
    }


def _read_artifact_payload(path: str, expected_type: type) -> tuple[Any, bool, str | None]:
    """Load one JSON artifact and validate its type."""
    data, read_error = _read_json_with_error(path)
    if read_error:
        return None, False, read_error
    if data is None:
        return None, False, None
    if not isinstance(data, expected_type):
        return (
            None,
            False,
            f"Invalid type: expected {expected_type.__name__}, got {type(data).__name__}",
        )
    return data, True, None


def _collection_counts(mongo_repository_module, db) -> dict[str, int]:
    """Return lightweight per-collection document counts."""
    return {
        "settings": 1 if mongo_repository_module.get_settings() is not None else 0,
        "accounts": 1 if mongo_repository_module.get_account() is not None else 0,
        "shopping": 1 if mongo_repository_module.get_shopping() is not None else 0,
        "missions": len(mongo_repository_module.get_missions()),
        "redemptions": len(mongo_repository_module.get_redemptions()),
        "last_run": 1 if mongo_repository_module.get_last_run() is not None else 0,
        "storage_state_assets": db.binary_assets.count_documents(
            {"category": "storage_state"}
        ),
        "screenshot_assets": db.binary_assets.count_documents(
            {"category": "screenshot"}
        ),
    }


def _upsert_binary_asset(
    db,
    *,
    asset_id: str,
    category: str,
    source_path: str,
    payload: bytes,
    content_type: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Upsert a binary asset and return True if Mongo was modified."""
    checksum = sha256(payload).hexdigest()
    existing = db.binary_assets.find_one(
        {"_id": asset_id},
        {"checksum_sha256": 1},
    )
    if existing and existing.get("checksum_sha256") == checksum:
        return False

    db.binary_assets.find_one_and_replace(
        {"_id": asset_id},
        {
            "_id": asset_id,
            "category": category,
            "source_path": source_path,
            "content_type": content_type,
            "size_bytes": len(payload),
            "checksum_sha256": checksum,
            "payload": Binary(payload),
            "metadata": metadata or {},
            "updated_at": datetime.now(tz=timezone.utc),
        },
        upsert=True,
    )
    return True


def _migrate_storage_state(db, storage_state_path: str, migrated: list[str]) -> dict[str, Any]:
    """Migrate storage-state JSON file into binary_assets collection."""
    path = Path(storage_state_path)
    if not path.is_file():
        return {"status": "missing"}

    payload = path.read_bytes()
    changed = _upsert_binary_asset(
        db,
        asset_id=f"storage_state:{path.name}",
        category="storage_state",
        source_path=str(path),
        payload=payload,
        content_type="application/json",
        metadata={"filename": path.name},
    )
    if changed:
        migrated.append("storage_state")
    return {
        "status": "upserted" if changed else "unchanged",
        "size_bytes": len(payload),
    }


def _migrate_screenshots(db, screenshot_dir: str, migrated: list[str]) -> dict[str, Any]:
    """Migrate screenshot files into binary_assets collection."""
    folder = Path(screenshot_dir)
    if not folder.is_dir():
        return {"status": "missing", "scanned": 0, "upserted": 0}

    scanned = 0
    upserted = 0
    for file_path in sorted(p for p in folder.rglob("*") if p.is_file()):
        scanned += 1
        relative_path = file_path.relative_to(folder).as_posix()
        content_type, _ = guess_type(file_path.name)
        changed = _upsert_binary_asset(
            db,
            asset_id=f"screenshot:{relative_path}",
            category="screenshot",
            source_path=str(file_path),
            payload=file_path.read_bytes(),
            content_type=content_type or "application/octet-stream",
            metadata={
                "filename": file_path.name,
                "relative_path": relative_path,
            },
        )
        if changed:
            upserted += 1

    if upserted:
        migrated.append(f"screenshots ({upserted} files)")
    return {
        "status": "completed",
        "scanned": scanned,
        "upserted": upserted,
    }


def migrate_if_needed(
    output_dir: str,
    storage_state_path: str | None = None,
    screenshot_dir: str | None = None,
) -> dict[str, Any]:
    """Check each MongoDB collection; migrate from JSON if empty.

    Args:
        output_dir: Absolute path to the output/ folder containing JSON files.
        storage_state_path: Absolute path to Playwright storage-state JSON file.
        screenshot_dir: Absolute path to screenshot directory.

    Returns:
        Structured migration report for diagnostics/tracing.
    """
    import sentry_sdk

    from repositories import MongoRepository
    from repositories.connection import get_connection_debug_info, get_db

    migrated: list[str] = []
    artifact_status: dict[str, dict[str, Any]] = {}
    db = get_db()
    output_dirs = _resolve_output_dirs(output_dir)

    def _path(filename: str) -> str:
        return _resolve_artifact_path(filename, output_dirs)

    with sentry_sdk.start_transaction(
        op="startup.mongo_migration",
        name="mongo-migration-check",
        sampled=True,
    ) as transaction:
        counts_before = _collection_counts(MongoRepository, db)

        # Settings
        settings_path = _path("settings.json")
        settings_status = _build_artifact_status(settings_path, counts_before["settings"])
        settings_data, settings_valid, settings_error = _read_artifact_payload(
            settings_path, dict
        )
        if settings_error:
            settings_status["parse_error"] = settings_error
            settings_status["action"] = "skipped_invalid"
        elif settings_data is None:
            settings_status["action"] = "skipped_missing"
        elif not settings_valid:
            settings_status["parse_error"] = "Invalid JSON payload"
            settings_status["action"] = "skipped_invalid"
        else:
            settings_status["read_ok"] = True
            if counts_before["settings"] == 0:
                MongoRepository.save_settings(settings_data)
                migrated.append("settings")
                settings_status["action"] = "migrated"
            elif _is_default_settings_payload(MongoRepository.get_settings()):
                MongoRepository.save_settings(settings_data)
                migrated.append("settings (replaced_default)")
                settings_status["action"] = "migrated_replaced_default"
            else:
                settings_status["action"] = "skipped_existing_data"
            settings_status["safe_to_delete"] = True
        artifact_status["settings.json"] = settings_status

        # Account
        account_path = _path("account.json")
        account_status = _build_artifact_status(account_path, counts_before["accounts"])
        account_data, account_valid, account_error = _read_artifact_payload(
            account_path, dict
        )
        if account_error:
            account_status["parse_error"] = account_error
            account_status["action"] = "skipped_invalid"
        elif account_data is None:
            account_status["action"] = "skipped_missing"
        elif not account_valid:
            account_status["parse_error"] = "Invalid JSON payload"
            account_status["action"] = "skipped_invalid"
        else:
            account_status["read_ok"] = True
            if counts_before["accounts"] == 0:
                MongoRepository.save_account(account_data)
                migrated.append("account")
                account_status["action"] = "migrated"
            elif _is_blank_account_payload(MongoRepository.get_account()):
                MongoRepository.save_account(account_data)
                migrated.append("account (replaced_blank)")
                account_status["action"] = "migrated_replaced_blank"
            else:
                account_status["action"] = "skipped_existing_data"
            account_status["safe_to_delete"] = True
        artifact_status["account.json"] = account_status

        # Shopping
        shopping_path = _path("shopping.json")
        shopping_status = _build_artifact_status(shopping_path, counts_before["shopping"])
        shopping_data, shopping_valid, shopping_error = _read_artifact_payload(
            shopping_path, dict
        )
        if shopping_error:
            shopping_status["parse_error"] = shopping_error
            shopping_status["action"] = "skipped_invalid"
        elif shopping_data is None:
            shopping_status["action"] = "skipped_missing"
        elif not shopping_valid:
            shopping_status["parse_error"] = "Invalid JSON payload"
            shopping_status["action"] = "skipped_invalid"
        else:
            shopping_status["read_ok"] = True
            if counts_before["shopping"] == 0:
                MongoRepository.save_shopping(shopping_data)
                migrated.append("shopping")
                shopping_status["action"] = "migrated"
            else:
                shopping_status["action"] = "skipped_existing_data"
            shopping_status["safe_to_delete"] = True
        artifact_status["shopping.json"] = shopping_status

        # Missions (list -> one doc per day)
        missions_path = _path("missions.json")
        missions_status = _build_artifact_status(missions_path, counts_before["missions"])
        missions_data, missions_valid, missions_error = _read_artifact_payload(
            missions_path, list
        )
        if missions_error:
            missions_status["parse_error"] = missions_error
            missions_status["action"] = "skipped_invalid"
        elif missions_data is None:
            missions_status["action"] = "skipped_missing"
        elif not missions_valid:
            missions_status["parse_error"] = "Invalid JSON payload"
            missions_status["action"] = "skipped_invalid"
        else:
            missions_status["read_ok"] = True
            if counts_before["missions"] == 0:
                for day_record in missions_data:
                    MongoRepository.save_mission_day(day_record)
                migrated.append(f"missions ({len(missions_data)} records)")
                missions_status["action"] = "migrated"
            else:
                missions_status["action"] = "skipped_existing_data"
            missions_status["safe_to_delete"] = True
        artifact_status["missions.json"] = missions_status

        # Redemptions (list -> one doc per entry)
        redeem_path = _path("redeem.json")
        redeem_status = _build_artifact_status(redeem_path, counts_before["redemptions"])
        redeem_data, redeem_valid, redeem_error = _read_artifact_payload(
            redeem_path, list
        )
        if redeem_error:
            redeem_status["parse_error"] = redeem_error
            redeem_status["action"] = "skipped_invalid"
        elif redeem_data is None:
            redeem_status["action"] = "skipped_missing"
        elif not redeem_valid:
            redeem_status["parse_error"] = "Invalid JSON payload"
            redeem_status["action"] = "skipped_invalid"
        else:
            redeem_status["read_ok"] = True
            if counts_before["redemptions"] == 0:
                for entry in redeem_data:
                    MongoRepository.save_redemption(entry)
                migrated.append(f"redemptions ({len(redeem_data)} records)")
                redeem_status["action"] = "migrated"
            else:
                redeem_status["action"] = "skipped_existing_data"
            redeem_status["safe_to_delete"] = True
        artifact_status["redeem.json"] = redeem_status

        # Last run
        last_run_path = _path("last_run.json")
        last_run_status = _build_artifact_status(last_run_path, counts_before["last_run"])
        last_run_data, last_run_valid, last_run_error = _read_artifact_payload(
            last_run_path, dict
        )
        if last_run_error:
            last_run_status["parse_error"] = last_run_error
            last_run_status["action"] = "skipped_invalid"
        elif last_run_data is None:
            last_run_status["action"] = "skipped_missing"
        elif not last_run_valid:
            last_run_status["parse_error"] = "Invalid JSON payload"
            last_run_status["action"] = "skipped_invalid"
        else:
            last_run_status["read_ok"] = True
            if counts_before["last_run"] == 0:
                MongoRepository.save_last_run(last_run_data)
                migrated.append("last_run")
                last_run_status["action"] = "migrated"
            else:
                last_run_status["action"] = "skipped_existing_data"
            last_run_status["safe_to_delete"] = True
        artifact_status["last_run.json"] = last_run_status

        storage_report = {"status": "skipped"}
        if storage_state_path:
            storage_report = _migrate_storage_state(db, storage_state_path, migrated)

        screenshot_report = {"status": "skipped", "scanned": 0, "upserted": 0}
        if screenshot_dir:
            screenshot_report = _migrate_screenshots(db, screenshot_dir, migrated)

        counts_after = _collection_counts(MongoRepository, db)
        artifact_status["settings.json"]["collection_after_count"] = counts_after["settings"]
        artifact_status["account.json"]["collection_after_count"] = counts_after["accounts"]
        artifact_status["shopping.json"]["collection_after_count"] = counts_after["shopping"]
        artifact_status["missions.json"]["collection_after_count"] = counts_after["missions"]
        artifact_status["redeem.json"]["collection_after_count"] = counts_after[
            "redemptions"
        ]
        artifact_status["last_run.json"]["collection_after_count"] = counts_after["last_run"]
        report = {
            "migrated": migrated,
            "counts_before": counts_before,
            "counts_after": counts_after,
            "artifact_status": artifact_status,
            "output_dirs_checked": [str(path) for path in output_dirs],
            "storage_state_report": storage_report,
            "screenshot_report": screenshot_report,
        }

        transaction.set_data("mongo.connection", get_connection_debug_info())
        transaction.set_data("mongo.migration_report", report)

    if migrated:
        logger.info(
            "Migrated to MongoDB: %s. Legacy JSON files are now backup-only.",
            ", ".join(migrated),
        )
    else:
        logger.info(
            "MongoDB already populated — no migration needed. Legacy JSON files remain backup-only."
        )

    logger.info("Mongo migration report: %s", report)
    return report
