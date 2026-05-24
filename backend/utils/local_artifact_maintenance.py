"""Local artifact cleanup.

Archives runtime artifacts (logs, screenshots, debug images, output JSON,
Playwright auth state) into a timestamped ZIP, then removes the local copies.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

logger = logging.getLogger(__name__)

BACKUP_RETENTION_COUNT = 5
BACKUP_FILENAME_PREFIX = "local-artifacts"


def _iter_files(root: Path, pattern: str) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.glob(pattern) if path.is_file())


def _iter_files_recursive(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def _delete_files(files: list[Path]) -> tuple[int, list[dict[str, str]]]:
    deleted = 0
    failures: list[dict[str, str]] = []
    for file_path in files:
        try:
            if file_path.is_file():
                file_path.unlink()
                deleted += 1
        except Exception as exc:
            failures.append({"path": str(file_path), "error": str(exc)})
    return deleted, failures


def _sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collect_json_deletion_targets(
    json_files: list[Path], migration_report: dict[str, Any]
) -> tuple[list[Path], list[dict[str, str]]]:
    """Filter JSON files to only those explicitly marked safe to delete."""
    artifact_status = migration_report.get("artifact_status", {})
    if not isinstance(artifact_status, dict):
        artifact_status = {}

    safe_files: list[Path] = []
    skipped_files: list[dict[str, str]] = []

    for file_path in json_files:
        status = artifact_status.get(file_path.name)
        if isinstance(status, dict) and status.get("safe_to_delete") is True:
            safe_files.append(file_path)
            continue

        entry: dict[str, str] = {"path": str(file_path), "reason": "unsafe_or_unknown"}
        if isinstance(status, dict):
            action = status.get("action")
            if isinstance(action, str) and action:
                entry["reason"] = action
            parse_error = status.get("parse_error")
            if isinstance(parse_error, str) and parse_error:
                entry["parse_error"] = parse_error
        skipped_files.append(entry)

    return safe_files, skipped_files


def _build_backup_entries(
    *,
    screenshot_dir: Path,
    debug_dir: Path,
    json_files: list[Path],
    screenshot_files: list[Path],
    debug_png_files: list[Path],
    log_files: list[Path],
    storage_state_file: Path,
) -> list[tuple[Path, str]]:
    """Build deterministic archive entries."""
    entries: list[tuple[Path, str]] = []
    seen_paths: set[str] = set()

    def add(path_item: Path, arcname: str) -> None:
        path_key = str(path_item.resolve()) if path_item.exists() else str(path_item)
        if path_key in seen_paths:
            return
        seen_paths.add(path_key)
        entries.append((path_item, arcname))

    for file_path in json_files:
        add(file_path, f"output/{file_path.name}")

    for file_path in screenshot_files:
        relative = file_path.name
        try:
            relative = file_path.relative_to(screenshot_dir).as_posix()
        except ValueError:
            pass
        add(file_path, f"screenshot/{relative}")

    for file_path in debug_png_files:
        relative = file_path.name
        try:
            relative = file_path.relative_to(debug_dir).as_posix()
        except ValueError:
            pass
        add(file_path, f"logs/errors/{relative}")

    for file_path in log_files:
        add(file_path, f"logs/{file_path.name}")

    add(storage_state_file, f"authentication data/{storage_state_file.name}")

    return entries


def _create_backup_archive(
    *,
    output_dir: Path,
    runtime_mode: str,
    cleanup_id: str,
    entries: list[tuple[Path, str]],
) -> dict[str, Any]:
    """Create a timestamped ZIP backup before deleting local artifacts."""
    if not entries:
        return {
            "status": "skipped_no_files",
            "archive_path": None,
            "files_backed_up": 0,
        }

    backup_dir = output_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_path = backup_dir / f"{BACKUP_FILENAME_PREFIX}-{runtime_mode}-{timestamp}.zip"
    manifest_files: list[dict[str, Any]] = []

    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for file_path, archive_name in entries:
            if not file_path.is_file():
                continue
            archive.write(file_path, arcname=archive_name)
            manifest_files.append(
                {
                    "path": str(file_path),
                    "archive_path": archive_name,
                    "size_bytes": file_path.stat().st_size,
                    "sha256": _sha256_file(file_path),
                }
            )

        manifest = {
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "runtime_mode": runtime_mode,
            "cleanup_id": cleanup_id,
            "files": manifest_files,
        }
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

    return {
        "status": "created",
        "archive_path": str(archive_path),
        "files_backed_up": len(manifest_files),
    }


def _prune_old_backups(backup_dir: Path) -> tuple[int, list[dict[str, str]]]:
    """Keep only the latest N cleanup backups."""
    if not backup_dir.exists() or not backup_dir.is_dir():
        return 0, []

    backups = sorted(
        (path for path in backup_dir.glob(f"{BACKUP_FILENAME_PREFIX}-*.zip") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    old_backups = backups[BACKUP_RETENTION_COUNT:]
    return _delete_files(old_backups)


def _try_prune_empty_dirs(root: Path) -> None:
    if not root.exists() or not root.is_dir():
        return

    for child in sorted((path for path in root.rglob("*") if path.is_dir()), reverse=True):
        try:
            child.rmdir()
        except OSError:
            continue


def collect_targets(config: dict, is_exe_mode: bool, exe_base_dir: str | None = None) -> dict:
    """Collect local artifact targets for cleanup."""
    output_dir = Path(config["OUTPUT_FOLDER"])
    screenshot_dir = Path(config["SCREENSHOT_FOLDER"])

    if is_exe_mode and exe_base_dir:
        log_root = Path(exe_base_dir) / "logs"
    else:
        log_root = Path("backend/logs")

    debug_dir = log_root / "errors"

    return {
        "output_dir": output_dir,
        "screenshot_dir": screenshot_dir,
        "debug_dir": debug_dir,
        "json_files": _iter_files(output_dir, "*.json"),
        "screenshot_files": _iter_files_recursive(screenshot_dir),
        "debug_png_files": _iter_files(debug_dir, "*.png"),
        "log_files": _iter_files(log_root, "*.log*"),
        "storage_state_file": Path(config["STORAGE_PATH"]),
    }


def cleanup_local_artifacts_once(
    config: dict,
    is_exe_mode: bool,
    runtime_mode: str,
    migration_report: dict[str, Any] | None = None,
    exe_base_dir: str | None = None,
) -> dict:
    """Archive local artifacts into a ZIP, then delete the local copies."""
    migration_report = migration_report or {}
    cleanup_id = f"cleanup:{runtime_mode}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    targets = collect_targets(config, is_exe_mode, exe_base_dir)
    safe_json_files, skipped_unsafe_json = _collect_json_deletion_targets(
        targets["json_files"], migration_report
    )

    backup_entries = _build_backup_entries(
        screenshot_dir=targets["screenshot_dir"],
        debug_dir=targets["debug_dir"],
        json_files=safe_json_files,
        screenshot_files=targets["screenshot_files"],
        debug_png_files=targets["debug_png_files"],
        log_files=targets["log_files"],
        storage_state_file=targets["storage_state_file"],
    )

    try:
        backup_report = _create_backup_archive(
            output_dir=targets["output_dir"],
            runtime_mode=runtime_mode,
            cleanup_id=cleanup_id,
            entries=backup_entries,
        )
    except Exception as exc:
        logger.error("Backup creation failed before cleanup: %s", exc)
        return {
            "status": "skipped_backup_failed",
            "cleanup_id": cleanup_id,
            "runtime_mode": runtime_mode,
            "backups": {
                "status": "failed",
                "error": str(exc),
                "retention_keep_count": BACKUP_RETENTION_COUNT,
            },
            "skipped_unsafe_json_files": skipped_unsafe_json,
            "deleted": {
                "json_files": 0,
                "screenshot_files": 0,
                "debug_png_files": 0,
                "log_files": 0,
                "auth_storage_file": 0,
                "backup_archives": 0,
            },
            "failures": {
                "json": [],
                "screenshot": [],
                "debug_png": [],
                "log_delete": [],
                "auth_storage": [],
                "backup_prune": [],
            },
        }

    json_deleted, json_failures = _delete_files(safe_json_files)
    screenshot_deleted, screenshot_failures = _delete_files(targets["screenshot_files"])
    debug_deleted, debug_failures = _delete_files(targets["debug_png_files"])
    log_deleted, log_delete_failures = _delete_files(targets["log_files"])
    auth_storage_deleted, auth_storage_failures = _delete_files([targets["storage_state_file"]])

    _try_prune_empty_dirs(targets["screenshot_dir"])
    _try_prune_empty_dirs(targets["debug_dir"])
    backup_deleted, backup_delete_failures = _prune_old_backups(targets["output_dir"] / "backups")

    return {
        "status": "completed",
        "cleanup_id": cleanup_id,
        "runtime_mode": runtime_mode,
        "backups": {
            **backup_report,
            "retention_keep_count": BACKUP_RETENTION_COUNT,
        },
        "skipped_unsafe_json_files": skipped_unsafe_json,
        "deleted": {
            "json_files": json_deleted,
            "screenshot_files": screenshot_deleted,
            "debug_png_files": debug_deleted,
            "log_files": log_deleted,
            "auth_storage_file": auth_storage_deleted,
            "backup_archives": backup_deleted,
        },
        "failures": {
            "json": json_failures,
            "screenshot": screenshot_failures,
            "debug_png": debug_failures,
            "log_delete": log_delete_failures,
            "auth_storage": auth_storage_failures,
            "backup_prune": backup_delete_failures,
        },
    }
