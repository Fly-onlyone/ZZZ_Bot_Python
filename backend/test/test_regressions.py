import sys
import threading
import asyncio
from importlib import import_module
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

image_processor_module = import_module("automation.ImageProcessor")
routes_module = import_module("api.routes")
from handlers import MissionHandler, ShoppingHandler
from core.frontend_env import resolve_frontend_sentry_dsn
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
        lambda self, mission_button, max_retries=5: calls.append(mission_button)
        or True,
    )

    todays_data = {}
    MissionHandler.doing_mission(1, cast(Any, FakePage()), todays_data)

    assert len(calls) == 1
    assert todays_data["missions"] == [{"name": "Daily check-in", "state": "Finished"}]


def test_handle_pop_up_marks_missing_popup_outcome_as_failed(monkeypatch):
    monkeypatch.setattr(
        MissionHandler, "handle_check_in", lambda page, todays_data: None
    )

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


def test_execute_shopping_with_existing_data_forces_reopen(monkeypatch):
    force_reopen_calls = []

    monkeypatch.setattr(
        ShoppingHandler,
        "open_shopping_screen",
        lambda page, force_reopen=False: force_reopen_calls.append(force_reopen)
        or False,
    )

    assert (
        ShoppingHandler.execute_shopping_with_existing_data(cast(Any, object()))
        is False
    )
    assert force_reopen_calls == [True]


def test_select_zzz_avatar_retries_after_detached_click(monkeypatch):
    reopen_calls = []
    clicked = {"value": 0}
    find_attempt = {"value": 0}

    def _detached_click():
        raise ShoppingHandler.PlaywrightTimeoutError(
            "Locator.click: Timeout 5000ms exceeded. element was detached from the DOM"
        )

    class FakePage:
        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    locators = [
        _FakeLocator(click_action=_detached_click),
        _FakeLocator(click_action=lambda: clicked.update(value=clicked["value"] + 1)),
    ]

    def fake_find_correct_avatar(page):
        locator = locators[min(find_attempt["value"], len(locators) - 1)]
        find_attempt["value"] += 1
        return locator

    monkeypatch.setattr(
        ShoppingHandler, "find_correct_avatar", fake_find_correct_avatar
    )
    monkeypatch.setattr(
        ShoppingHandler,
        "open_shopping_screen",
        lambda page, force_reopen=False: reopen_calls.append(force_reopen) or True,
    )

    assert ShoppingHandler.select_zzz_avatar(cast(Any, FakePage())) is True
    assert reopen_calls == [True]
    assert clicked["value"] == 1
    assert find_attempt["value"] == 2


def test_select_zzz_avatar_records_failure_after_retry_exhaustion(monkeypatch):
    reopen_calls = []
    recorded_errors = []

    def _detached_click():
        raise ShoppingHandler.PlaywrightTimeoutError(
            "Locator.click: Timeout 5000ms exceeded. element was detached from the DOM"
        )

    class FakePage:
        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(
        ShoppingHandler,
        "find_correct_avatar",
        lambda page: _FakeLocator(click_action=_detached_click),
    )
    monkeypatch.setattr(
        ShoppingHandler,
        "open_shopping_screen",
        lambda page, force_reopen=False: reopen_calls.append(force_reopen) or True,
    )
    monkeypatch.setattr(
        ShoppingHandler,
        "_record_avatar_selection_failure",
        lambda page, error: recorded_errors.append(str(error)),
    )

    assert ShoppingHandler.select_zzz_avatar(cast(Any, FakePage())) is False
    assert reopen_calls == [True, True]
    assert len(recorded_errors) == 1
    assert "Locator.click" in recorded_errors[0]


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
        "sentry_dsn": "",
        "sentry_frontend_dsn": "",
        "sentry_send_test_event": False,
        "sentry_traces_sample_rate": 1.0,
        "theme": "venom",
    }

    advanced_settings = extract_advanced_settings(full_settings)

    assert set(advanced_settings) == set(ADVANCED_SETTINGS_KEYS)
    assert "schedule_times" not in advanced_settings
    assert "theme" not in advanced_settings
    assert "autostart_on_login" not in advanced_settings


def test_resolve_frontend_sentry_dsn_prefers_runtime_env():
    dsn, source = resolve_frontend_sentry_dsn(
        {
            "VITE_SENTRY_DSN": "https://vite.example/123",
            "SENTRY_FRONTEND_DSN": "https://root.example/456",
        },
        "https://settings.example/789",
    )

    assert dsn == "https://vite.example/123"
    assert source == "env:VITE_SENTRY_DSN"


def test_resolve_frontend_sentry_dsn_falls_back_to_settings():
    dsn, source = resolve_frontend_sentry_dsn({}, "https://settings.example/789")

    assert dsn == "https://settings.example/789"
    assert source == "settings.sentry_frontend_dsn"


def test_settings_repository_uses_safe_hunt_early_exit_default(tmp_path: Path):
    repository = SettingsRepository(str(tmp_path))

    settings = repository.get_settings()

    assert settings["hunt_early_exit_on_unavailable"] is False


def test_dynamic_routes_hide_internal_action_endpoints():
    assert routes_module._is_public_route("/shopping") is True
    assert routes_module._is_public_route("/overview/mission") is True
    assert routes_module._is_public_route("/shutdown") is False
    assert routes_module._is_public_route("/tasks/run-playwright") is False
    assert routes_module._is_public_route("/maintenance/local-cleanup") is False


def test_shutdown_rejects_invalid_desktop_token(monkeypatch):
    monkeypatch.setenv("ZZZ_DESKTOP_TOKEN", "expected-token")

    class FakeRequest:
        headers = {"x-desktop-token": "wrong-token"}

        async def body(self):
            return b""

    response = asyncio.run(routes_module.shutdown(FakeRequest()))

    assert response.status_code == 401
    assert response.body == b'{"status":"rejected"}'


def test_shutdown_accepts_request_and_starts_worker(monkeypatch):
    monkeypatch.setenv("ZZZ_DESKTOP_TOKEN", "expected-token")
    started_contexts: list[dict[str, object]] = []

    class FakeRequest:
        headers = {"x-desktop-token": "expected-token"}

        async def body(self):
            return (
                b'{"source":"tauri","run_event":"exit_requested","reason":"app_run_event",'
                b'"tracked_pid":321,"shutdown_started_at":"123456"}'
            )

    monkeypatch.setattr(
        routes_module,
        "_start_shutdown_worker",
        lambda shutdown_context: started_contexts.append(dict(shutdown_context)),
    )

    response = asyncio.run(routes_module.shutdown(FakeRequest()))

    assert response.status_code == 202
    assert response.body == b'{"status":"accepted"}'
    assert started_contexts == [
        {
            "source": "tauri",
            "run_event": "exit_requested",
            "reason": "app_run_event",
            "tracked_pid": 321,
            "shutdown_started_at": "123456",
            "hosted_by_tauri": True,
            "is_exe": False,
        }
    ]


def test_perform_desktop_shutdown_flushes_sentry_before_exit():
    exit_codes: list[int] = []

    class FakeSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeTransaction:
        def __init__(self):
            self.tags: dict[str, object] = {}
            self.data: dict[str, object] = {}
            self.statuses: list[str] = []
            self.finished = False
            self.children: list[tuple[str, str]] = []

        def set_tag(self, key, value):
            self.tags[key] = value

        def set_data(self, key, value):
            self.data[key] = value

        def set_status(self, value):
            self.statuses.append(value)

        def start_child(self, *, op, description):
            self.children.append((op, description))
            return FakeSpan()

        def finish(self):
            self.finished = True

    class FakeSentry:
        def __init__(self):
            self.transaction = FakeTransaction()
            self.flush_calls: list[float] = []
            self.captured = 0

        class _Client:
            @staticmethod
            def is_active():
                return True

        def get_client(self):
            return self._Client()

        def start_transaction(self, **_kwargs):
            return self.transaction

        def flush(self, timeout):
            self.flush_calls.append(timeout)

        def capture_exception(self):
            self.captured += 1

    fake_sentry = FakeSentry()
    routes_module._perform_desktop_shutdown(
        {
            "source": "tauri",
            "run_event": "exit",
            "reason": "app_run_event",
            "tracked_pid": 444,
            "shutdown_started_at": "123456",
            "hosted_by_tauri": True,
            "is_exe": True,
        },
        sentry_sdk_module=fake_sentry,
        exit_func=lambda code: exit_codes.append(code),
        sleep_func=lambda _seconds: None,
    )

    assert fake_sentry.transaction.tags == {
        "shutdown.source": "tauri",
        "shutdown.run_event": "exit",
        "shutdown.reason": "app_run_event",
    }
    assert fake_sentry.transaction.data["tracked_pid"] == 444
    assert fake_sentry.transaction.finished is True
    assert fake_sentry.flush_calls == [
        routes_module.SHUTDOWN_SENTRY_FLUSH_TIMEOUT_SECONDS
    ]
    assert exit_codes == [0]
