"""One-time JSON -> MongoDB migration.

Called automatically on startup when MongoDB collections are empty.
Preserves all existing data from output/ JSON files.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Callable

from bson.binary import Binary

logger = logging.getLogger(__name__)

_DEFAULT_SETTINGS_PAYLOAD = {
    "schedule_times": ["08:00", "20:00"],
    "exit_after_run": False,
    "show_window_on_startup": True,
    "window_x": None,
    "window_y": None,
    "window_width": None,
    "window_height": None,
    "hide_browser": False,
    "run_task": True,
    "gather_shopping_data": True,
    "exchange_good": False,
    "buy_all": False,
    "draw_item": False,
    "enable_hunt_mode": False,
    "stop_on_failed_exchange": False,
    "hunt_poll_max_wait_seconds": 180,
    "hunt_poll_interval_seconds": 1,
    "hunt_poll_backoff_enabled": True,
    "hunt_early_exit_on_unavailable": False,
    "theme": "purple",
    "sentry_dsn": "",
    "sentry_frontend_dsn": "",
    "sentry_send_test_event": False,
    "sentry_traces_sample_rate": 1.0,
    "mongodb_uri": "",
}


# ============================================================
# Path Resolution
# ============================================================


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


# ============================================================
# Payload Validation
# ============================================================


def _is_default_settings_payload(data: Any) -> bool:
    """Return True when settings payload matches app defaults."""
    if not isinstance(data, dict):
        return False
    normalized = dict(data)
    if "show_window_on_startup" not in normalized and "open_web_ui" in normalized:
        normalized["show_window_on_startup"] = normalized["open_web_ui"]
    return all(
        normalized.get(key) == value for key, value in _DEFAULT_SETTINGS_PAYLOAD.items()
    )


def _is_blank_account_payload(data: Any) -> bool:
    """Return True when account payload has no credentials."""
    if not isinstance(data, dict):
        return True
    fields = ("username", "app_password", "hoyo_username", "hoyo_password")
    return not any(str(data.get(field, "")).strip() for field in fields)


# ============================================================
# JSON Reading
# ============================================================


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


def _read_artifact_payload(path: str, expected_type: type) -> tuple[Any, str | None]:
    """Load one JSON artifact and validate its type.

    Returns:
        (data, error) — data is None when file is missing or invalid.
    """
    data, read_error = _read_json_with_error(path)
    if read_error:
        return None, read_error
    if data is None:
        return None, None
    if not isinstance(data, expected_type):
        return (
            None,
            f"Invalid type: expected {expected_type.__name__}, got {type(data).__name__}",
        )
    return data, None


# ============================================================
# Artifact Specs
# ============================================================


@dataclass(frozen=True, slots=True)
class _ArtifactSpec:
    """Descriptor for one JSON artifact to migrate."""

    filename: str
    expected_type: type
    count_key: str
    save_method: str
    label: str
    multi_record: bool = False
    replace_getter: str | None = None
    replace_checker: Callable[[Any], bool] | None = None
    replace_label: str | None = None
    replace_action: str | None = None


_ARTIFACT_SPECS: list[_ArtifactSpec] = [
    _ArtifactSpec(
        filename="settings.json",
        expected_type=dict,
        count_key="settings",
        save_method="save_settings",
        label="settings",
        replace_getter="get_settings",
        replace_checker=_is_default_settings_payload,
        replace_label="settings (replaced_default)",
        replace_action="migrated_replaced_default",
    ),
    _ArtifactSpec(
        filename="account.json",
        expected_type=dict,
        count_key="accounts",
        save_method="save_account",
        label="account",
        replace_getter="get_account",
        replace_checker=_is_blank_account_payload,
        replace_label="account (replaced_blank)",
        replace_action="migrated_replaced_blank",
    ),
    _ArtifactSpec(
        filename="shopping.json",
        expected_type=dict,
        count_key="shopping",
        save_method="save_shopping",
        label="shopping",
    ),
    _ArtifactSpec(
        filename="missions.json",
        expected_type=list,
        count_key="missions",
        save_method="save_mission_day",
        label="missions",
        multi_record=True,
    ),
    _ArtifactSpec(
        filename="redeem.json",
        expected_type=list,
        count_key="redemptions",
        save_method="save_redemption",
        label="redemptions",
        multi_record=True,
    ),
    _ArtifactSpec(
        filename="last_run.json",
        expected_type=dict,
        count_key="last_run",
        save_method="save_last_run",
        label="last_run",
    ),
]


# ============================================================
# Artifact Migration
# ============================================================


def _migrate_artifact(
    spec: _ArtifactSpec,
    repo: Any,
    path: str,
    before_count: int,
    migrated: list[str],
) -> dict[str, Any]:
    """Migrate one JSON artifact into MongoDB."""
    status = _build_artifact_status(path, before_count)
    data, error = _read_artifact_payload(path, spec.expected_type)

    if error:
        status["parse_error"] = error
        status["action"] = "skipped_invalid"
        return status

    if data is None:
        return status

    status["read_ok"] = True

    if before_count == 0:
        _save_artifact_data(spec, repo, data, migrated, status)
    elif spec.replace_checker is not None:
        existing = getattr(repo, spec.replace_getter)()
        if spec.replace_checker(existing):
            getattr(repo, spec.save_method)(data)
            migrated.append(spec.replace_label)
            status["action"] = spec.replace_action
        else:
            status["action"] = "skipped_existing_data"
    else:
        status["action"] = "skipped_existing_data"

    status["safe_to_delete"] = True
    return status


def _save_artifact_data(
    spec: _ArtifactSpec,
    repo: Any,
    data: Any,
    migrated: list[str],
    status: dict[str, Any],
) -> None:
    """Persist artifact data into MongoDB, handling multi-record collections."""
    save_fn = getattr(repo, spec.save_method)

    if not spec.multi_record:
        save_fn(data)
        migrated.append(spec.label)
        status["action"] = "migrated"
        return

    saved, total = 0, len(data)
    for record in data:
        try:
            save_fn(record)
            saved += 1
        except Exception as exc:
            logger.warning("Failed to save %s record: %s", spec.label, exc)

    if saved == total:
        status["action"] = "migrated"
        migrated.append(f"{spec.label} ({total} records)")
    else:
        status["action"] = "migrated_partial"
        status["records_failed"] = total - saved
        migrated.append(f"{spec.label} ({saved}/{total} records)")


# ============================================================
# Collection Counts
# ============================================================


def _collection_counts(repo: Any, db: Any) -> dict[str, int]:
    """Return lightweight per-collection document counts.

    Args:
        repo: MongoRepository module (used for document-level queries).
        db: Raw pymongo database (used for binary_assets counts).
    """
    return {
        "settings": 1 if repo.get_settings() is not None else 0,
        "accounts": 1 if repo.get_account() is not None else 0,
        "shopping": 1 if repo.get_shopping() is not None else 0,
        "missions": len(repo.get_missions()),
        "redemptions": len(repo.get_redemptions()),
        "last_run": 1 if repo.get_last_run() is not None else 0,
        "storage_state_assets": db.binary_assets.count_documents(
            {"category": "storage_state"}
        ),
        "screenshot_assets": db.binary_assets.count_documents(
            {"category": "screenshot"}
        ),
    }


# ============================================================
# Binary Assets
# ============================================================


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


def _migrate_storage_state(
    db, storage_state_path: str, migrated: list[str]
) -> dict[str, Any]:
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


def _migrate_screenshots(
    db, screenshot_dir: str, migrated: list[str]
) -> dict[str, Any]:
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


# ============================================================
# Settings Backfill
# ============================================================


def _backfill_settings(db: Any) -> None:
    """Remove deprecated fields and populate missing Sentry DSNs."""
    db.settings.update_many({}, {"$unset": {"sentry_profiles_sample_rate": ""}})
    db.settings.update_many(
        {
            "show_window_on_startup": {"$exists": False},
            "open_web_ui": {"$exists": True},
        },
        [
            {
                "$set": {
                    "show_window_on_startup": "$open_web_ui",
                }
            },
            {
                "$unset": "open_web_ui",
            },
        ],
    )
    db.settings.update_many(
        {
            "show_window_on_startup": {"$exists": True},
            "open_web_ui": {"$exists": True},
        },
        {"$unset": {"open_web_ui": ""}},
    )

    for env_var, field in [
        ("SENTRY_DSN", "sentry_dsn"),
        ("SENTRY_FRONTEND_DSN", "sentry_frontend_dsn"),
    ]:
        dsn = os.getenv(env_var, "").strip()
        if dsn:
            db.settings.update_many(
                {
                    "$or": [
                        {field: {"$in": [None, ""]}},
                        {field: {"$exists": False}},
                    ]
                },
                {"$set": {field: dsn}},
            )


# ============================================================
# Main Entry
# ============================================================


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

    with sentry_sdk.start_span(
        op="startup.mongo_migration",
        name="mongo-migration-check",
    ) as span:
        counts_before = _collection_counts(MongoRepository, db)

        for spec in _ARTIFACT_SPECS:
            path = _path(spec.filename)
            status = _migrate_artifact(
                spec, MongoRepository, path, counts_before[spec.count_key], migrated
            )
            artifact_status[spec.filename] = status

        _backfill_settings(db)

        storage_report = {"status": "skipped"}
        if storage_state_path:
            storage_report = _migrate_storage_state(db, storage_state_path, migrated)

        screenshot_report = {"status": "skipped", "scanned": 0, "upserted": 0}
        if screenshot_dir:
            screenshot_report = _migrate_screenshots(db, screenshot_dir, migrated)

        counts_after = _collection_counts(MongoRepository, db)
        for spec in _ARTIFACT_SPECS:
            artifact_status[spec.filename]["collection_after_count"] = counts_after[
                spec.count_key
            ]

        report = {
            "migrated": migrated,
            "counts_before": counts_before,
            "counts_after": counts_after,
            "artifact_status": artifact_status,
            "output_dirs_checked": [str(path) for path in output_dirs],
            "storage_state_report": storage_report,
            "screenshot_report": screenshot_report,
        }

        span.set_data("mongo.connection", get_connection_debug_info())
        span.set_data("mongo.migration_report", report)

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
