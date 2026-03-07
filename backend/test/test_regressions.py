import sys
import threading
from importlib import import_module
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

image_processor_module = import_module("automation.ImageProcessor")
from handlers import MissionHandler, ShoppingHandler
from core.mission_email import schedule_mission_email_delivery
from core.settings_compat import (
    HUNT_EARLY_EXIT_RESET_MARKER,
    normalize_hunt_early_exit_default,
)
from core.settings_contract import ADVANCED_SETTINGS_KEYS, extract_advanced_settings
from repositories.DataRepository import SettingsRepository


class _FakeContext:
    def on(self, *_args, **_kwargs):
        return None

    def remove_listener(self, *_args, **_kwargs):
        return None


class _FakeLocator:
    def __init__(
        self,
        *,
        count=None,
        visible=None,
        click_action=None,
        text="",
        page=None,
    ):
        self._count = 1 if count is None else count
        self._visible = False if visible is None else visible
        self._click_action = click_action
        self._text = text
        self.page = page

    @property
    def first(self):
        return self

    def nth(self, _index):
        return self

    def count(self):
        return self._count() if callable(self._count) else self._count

    def is_visible(self, timeout=None):
        return self._visible() if callable(self._visible) else self._visible

    def click(self, *args, **kwargs):
        if self._click_action:
            self._click_action()

    def inner_text(self):
        return self._text() if callable(self._text) else self._text

    def wait_for(self, *args, **kwargs):
        return None

    def get_attribute(self, *_args, **_kwargs):
        return None


class _FakeShoppingButton(_FakeLocator):
    pass


def test_doing_mission_attempts_unfinished_missions(monkeypatch):
    calls = []

    class FakeImageProcessor:
        def __init__(self, page, button):
            self.page = page
            self.button = button

        def detect_button_state(self):
            return "Unfinished"

    class FakePage:
        def __init__(self):
            self.context = _FakeContext()

        def locator(self, selector):
            if ".top-ohhwaM" in selector:
                return _FakeLocator(text="Daily check-in", page=self)
            if ".icon2-Y7R3Mu" in selector:
                return _FakeLocator(page=self)
            return _FakeLocator(page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(MissionHandler, "ImageProcessor", FakeImageProcessor)
    monkeypatch.setattr(
        MissionHandler.Mission,
        "perform_mission",
        lambda self, mission_button, max_retries=5: calls.append(mission_button) or True,
    )

    todays_data = {}
    MissionHandler.doing_mission(1, cast(Any, FakePage()), todays_data)

    assert len(calls) == 1
    assert todays_data["missions"] == [{"name": "Daily check-in", "state": "Finished"}]


def test_handle_pop_up_marks_missing_popup_outcome_as_failed(monkeypatch):
    monkeypatch.setattr(MissionHandler, "handle_check_in", lambda page, todays_data: None)

    closed = {"value": False}

    class FakePopupPage:
        url = MissionHandler.CHECK_IN_URL

        def close(self):
            closed["value"] = True

    todays_data = {}
    outcome = MissionHandler.handle_pop_up(cast(Any, FakePopupPage()), todays_data)

    assert outcome == MissionHandler.POPUP_OUTCOME_FAILED
    assert todays_data["check_in"] == MissionHandler.STATUS_FAILED
    assert closed["value"] is True


def test_open_shopping_screen_resets_dialogs_before_clicking(monkeypatch):
    state = {
        "reward_open": True,
        "panel_open": True,
        "ready": False,
        "button_clicks": 0,
        "reward_closes": 0,
        "panel_closes": 0,
    }

    class FakePage:
        def locator(self, selector):
            if selector == ShoppingHandler.SHOPPING_DURATION:
                return _FakeLocator(
                    count=lambda: 1 if state["ready"] else 0,
                    visible=lambda: state["ready"],
                    page=self,
                )
            if selector == ShoppingHandler.SHOPPING_CURRENT_POINTS:
                return _FakeLocator(
                    count=lambda: 1 if state["ready"] else 0,
                    visible=lambda: state["ready"],
                    page=self,
                )
            if selector == ShoppingHandler.AVATAR_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["ready"] else 0,
                    visible=lambda: state["ready"],
                    page=self,
                )
            if selector == ShoppingHandler.SHOPPING_CLOSE_BUTTON:
                return _FakeLocator(
                    count=lambda: 1 if state["reward_open"] else 0,
                    visible=lambda: state["reward_open"],
                    click_action=lambda: state.update(
                        reward_open=False,
                        reward_closes=state["reward_closes"] + 1,
                    ),
                    page=self,
                )
            if selector == ShoppingHandler.PANEL_BACK_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["panel_open"] else 0,
                    visible=lambda: state["panel_open"],
                    click_action=lambda: state.update(
                        panel_open=False,
                        panel_closes=state["panel_closes"] + 1,
                    ),
                    page=self,
                )
            if selector == ShoppingHandler.SHOPPING_SCREEN:
                return _FakeLocator(count=0, visible=False, page=self)
            return _FakeLocator(count=0, visible=False, page=self)

        def get_by_role(self, role):
            assert role == "img"
            return _FakeShoppingButton(
                click_action=lambda: state.update(
                    ready=not state["reward_open"] and not state["panel_open"],
                    button_clicks=state["button_clicks"] + 1,
                ),
                page=self,
            )

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    assert ShoppingHandler.open_shopping_screen(cast(Any, FakePage())) is True
    assert state["reward_closes"] == 1
    assert state["panel_closes"] == 1
    assert state["button_clicks"] == 1


def test_find_correct_avatar_retries_transient_fetch_failures(monkeypatch):
    avatar_locator = _FakeLocator()
    avatar_collection = _FakeLocator(count=1)
    avatar_collection.nth = lambda _index: avatar_locator

    class FakePage:
        def locator(self, selector):
            assert selector == "div.avatarsItemImg-AiUG1h"
            return avatar_collection

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    calls = {"count": 0}

    monkeypatch.setattr(
        image_processor_module.RetryHelper, "retry_until_non_zero_count", lambda loc: 1
    )
    monkeypatch.setattr(image_processor_module.cv2, "imread", lambda path: object())

    def fake_fetch(page, locator):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("temporary image fetch failure")
        return object()

    monkeypatch.setattr(image_processor_module, "fetch_image_from_locator", fake_fetch)
    monkeypatch.setattr(image_processor_module, "compare_images", lambda a, b: 0.0)

    result = image_processor_module.find_correct_avatar(cast(Any, FakePage()))

    assert result is avatar_locator
    assert calls["count"] == 2


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
