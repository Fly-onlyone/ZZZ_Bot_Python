"""Tests for the Mongo -> SQLite migration script."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.migrate_mongo_to_sqlite as migrate_module


class _FakeCollection:
    """Minimal stand-in for a pymongo Collection."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self):
        return [dict(d) for d in self.docs]

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def count_documents(self, query, limit=None):
        matches = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        if limit is not None:
            matches = matches[:limit]
        return len(matches)

    def estimated_document_count(self):
        return len(self.docs)


class _FakeMongoDb:
    """Minimal stand-in for a pymongo Database that supports db[name]."""

    def __init__(self, collections=None):
        self._collections = {}
        for name, docs in (collections or {}).items():
            self._collections[name] = _FakeCollection(docs)

    def __getitem__(self, name):
        if name not in self._collections:
            self._collections[name] = _FakeCollection()
        return self._collections[name]


def _patch_connect(monkeypatch, db, message="Using database: zzz_bot_dev"):
    monkeypatch.setattr(migrate_module, "_connect_or_none", lambda uri, db_name: (db, message))


def test_migrate_empty_mongo_does_not_wipe_sqlite_missions_or_redemptions(sqlite_db, monkeypatch):
    # SQLite already has a previous migration's data.
    sqlite_db.save_mission_day({"day": "01/01/2026", "missions": [{"name": "Check-in"}]})
    sqlite_db.save_redemption({"code": "ABC", "day": "10:00 01/01/2026", "state": True})
    assert len(sqlite_db.get_missions()) == 1
    assert len(sqlite_db.get_redemptions()) == 1

    # Source MongoDB is reachable but contains no rows at all (e.g. the user
    # dropped the db after the first migration).
    fake_db = _FakeMongoDb(
        {
            "settings": [],
            "accounts": [],
            "shopping": [],
            "last_run": [],
            "backup_config": [],
            "missions": [],
            "redemptions": [],
            "app_metadata": [],
            "binary_assets": [],
        }
    )
    _patch_connect(monkeypatch, fake_db)

    report = migrate_module.migrate()

    # Migration bails out with no_source instead of running destructive writes.
    assert report["status"] == "no_source"
    assert report["summary"] == {}
    # And SQLite is untouched.
    assert len(sqlite_db.get_missions()) == 1
    assert len(sqlite_db.get_redemptions()) == 1


def test_migrate_partial_mongo_only_replaces_collections_with_rows(sqlite_db, monkeypatch):
    # SQLite is seeded.
    sqlite_db.save_mission_day({"day": "01/01/2026", "missions": []})
    sqlite_db.save_redemption({"code": "OLD", "day": "10:00 01/01/2026", "state": True})

    # Mongo has settings only — missions and redemptions are empty.
    fake_db = _FakeMongoDb(
        {
            "settings": [{"_id": "default", "theme": "venom"}],
            "missions": [],
            "redemptions": [],
        }
    )
    _patch_connect(monkeypatch, fake_db)

    report = migrate_module.migrate()

    assert report["status"] == "completed"
    assert report["summary"]["settings"] == 1
    assert report["summary"]["missions"] == 0
    assert report["summary"]["redemptions"] == 0
    # The destructive replace_all_* MUST NOT have been called for empty sources.
    assert len(sqlite_db.get_missions()) == 1
    assert len(sqlite_db.get_redemptions()) == 1
    # Settings was imported.
    assert sqlite_db.get_settings() == {"theme": "venom"}


def test_migrate_no_reachable_source_is_safe(sqlite_db, monkeypatch):
    sqlite_db.save_mission_day({"day": "01/01/2026", "missions": []})

    monkeypatch.setattr(
        migrate_module,
        "_connect_or_none",
        lambda uri, db_name: (None, f"MongoDB not reachable at {uri}: nope"),
    )

    report = migrate_module.migrate()

    assert report["status"] == "no_source"
    assert report["summary"] == {}
    assert len(sqlite_db.get_missions()) == 1


def test_candidate_db_names_prefers_runtime_mode(monkeypatch):
    # migrate_module imports get_runtime_mode by name, so patch the local binding.
    monkeypatch.setattr(migrate_module, "get_runtime_mode", lambda: "dev")
    assert migrate_module._candidate_db_names() == ("zzz_bot_dev", "zzz_bot")

    monkeypatch.setattr(migrate_module, "get_runtime_mode", lambda: "exe")
    assert migrate_module._candidate_db_names() == ("zzz_bot", "zzz_bot_dev")


def test_migrate_imports_locator_tracker_and_failures(sqlite_db, monkeypatch, tmp_path):
    fake_db = _FakeMongoDb(
        {
            "locator_tracker": [
                {
                    "_id": "locator:MissionHandler:visibility_check:abc123",
                    "selector": "button.launch",
                    "selector_hash": "abc123",
                    "handler": "MissionHandler",
                    "action": "visibility_check",
                    "last_success": True,
                    "hit_count": 1,
                    "success_count": 1,
                    "failure_count": 0,
                    "child_scan": [],
                    "first_seen": "2026-05-23T00:00:00.000000+00:00",
                    "last_seen": "2026-05-23T00:00:00.000000+00:00",
                }
            ],
            "locator_tracker_failures": [
                {
                    "_id": "locator-failure:00000000-0000-0000-0000-000000000001",
                    "summary_id": "locator:MissionHandler:visibility_check:abc123",
                    "selector": "button.launch",
                    "selector_hash": "abc123",
                    "handler": "MissionHandler",
                    "action": "visibility_check",
                    "error_message": "timeout",
                    "seen_at": "2026-05-23T00:00:00.000000+00:00",
                },
            ],
        }
    )
    _patch_connect(monkeypatch, fake_db)
    # Keep log_lines from touching the real filesystem.
    monkeypatch.setattr(migrate_module, "_resolve_archive_dir", lambda: str(tmp_path))

    report = migrate_module.migrate()

    assert report["status"] == "completed"
    assert report["summary"]["locator_tracker"] == 1
    assert report["summary"]["locator_tracker_failures"] == 1
    entries = sqlite_db.get_locator_entries()
    assert len(entries) == 1
    assert entries[0]["selector"] == "button.launch"
    failures = sqlite_db.get_locator_failure_events()
    assert len(failures) == 1
    assert failures[0]["summary_id"] == "locator:MissionHandler:visibility_check:abc123"


def test_migrate_log_lines_writes_ndjson_archive(sqlite_db, monkeypatch, tmp_path):
    fake_db = _FakeMongoDb(
        {
            # Need at least one non-log_lines doc so _source_has_any_data passes
            # without forcing log_lines into the precheck output.
            "settings": [{"_id": "default", "theme": "venom"}],
            "log_lines": [
                {
                    "_id": "abc123",
                    "source_mode": "dev",
                    "source_file": "backend/logs/app.log",
                    "line_number": 1,
                    "raw_line": "2026-05-23 00:00:00,000 - boot - INFO - hello",
                    "parsed_ts": "2026-05-23T00:00:00.000000+00:00",
                    "level": "INFO",
                    "ingested_at": "2026-05-23T00:00:00.000000+00:00",
                },
                {
                    "_id": "def456",
                    "source_mode": "dev",
                    "source_file": "backend/logs/app.log",
                    "line_number": 2,
                    "raw_line": "2026-05-23 00:00:01,000 - boot - INFO - second",
                    "parsed_ts": "2026-05-23T00:00:01.000000+00:00",
                    "level": "INFO",
                    "ingested_at": "2026-05-23T00:00:01.000000+00:00",
                },
            ],
        }
    )
    _patch_connect(monkeypatch, fake_db)
    monkeypatch.setattr(migrate_module, "_resolve_archive_dir", lambda: str(tmp_path))

    report = migrate_module.migrate()

    assert report["status"] == "completed"
    assert report["summary"]["log_lines"] == 2
    archive_path = report["archives"]["log_lines"]
    assert archive_path.startswith(str(tmp_path))
    archived = Path(archive_path).read_text(encoding="utf-8").splitlines()
    assert len(archived) == 2
    first = json.loads(archived[0])
    assert first["raw_line"].endswith("hello")
    assert first["level"] == "INFO"


def test_migrate_log_lines_only_creates_archive_when_source_has_rows(
    sqlite_db, monkeypatch, tmp_path
):
    fake_db = _FakeMongoDb(
        {
            "settings": [{"_id": "default", "theme": "nebula"}],
            "log_lines": [],
        }
    )
    _patch_connect(monkeypatch, fake_db)
    # tmp_path is shared with the sqlite_db fixture's database file, so use a
    # dedicated subdir to detect whether the migration touched it.
    archive_dir = tmp_path / "archives"
    monkeypatch.setattr(migrate_module, "_resolve_archive_dir", lambda: str(archive_dir))

    report = migrate_module.migrate()

    assert report["status"] == "completed"
    assert report["summary"]["log_lines"] == 0
    assert report["archives"] == {}
    # _migrate_log_lines bails before calling makedirs when the cursor is empty.
    assert not archive_dir.exists()
