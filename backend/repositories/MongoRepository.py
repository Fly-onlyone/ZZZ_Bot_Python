"""MongoDB repository — all ZZZ Bot collections in one place.

Single-document collections use _id="default" + find_one_and_replace upsert.
Multi-document collections (missions, redemptions) use TTL indexes for rotation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from repositories.connection import get_db

logger = logging.getLogger(__name__)

_indexed_db_identity: tuple[int, str] | None = None
APP_METADATA_COLLECTION = "app_metadata"
LOCATOR_TRACKER_FAILURES_COLLECTION = "locator_tracker_failures"
LOCATOR_TRACKER_ASSET_OWNER = "locator_tracker"
LOCATOR_TRACKER_TTL_SECONDS = 7 * 24 * 60 * 60
# Bump the schema marker when ephemeral locator diagnostics need a one-time reset.
LOCATOR_TRACKER_SCHEMA_MARKER = "locator_tracker_schema_v3"


# ============================================================================
# Internal helpers
# ============================================================================


def _ensure_indexes() -> None:
    global _indexed_db_identity

    db = get_db()
    current_identity = (id(db.client), db.name)
    if _indexed_db_identity == current_identity:
        return

    # Missions: 5-day TTL
    db.missions.create_index(
        [("indexed_at", ASCENDING)],
        expireAfterSeconds=5 * 24 * 60 * 60,
        name="missions_ttl",
    )
    # Redemptions: 30-day TTL
    db.redemptions.create_index(
        [("indexed_at", ASCENDING)],
        expireAfterSeconds=30 * 24 * 60 * 60,
        name="redemptions_ttl",
    )
    # Locator tracker: 7-day TTL
    db.locator_tracker.create_index(
        [("indexed_at", ASCENDING)],
        expireAfterSeconds=LOCATOR_TRACKER_TTL_SECONDS,
        name="locator_tracker_ttl",
    )
    db[LOCATOR_TRACKER_FAILURES_COLLECTION].create_index(
        [("indexed_at", ASCENDING)],
        expireAfterSeconds=LOCATOR_TRACKER_TTL_SECONDS,
        name="locator_tracker_failures_ttl",
    )
    db[LOCATOR_TRACKER_FAILURES_COLLECTION].create_index(
        [("summary_id", ASCENDING), ("seen_at", DESCENDING)],
        name="locator_tracker_failures_summary_seen_at",
    )
    db.binary_assets.create_index(
        [("updated_at", ASCENDING)],
        expireAfterSeconds=LOCATOR_TRACKER_TTL_SECONDS,
        partialFilterExpression={"metadata.owner": LOCATOR_TRACKER_ASSET_OWNER},
        name="locator_tracker_binary_assets_ttl",
    )

    _ensure_locator_tracker_schema(db)

    _indexed_db_identity = current_identity
    logger.debug("MongoDB TTL indexes ensured for db=%s", db.name)


def ensure_indexes() -> None:
    """Public wrapper for startup warmup and maintenance tasks."""
    _ensure_indexes()


def _ensure_locator_tracker_schema(db) -> None:
    marker = db[APP_METADATA_COLLECTION].find_one(
        {"_id": LOCATOR_TRACKER_SCHEMA_MARKER},
        {"_id": 1},
    )
    if marker:
        return

    try:
        db.locator_tracker.delete_many({})
        db[LOCATOR_TRACKER_FAILURES_COLLECTION].delete_many({})
        db.binary_assets.delete_many(
            {
                "$or": [
                    {"metadata.owner": LOCATOR_TRACKER_ASSET_OWNER},
                    {"_id": {"$regex": r"^screenshot:locator(?:_el|_dom)?_"}},
                    {"source_path": {"$regex": r"^locator(?:_el|_dom)?_"}},
                ]
            }
        )
        db[APP_METADATA_COLLECTION].find_one_and_replace(
            {"_id": LOCATOR_TRACKER_SCHEMA_MARKER},
            {"_id": LOCATOR_TRACKER_SCHEMA_MARKER, "updated_at": _now_utc()},
            upsert=True,
        )
        logger.info("locator tracker schema reset completed")
    except PyMongoError:
        logger.error("locator tracker schema reset failed", exc_info=True)
        raise


def _clean(doc: Dict) -> Dict:
    """Strip MongoDB-internal fields before returning to callers."""
    return {k: v for k, v in doc.items() if k not in ("_id", "indexed_at")}


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


# ============================================================================
# Settings
# ============================================================================


def get_settings() -> Optional[Dict]:
    doc = get_db().settings.find_one({"_id": "default"})
    result = _clean(doc) if doc else None
    logger.debug("get_settings: found=%s", result is not None)
    return result


def save_settings(data: Dict) -> None:
    clean = {k: v for k, v in data.items() if k != "_id"}
    try:
        get_db().settings.find_one_and_replace(
            {"_id": "default"}, {"_id": "default", **clean}, upsert=True
        )
        logger.info("save_settings: upserted settings document")
    except Exception:
        logger.error("save_settings: failed to upsert settings", exc_info=True)
        raise


def has_app_metadata_marker(marker_id: str) -> bool:
    doc = get_db()[APP_METADATA_COLLECTION].find_one({"_id": marker_id}, {"_id": 1})
    return doc is not None


def set_app_metadata_marker(marker_id: str) -> None:
    get_db()[APP_METADATA_COLLECTION].find_one_and_replace(
        {"_id": marker_id},
        {"_id": marker_id, "updated_at": _now_utc()},
        upsert=True,
    )


# ============================================================================
# Account
# ============================================================================


def get_account() -> Optional[Dict]:
    doc = get_db().accounts.find_one({"_id": "default"})
    result = _clean(doc) if doc else None
    logger.debug("get_account: found=%s", result is not None)
    return result


def save_account(data: Dict) -> None:
    clean = {k: v for k, v in data.items() if k != "_id"}
    try:
        get_db().accounts.find_one_and_replace(
            {"_id": "default"}, {"_id": "default", **clean}, upsert=True
        )
        logger.info("save_account: upserted account document")
    except Exception:
        logger.error("save_account: failed to upsert account", exc_info=True)
        raise


# ============================================================================
# Shopping
# ============================================================================


def get_shopping() -> Optional[Dict]:
    doc = get_db().shopping.find_one({"_id": "default"})
    result = _clean(doc) if doc else None
    logger.debug("get_shopping: found=%s", result is not None)
    return result


def save_shopping(data: Dict) -> None:
    clean = {k: v for k, v in data.items() if k != "_id"}
    try:
        get_db().shopping.find_one_and_replace(
            {"_id": "default"}, {"_id": "default", **clean}, upsert=True
        )
        logger.info("save_shopping: upserted shopping document")
    except Exception:
        logger.error("save_shopping: failed to upsert shopping", exc_info=True)
        raise


# ============================================================================
# Missions
# ============================================================================


def get_missions() -> List[Dict]:
    """Return all mission day records (TTL keeps only last 5 days)."""
    _ensure_indexes()
    results = [_clean(d) for d in get_db().missions.find()]
    logger.debug("get_missions: returned %d records", len(results))
    return results


def get_today_mission(today_str: str) -> Optional[Dict]:
    _ensure_indexes()
    doc = get_db().missions.find_one({"day": today_str})
    result = _clean(doc) if doc else None
    logger.debug("get_today_mission: day=%s found=%s", today_str, result is not None)
    return result


def save_mission_day(day_record: Dict) -> None:
    """Upsert a day's mission record; TTL index handles old-record cleanup."""
    _ensure_indexes()
    day = day_record["day"]
    record = {
        **{k: v for k, v in day_record.items() if k != "_id"},
        "indexed_at": _now_utc(),
    }
    try:
        get_db().missions.find_one_and_replace({"day": day}, record, upsert=True)
        logger.info("save_mission_day: upserted mission record for day=%s", day)
    except Exception:
        logger.error("save_mission_day: failed to upsert day=%s", day, exc_info=True)
        raise


def replace_all_missions(day_records: List[Dict]) -> None:
    """Replace the entire missions collection during backup restore."""
    _ensure_indexes()
    col = get_db().missions
    before_count = col.count_documents({})
    logger.warning(
        "replace_all_missions: deleting %d existing documents before replace",
        before_count,
    )
    try:
        # Validate mission records before clearing the collection so a malformed
        # backup does not destroy existing data first.
        records = []
        for day_record in day_records:
            day = day_record["day"]
            records.append(
                {**{k: v for k, v in day_record.items() if k != "_id"}, "day": day}
            )

        # delete_many keeps the collection + its TTL index intact
        col.delete_many({})
        if records:
            indexed_at = _now_utc()
            for record in records:
                col.find_one_and_replace(
                    {"day": record["day"]},
                    {**record, "indexed_at": indexed_at},
                    upsert=True,
                )
            logger.info(
                "replace_all_missions: restored %d documents (replaced %d)",
                len(records),
                before_count,
            )
        else:
            logger.info("replace_all_missions: cleared collection (no new entries)")
    except Exception:
        logger.error("replace_all_missions: operation failed", exc_info=True)
        raise


# ============================================================================
# Redemptions
# ============================================================================


def get_redemptions() -> List[Dict]:
    """Return all redemption records (TTL keeps only last 30 days)."""
    _ensure_indexes()
    results = [_clean(d) for d in get_db().redemptions.find()]
    logger.debug("get_redemptions: returned %d records", len(results))
    return results


def save_redemption(entry: Dict) -> None:
    """Append a single redemption entry; TTL index handles cleanup."""
    _ensure_indexes()
    record = {
        **{k: v for k, v in entry.items() if k != "_id"},
        "indexed_at": _now_utc(),
    }
    try:
        get_db().redemptions.insert_one(record)
        logger.info("save_redemption: inserted entry code=%s", entry.get("code", "?"))
    except Exception:
        logger.error("save_redemption: failed to insert entry", exc_info=True)
        raise


def replace_all_redemptions(entries: List[Dict]) -> None:
    """Replace the entire redemptions collection (used by POST /redeem)."""
    _ensure_indexes()
    col = get_db().redemptions
    before_count = col.count_documents({})
    logger.warning(
        "replace_all_redemptions: deleting %d existing documents before replace",
        before_count,
    )
    try:
        # delete_many keeps the collection + its TTL index intact
        col.delete_many({})
        if entries:
            now = _now_utc()
            records = [
                {**{k: v for k, v in e.items() if k != "_id"}, "indexed_at": now}
                for e in entries
            ]
            col.insert_many(records)
            logger.info(
                "replace_all_redemptions: inserted %d documents (replaced %d)",
                len(records),
                before_count,
            )
        else:
            logger.info("replace_all_redemptions: cleared collection (no new entries)")
    except Exception:
        logger.error("replace_all_redemptions: operation failed", exc_info=True)
        raise


# ============================================================================
# Last run
# ============================================================================


def get_last_run() -> Optional[Dict]:
    doc = get_db().last_run.find_one({"_id": "default"})
    result = _clean(doc) if doc else None
    logger.debug("get_last_run: found=%s", result is not None)
    return result


def save_last_run(data: Dict) -> None:
    clean = {k: v for k, v in data.items() if k != "_id"}
    try:
        get_db().last_run.find_one_and_replace(
            {"_id": "default"}, {"_id": "default", **clean}, upsert=True
        )
        logger.info("save_last_run: upserted last_run document")
    except Exception:
        logger.error("save_last_run: failed to upsert last_run", exc_info=True)
        raise


# ============================================================================
# Locator tracker
# ============================================================================


def upsert_locator_entry(entry: Dict) -> None:
    """Insert or replace a locator tracking entry (keyed by _id)."""
    _ensure_indexes()
    doc_id = entry["_id"]
    try:
        get_db().locator_tracker.find_one_and_replace(
            {"_id": doc_id}, {**entry, "indexed_at": _now_utc()}, upsert=True
        )
    except PyMongoError:
        logger.error("upsert_locator_entry: failed for _id=%s", doc_id, exc_info=True)


def get_locator_entries() -> List[Dict]:
    """Return all locator tracker documents."""
    _ensure_indexes()
    results = []
    for doc in get_db().locator_tracker.find().sort("last_seen", DESCENDING):
        cleaned = {k: v for k, v in doc.items() if k != "indexed_at"}
        # Expose _id as 'id' for the frontend
        cleaned["id"] = cleaned.pop("_id", None)
        results.append(cleaned)
    return results


def save_locator_failure_event(entry: Dict) -> None:
    """Append a single locator tracker failure event."""
    _ensure_indexes()
    record = {
        **{k: v for k, v in entry.items() if k != "_id"},
        "indexed_at": _now_utc(),
    }
    if "_id" in entry:
        record["_id"] = entry["_id"]
    try:
        get_db()[LOCATOR_TRACKER_FAILURES_COLLECTION].insert_one(record)
    except PyMongoError:
        logger.error(
            "save_locator_failure_event: failed to insert failure", exc_info=True
        )


def get_locator_failure_events(
    limit: int = 100,
    summary_id: str | None = None,
) -> List[Dict]:
    """Return recent locator tracker failure events."""
    _ensure_indexes()
    query = {"summary_id": summary_id} if summary_id else {}
    results = []
    cursor = (
        get_db()[LOCATOR_TRACKER_FAILURES_COLLECTION]
        .find(query)
        .sort("seen_at", DESCENDING)
        .limit(max(1, limit))
    )
    for doc in cursor:
        cleaned = {k: v for k, v in doc.items() if k != "indexed_at"}
        doc_id = cleaned.pop("_id", None)
        cleaned["id"] = str(doc_id) if doc_id is not None else None
        results.append(cleaned)
    return results


def clear_locator_entries() -> None:
    """Remove all locator tracker documents."""
    _ensure_indexes()
    get_db().locator_tracker.delete_many({})
    get_db()[LOCATOR_TRACKER_FAILURES_COLLECTION].delete_many({})
    get_db().binary_assets.delete_many({"metadata.owner": LOCATOR_TRACKER_ASSET_OWNER})
    logger.info("clear_locator_entries: collection cleared")


# ============================================================================
# Backup & Restore
# ============================================================================

_BACKUP_CONFIG_DEFAULTS: Dict[str, Any] = {"export_path": ""}

_BACKUP_VERSION = 1

# Single-document collections use their save_*() helper directly
_SINGLE_DOC_COLLECTIONS = {"settings", "account", "shopping", "last_run"}
_MULTI_DOC_COLLECTIONS = {"missions", "redemptions"}
_EPHEMERAL_COLLECTIONS = {"locator_tracker", LOCATOR_TRACKER_FAILURES_COLLECTION}
_ALL_COLLECTIONS = (
    _SINGLE_DOC_COLLECTIONS | _MULTI_DOC_COLLECTIONS | _EPHEMERAL_COLLECTIONS
)

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
    """Aggregate all collections into a single backup document."""
    return {
        "version": _BACKUP_VERSION,
        "exported_at": _now_utc().isoformat(),
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
        data: Full backup document with version and collections keys
        collections: List of collection names to restore

    Returns:
        Report dict with restored, skipped, and errors keys
    """
    report: Dict[str, Any] = {"restored": [], "skipped": [], "errors": {}}

    version = data.get("version")
    if version != _BACKUP_VERSION:
        report["errors"][
            "_version"
        ] = f"Unsupported backup version: {version} (expected {_BACKUP_VERSION})"
        return report

    source = data.get("collections", {})

    for name in collections:
        if name in _EPHEMERAL_COLLECTIONS:
            report["skipped"].append(name)
            continue

        if name not in _ALL_COLLECTIONS:
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
            logger.error(
                "import_data: failed to restore %s: %s", name, exc, exc_info=True
            )
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
    summary["missions"] = {
        "exists": len(missions) > 0,
        "count": len(missions),
    }

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
    doc = get_db().backup_config.find_one({"_id": "default"})
    if doc:
        return _clean(doc)
    return dict(_BACKUP_CONFIG_DEFAULTS)


def save_backup_config(data: Dict) -> None:
    clean = {k: v for k, v in data.items() if k != "_id"}
    merged = {**_BACKUP_CONFIG_DEFAULTS, **clean}
    get_db().backup_config.find_one_and_replace(
        {"_id": "default"}, {"_id": "default", **merged}, upsert=True
    )
    logger.info("save_backup_config: upserted backup config")
