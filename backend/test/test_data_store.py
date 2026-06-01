"""Tests for the SQLite-backed DataStore."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from repositories import connection


def test_ensure_schema_is_idempotent(sqlite_db):
    sqlite_db.ensure_schema()
    sqlite_db.ensure_schema()

    assert sqlite_db.get_missions() == []
    assert sqlite_db.get_redemptions() == []


def test_single_doc_round_trip_strips_legacy_id(sqlite_db):
    assert sqlite_db.get_settings() is None

    sqlite_db.save_settings({"theme": "cyber", "_id": "default"})

    assert sqlite_db.get_settings() == {"theme": "cyber"}


def test_save_redemption_returns_int_id_and_updates(sqlite_db):
    record_id = sqlite_db.save_redemption(
        {"code": "ABC", "day": "10:00 01/01/2026", "state": False}
    )
    assert isinstance(record_id, int)

    sqlite_db.update_redemption(
        record_id, {"code": "ABC", "day": "10:00 01/01/2026", "state": True}
    )

    assert sqlite_db.get_redemptions() == [
        {"code": "ABC", "day": "10:00 01/01/2026", "state": True}
    ]


def test_update_redemption_raises_for_missing_id(sqlite_db):
    with pytest.raises(ValueError):
        sqlite_db.update_redemption(9999, {"code": "X"})


def test_purge_expired_removes_stale_rows(sqlite_db):
    sqlite_db.save_mission_day({"day": "old-day", "missions": []})
    sqlite_db.save_mission_day({"day": "fresh-day", "missions": []})

    conn = connection.get_connection()
    conn.execute(
        "UPDATE missions SET expires_at = ? WHERE day = ?",
        ("2000-01-01T00:00:00.000000+00:00", "old-day"),
    )
    conn.commit()

    sqlite_db.purge_expired()

    assert {m["day"] for m in sqlite_db.get_missions()} == {"fresh-day"}


def test_binary_asset_round_trip(sqlite_db):
    sqlite_db.upsert_binary_asset(
        "screenshot:test.png",
        category="screenshot",
        source_path="test.png",
        content_type="image/png",
        size_bytes=3,
        payload=b"abc",
        metadata={"full_page": True},
    )

    asset = sqlite_db.get_binary_asset("screenshot:test.png")

    assert asset["payload"] == b"abc"
    assert asset["content_type"] == "image/png"
    assert asset["metadata"] == {"full_page": True}
    assert sqlite_db.get_binary_asset("screenshot:missing.png") is None


def test_locator_owned_binary_asset_gets_expiry(sqlite_db):
    sqlite_db.upsert_binary_asset(
        "screenshot:loc.png",
        category="screenshot",
        source_path="loc.png",
        content_type="image/png",
        size_bytes=1,
        payload=b"x",
        metadata={"owner": sqlite_db.LOCATOR_TRACKER_ASSET_OWNER},
    )
    sqlite_db.upsert_binary_asset(
        "storage_state:hoyo.json",
        category="storage_state",
        source_path="hoyo.json",
        content_type="application/json",
        size_bytes=1,
        payload=b"y",
        metadata={},
    )

    conn = connection.get_connection()
    expiries = dict(conn.execute("SELECT asset_id, expires_at FROM binary_assets").fetchall())

    assert expiries["screenshot:loc.png"] is not None
    assert expiries["storage_state:hoyo.json"] is None


def test_screenshot_asset_gets_default_expiry_without_owner(sqlite_db):
    # Untracked screenshots (e.g. event-page auth captures) must still expire so they
    # cannot bloat the database; storage-state assets must never expire.
    sqlite_db.upsert_binary_asset(
        "screenshot:event_page_auth_required_x.png",
        category="screenshot",
        source_path="event_page_auth_required_x.png",
        content_type="image/png",
        size_bytes=1,
        payload=b"x",
        metadata={},
    )
    sqlite_db.upsert_binary_asset(
        "storage_state:hoyo.json",
        category="storage_state",
        source_path="hoyo.json",
        content_type="application/json",
        size_bytes=1,
        payload=b"y",
        metadata={},
    )

    conn = connection.get_connection()
    expiries = dict(conn.execute("SELECT asset_id, expires_at FROM binary_assets").fetchall())

    assert expiries["screenshot:event_page_auth_required_x.png"] is not None
    assert expiries["storage_state:hoyo.json"] is None


def test_compact_database_purges_and_returns_report(sqlite_db):
    sqlite_db.upsert_binary_asset(
        "screenshot:stale.png",
        category="screenshot",
        source_path="stale.png",
        content_type="image/png",
        size_bytes=3,
        payload=b"abc",
        metadata={},
    )
    conn = connection.get_connection()
    conn.execute(
        "UPDATE binary_assets SET expires_at = ? WHERE asset_id = ?",
        ("2000-01-01T00:00:00.000000+00:00", "screenshot:stale.png"),
    )
    conn.commit()

    report = sqlite_db.compact_database()

    assert set(report) == {"size_before", "size_after", "reclaimed_bytes"}
    assert report["reclaimed_bytes"] >= 0
    assert sqlite_db.get_binary_asset("screenshot:stale.png") is None


def test_get_latest_binary_asset_filters_by_category(sqlite_db):
    sqlite_db.upsert_binary_asset(
        "storage_state:hoyo.json",
        category="storage_state",
        source_path="hoyo.json",
        content_type="application/json",
        size_bytes=1,
        payload=b"state",
        metadata={},
    )

    latest = sqlite_db.get_latest_binary_asset("storage_state")

    assert latest is not None
    assert latest["category"] == "storage_state"
    assert latest["payload"] == b"state"
    assert sqlite_db.get_latest_binary_asset("nonexistent") is None


def test_export_and_import_round_trip(sqlite_db):
    sqlite_db.save_settings({"theme": "venom"})
    sqlite_db.save_mission_day({"day": "d1", "missions": [{"name": "Check-in"}]})

    backup = sqlite_db.export_all_data()
    assert backup["version"] == 1

    sqlite_db.save_settings({"theme": "nebula"})
    report = sqlite_db.import_data(backup, ["settings", "missions"])

    assert set(report["restored"]) == {"settings", "missions"}
    assert sqlite_db.get_settings() == {"theme": "venom"}
    assert sqlite_db.get_missions() == [{"day": "d1", "missions": [{"name": "Check-in"}]}]


def test_locator_failure_events_filter_by_summary(sqlite_db):
    sqlite_db.save_locator_failure_event(
        {"summary_id": "locator:a", "seen_at": "2026-01-01T00:00:00+00:00"}
    )
    sqlite_db.save_locator_failure_event(
        {"summary_id": "locator:b", "seen_at": "2026-01-02T00:00:00+00:00"}
    )

    only_a = sqlite_db.get_locator_failure_events(summary_id="locator:a")

    assert len(only_a) == 1
    assert only_a[0]["summary_id"] == "locator:a"
    assert len(sqlite_db.get_locator_failure_events()) == 2
