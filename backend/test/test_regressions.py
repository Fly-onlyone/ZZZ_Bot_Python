import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.mission_email import schedule_mission_email_delivery
from core.settings_compat import (
    HUNT_EARLY_EXIT_RESET_MARKER,
    normalize_hunt_early_exit_default,
)
from core.settings_contract import ADVANCED_SETTINGS_KEYS, extract_advanced_settings
from repositories.DataRepository import SettingsRepository


def test_normalize_hunt_early_exit_default_resets_true_once():
    markers: set[str] = set()
    saved_payloads: list[dict] = []

    normalized = normalize_hunt_early_exit_default(
        {"hunt_early_exit_on_unavailable": True, "theme": "venom"},
        has_marker=lambda marker: marker in markers,
        set_marker=markers.add,
        save_settings=lambda payload: saved_payloads.append(dict(payload)),
    )

    assert normalized == {
        "hunt_early_exit_on_unavailable": False,
        "theme": "venom",
    }
    assert saved_payloads == [normalized]
    assert HUNT_EARLY_EXIT_RESET_MARKER in markers

    preserved = normalize_hunt_early_exit_default(
        {"hunt_early_exit_on_unavailable": True, "theme": "venom"},
        has_marker=lambda marker: marker in markers,
        set_marker=markers.add,
        save_settings=lambda payload: saved_payloads.append(dict(payload)),
    )

    assert preserved == {
        "hunt_early_exit_on_unavailable": True,
        "theme": "venom",
    }
    assert saved_payloads == [normalized]


def test_schedule_mission_email_delivery_runs_inline_for_exit_after_run():
    deliveries: list[dict] = []

    result = schedule_mission_email_delivery(
        {"day": "06/03/2026"},
        exit_after_run=True,
        send_func=lambda payload: deliveries.append(payload),
    )

    assert result is None
    assert deliveries == [{"day": "06/03/2026"}]


def test_schedule_mission_email_delivery_uses_daemon_thread_for_normal_runs():
    thread_events: list[dict[str, object]] = []

    class FakeThread(threading.Thread):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.kwargs = kwargs
            self.started = False
            thread_events.append(dict(kwargs))

        def start(self):
            self.started = True

    result = schedule_mission_email_delivery(
        {"day": "06/03/2026"},
        exit_after_run=False,
        send_func=lambda payload: None,
        thread_factory=FakeThread,
    )

    assert result is not None
    assert thread_events[0]["daemon"] is True
    assert thread_events[0]["name"] == "mission-email-sender"


def test_extract_advanced_settings_returns_only_advanced_fields():
    full_settings = {
        "schedule_times": ["08:00", "20:00"],
        "open_web_ui": True,
        "exit_after_run": False,
        "autostart_on_login": True,
        "hunt_poll_max_wait_seconds": 180,
        "hunt_poll_interval_seconds": 1,
        "hunt_poll_backoff_enabled": True,
        "hunt_early_exit_on_unavailable": False,
        "sentry_send_test_event": False,
        "sentry_traces_sample_rate": 1.0,
        "sentry_profiles_sample_rate": 1.0,
        "theme": "venom",
    }

    advanced_settings = extract_advanced_settings(full_settings)

    assert set(advanced_settings) == set(ADVANCED_SETTINGS_KEYS)
    assert "schedule_times" not in advanced_settings
    assert "theme" not in advanced_settings
    assert "autostart_on_login" not in advanced_settings


def test_settings_repository_uses_safe_hunt_early_exit_default(tmp_path: Path):
    repository = SettingsRepository(str(tmp_path))

    settings = repository.get_settings()

    assert settings["hunt_early_exit_on_unavailable"] is False
