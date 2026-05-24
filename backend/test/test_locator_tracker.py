import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

locator_tracker = import_module("automation.LocatorTracker")
from repositories import connection


def _patch_locator_store(monkeypatch, store, upserts, failure_events):
    """Wire LocatorTracker's DataStore calls to an in-memory dict."""
    monkeypatch.setattr(
        locator_tracker.DataStore,
        "get_locator_entry",
        lambda summary_id: dict(store[summary_id]) if summary_id in store else None,
    )
    monkeypatch.setattr(
        locator_tracker.DataStore,
        "upsert_locator_entry",
        lambda entry: upserts.append(dict(entry)) or store.__setitem__(entry["_id"], dict(entry)),
    )
    monkeypatch.setattr(
        locator_tracker.DataStore,
        "save_locator_failure_event",
        lambda entry: failure_events.append(dict(entry)),
    )


class _FakePage:
    def __init__(self, *, screenshot_bytes=b"page-bytes", html="<html></html>"):
        self._screenshot_bytes = screenshot_bytes
        self._html = html

    def screenshot(self, **_kwargs):
        if isinstance(self._screenshot_bytes, Exception):
            raise self._screenshot_bytes
        return self._screenshot_bytes

    def content(self):
        return self._html

    def evaluate(self, *_args, **_kwargs):
        return {"children": []}


def test_track_locator_success_updates_summary_without_capturing(monkeypatch):
    store = {}
    upserts = []
    failure_events = []

    _patch_locator_store(monkeypatch, store, upserts, failure_events)
    monkeypatch.setattr(
        locator_tracker,
        "_capture_artifacts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("success tracking should not capture artifacts")
        ),
    )

    locator_tracker.track_locator(
        page=object(),
        selector="button.launch",
        handler="MissionHandler",
        action="visibility_check",
        success=True,
    )

    assert len(upserts) == 1
    assert upserts[0]["success_count"] == 1
    assert upserts[0]["failure_count"] == 0
    assert upserts[0]["child_scan"] == []
    assert failure_events == []


def test_track_locator_failure_respects_capture_cooldown(monkeypatch):
    store = {}
    upserts = []
    failure_events = []
    capture_calls = []

    monkeypatch.setattr(locator_tracker.time, "time", lambda: 1000.0)
    locator_tracker._failure_capture_cache.clear()

    _patch_locator_store(monkeypatch, store, upserts, failure_events)
    summary_id = locator_tracker._summary_id(
        "RetryHelper",
        "wait_for",
        locator_tracker._selector_hash("button.launch"),
    )

    def _fake_capture(*_args, **_kwargs):
        capture_calls.append("captured")
        locator_tracker._failure_capture_cache[summary_id] = 1000.0
        return {
            "page_asset_id": "page-asset",
            "locator_asset_id": "locator-asset",
            "dom_snapshot_asset_id": "dom-asset",
            "child_scan": [{"asset_id": "child-asset"}],
        }

    monkeypatch.setattr(locator_tracker, "_capture_artifacts", _fake_capture)

    for _ in range(2):
        locator_tracker.track_locator(
            page=object(),
            selector="button.launch",
            handler="RetryHelper",
            action="wait_for",
            success=False,
            error_message="timeout",
        )

    assert capture_calls == ["captured"]
    assert len(failure_events) == 2
    assert failure_events[0]["page_asset_id"] == "page-asset"
    assert failure_events[1]["page_asset_id"] is None
    assert upserts[-1]["failure_count"] == 2
    assert upserts[-1]["page_asset_id"] == "page-asset"


def test_clear_entries_resets_failure_capture_cache(monkeypatch):
    cleared = []
    locator_tracker._failure_capture_cache["locator:test"] = 123.0

    monkeypatch.setattr(
        locator_tracker.DataStore,
        "clear_locator_entries",
        lambda: cleared.append(True),
    )

    locator_tracker.clear_entries()

    assert locator_tracker._failure_capture_cache == {}
    assert cleared == [True]


def test_capture_artifacts_only_arms_failure_cooldown_when_asset_saved(monkeypatch):
    locator_tracker._failure_capture_cache.clear()
    monkeypatch.setattr(locator_tracker.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        locator_tracker,
        "save_screenshot_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("save failed")),
    )

    artifacts = locator_tracker._capture_artifacts(
        _FakePage(screenshot_bytes=RuntimeError("shot failed")),
        "abcd1234",
        "locator:test",
        "RetryHelper",
        "wait_for",
        "failure",
        None,
    )

    assert artifacts["page_asset_id"] is None
    assert artifacts["dom_snapshot_asset_id"] is None
    assert artifacts["child_scan"] == []
    assert locator_tracker._failure_capture_cache == {}


def test_track_locator_recovery_capture_preserves_previous_failure_context(
    monkeypatch,
):
    summary_id = locator_tracker._summary_id(
        "RetryHelper",
        "wait_for",
        locator_tracker._selector_hash("button.launch"),
    )
    existing_entry = {
        "_id": summary_id,
        "last_success": False,
        "hit_count": 2,
        "success_count": 0,
        "failure_count": 2,
        "first_seen": datetime(2026, 3, 31, tzinfo=timezone.utc).isoformat(),
        "page_asset_id": "page-failure",
        "locator_asset_id": "locator-failure",
        "dom_snapshot_asset_id": "dom-failure",
        "child_scan": [{"asset_id": "child-failure"}],
    }
    store = {summary_id: dict(existing_entry)}
    upserts = []

    _patch_locator_store(monkeypatch, store, upserts, [])
    monkeypatch.setattr(
        locator_tracker.DataStore,
        "save_locator_failure_event",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("recovery success should not write failure history")
        ),
    )

    def _fake_capture(*_args, **_kwargs):
        return {
            "page_asset_id": None,
            "locator_asset_id": "locator-recovery",
            "dom_snapshot_asset_id": None,
            "child_scan": [],
        }

    monkeypatch.setattr(locator_tracker, "_capture_artifacts", _fake_capture)

    locator_tracker.track_locator(
        page=object(),
        selector="button.launch",
        handler="RetryHelper",
        action="wait_for",
        success=True,
    )

    assert upserts[-1]["last_capture_mode"] == "recovery"
    assert upserts[-1]["locator_asset_id"] == "locator-recovery"
    assert upserts[-1]["page_asset_id"] == "page-failure"
    assert upserts[-1]["dom_snapshot_asset_id"] == "dom-failure"
    assert upserts[-1]["child_scan"] == [{"asset_id": "child-failure"}]
    assert upserts[-1]["success_count"] == 1
    assert upserts[-1]["failure_count"] == 2


def test_recovery_capture_clears_failure_cooldown(monkeypatch):
    locator_tracker._failure_capture_cache.clear()
    locator_tracker._failure_capture_cache["locator:test"] = 1000.0
    monkeypatch.setattr(
        locator_tracker,
        "save_screenshot_bytes",
        lambda *_args, **_kwargs: "page-asset",
    )

    artifacts = locator_tracker._capture_artifacts(
        _FakePage(),
        "abcd1234",
        "locator:test",
        "RetryHelper",
        "wait_for",
        "recovery",
        None,
    )

    assert artifacts["page_asset_id"] is not None
    assert artifacts["dom_snapshot_asset_id"] is None
    assert locator_tracker._failure_capture_cache == {}


def test_locator_tracker_schema_reset_clears_existing_diagnostics(sqlite_db):
    # Simulate diagnostics left over from a previous schema version.
    sqlite_db.upsert_locator_entry({"_id": "locator:test", "selector": "button.x"})
    sqlite_db.save_locator_failure_event(
        {"summary_id": "locator:test", "seen_at": None, "error_message": "boom"}
    )
    conn = connection.get_connection()
    conn.execute(
        "DELETE FROM app_metadata WHERE marker_id = ?",
        (sqlite_db.LOCATOR_TRACKER_SCHEMA_MARKER,),
    )
    conn.commit()

    sqlite_db._ensure_locator_tracker_schema()

    assert sqlite_db.get_locator_entries() == []
    assert sqlite_db.get_locator_failure_events() == []
    assert sqlite_db.has_app_metadata_marker(sqlite_db.LOCATOR_TRACKER_SCHEMA_MARKER)
