import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.local_artifact_maintenance as local_artifact_maintenance
from utils.local_artifact_maintenance import (
    BACKUP_FILENAME_PREFIX,
    BACKUP_RETENTION_COUNT,
    cleanup_local_artifacts_once,
)

collect_json_deletion_targets = local_artifact_maintenance._collect_json_deletion_targets
prune_old_backups = local_artifact_maintenance._prune_old_backups


def test_collect_json_deletion_targets_respects_safe_flags(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    account_file = tmp_path / "account.json"
    settings_file.write_text("{}", encoding="utf-8")
    account_file.write_text("{}", encoding="utf-8")

    migration_report = {
        "artifact_status": {
            "settings.json": {
                "safe_to_delete": True,
                "action": "migrated",
            },
            "account.json": {
                "safe_to_delete": False,
                "action": "skipped_invalid",
                "parse_error": "bad json",
            },
        }
    }

    safe_files, skipped_files = collect_json_deletion_targets(
        [settings_file, account_file], migration_report
    )

    assert safe_files == [settings_file]
    assert skipped_files == [
        {
            "path": str(account_file),
            "reason": "skipped_invalid",
            "parse_error": "bad json",
        }
    ]


def test_prune_old_backups_keeps_latest_five(tmp_path: Path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for index in range(BACKUP_RETENTION_COUNT + 2):
        archive = backup_dir / f"{BACKUP_FILENAME_PREFIX}-dev-20250101_00000{index}.zip"
        archive.write_bytes(b"test")
        ts = 1_700_000_000 + index
        os.utime(archive, (ts, ts))

    deleted_count, failures = prune_old_backups(backup_dir)

    remaining = list(backup_dir.glob(f"{BACKUP_FILENAME_PREFIX}-*.zip"))

    assert deleted_count == 2
    assert failures == []
    assert len(remaining) == BACKUP_RETENTION_COUNT


def test_cleanup_deletes_auth_storage_file(tmp_path: Path):
    output_dir = tmp_path / "output"
    screenshot_dir = tmp_path / "screenshot"
    storage_dir = tmp_path / "authentication data"
    log_dir = tmp_path / "logs"
    output_dir.mkdir()
    screenshot_dir.mkdir()
    storage_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    storage_path = storage_dir / "hoyo.json"
    storage_path.write_text("{}", encoding="utf-8")

    # exe mode keeps the log search rooted under tmp_path (isolated from the repo).
    report = cleanup_local_artifacts_once(
        config={
            "OUTPUT_FOLDER": str(output_dir),
            "SCREENSHOT_FOLDER": str(screenshot_dir),
            "STORAGE_PATH": str(storage_path),
        },
        is_exe_mode=True,
        runtime_mode="exe",
        exe_base_dir=str(tmp_path),
    )

    assert report["status"] == "completed"
    assert report["deleted"]["auth_storage_file"] == 1
    assert report["failures"]["auth_storage"] == []
    assert report["backups"]["status"] == "created"
    assert not storage_path.exists()
