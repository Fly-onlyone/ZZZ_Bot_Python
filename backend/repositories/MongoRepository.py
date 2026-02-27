"""MongoDB repository — all ZZZ Bot collections in one place.

Single-document collections use _id="default" + find_one_and_replace upsert.
Multi-document collections (missions, redemptions) use TTL indexes for rotation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pymongo import ASCENDING

from repositories.connection import get_db

logger = logging.getLogger(__name__)

_indexed_db_identity: tuple[int, str] | None = None


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

    _indexed_db_identity = current_identity
    logger.debug("MongoDB TTL indexes ensured for db=%s", db.name)


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
