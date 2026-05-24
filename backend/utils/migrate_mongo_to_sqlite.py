"""One-time migration: copy an existing local MongoDB database into SQLite.

ZZZ Bot moved from MongoDB to an embedded SQLite store. Run this once if you
have data in a local MongoDB instance you want to keep. Two equivalent ways:

* In-app:  **Backup → Maintenance → Migrate from MongoDB**.
* CLI:     ``uv run python backend/utils/migrate_mongo_to_sqlite.py``.

``migrate()`` returns a structured report dict so the CLI wrapper and the
``POST /maintenance/mongo-migration`` HTTP endpoint can both call it. ``pymongo``
is imported lazily inside ``_connect_or_none`` — importing this module is cheap
and does not require pymongo at import time (only at call time).

What gets copied
----------------

Into SQLite via the normal DataStore API (so schema and TTL rules are reused):

* Single-doc collections — settings, accounts, shopping, last_run, backup_config
* Multi-doc collections — missions, redemptions
* App-metadata markers
* Binary assets (screenshots, Playwright auth state) — BSON Binary → SQLite BLOB
* Locator telemetry — locator_tracker, locator_tracker_failures

Written to disk as a side effect (no SQLite table — the running app reads logs
from ``backend/logs/*.log`` directly, this is pure archival):

* log_lines — Mongo's old log-mirror collection, dumped to
  ``output/migrations/log_lines-<timestamp>.ndjson`` (one JSON record per line).

Re-running is safe even after Mongo has been emptied or partially cleared:
the migration refuses to run when the source has no migratable data
(``_source_has_any_data``), and the multi-doc step skips its destructive
``replace_all_*`` calls for any collection whose Mongo source is empty.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running this file directly: put backend/ on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from repositories import DataStore  # noqa: E402
from repositories.connection import get_connection_debug_info, get_runtime_mode  # noqa: E402

DEFAULT_MONGO_URI = "mongodb://localhost:27017"


def _candidate_db_names() -> tuple[str, ...]:
    """Pick the Mongo database to try first based on the current runtime mode.

    Dev runs target ``zzz_bot_dev`` (the old MongoRepository's dev default);
    packaged exe runs target ``zzz_bot``. The other name is kept as a fallback
    so a user who happens to have both still gets a sensible default.
    """
    if get_runtime_mode() == "exe":
        return ("zzz_bot", "zzz_bot_dev")
    return ("zzz_bot_dev", "zzz_bot")


_SINGLE_DOC_SAVERS = {
    "settings": DataStore.save_settings,
    "accounts": DataStore.save_account,  # MongoDB collection is named "accounts"
    "shopping": DataStore.save_shopping,
    "last_run": DataStore.save_last_run,
    "backup_config": DataStore.save_backup_config,
}


def _strip_mongo_id(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


def _connect_or_none(uri: str, db_name: str | None) -> tuple[object | None, str]:
    """Connect to MongoDB and return (database, message).

    Returns ``(None, reason)`` when the source isn't reachable / present, so
    callers can report the reason without printing.
    """
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except PyMongoError as exc:
        return None, f"MongoDB not reachable at {uri}: {exc}"

    existing = set(client.list_database_names())
    if db_name:
        if db_name not in existing:
            return None, f"Database '{db_name}' not found at {uri}"
        return client[db_name], f"Using database: {db_name}"

    candidates = _candidate_db_names()
    for candidate in candidates:
        if candidate in existing:
            return client[candidate], f"Using database: {candidate}"

    return None, f"None of {candidates} found at {uri}"


_MULTI_DOC_COLLECTIONS = (
    "missions",
    "redemptions",
    "app_metadata",
    "binary_assets",
    "locator_tracker",
    "locator_tracker_failures",
    "log_lines",
)


def _source_has_any_data(db) -> bool:
    """True if at least one migratable Mongo collection is non-empty."""
    for collection in _SINGLE_DOC_SAVERS:
        if db[collection].count_documents({"_id": "default"}, limit=1) > 0:
            return True
    for collection in _MULTI_DOC_COLLECTIONS:
        if db[collection].estimated_document_count() > 0:
            return True
    return False


def _migrate_single_docs(db, summary: dict) -> None:
    for collection, saver in _SINGLE_DOC_SAVERS.items():
        doc = db[collection].find_one({"_id": "default"})
        if doc:
            saver(_strip_mongo_id(doc))
            summary[collection] = 1
        else:
            summary[collection] = 0


def _migrate_multi_docs(db, summary: dict) -> None:
    missions = [_strip_mongo_id(d) for d in db["missions"].find()]
    # An empty Mongo collection MUST NOT wipe an already-migrated SQLite table.
    # replace_all_* is destructive (DELETE FROM ... before INSERT), so skip it
    # entirely when the source has nothing to contribute.
    if missions:
        DataStore.replace_all_missions(missions)
    summary["missions"] = len(missions)

    redemptions = [_strip_mongo_id(d) for d in db["redemptions"].find()]
    if redemptions:
        DataStore.replace_all_redemptions(redemptions)
    summary["redemptions"] = len(redemptions)


def _migrate_app_metadata(db, summary: dict) -> None:
    count = 0
    for doc in db["app_metadata"].find():
        marker_id = doc.get("_id")
        if isinstance(marker_id, str):
            DataStore.set_app_metadata_marker(marker_id)
            count += 1
    summary["app_metadata"] = count


def _migrate_binary_assets(db, summary: dict) -> None:
    count = 0
    for doc in db["binary_assets"].find():
        payload = doc.get("payload")
        if payload is None:
            continue
        DataStore.upsert_binary_asset(
            doc["_id"],
            category=doc.get("category", "screenshot"),
            source_path=doc.get("source_path"),
            content_type=doc.get("content_type"),
            size_bytes=doc.get("size_bytes", len(bytes(payload))),
            payload=bytes(payload),
            metadata=doc.get("metadata") or {},
        )
        count += 1
    summary["binary_assets"] = count


def _migrate_locator_tracker(db, summary: dict) -> None:
    """Copy locator tracker summary rows. upsert_locator_entry is idempotent
    (keyed by ``_id``) so re-running won't duplicate.
    """
    count = 0
    for entry in db["locator_tracker"].find():
        if not isinstance(entry.get("_id"), str):
            continue  # locator entries always have a string _id; skip junk
        DataStore.upsert_locator_entry(entry)
        count += 1
    summary["locator_tracker"] = count


def _migrate_locator_failures(db, summary: dict) -> None:
    """Copy locator failure events. These use SQLite autoincrement ids so
    re-running with the same source would duplicate — TTL (7 days) cleans up.
    """
    count = 0
    for event in db["locator_tracker_failures"].find():
        DataStore.save_locator_failure_event(event)
        count += 1
    summary["locator_tracker_failures"] = count


def _archive_json_default(value):
    """JSON encoder fallback for log_lines docs (datetime fields)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _resolve_archive_dir() -> str:
    """Resolve ``output/migrations`` via resource_path, lazily."""
    # Lazy import — keep this module importable without the full backend.
    from core.GlobalVar import resource_path

    return resource_path(os.path.join("output", "migrations"), outside_path=True)


def _migrate_log_lines(db, summary: dict, archives: dict) -> None:
    """Dump Mongo log_lines to a timestamped NDJSON file under output/migrations.

    The SQLite schema has no log_lines table — application logs already live
    on disk in ``backend/logs/*.log``. This is pure archival so the Mongo
    mirror's contents survive the migration.
    """
    cursor = db["log_lines"].find()
    archive_path: str | None = None
    file_handle = None
    count = 0
    try:
        for doc in cursor:
            if file_handle is None:
                archive_dir = _resolve_archive_dir()
                os.makedirs(archive_dir, exist_ok=True)
                timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
                archive_path = os.path.join(archive_dir, f"log_lines-{timestamp}.ndjson")
                file_handle = open(archive_path, "w", encoding="utf-8")
            file_handle.write(json.dumps(doc, default=_archive_json_default))
            file_handle.write("\n")
            count += 1
    finally:
        if file_handle is not None:
            file_handle.close()

    summary["log_lines"] = count
    if archive_path is not None:
        archives["log_lines"] = archive_path


def migrate(uri: str = DEFAULT_MONGO_URI, db_name: str | None = None) -> dict:
    """Copy a local MongoDB database into the SQLite store.

    Returns a structured report:

    * ``status``   — ``"completed"`` on success or ``"no_source"`` when the
      MongoDB source isn't reachable / present (not an error — just nothing
      to do).
    * ``message``  — human-readable explanation of the status.
    * ``summary``  — dict of per-collection row counts (empty when no source).
    * ``archives`` — dict of side-effect file paths (currently ``log_lines``).
    * ``db_path``  — absolute path to the SQLite database that was written to.
    """
    db_path = get_connection_debug_info()["db_path"]
    db, source_message = _connect_or_none(uri, db_name)
    if db is None:
        return {
            "status": "no_source",
            "message": source_message,
            "summary": {},
            "archives": {},
            "db_path": db_path,
        }

    # Defence in depth: a Mongo database that is reachable but completely empty
    # would otherwise let the multi-doc migration's destructive replace_all_*
    # calls wipe an already-migrated SQLite store. Bail out before touching
    # anything when there is nothing to migrate.
    if not _source_has_any_data(db):
        return {
            "status": "no_source",
            "message": f"{source_message} — but it contains no migratable data.",
            "summary": {},
            "archives": {},
            "db_path": db_path,
        }

    DataStore.ensure_schema()
    summary: dict[str, int] = {}
    archives: dict[str, str] = {}
    _migrate_single_docs(db, summary)
    _migrate_multi_docs(db, summary)
    _migrate_app_metadata(db, summary)
    _migrate_binary_assets(db, summary)
    _migrate_locator_tracker(db, summary)
    _migrate_locator_failures(db, summary)
    _migrate_log_lines(db, summary, archives)

    return {
        "status": "completed",
        "message": source_message,
        "summary": summary,
        "archives": archives,
        "db_path": db_path,
    }


def _print_report(report: dict) -> None:
    """Render a migration report for the CLI."""
    print(f"\n{'=' * 56}")
    print("  Migrate MongoDB -> SQLite")
    print(f"{'=' * 56}\n")
    print(f"  {report['message']}")

    if report["status"] == "no_source":
        print("\nNothing migrated (no reachable MongoDB source).")
        return

    print("\nMigration summary (rows written):")
    for name, count in report["summary"].items():
        print(f"  {name:<28} {count}")
    archives = report.get("archives", {})
    if archives:
        print("\nArchived to disk (no SQLite table for these):")
        for name, path in archives.items():
            print(f"  {name:<28} {path}")
    print(f"\nSQLite database: {report['db_path']}")
    print("\nDone. MongoDB is no longer used — uninstall it whenever you like.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy a local MongoDB database into ZZZ Bot's SQLite store."
    )
    parser.add_argument(
        "--mongo-uri",
        default=DEFAULT_MONGO_URI,
        help=f"MongoDB connection URI (default: {DEFAULT_MONGO_URI})",
    )
    parser.add_argument(
        "--mongo-db",
        default=None,
        help=f"Source database name (default: first of {_candidate_db_names()})",
    )
    args = parser.parse_args()
    _print_report(migrate(uri=args.mongo_uri, db_name=args.mongo_db))


if __name__ == "__main__":
    main()
