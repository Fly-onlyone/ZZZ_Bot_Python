"""SQLite data store — every ZZZ Bot collection in one embedded database.

Replaces the former MongoDB backend. Single-document collections (settings,
account, shopping, last_run, backup_config) share a generic key-value table;
missions / redemptions / locator telemetry / binary assets get dedicated tables.

MongoDB TTL indexes have no SQLite equivalent, so rows carry an ``expires_at``
column and ``purge_expired()`` sweeps them — once at startup and, throttled,
before reads of TTL collections.

The backend is multi-threaded (uvicorn workers + scheduler + deferred-startup
thread); every public function serializes through ``connection.get_lock()``.
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from repositories.connection import get_connection, get_lock

logger = logging.getLogger(__name__)

APP_METADATA_COLLECTION = "app_metadata"
LOCATOR_TRACKER_FAILURES_COLLECTION = "locator_tracker_failures"
LOCATOR_TRACKER_ASSET_OWNER = "locator_tracker"
LOCATOR_TRACKER_TTL_SECONDS = 7 * 24 * 60 * 60
_MISSIONS_TTL_SECONDS = 5 * 24 * 60 * 60
_REDEMPTIONS_TTL_SECONDS = 30 * 24 * 60 * 60
# Bump the schema marker when ephemeral locator diagnostics need a one-time reset.
LOCATOR_TRACKER_SCHEMA_MARKER = "locator_tracker_schema_v3"
REDEMPTIONS_INDEXED_AT_REPAIR_MARKER = "redemptions_indexed_at_repair_v1"

_PURGE_INTERVAL_SECONDS = 60

_schema_ready = False
_last_purge_monotonic = 0.0


# ============================================================================
# Schema
# ============================================================================

_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    collection TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (collection, doc_id)
);

CREATE TABLE IF NOT EXISTS app_metadata (
    marker_id TEXT PRIMARY KEY,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS missions (
    day TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_missions_expires_at ON missions (expires_at);

CREATE TABLE IF NOT EXISTS redemptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_redemptions_expires_at ON redemptions (expires_at);

CREATE TABLE IF NOT EXISTS locator_tracker (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    last_seen TEXT,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_locator_tracker_expires_at ON locator_tracker (expires_at);
CREATE INDEX IF NOT EXISTS idx_locator_tracker_last_seen ON locator_tracker (last_seen DESC);

CREATE TABLE IF NOT EXISTS locator_tracker_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id TEXT,
    seen_at TEXT,
    data TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_loc_fail_summary_seen
    ON locator_tracker_failures (summary_id, seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_loc_fail_expires_at ON locator_tracker_failures (expires_at);

CREATE TABLE IF NOT EXISTS binary_assets (
    asset_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    source_path TEXT,
    content_type TEXT,
    size_bytes INTEGER,
    payload BLOB NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_binary_assets_category
    ON binary_assets (category, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_binary_assets_expires_at ON binary_assets (expires_at);
"""

# Tables whose rows carry an expires_at TTL column.
_TTL_TABLES = (
    "missions",
    "redemptions",
    "locator_tracker",
    LOCATOR_TRACKER_FAILURES_COLLECTION,
    "binary_assets",
)


def ensure_schema() -> None:
    """Create tables/indexes idempotently, reset locator schema, purge expired rows."""
    global _schema_ready

    with get_lock():
        if _schema_ready:
            return
        conn = get_connection()
        conn.executescript(_SCHEMA_DDL)
        conn.commit()
        _schema_ready = True

    # Marker helpers below see _schema_ready=True, so they will not recurse.
    _ensure_locator_tracker_schema()
    purge_expired()
    logger.debug("SQLite schema ensured")


# Back-compat alias for callers/tests that still say "ensure_indexes".
ensure_indexes = ensure_schema


def _require_schema() -> None:
    """Guarantee the schema exists before any operation (cheap after first run)."""
    if not _schema_ready:
        ensure_schema()


def _ensure_locator_tracker_schema() -> None:
    """Wipe ephemeral locator diagnostics once when the schema marker is bumped."""
    if has_app_metadata_marker(LOCATOR_TRACKER_SCHEMA_MARKER):
        return

    try:
        with get_lock():
            conn = get_connection()
            conn.execute("DELETE FROM locator_tracker")
            conn.execute(f"DELETE FROM {LOCATOR_TRACKER_FAILURES_COLLECTION}")
            conn.execute(
                "DELETE FROM binary_assets WHERE json_extract(metadata, '$.owner') = ?",
                (LOCATOR_TRACKER_ASSET_OWNER,),
            )
            conn.commit()
        set_app_metadata_marker(LOCATOR_TRACKER_SCHEMA_MARKER)
        logger.info("locator tracker schema reset completed")
    except Exception:
        logger.error("locator tracker schema reset failed", exc_info=True)
        raise


# ============================================================================
# Internal helpers
# ============================================================================


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(value: datetime) -> str:
    """Render a datetime as a fixed-width UTC ISO string (lexically sortable)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _now_iso() -> str:
    return _iso(_now_utc())


def _expires_iso(seconds: int) -> str:
    return _iso(_now_utc() + timedelta(seconds=seconds))


def _coerce_iso(value: Any) -> str | None:
    """Normalize a datetime or pre-formatted string to an ISO string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, str):
        return value
    return str(value)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return _iso(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=_json_default, ensure_ascii=False)


def _loads(text: str) -> Any:
    return json.loads(text)


def _strip_id(data: Dict) -> Dict:
    """Drop a legacy '_id' key so it never leaks into a stored payload."""
    return {k: v for k, v in data.items() if k != "_id"}


def _normalize_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_redemption_day(day_value: Any) -> datetime | None:
    if not isinstance(day_value, str):
        return None
    try:
        parsed_day = datetime.strptime(day_value, "%H:%M %d/%m/%Y")
    except ValueError:
        logger.debug("Could not parse redemption day for TTL: %s", day_value)
        return None
    return parsed_day.replace(tzinfo=timezone.utc)


def _resolve_redemption_indexed_at(entry: Dict) -> datetime:
    """Prefer the original redeem timestamp so TTL matches the visible redeem day."""
    indexed_at = _normalize_utc_datetime(entry.get("indexed_at"))
    if indexed_at is not None:
        return indexed_at

    parsed_day = _parse_redemption_day(entry.get("day"))
    if parsed_day is not None:
        return parsed_day

    return _now_utc()


# ============================================================================
# TTL purge
# ============================================================================


def purge_expired() -> None:
    """Delete rows whose expires_at has passed (MongoDB TTL-index replacement)."""
    global _last_purge_monotonic

    now = _now_iso()
    with get_lock():
        conn = get_connection()
        for table in _TTL_TABLES:
            conn.execute(
                f"DELETE FROM {table} WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
        conn.commit()
    _last_purge_monotonic = time.monotonic()


def _maybe_purge() -> None:
    """Run purge_expired() at most once per minute, before TTL-collection reads."""
    if time.monotonic() - _last_purge_monotonic < _PURGE_INTERVAL_SECONDS:
        return
    try:
        purge_expired()
    except Exception:
        logger.debug("purge_expired failed", exc_info=True)


# ============================================================================
# Single-document collections
# ============================================================================


def _get_document(collection: str) -> Optional[Dict]:
    _require_schema()
    with get_lock():
        row = (
            get_connection()
            .execute(
                "SELECT data FROM documents WHERE collection = ? AND doc_id = 'default'",
                (collection,),
            )
            .fetchone()
        )
    return _loads(row["data"]) if row else None


def _save_document(collection: str, data: Dict) -> None:
    _require_schema()
    payload = _dumps(_strip_id(data))
    with get_lock():
        conn = get_connection()
        conn.execute(
            "INSERT INTO documents (collection, doc_id, data, updated_at) "
            "VALUES (?, 'default', ?, ?) "
            "ON CONFLICT(collection, doc_id) DO UPDATE SET "
            "data = excluded.data, updated_at = excluded.updated_at",
            (collection, payload, _now_iso()),
        )
        conn.commit()


def get_settings() -> Optional[Dict]:
    result = _get_document("settings")
    logger.debug("get_settings: found=%s", result is not None)
    return result


def save_settings(data: Dict) -> None:
    _save_document("settings", data)
    logger.info("save_settings: upserted settings document")


def get_account() -> Optional[Dict]:
    result = _get_document("account")
    logger.debug("get_account: found=%s", result is not None)
    return result


def save_account(data: Dict) -> None:
    _save_document("account", data)
    logger.info("save_account: upserted account document")


def get_shopping() -> Optional[Dict]:
    result = _get_document("shopping")
    logger.debug("get_shopping: found=%s", result is not None)
    return result


def save_shopping(data: Dict) -> None:
    _save_document("shopping", data)
    logger.info("save_shopping: upserted shopping document")


def get_last_run() -> Optional[Dict]:
    result = _get_document("last_run")
    logger.debug("get_last_run: found=%s", result is not None)
    return result


def save_last_run(data: Dict) -> None:
    _save_document("last_run", data)
    logger.info("save_last_run: upserted last_run document")


# ============================================================================
# App metadata markers
# ============================================================================


def has_app_metadata_marker(marker_id: str) -> bool:
    _require_schema()
    with get_lock():
        row = (
            get_connection()
            .execute("SELECT 1 FROM app_metadata WHERE marker_id = ?", (marker_id,))
            .fetchone()
        )
    return row is not None


def set_app_metadata_marker(marker_id: str) -> None:
    _require_schema()
    with get_lock():
        conn = get_connection()
        conn.execute(
            "INSERT INTO app_metadata (marker_id, updated_at) VALUES (?, ?) "
            "ON CONFLICT(marker_id) DO UPDATE SET updated_at = excluded.updated_at",
            (marker_id, _now_iso()),
        )
        conn.commit()


# ============================================================================
# Missions
# ============================================================================


def get_missions() -> List[Dict]:
    """Return all mission day records (TTL keeps only the last 5 days)."""
    _require_schema()
    _maybe_purge()
    with get_lock():
        rows = get_connection().execute("SELECT data FROM missions").fetchall()
    results = [_loads(r["data"]) for r in rows]
    logger.debug("get_missions: returned %d records", len(results))
    return results


def get_today_mission(today_str: str) -> Optional[Dict]:
    _require_schema()
    _maybe_purge()
    with get_lock():
        row = (
            get_connection()
            .execute("SELECT data FROM missions WHERE day = ?", (today_str,))
            .fetchone()
        )
    result = _loads(row["data"]) if row else None
    logger.debug("get_today_mission: day=%s found=%s", today_str, result is not None)
    return result


def save_mission_day(day_record: Dict) -> None:
    """Upsert a day's mission record; expired days are swept by purge_expired()."""
    _require_schema()
    day = day_record["day"]
    payload = _dumps(_strip_id(day_record))
    try:
        with get_lock():
            conn = get_connection()
            conn.execute(
                "INSERT INTO missions (day, data, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(day) DO UPDATE SET "
                "data = excluded.data, expires_at = excluded.expires_at",
                (day, payload, _expires_iso(_MISSIONS_TTL_SECONDS)),
            )
            conn.commit()
        logger.info("save_mission_day: upserted mission record for day=%s", day)
    except Exception:
        logger.error("save_mission_day: failed to upsert day=%s", day, exc_info=True)
        raise


def replace_all_missions(day_records: List[Dict]) -> None:
    """Replace the entire missions table during backup restore."""
    _require_schema()
    # Validate + serialize before deleting so a malformed backup cannot destroy
    # existing data first.
    rows = [
        (
            record["day"],
            _dumps(_strip_id(record)),
            _expires_iso(_MISSIONS_TTL_SECONDS),
        )
        for record in day_records
    ]
    with get_lock():
        conn = get_connection()
        try:
            before = conn.execute("SELECT COUNT(*) FROM missions").fetchone()[0]
            logger.warning(
                "replace_all_missions: deleting %d existing records before replace",
                before,
            )
            conn.execute("DELETE FROM missions")
            if rows:
                conn.executemany(
                    "INSERT INTO missions (day, data, expires_at) VALUES (?, ?, ?)",
                    rows,
                )
            conn.commit()
            logger.info("replace_all_missions: restored %d records", len(rows))
        except Exception:
            conn.rollback()
            logger.error("replace_all_missions: operation failed", exc_info=True)
            raise


# ============================================================================
# Redemptions
# ============================================================================


def get_redemptions() -> List[Dict]:
    """Return all redemption records (TTL keeps only the last 30 days)."""
    _require_schema()
    _maybe_purge()
    with get_lock():
        rows = get_connection().execute("SELECT data FROM redemptions ORDER BY id").fetchall()
    results = [_loads(r["data"]) for r in rows]
    logger.debug("get_redemptions: returned %d records", len(results))
    return results


def save_redemption(entry: Dict) -> int:
    """Append a single redemption entry; returns the new row id."""
    _require_schema()
    indexed_at = _resolve_redemption_indexed_at(entry)
    payload = _dumps(_strip_id(entry))
    try:
        with get_lock():
            conn = get_connection()
            cursor = conn.execute(
                "INSERT INTO redemptions (data, indexed_at, expires_at) VALUES (?, ?, ?)",
                (
                    payload,
                    _iso(indexed_at),
                    _iso(indexed_at + timedelta(seconds=_REDEMPTIONS_TTL_SECONDS)),
                ),
            )
            conn.commit()
            record_id = cursor.lastrowid
        logger.info("save_redemption: inserted entry code=%s", entry.get("code", "?"))
        return record_id
    except Exception:
        logger.error("save_redemption: failed to insert entry", exc_info=True)
        raise


def update_redemption(record_id: int, entry: Dict) -> None:
    """Update an existing redemption entry without creating a duplicate row."""
    _require_schema()
    indexed_at = _resolve_redemption_indexed_at(entry)
    payload = _dumps(_strip_id(entry))
    try:
        with get_lock():
            conn = get_connection()
            cursor = conn.execute(
                "UPDATE redemptions SET data = ?, indexed_at = ?, expires_at = ? WHERE id = ?",
                (
                    payload,
                    _iso(indexed_at),
                    _iso(indexed_at + timedelta(seconds=_REDEMPTIONS_TTL_SECONDS)),
                    record_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Redemption record not found: {record_id}")
            conn.commit()
        logger.info(
            "update_redemption: updated entry id=%s code=%s",
            record_id,
            entry.get("code", "?"),
        )
    except Exception:
        logger.error("update_redemption: failed to update entry", exc_info=True)
        raise


def replace_all_redemptions(entries: List[Dict]) -> None:
    """Replace the entire redemptions table (used by POST /redeem)."""
    _require_schema()
    rows = []
    for entry in entries:
        indexed_at = _resolve_redemption_indexed_at(entry)
        rows.append(
            (
                _dumps(_strip_id(entry)),
                _iso(indexed_at),
                _iso(indexed_at + timedelta(seconds=_REDEMPTIONS_TTL_SECONDS)),
            )
        )
    with get_lock():
        conn = get_connection()
        try:
            before = conn.execute("SELECT COUNT(*) FROM redemptions").fetchone()[0]
            logger.warning(
                "replace_all_redemptions: deleting %d existing records before replace",
                before,
            )
            conn.execute("DELETE FROM redemptions")
            if rows:
                conn.executemany(
                    "INSERT INTO redemptions (data, indexed_at, expires_at) VALUES (?, ?, ?)",
                    rows,
                )
            conn.commit()
            logger.info("replace_all_redemptions: inserted %d records", len(rows))
        except Exception:
            conn.rollback()
            logger.error("replace_all_redemptions: operation failed", exc_info=True)
            raise


def repair_redemptions_indexed_at_once() -> Dict[str, int | bool]:
    """No-op on SQLite — redemption rows store indexed_at/expires_at at write time.

    Kept so startup/backup callers and tests inherited from the MongoDB backend
    continue to work; the TTL repair pass is unnecessary for a fresh database.
    """
    _require_schema()
    if not has_app_metadata_marker(REDEMPTIONS_INDEXED_AT_REPAIR_MARKER):
        set_app_metadata_marker(REDEMPTIONS_INDEXED_AT_REPAIR_MARKER)
    return {"already_applied": True, "scanned": 0, "updated": 0, "skipped": 0}


# ============================================================================
# Locator tracker
# ============================================================================


def upsert_locator_entry(entry: Dict) -> None:
    """Insert or replace a locator tracking summary row (keyed by its id)."""
    _require_schema()
    doc_id = entry["_id"]
    try:
        with get_lock():
            conn = get_connection()
            conn.execute(
                "INSERT INTO locator_tracker (id, data, last_seen, expires_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET data = excluded.data, "
                "last_seen = excluded.last_seen, expires_at = excluded.expires_at",
                (
                    doc_id,
                    _dumps(_strip_id(entry)),
                    _coerce_iso(entry.get("last_seen")),
                    _expires_iso(LOCATOR_TRACKER_TTL_SECONDS),
                ),
            )
            conn.commit()
    except Exception:
        logger.error("upsert_locator_entry: failed for id=%s", doc_id, exc_info=True)


def get_locator_entries() -> List[Dict]:
    """Return all locator tracker summary rows (newest first)."""
    _require_schema()
    _maybe_purge()
    with get_lock():
        rows = (
            get_connection()
            .execute("SELECT id, data FROM locator_tracker ORDER BY last_seen DESC")
            .fetchall()
        )
    results = []
    for row in rows:
        entry = _loads(row["data"])
        entry["id"] = row["id"]
        results.append(entry)
    return results


def get_locator_entry(summary_id: str) -> Optional[Dict]:
    """Return a single locator tracker summary row, or None."""
    _require_schema()
    with get_lock():
        row = (
            get_connection()
            .execute("SELECT id, data FROM locator_tracker WHERE id = ?", (summary_id,))
            .fetchone()
        )
    if not row:
        return None
    entry = _loads(row["data"])
    entry["id"] = row["id"]
    return entry


def get_locator_child_scan(summary_id: str) -> Optional[Dict]:
    """Return {'child_scan': [...]} for a locator summary, or None if missing."""
    entry = get_locator_entry(summary_id)
    if entry is None:
        return None
    return {"child_scan": entry.get("child_scan", [])}


def save_locator_failure_event(entry: Dict) -> None:
    """Append a single locator tracker failure event."""
    _require_schema()
    try:
        with get_lock():
            conn = get_connection()
            conn.execute(
                f"INSERT INTO {LOCATOR_TRACKER_FAILURES_COLLECTION} "
                "(summary_id, seen_at, data, expires_at) VALUES (?, ?, ?, ?)",
                (
                    entry.get("summary_id"),
                    _coerce_iso(entry.get("seen_at")),
                    _dumps(_strip_id(entry)),
                    _expires_iso(LOCATOR_TRACKER_TTL_SECONDS),
                ),
            )
            conn.commit()
    except Exception:
        logger.error("save_locator_failure_event: failed to insert failure", exc_info=True)


def get_locator_failure_events(
    limit: int = 100,
    summary_id: str | None = None,
) -> List[Dict]:
    """Return recent locator tracker failure events (newest first)."""
    _require_schema()
    _maybe_purge()
    sql = f"SELECT id, data FROM {LOCATOR_TRACKER_FAILURES_COLLECTION}"
    params: list[Any] = []
    if summary_id:
        sql += " WHERE summary_id = ?"
        params.append(summary_id)
    sql += " ORDER BY seen_at DESC, id DESC LIMIT ?"
    params.append(max(1, limit))

    with get_lock():
        rows = get_connection().execute(sql, params).fetchall()
    results = []
    for row in rows:
        entry = _loads(row["data"])
        entry["id"] = str(row["id"])
        results.append(entry)
    return results


def clear_locator_entries() -> None:
    """Remove all locator tracker rows and their captured binary assets."""
    _require_schema()
    with get_lock():
        conn = get_connection()
        conn.execute("DELETE FROM locator_tracker")
        conn.execute(f"DELETE FROM {LOCATOR_TRACKER_FAILURES_COLLECTION}")
        conn.execute(
            "DELETE FROM binary_assets WHERE json_extract(metadata, '$.owner') = ?",
            (LOCATOR_TRACKER_ASSET_OWNER,),
        )
        conn.commit()
    logger.info("clear_locator_entries: locator data cleared")


# ============================================================================
# Binary assets (screenshots, Playwright storage state)
# ============================================================================


def upsert_binary_asset(
    asset_id: str,
    *,
    category: str,
    source_path: str | None,
    content_type: str | None,
    size_bytes: int,
    payload: bytes,
    metadata: Dict | None = None,
    expires_at: str | None = None,
) -> str:
    """Insert or replace a binary asset; returns its asset id.

    Locator-tracker-owned assets expire after 7 days (replacing MongoDB's
    partial-filter TTL index); all other assets are kept indefinitely.
    """
    _require_schema()
    meta = metadata or {}
    if expires_at is None and meta.get("owner") == LOCATOR_TRACKER_ASSET_OWNER:
        expires_at = _expires_iso(LOCATOR_TRACKER_TTL_SECONDS)

    with get_lock():
        conn = get_connection()
        conn.execute(
            "INSERT INTO binary_assets (asset_id, category, source_path, "
            "content_type, size_bytes, payload, metadata, updated_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(asset_id) DO UPDATE SET category = excluded.category, "
            "source_path = excluded.source_path, content_type = excluded.content_type, "
            "size_bytes = excluded.size_bytes, payload = excluded.payload, "
            "metadata = excluded.metadata, updated_at = excluded.updated_at, "
            "expires_at = excluded.expires_at",
            (
                asset_id,
                category,
                source_path,
                content_type,
                size_bytes,
                payload,
                _dumps(meta),
                _now_iso(),
                expires_at,
            ),
        )
        conn.commit()
    return asset_id


def _row_to_asset(row: Any) -> Dict[str, Any]:
    return {
        "payload": bytes(row["payload"]),
        "content_type": row["content_type"] or "application/octet-stream",
        "metadata": _loads(row["metadata"]) if row["metadata"] else {},
        "source_path": row["source_path"],
        "category": row["category"],
    }


def get_binary_asset(asset_id: str) -> Optional[Dict[str, Any]]:
    """Load a binary asset payload + metadata by asset id."""
    _require_schema()
    _maybe_purge()
    with get_lock():
        row = (
            get_connection()
            .execute(
                "SELECT category, source_path, content_type, payload, metadata "
                "FROM binary_assets WHERE asset_id = ?",
                (asset_id,),
            )
            .fetchone()
        )
    return _row_to_asset(row) if row else None


def get_latest_binary_asset(category: str) -> Optional[Dict[str, Any]]:
    """Load the most recently updated binary asset within a category."""
    _require_schema()
    _maybe_purge()
    with get_lock():
        row = (
            get_connection()
            .execute(
                "SELECT category, source_path, content_type, payload, metadata "
                "FROM binary_assets WHERE category = ? ORDER BY updated_at DESC LIMIT 1",
                (category,),
            )
            .fetchone()
        )
    return _row_to_asset(row) if row else None


def delete_binary_asset(asset_id: str) -> None:
    _require_schema()
    with get_lock():
        conn = get_connection()
        conn.execute("DELETE FROM binary_assets WHERE asset_id = ?", (asset_id,))
        conn.commit()


# ============================================================================
# Backup & restore
# ============================================================================

_BACKUP_CONFIG_DEFAULTS: Dict[str, Any] = {"export_path": ""}
_BACKUP_VERSION = 1

_SINGLE_DOC_COLLECTIONS = {"settings", "account", "shopping", "last_run"}
_MULTI_DOC_COLLECTIONS = {"missions", "redemptions"}
_EPHEMERAL_COLLECTIONS = {"locator_tracker", LOCATOR_TRACKER_FAILURES_COLLECTION}
_ALL_COLLECTIONS = _SINGLE_DOC_COLLECTIONS | _MULTI_DOC_COLLECTIONS | _EPHEMERAL_COLLECTIONS

_SINGLE_DOC_GETTERS: Dict[str, Any] = {
    "settings": get_settings,
    "account": get_account,
    "shopping": get_shopping,
    "last_run": get_last_run,
}

_SINGLE_DOC_SAVERS: Dict[str, Any] = {
    "settings": save_settings,
    "account": save_account,
    "shopping": save_shopping,
    "last_run": save_last_run,
}


def export_all_data() -> Dict:
    """Aggregate every backed-up table into a single backup document."""
    return {
        "version": _BACKUP_VERSION,
        "exported_at": _now_iso(),
        "collections": {
            "settings": get_settings(),
            "account": get_account(),
            "shopping": get_shopping(),
            "redemptions": get_redemptions(),
            "missions": get_missions(),
            "last_run": get_last_run(),
        },
    }


def import_data(data: Dict, collections: List[str]) -> Dict:
    """Selectively restore collections from a backup document.

    Args:
        data: Full backup document with version and collections keys.
        collections: Collection names to restore.

    Returns:
        Report dict with restored, skipped, and errors keys.
    """
    report: Dict[str, Any] = {"restored": [], "skipped": [], "errors": {}}

    version = data.get("version")
    if version != _BACKUP_VERSION:
        report["errors"]["_version"] = (
            f"Unsupported backup version: {version} (expected {_BACKUP_VERSION})"
        )
        return report

    source = data.get("collections", {})

    for name in collections:
        if name in _EPHEMERAL_COLLECTIONS or name not in _ALL_COLLECTIONS:
            report["skipped"].append(name)
            continue

        collection_data = source.get(name)
        if collection_data is None:
            report["skipped"].append(name)
            continue

        try:
            if name in _SINGLE_DOC_COLLECTIONS:
                _SINGLE_DOC_SAVERS[name](collection_data)
            elif name == "missions":
                if isinstance(collection_data, list):
                    replace_all_missions(collection_data)
                else:
                    report["errors"][name] = "Expected a list of mission records"
                    continue
            elif name == "redemptions":
                if isinstance(collection_data, list):
                    replace_all_redemptions(collection_data)
                else:
                    report["errors"][name] = "Expected a list of redemption records"
                    continue

            report["restored"].append(name)
        except Exception as exc:
            logger.error("import_data: failed to restore %s: %s", name, exc, exc_info=True)
            report["errors"][name] = str(exc)

    logger.info(
        "import_data: restored=%s skipped=%s errors=%s",
        report["restored"],
        report["skipped"],
        list(report["errors"].keys()),
    )
    return report


def get_data_summary() -> Dict:
    """Return metadata about each collection for the backup summary page."""
    summary: Dict[str, Any] = {}

    for name, getter in _SINGLE_DOC_GETTERS.items():
        doc = getter()
        summary[name] = {
            "exists": doc is not None,
            "field_count": len(doc) if doc else 0,
        }

    missions = get_missions()
    summary["missions"] = {"exists": len(missions) > 0, "count": len(missions)}

    redemptions = get_redemptions()
    summary["redemptions"] = {
        "exists": len(redemptions) > 0,
        "count": len(redemptions),
    }

    return summary


# ============================================================================
# Backup config (export path)
# ============================================================================


def get_backup_config() -> Dict:
    doc = _get_document("backup_config")
    if doc:
        return {**_BACKUP_CONFIG_DEFAULTS, **doc}
    return dict(_BACKUP_CONFIG_DEFAULTS)


def save_backup_config(data: Dict) -> None:
    merged = {**_BACKUP_CONFIG_DEFAULTS, **_strip_id(data)}
    _save_document("backup_config", merged)
    logger.info("save_backup_config: upserted backup config")
