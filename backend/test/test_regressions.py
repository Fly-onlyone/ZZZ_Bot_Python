import asyncio
import json
import logging
import sys
import threading
from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from playwright.sync_api import Error as PlaywrightError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

image_processor_module = import_module("automation.ImageProcessor")
redeem_autofill_module = import_module("automation.RedeemAutofill")
routes_module = import_module("api.routes")
bot_module = import_module("Bot")
data_store_module = import_module("repositories.DataStore")
global_var_module = import_module("core.GlobalVar")
from automation import EventNavigator
from core.frontend_env import resolve_frontend_sentry_dsn
from core.mission_email import schedule_mission_email_delivery
from core.settings_contract import ADVANCED_SETTINGS_KEYS, extract_advanced_settings
from handlers import DrawHandler, HuntModeHandler, MissionHandler, ShoppingHandler
from repositories.DataRepository import SettingsRepository
from utils.Logger import StreamToLogger


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

    def filter(self, **_kwargs):
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
                visible=True,
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


def test_close_open_panel_returns_false_when_back_button_click_races():
    class FakePage:
        def locator(self, selector):
            if selector == ShoppingHandler.PANEL_BACK_SELECTOR:
                return _FakeLocator(
                    count=1,
                    visible=True,
                    click_action=lambda: (_ for _ in ()).throw(RuntimeError("detached")),
                    page=self,
                )
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    assert ShoppingHandler._close_open_panel(cast(Any, FakePage())) is False


def test_close_open_panel_returns_false_when_back_button_stays_visible():
    class FakePage:
        def locator(self, selector):
            if selector == ShoppingHandler.PANEL_BACK_SELECTOR:
                return _FakeLocator(
                    count=1,
                    visible=True,
                    click_action=lambda: None,
                    page=self,
                )
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    assert ShoppingHandler._close_open_panel(cast(Any, FakePage())) is False


def test_event_navigator_open_panel_uses_fresh_candidates_until_ready():
    state = {"launcher_clicks": 0, "panel_open": False}

    class FakePage:
        def locator(self, selector):
            if selector == "launcher":
                return _FakeLocator(
                    count=1,
                    visible=True,
                    click_action=lambda: state.update(
                        launcher_clicks=state["launcher_clicks"] + 1,
                        panel_open=True,
                    ),
                    page=self,
                )
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    page = FakePage()

    result = EventNavigator.open_panel(
        cast(Any, page),
        panel_name="test panel",
        ready_predicate=lambda: state["panel_open"],
        candidates=(("launcher", lambda: page.locator("launcher")),),
        max_attempts=2,
    )

    assert result.opened is True
    assert result.candidate_name == "launcher"
    assert state["launcher_clicks"] == 1


def test_close_shopping_screen_helper_ignores_stale_wrapper_visibility(monkeypatch):
    class FakePage:
        class _Keyboard:
            @staticmethod
            def press(_key):
                return None

        keyboard = _Keyboard()

        def locator(self, selector):
            if selector == ".wrapper-O3T67n":
                return _FakeLocator(count=1, visible=True, page=self)
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(
        EventNavigator,
        "close_reward_dialog",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        EventNavigator,
        "close_panel_back",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(ShoppingHandler, "_shopping_ready", lambda page: False)

    assert bot_module._close_shopping_screen_helper(cast(Any, FakePage())) is True


def test_execute_shopping_with_existing_data_forces_reopen(monkeypatch):
    force_reopen_calls = []

    monkeypatch.setattr(
        ShoppingHandler,
        "open_shopping_screen",
        lambda page, force_reopen=False: force_reopen_calls.append(force_reopen) or False,
    )

    assert ShoppingHandler.execute_shopping_with_existing_data(cast(Any, object())) is False
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

    monkeypatch.setattr(ShoppingHandler, "find_correct_avatar", fake_find_correct_avatar)
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


def test_fetch_image_from_locator_uses_screenshot_fallback_when_url_missing(
    monkeypatch,
):
    class FakePage:
        url = "https://example.com/"

    class FakeLocator:
        def get_attribute(self, *_args, **_kwargs):
            return None

        def evaluate(self, *_args, **_kwargs):
            return "none"

        def locator(self, *_args, **_kwargs):
            return _FakeLocator(count=0)

        def screenshot(self):
            return b"fake-png-bytes"

    monkeypatch.setattr(
        image_processor_module.cv2,
        "imdecode",
        lambda arr, _flag: object() if arr.tobytes() == b"fake-png-bytes" else None,
    )

    result = image_processor_module.fetch_image_from_locator(
        cast(Any, FakePage()), cast(Any, FakeLocator())
    )

    assert result is not None


def test_run_hunt_skips_mismatched_target_date_without_backend_import(caplog):
    caplog.set_level(logging.INFO)
    HuntModeHandler.set_hunt_target_date(datetime.now() + timedelta(days=1))

    try:
        HuntModeHandler.run_hunt()
    finally:
        HuntModeHandler.set_hunt_target_date(None)

    assert "Skipping until correct date." in caplog.text


def test_open_event_page_retries_until_navigation_succeeds(monkeypatch):
    class FakePage:
        def __init__(self):
            self.goto_calls: list[dict[str, object]] = []
            self.waits: list[int] = []

        def goto(self, url, **kwargs):
            self.goto_calls.append({"url": url, **kwargs})
            if len(self.goto_calls) < 3:
                raise PlaywrightError("temporary timeout")

        def wait_for_timeout(self, timeout):
            self.waits.append(timeout)

    monkeypatch.setattr(
        "automation.EventNavigator.save_page_screenshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("screenshot should not be saved on eventual success")
        ),
    )

    page = FakePage()
    EventNavigator.open_event_page(
        cast(Any, page),
        url="https://example.invalid/event",
        timeout=12345,
        max_attempts=3,
        retry_wait_ms=321,
        wait_until="domcontentloaded",
    )

    assert len(page.goto_calls) == 3
    assert all(call["wait_until"] == "domcontentloaded" for call in page.goto_calls)
    assert all(call["timeout"] == 12345 for call in page.goto_calls)
    assert page.waits == [321, 321]


def test_open_event_page_captures_diagnostics_after_final_failure(monkeypatch, caplog):
    class _NullScope:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePage:
        def __init__(self):
            self.waits: list[int] = []

        def goto(self, *_args, **_kwargs):
            raise PlaywrightError("navigation stayed too slow")

        def wait_for_timeout(self, timeout):
            self.waits.append(timeout)

    screenshots: list[str] = []
    sentry_tags: list[tuple[str, str]] = []
    sentry_contexts: list[tuple[str, dict[str, object]]] = []
    captured_errors: list[str] = []

    monkeypatch.setattr(
        "automation.EventNavigator.save_page_screenshot",
        lambda *_args, **_kwargs: screenshots.append("saved") or "screenshot:event",
    )
    monkeypatch.setattr("sentry_sdk.isolation_scope", lambda: _NullScope())
    monkeypatch.setattr("sentry_sdk.set_tag", lambda key, value: sentry_tags.append((key, value)))
    monkeypatch.setattr(
        "sentry_sdk.set_context",
        lambda key, value: sentry_contexts.append((key, value)),
    )
    monkeypatch.setattr(
        "sentry_sdk.capture_exception",
        lambda exc: captured_errors.append(str(exc)),
    )

    caplog.set_level(logging.ERROR, logger="automation.EventNavigator")
    page = FakePage()

    try:
        EventNavigator.open_event_page(
            cast(Any, page),
            url="https://example.invalid/event",
            timeout=222,
            max_attempts=2,
            retry_wait_ms=111,
            wait_until="domcontentloaded",
        )
        raise AssertionError("Expected navigation failure")
    except PlaywrightError as exc:
        assert str(exc) == "navigation stayed too slow"

    assert page.waits == [111]
    assert screenshots == ["saved"]
    assert ("event_page.issue", "navigation_failed") in sentry_tags
    assert ("event_page.attempts", "2") in sentry_tags
    assert sentry_contexts[0][0] == "event_page_navigation"
    assert sentry_contexts[0][1]["screenshot_asset_id"] == "screenshot:event"
    assert captured_errors == ["navigation stayed too slow"]
    assert any(
        "Failed to open HoYoLab event page after 2 attempts" in record.message
        for record in caplog.records
    )


def test_wait_for_authenticated_event_home_returns_ready_without_login_prompt(
    monkeypatch,
):
    class FakePage:
        url = "https://example.invalid/event"

        def __init__(self):
            self.waits: list[int] = []

        def get_by_role(self, role, name=None):
            if role == "link" and name == "Log In":
                return _FakeLocator(visible=False, page=self)
            if role == "button" and name == "Log In":
                return _FakeLocator(visible=False, page=self)
            if role == "img":
                return _FakeLocator(count=2, page=self)
            raise AssertionError(f"unexpected role lookup: {(role, name)}")

        def get_by_text(self, text, exact=False):
            assert "Carry out missions to earn" in text
            return _FakeLocator(visible=True, page=self)

        def locator(self, selector):
            if selector == "#hyv-account-frame":
                return _FakeLocator(visible=False, page=self)
            raise AssertionError(f"unexpected selector lookup: {selector}")

        def wait_for_timeout(self, timeout):
            self.waits.append(timeout)

    monkeypatch.setattr(
        "automation.EventNavigator.save_page_screenshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("screenshot should not be captured when page is ready")
        ),
    )

    result = EventNavigator.wait_for_authenticated_event_home(
        cast(Any, FakePage()),
        context="starting automation",
        timeout_ms=1000,
        poll_interval_ms=200,
    )

    assert result == EventNavigator.EventPageAuthResult(
        ready=True,
        auth_required=False,
        reason="event_home_ready",
        screenshot_asset_id=None,
    )


def test_wait_for_authenticated_event_home_reports_manual_login(monkeypatch):
    class _NullScope:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePage:
        url = "https://example.invalid/event"

        def get_by_role(self, role, name=None):
            if role == "link" and name == "Log In":
                return _FakeLocator(visible=True, page=self)
            if role == "button" and name == "Log In":
                return _FakeLocator(visible=False, page=self)
            if role == "img":
                return _FakeLocator(count=2, page=self)
            raise AssertionError(f"unexpected role lookup: {(role, name)}")

        def get_by_text(self, text, exact=False):
            assert "Carry out missions to earn" in text
            return _FakeLocator(visible=True, page=self)

        def locator(self, selector):
            if selector == "#hyv-account-frame":
                return _FakeLocator(visible=False, page=self)
            raise AssertionError(f"unexpected selector lookup: {selector}")

        def wait_for_timeout(self, _timeout):
            raise AssertionError("auth failure should not poll once login is visible")

    sentry_tags: list[tuple[str, str]] = []
    sentry_contexts: list[tuple[str, dict[str, object]]] = []
    sentry_messages: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        "automation.EventNavigator.save_page_screenshot",
        lambda *_args, **_kwargs: "screenshot:event_auth",
    )
    monkeypatch.setattr("sentry_sdk.isolation_scope", lambda: _NullScope())
    monkeypatch.setattr("sentry_sdk.set_tag", lambda key, value: sentry_tags.append((key, value)))
    monkeypatch.setattr(
        "sentry_sdk.set_context",
        lambda key, value: sentry_contexts.append((key, value)),
    )
    monkeypatch.setattr(
        "sentry_sdk.capture_message",
        lambda message, level=None: sentry_messages.append((message, level)),
    )

    result = EventNavigator.wait_for_authenticated_event_home(
        cast(Any, FakePage()),
        context="starting automation",
        timeout_ms=1000,
        poll_interval_ms=200,
    )

    assert result == EventNavigator.EventPageAuthResult(
        ready=False,
        auth_required=True,
        reason="login_prompt_visible",
        screenshot_asset_id="screenshot:event_auth",
    )
    assert ("event_page.issue", "manual_login_required") in sentry_tags
    assert ("event_page.auth_required", "true") in sentry_tags
    assert ("event_page.reason", "login_prompt_visible") in sentry_tags
    assert sentry_contexts[0][0] == "event_page_auth"
    assert sentry_contexts[0][1]["screenshot_asset_id"] == "screenshot:event_auth"
    assert sentry_messages == [("Event page requires manual login", "warning")]


def test_wait_for_authenticated_event_home_times_out_when_home_never_stabilizes(
    monkeypatch,
):
    class _NullScope:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePage:
        url = "https://example.invalid/event"

        def __init__(self):
            self.waits: list[int] = []

        def get_by_role(self, role, name=None):
            if role == "link" and name == "Log In":
                return _FakeLocator(visible=False, page=self)
            if role == "button" and name == "Log In":
                return _FakeLocator(visible=False, page=self)
            if role == "img":
                return _FakeLocator(count=0, page=self)
            raise AssertionError(f"unexpected role lookup: {(role, name)}")

        def get_by_text(self, text, exact=False):
            assert "Carry out missions to earn" in text
            return _FakeLocator(visible=False, page=self)

        def locator(self, selector):
            if selector == "#hyv-account-frame":
                return _FakeLocator(visible=False, page=self)
            raise AssertionError(f"unexpected selector lookup: {selector}")

        def wait_for_timeout(self, timeout):
            self.waits.append(timeout)

    monkeypatch.setattr(
        "automation.EventNavigator.save_page_screenshot",
        lambda *_args, **_kwargs: "screenshot:event_timeout",
    )
    monkeypatch.setattr("sentry_sdk.isolation_scope", lambda: _NullScope())
    monkeypatch.setattr("sentry_sdk.set_tag", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("sentry_sdk.set_context", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("sentry_sdk.capture_message", lambda *_args, **_kwargs: None)

    page = FakePage()
    result = EventNavigator.wait_for_authenticated_event_home(
        cast(Any, page),
        context="starting automation",
        timeout_ms=600,
        poll_interval_ms=200,
    )

    assert result == EventNavigator.EventPageAuthResult(
        ready=False,
        auth_required=True,
        reason="event_home_not_ready",
        screenshot_asset_id="screenshot:event_timeout",
    )
    assert page.waits == [200, 200, 200]


def test_playwright_task_uses_shared_event_navigation(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePage:
        pass

    class FakeContext:
        def new_page(self):
            return FakePage()

    class FakeBrowser:
        def new_context(self, **_kwargs):
            return FakeContext()

        def close(self):
            return None

    class FakePlaywright:
        def __init__(self):
            self.firefox = self

        def launch(self, **_kwargs):
            return FakeBrowser()

    class FakePlaywrightContext:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    event_pages: list[object] = []
    mission_calls: list[tuple[object, object, object, object]] = []
    notifications: list[dict[str, object]] = []

    monkeypatch.setattr(bot_module.settings, "run_task", True)
    monkeypatch.setattr(bot_module.settings, "gather_shopping_data", False)
    monkeypatch.setattr(bot_module.settings, "exchange_good", False)
    monkeypatch.setattr(bot_module.settings, "draw_item", False)
    monkeypatch.setattr(bot_module.settings, "exit_after_run", False)
    monkeypatch.setattr(bot_module, "is_exe", True)
    monkeypatch.setattr(bot_module, "prepare_mission_data", lambda *_args, **_kwargs: ({}, {}))
    monkeypatch.setattr(bot_module, "sync_playwright", lambda: FakePlaywrightContext())
    monkeypatch.setattr(
        bot_module.EventNavigator,
        "open_event_page",
        lambda page: event_pages.append(page),
    )
    monkeypatch.setattr(
        bot_module.EventNavigator,
        "wait_for_authenticated_event_home",
        lambda *_args, **_kwargs: EventNavigator.EventPageAuthResult(
            ready=True,
            auth_required=False,
            reason="event_home_ready",
        ),
    )
    monkeypatch.setattr(
        bot_module.Mission,
        "run",
        lambda output_file, page, previous_data, todays_data: (
            mission_calls.append((output_file, page, previous_data, todays_data)) or False
        ),
    )
    monkeypatch.setattr(bot_module, "save_last_run", lambda: None)
    monkeypatch.setattr(bot_module, "save_context_storage_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        bot_module.NotificationModule,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(bot_module, "schedule_mission_email_delivery", lambda *args, **kwargs: None)
    monkeypatch.setattr("sentry_sdk.start_transaction", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())

    bot_module.playwright_task()

    assert len(event_pages) == 1
    assert len(mission_calls) == 1
    assert mission_calls[0][1] is event_pages[0]
    assert notifications[-1]["message"] == "Task finished"


def test_playwright_task_aborts_when_event_page_requires_manual_login(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePage:
        pass

    class FakeContext:
        def new_page(self):
            return FakePage()

    class FakeBrowser:
        def new_context(self, **_kwargs):
            return FakeContext()

        def close(self):
            return None

    class FakePlaywright:
        def __init__(self):
            self.firefox = self

        def launch(self, **_kwargs):
            return FakeBrowser()

    class FakePlaywrightContext:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    notifications: list[dict[str, object]] = []
    saved_states: list[bool] = []

    monkeypatch.setattr(bot_module.settings, "run_task", True)
    monkeypatch.setattr(bot_module.settings, "gather_shopping_data", False)
    monkeypatch.setattr(bot_module.settings, "exchange_good", False)
    monkeypatch.setattr(bot_module.settings, "draw_item", False)
    monkeypatch.setattr(bot_module.settings, "exit_after_run", False)
    monkeypatch.setattr(bot_module, "is_exe", True)
    monkeypatch.setattr(bot_module, "prepare_mission_data", lambda *_args, **_kwargs: ({}, {}))
    monkeypatch.setattr(bot_module, "sync_playwright", lambda: FakePlaywrightContext())
    monkeypatch.setattr(bot_module.EventNavigator, "open_event_page", lambda _page: None)
    monkeypatch.setattr(
        bot_module.EventNavigator,
        "wait_for_authenticated_event_home",
        lambda *_args, **_kwargs: EventNavigator.EventPageAuthResult(
            ready=False,
            auth_required=True,
            reason="login_prompt_visible",
            screenshot_asset_id="screenshot:event_auth",
        ),
    )
    monkeypatch.setattr(
        bot_module.Mission,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("mission should not run when event-page auth fails")
        ),
    )
    monkeypatch.setattr(bot_module, "save_last_run", lambda: None)
    monkeypatch.setattr(
        bot_module,
        "save_context_storage_state",
        lambda *_args, **_kwargs: saved_states.append(True),
    )
    monkeypatch.setattr(
        bot_module.NotificationModule,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(bot_module, "schedule_mission_email_delivery", lambda *args, **kwargs: None)
    monkeypatch.setattr("sentry_sdk.start_transaction", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())

    bot_module.playwright_task()

    assert notifications == [
        {
            "title": "ZZZ Bot",
            "message": "Please log in manually",
            "app_icon": bot_module.CONFIG["SAD_ICON"],
        }
    ]
    assert saved_states == []


def test_run_hunt_uses_shared_event_navigation(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_data(self, *_args, **_kwargs):
            return None

    class FakePage:
        pass

    class FakeContext:
        def new_page(self):
            return FakePage()

    class FakeBrowser:
        def new_context(self, **_kwargs):
            return FakeContext()

        def close(self):
            return None

    class FakePlaywright:
        def __init__(self):
            self.firefox = self

        def launch(self, **_kwargs):
            return FakeBrowser()

    class FakePlaywrightContext:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    event_pages: list[object] = []

    monkeypatch.setattr(HuntModeHandler.settings, "run_task", True)
    monkeypatch.setattr(HuntModeHandler.settings, "enable_hunt_mode", True)
    monkeypatch.setattr(HuntModeHandler, "get_hunt_items", lambda: ["Polychrome ×100"])
    monkeypatch.setattr(HuntModeHandler, "get_next_hunt_time", lambda: "20:00 28/03/26")
    monkeypatch.setattr(HuntModeHandler, "sync_playwright", lambda: FakePlaywrightContext())
    monkeypatch.setattr(
        HuntModeHandler.EventNavigator,
        "open_event_page",
        lambda page: event_pages.append(page),
    )
    monkeypatch.setattr(
        HuntModeHandler.EventNavigator,
        "wait_for_authenticated_event_home",
        lambda *_args, **_kwargs: EventNavigator.EventPageAuthResult(
            ready=True,
            auth_required=False,
            reason="event_home_ready",
        ),
    )
    monkeypatch.setattr(
        HuntModeHandler.ShoppingHandler, "open_shopping_screen", lambda _page: False
    )
    monkeypatch.setattr(
        HuntModeHandler.NotificationHelper,
        "notify",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("manual login notification should not fire")
        ),
    )
    monkeypatch.setattr("sentry_sdk.start_transaction", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())

    HuntModeHandler.run_hunt()

    assert len(event_pages) == 1


def test_run_hunt_aborts_when_event_page_requires_manual_login(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_data(self, *_args, **_kwargs):
            return None

    class FakePage:
        pass

    class FakeContext:
        def new_page(self):
            return FakePage()

    class FakeBrowser:
        def new_context(self, **_kwargs):
            return FakeContext()

        def close(self):
            return None

    class FakePlaywright:
        def __init__(self):
            self.firefox = self

        def launch(self, **_kwargs):
            return FakeBrowser()

    class FakePlaywrightContext:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    notifications: list[dict[str, object]] = []
    saved_states: list[bool] = []

    monkeypatch.setattr(HuntModeHandler.settings, "run_task", True)
    monkeypatch.setattr(HuntModeHandler.settings, "enable_hunt_mode", True)
    monkeypatch.setattr(HuntModeHandler, "get_hunt_items", lambda: ["Polychrome ×100"])
    monkeypatch.setattr(HuntModeHandler, "get_next_hunt_time", lambda: "20:00 28/03/26")
    monkeypatch.setattr(HuntModeHandler, "sync_playwright", lambda: FakePlaywrightContext())
    monkeypatch.setattr(HuntModeHandler.EventNavigator, "open_event_page", lambda _page: None)
    monkeypatch.setattr(
        HuntModeHandler.EventNavigator,
        "wait_for_authenticated_event_home",
        lambda *_args, **_kwargs: EventNavigator.EventPageAuthResult(
            ready=False,
            auth_required=True,
            reason="login_prompt_visible",
            screenshot_asset_id="screenshot:event_auth",
        ),
    )
    monkeypatch.setattr(
        HuntModeHandler,
        "save_context_storage_state",
        lambda *_args, **_kwargs: saved_states.append(True),
    )
    monkeypatch.setattr(
        HuntModeHandler.ShoppingHandler,
        "open_shopping_screen",
        lambda _page: (_ for _ in ()).throw(
            AssertionError("shopping should not open when event-page auth fails")
        ),
    )
    monkeypatch.setattr(
        HuntModeHandler.NotificationHelper,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr("sentry_sdk.start_transaction", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())

    HuntModeHandler.run_hunt()

    assert notifications == [
        {
            "title": "ZZZ Bot - Hunt Mode",
            "message": "Please log in manually",
            "app_icon": HuntModeHandler.CONFIG["SAD_ICON"],
        }
    ]
    assert saved_states == []


def test_stream_to_logger_buffers_partial_lines(caplog):
    stream_logger = logging.getLogger("test.stream_to_logger")
    caplog.set_level(logging.ERROR, logger=stream_logger.name)

    stream = StreamToLogger(stream_logger, logging.ERROR)
    stream.write("Exception in thread ")
    stream.write("Thread-2\nTraceback")
    stream.write(" (most recent call last):")
    stream.flush()

    messages = [record.message for record in caplog.records if record.name == stream_logger.name]
    assert messages == [
        "Exception in thread Thread-2",
        "Traceback (most recent call last):",
    ]


def test_retry_until_screen_appears_keeps_diagnostics_below_error(monkeypatch, caplog):
    class FakeImages:
        def count(self):
            return 1

        def nth(self, _index):
            return _FakeLocator()

    class FakePage:
        def get_by_role(self, role):
            assert role == "img"
            return FakeImages()

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(
        "utils.screenshot_store.save_page_screenshot",
        lambda page, filename: f"screenshot:{filename}",
    )

    button = _FakeLocator(page=FakePage())
    screen = _FakeLocator(count=0, visible=False)

    caplog.set_level(logging.WARNING, logger="automation.RetryHelper")
    result = MissionHandler.RetryHelper.retry_until_screen_appears(
        cast(Any, screen),
        cast(Any, button),
        max_retries=1,
    )

    error_messages = [
        record.message
        for record in caplog.records
        if record.name == "automation.RetryHelper" and record.levelno >= logging.ERROR
    ]
    warning_messages = [
        record.message
        for record in caplog.records
        if record.name == "automation.RetryHelper" and record.levelno == logging.WARNING
    ]

    assert result is False
    assert error_messages == ["Max retries (1) reached. Target screen did not appear."]
    assert any(
        message.startswith("Screenshot saved to MongoDB asset:") for message in warning_messages
    )


def test_redeem_autofill_records_unconfirmed_redeem(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeVisibility:
        def __init__(self, visible=False):
            self.visible = visible

        def is_visible(self):
            return self.visible

        def click(self):
            return None

    class FakeFrame:
        def get_by_text(self, _text):
            return FakeVisibility(False)

    class FakeLocator:
        @property
        def content_frame(self):
            return FakeFrame()

    class FakeInput:
        def __init__(self, page):
            self.page = page

        def fill(self, value):
            self.page.filled_code = value

    class FakeButton:
        def __init__(self, page):
            self.page = page

        def click(self):
            self.page.submit_clicked = True

    class FakePage:
        def __init__(self):
            self.filled_code = None
            self.submit_clicked = False
            self.closed = False

        def goto(self, _url):
            return None

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def get_by_text(self, text):
            if text in {
                "Please Log in to Redeem",
                "Successfully redeemed. Please claim rewards from in-game mail.",
                "Select a server",
            }:
                return FakeVisibility(False)
            return FakeVisibility(False)

        def locator(self, _selector):
            return FakeLocator()

        def get_by_placeholder(self, _text):
            return FakeInput(self)

        def get_by_role(self, _role, name=None):
            assert name == "Redeem"
            return FakeButton(self)

        def close(self):
            self.closed = True

    class FakeContext:
        def __init__(self, page):
            self.page = page

        def new_page(self):
            events.append("new_page")
            return self.page

    notifications: list[dict[str, object]] = []
    saved_attempts: list[dict[str, object]] = []
    state_saves: list[bool] = []
    events: list[str] = []
    page = FakePage()

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr(
        redeem_autofill_module.NotificationHelper,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_context_storage_state",
        lambda *_args, **_kwargs: state_saves.append(True),
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_redeem_data",
        lambda item_name, code, current_day, redeem_file_path, state, detail=None, status=None, record_id=None: (
            saved_attempts.append(
                {
                    "item_name": item_name,
                    "code": code,
                    "state": state,
                    "detail": detail,
                    "status": status,
                    "record_id": record_id,
                }
            )
            or events.append(f"save:{status}")
            or ("record-1" if record_id is None else record_id)
        ),
    )

    result = redeem_autofill_module.run(
        FakeContext(page),
        "ABCD1234EFGH",
        "Polychrome ×10",
    )

    assert result == {
        "ok": False,
        "status": "redeem_not_confirmed",
        "detail": "Redeem page did not show the success confirmation popup.",
    }
    assert notifications == [
        {
            "title": "ZZZ Bot",
            "message": "Redeem for Polychrome ×10 could not be confirmed. Code was saved for manual use.",
            "app_icon": redeem_autofill_module.CONFIG["SAD_ICON"],
        }
    ]
    assert saved_attempts == [
        {
            "item_name": "Polychrome ×10",
            "code": "ABCD1234EFGH",
            "state": False,
            "detail": "Code saved before redeem attempt started.",
            "status": "redeem_pending",
            "record_id": None,
        },
        {
            "item_name": "Polychrome ×10",
            "code": "ABCD1234EFGH",
            "state": False,
            "detail": "Redeem page did not show the success confirmation popup.",
            "status": "redeem_not_confirmed",
            "record_id": "record-1",
        },
    ]
    assert events[:2] == ["save:redeem_pending", "new_page"]
    assert state_saves == [True]
    assert page.filled_code == "ABCD1234EFGH"
    assert page.submit_clicked is True
    assert page.closed is True


def test_redeem_autofill_reports_manual_captcha_required(monkeypatch):
    class _TestNullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeVisibility:
        def __init__(self, visible=False):
            self.visible = visible

        def is_visible(self):
            return self.visible

    class FakeFrame:
        def get_by_text(self, text):
            return FakeVisibility(text == "Slide to complete the puzzle")

    class FakeLocator:
        @property
        def content_frame(self):
            return FakeFrame()

    class FakePage:
        def __init__(self):
            self.closed = False

        def goto(self, _url):
            return None

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def get_by_text(self, text):
            if text == "Please Log in to Redeem":
                return FakeVisibility(True)
            return FakeVisibility(False)

        def locator(self, _selector):
            return FakeLocator()

        def close(self):
            self.closed = True

    class FakeContext:
        def __init__(self, page):
            self.page = page

        def new_page(self):
            return self.page

    notifications: list[dict[str, object]] = []
    saved_attempts: list[dict[str, object]] = []
    sentry_messages: list[tuple[str, str]] = []
    sentry_tags: dict[str, str] = {}
    sentry_contexts: list[tuple[str, dict[str, object]]] = []
    state_saves: list[bool] = []
    page = FakePage()

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _TestNullSpan())
    monkeypatch.setattr("sentry_sdk.isolation_scope", lambda: _TestNullSpan())
    monkeypatch.setattr(
        "sentry_sdk.capture_message",
        lambda message, level=None: sentry_messages.append((message, level)),
    )
    monkeypatch.setattr(
        "sentry_sdk.set_tag", lambda key, value: sentry_tags.__setitem__(key, value)
    )
    monkeypatch.setattr(
        "sentry_sdk.set_context",
        lambda key, value: sentry_contexts.append((key, value)),
    )
    monkeypatch.setattr(
        redeem_autofill_module.NotificationHelper,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_context_storage_state",
        lambda *_args, **_kwargs: state_saves.append(True),
    )
    monkeypatch.setattr(
        redeem_autofill_module.AutoLogin,
        "run",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        redeem_autofill_module.RetryHelper,
        "retry_until_screen_appears",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_redeem_data",
        lambda item_name, code, current_day, redeem_file_path, state, detail=None, status=None, record_id=None: (
            saved_attempts.append(
                {
                    "item_name": item_name,
                    "code": code,
                    "state": state,
                    "detail": detail,
                    "status": status,
                    "record_id": record_id,
                }
            )
            or ("record-1" if record_id is None else record_id)
        ),
    )

    result = redeem_autofill_module.run(
        FakeContext(page),
        "ABCD1234EFGH",
        "Polychrome",
    )

    assert result == {
        "ok": False,
        "status": "manual_captcha_required",
        "detail": "Captcha blocked automatic redeem login.",
    }
    assert sentry_messages == [("Redeem requires manual captcha completion", "warning")]
    assert sentry_tags == {
        "redeem.status": "manual_captcha_required",
        "redeem.manual_captcha_required": "true",
    }
    assert sentry_contexts == [
        (
            "redeem",
            {
                "item_name": "Polychrome",
                "masked_code": "ABCD...EFGH",
            },
        )
    ]
    assert notifications == [
        {
            "title": "ZZZ Bot",
            "message": "Captcha detected. Please do manual login.",
            "app_icon": redeem_autofill_module.CONFIG["SAD_ICON"],
        }
    ]
    assert saved_attempts == [
        {
            "item_name": "Polychrome",
            "code": "ABCD1234EFGH",
            "state": False,
            "detail": "Code saved before redeem attempt started.",
            "status": "redeem_pending",
            "record_id": None,
        },
        {
            "item_name": "Polychrome",
            "code": "ABCD1234EFGH",
            "state": False,
            "detail": "Captcha blocked automatic redeem login.",
            "status": "manual_captcha_required",
            "record_id": "record-1",
        },
    ]
    assert state_saves == [True]
    assert page.closed is True


def test_redeem_autofill_reports_manual_login_required_when_login_prompt_persists(
    monkeypatch,
):
    class _TestNullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeVisibility:
        def __init__(self, visible=False):
            self.visible = visible

        def is_visible(self):
            return self.visible

    class FakeFrame:
        def get_by_text(self, text):
            return FakeVisibility(text == "Account Log In")

    class FakeLocator:
        @property
        def content_frame(self):
            return FakeFrame()

    class FakePage:
        def __init__(self):
            self.closed = False

        def goto(self, _url):
            return None

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def get_by_text(self, text):
            if text == "Please Log in to Redeem":
                return FakeVisibility(True)
            if text == "Select a server":
                return FakeVisibility(False)
            return FakeVisibility(False)

        def locator(self, _selector):
            return FakeLocator()

        def close(self):
            self.closed = True

    class FakeContext:
        def __init__(self, page):
            self.page = page

        def new_page(self):
            return self.page

    notifications: list[dict[str, object]] = []
    saved_attempts: list[dict[str, object]] = []
    sentry_messages: list[tuple[str, str]] = []
    state_saves: list[bool] = []
    page = FakePage()

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _TestNullSpan())
    monkeypatch.setattr("sentry_sdk.isolation_scope", lambda: _TestNullSpan())
    monkeypatch.setattr(
        "sentry_sdk.capture_message",
        lambda message, level=None: sentry_messages.append((message, level)),
    )
    monkeypatch.setattr("sentry_sdk.set_tag", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("sentry_sdk.set_context", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        redeem_autofill_module.NotificationHelper,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_context_storage_state",
        lambda *_args, **_kwargs: state_saves.append(True),
    )
    monkeypatch.setattr(
        redeem_autofill_module.AutoLogin,
        "run",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        redeem_autofill_module.RetryHelper,
        "retry_until_screen_appears",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        redeem_autofill_module,
        "save_redeem_data",
        lambda item_name, code, current_day, redeem_file_path, state, detail=None, status=None, record_id=None: (
            saved_attempts.append(
                {
                    "item_name": item_name,
                    "code": code,
                    "state": state,
                    "detail": detail,
                    "status": status,
                    "record_id": record_id,
                }
            )
            or ("record-1" if record_id is None else record_id)
        ),
    )

    result = redeem_autofill_module.run(
        FakeContext(page),
        "ABCD1234EFGH",
        "Polychrome",
    )

    assert result == {
        "ok": False,
        "status": "manual_login_required",
        "detail": "Redeem page still requires login after automatic login attempt.",
    }
    assert sentry_messages == []
    assert notifications == [
        {
            "title": "ZZZ Bot",
            "message": "Manual login required to continue redeem.",
            "app_icon": redeem_autofill_module.CONFIG["SAD_ICON"],
        }
    ]
    assert saved_attempts[-1]["status"] == "manual_login_required"
    assert state_saves == [True]
    assert page.closed is True


def test_process_single_item_logs_unconfirmed_redeem(monkeypatch, caplog):
    class FakeExchangeButton:
        def inner_text(self):
            return ShoppingHandler.EXCHANGE_BUTTON_TEXT

        def click(self):
            return None

    class FakeItemLocator:
        def count(self):
            return 1

        def locator(self, selector):
            assert selector == ShoppingHandler.SHOPPING_ITEM_BUTTON
            return FakeExchangeButton()

    class FakeItemCollection:
        def filter(self, **_kwargs):
            return FakeItemLocator()

    class FakePage:
        def __init__(self):
            self.context = object()

        def locator(self, selector):
            assert selector == ShoppingHandler.SHOPPING_ITEM
            return FakeItemCollection()

        def get_by_text(self, text, exact=None):
            assert exact is True
            return text

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(ShoppingHandler, "handle_exchange_dialog", lambda *_args: "CODE123")
    monkeypatch.setattr(
        ShoppingHandler.RedeemAutofill,
        "run",
        lambda *_args, **_kwargs: {
            "ok": False,
            "status": "manual_captcha_required",
            "detail": "Captcha blocked automatic redeem login.",
        },
    )

    caplog.set_level(logging.WARNING, logger="handlers.ShoppingHandler")
    result = ShoppingHandler._process_single_item(cast(Any, FakePage()), "Polychrome ×10")

    warning_messages = [
        record.message
        for record in caplog.records
        if record.name == "handlers.ShoppingHandler" and record.levelno == logging.WARNING
    ]

    assert result is False
    assert warning_messages == [
        "Exchanged 'Polychrome ×10' but redemption was not confirmed (status=manual_captcha_required, detail=Captcha blocked automatic redeem login.)"
    ]


def test_mission_run_returns_false_when_screen_does_not_open(monkeypatch):
    monkeypatch.setattr(MissionHandler, "open_mission_screen", lambda page: False)

    result = MissionHandler.run(
        "output.json",
        cast(Any, object()),
        [],
        {},
    )

    assert result is False


def test_single_draw_reports_missing_result_dialog(monkeypatch):
    reported: list[tuple[int, int]] = []
    notifications: list[dict[str, str]] = []

    class FakePage:
        url = "https://example.com/draw"

        def locator(self, selector):
            if selector == DrawHandler.DRAW_BUTTON_SELECTOR:
                return _FakeLocator(visible=True, page=self)
            return _FakeLocator(page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(DrawHandler, "_wait_for_success_dialog", lambda page, draw_number: None)
    monkeypatch.setattr(
        DrawHandler,
        "_capture_missing_draw_result_event",
        lambda page, draw_number, total_draws: reported.append((draw_number, total_draws)),
    )
    monkeypatch.setattr(DrawHandler, "ensure_draw_ui_cleared", lambda page: True)
    monkeypatch.setattr(
        DrawHandler.NotificationHelper,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )

    result = DrawHandler._perform_single_draw(cast(Any, FakePage()), 1, 4)

    assert result is False
    assert reported == [(1, 4)]
    assert (
        notifications[0]["message"] == "Draw button clicked but no result - draws may be exhausted"
    )


def test_wait_for_success_dialog_accepts_visible_modal_without_old_text():
    class FakeDialogLocator:
        def __init__(self, *, visible: bool, filtered=None):
            self._visible = visible
            self._filtered = filtered or self

        @property
        def first(self):
            return self

        def filter(self, **_kwargs):
            return self._filtered

        def count(self):
            return 1 if self._visible else 0

        def is_visible(self, timeout=None):
            return self._visible

    class FakePage:
        def __init__(self):
            self.text_dialog = FakeDialogLocator(visible=False)
            self.generic_dialog = FakeDialogLocator(
                visible=True,
                filtered=self.text_dialog,
            )
            self.fallback = FakeDialogLocator(visible=False)
            self.page_root = FakeDialogLocator(visible=True)

        def locator(self, selector):
            if selector == "body":
                return self.page_root
            if selector == DrawHandler.SUCCESS_DIALOG_SELECTOR:
                return self.generic_dialog
            if selector in {
                DrawHandler.REWARD_IMAGE_SELECTOR,
                DrawHandler.REWARD_IMAGE_SELECTOR_ALT,
                DrawHandler.REWARD_CODE_IMAGE_SELECTOR,
                DrawHandler.REWARD_CODE_IMAGE_CONTAINER_SELECTOR,
                DrawHandler.REDEEM_CODE_SELECTOR_ALT,
                DrawHandler.CLOSE_DIALOG_SELECTOR,
            }:
                return self.fallback
            raise AssertionError(f"Unexpected selector: {selector}")

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    page = FakePage()

    result = DrawHandler._wait_for_success_dialog(cast(Any, page), 1)

    assert result is page.generic_dialog


def test_wait_for_success_dialog_uses_page_root_when_modal_selector_missing():
    class FakeLocator:
        def __init__(self, *, visible=False):
            self._visible = visible

        @property
        def first(self):
            return self

        def filter(self, **_kwargs):
            return self

        def count(self):
            return 1 if self._visible else 0

        def is_visible(self, timeout=None):
            return self._visible

    class FakePage:
        def __init__(self):
            self.page_root = FakeLocator(visible=True)
            self.empty_dialog = FakeLocator(visible=False)
            self.fallback = FakeLocator(visible=True)

        def locator(self, selector):
            if selector == "body":
                return self.page_root
            if selector == DrawHandler.SUCCESS_DIALOG_SELECTOR:
                return self.empty_dialog
            if selector in {
                DrawHandler.REWARD_IMAGE_SELECTOR,
                DrawHandler.REWARD_IMAGE_SELECTOR_ALT,
                DrawHandler.REWARD_CODE_IMAGE_SELECTOR,
                DrawHandler.REWARD_CODE_IMAGE_CONTAINER_SELECTOR,
                DrawHandler.REDEEM_CODE_SELECTOR_ALT,
                DrawHandler.CLOSE_DIALOG_SELECTOR,
            }:
                return self.fallback
            raise AssertionError(f"Unexpected selector: {selector}")

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    page = FakePage()

    result = DrawHandler._wait_for_success_dialog(cast(Any, page), 1)

    assert result is page.page_root


def test_find_reward_image_waits_for_delayed_selector_visibility():
    class FakeRewardLocator:
        def __init__(self, *, succeeds: bool):
            self.succeeds = succeeds

        @property
        def first(self):
            return self

        def wait_for(self, *args, **kwargs):
            if not self.succeeds:
                raise DrawHandler.PlaywrightTimeoutError("not visible yet")

    class FakeSuccessDialog:
        def locator(self, selector):
            return FakeRewardLocator(succeeds=selector == DrawHandler.REWARD_CODE_IMAGE_SELECTOR)

    result = DrawHandler._find_reward_image(cast(Any, FakeSuccessDialog()), 1)

    assert result is not None


def test_reward_image_selectors_target_nested_images():
    assert DrawHandler.REWARD_IMAGE_SELECTOR == (
        f":is({DrawHandler.REWARD_IMAGE_CONTAINER_SELECTOR}) img"
    )
    assert DrawHandler.REWARD_CODE_IMAGE_SELECTOR == (
        f":is({DrawHandler.REWARD_CODE_IMAGE_CONTAINER_SELECTOR}) img"
    )


def test_find_reward_image_does_not_fallback_to_generic_page_images():
    attempted_selectors = []

    class FakeRewardLocator:
        def __init__(self, *, succeeds: bool):
            self.succeeds = succeeds

        @property
        def first(self):
            return self

        def wait_for(self, *args, **kwargs):
            if not self.succeeds:
                raise DrawHandler.PlaywrightTimeoutError("not visible yet")

    class FakeSuccessDialog:
        def locator(self, selector):
            attempted_selectors.append(selector)
            if selector == "img":
                raise AssertionError("Generic page image fallback should not be used")
            return FakeRewardLocator(
                succeeds=selector == DrawHandler.REWARD_CODE_IMAGE_CONTAINER_SELECTOR
            )

    result = DrawHandler._find_reward_image(cast(Any, FakeSuccessDialog()), 1)

    assert result is not None
    assert attempted_selectors == [
        DrawHandler.REWARD_IMAGE_SELECTOR,
        DrawHandler.REWARD_IMAGE_SELECTOR_ALT,
        DrawHandler.REWARD_CODE_IMAGE_SELECTOR,
        DrawHandler.REWARD_CODE_IMAGE_CONTAINER_SELECTOR,
    ]


def test_close_draw_screen_clears_reward_dialog_then_panel_back(monkeypatch):
    state = {"dialog_open": True, "draw_screen_open": True}

    class FakePage:
        def locator(self, selector):
            if selector == DrawHandler.CLOSE_DIALOG_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["dialog_open"] else 0,
                    visible=lambda: state["dialog_open"],
                    click_action=lambda: state.update(dialog_open=False),
                    page=self,
                )
            if selector == DrawHandler.SCREEN_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["draw_screen_open"] else 0,
                    visible=lambda: state["draw_screen_open"],
                    page=self,
                )
            if selector == DrawHandler.DRAW_BUTTON_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["draw_screen_open"] else 0,
                    visible=lambda: state["draw_screen_open"],
                    page=self,
                )
            if selector == ShoppingHandler.PANEL_BACK_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["draw_screen_open"] else 0,
                    visible=lambda: state["draw_screen_open"],
                    click_action=lambda: state.update(draw_screen_open=False),
                    page=self,
                )
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

    assert DrawHandler.close_draw_screen(cast(Any, FakePage())) is True
    assert state["dialog_open"] is False
    assert state["draw_screen_open"] is False


def test_ensure_draw_ui_cleared_closes_visible_mask_via_close_button():
    state = {"overlay_open": True, "close_clicks": 0}

    class FakePage:
        class _Keyboard:
            @staticmethod
            def press(_key):
                return None

        keyboard = _Keyboard()

        def locator(self, selector):
            if selector == DrawHandler.CLOSE_DIALOG_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["overlay_open"] else 0,
                    visible=lambda: state["overlay_open"],
                    click_action=lambda: state.update(
                        overlay_open=False,
                        close_clicks=state["close_clicks"] + 1,
                    ),
                    page=self,
                )
            if selector == DrawHandler.DRAW_MASK_SELECTOR:
                return _FakeLocator(
                    count=lambda: 1 if state["overlay_open"] else 0,
                    visible=lambda: state["overlay_open"],
                    page=self,
                )
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    assert DrawHandler.ensure_draw_ui_cleared(cast(Any, FakePage())) is True
    assert state["close_clicks"] == 1
    assert state["overlay_open"] is False


def test_ensure_draw_ui_cleared_ignores_mask_without_result_controls():
    class FakePage:
        class _Keyboard:
            @staticmethod
            def press(_key):
                return None

        keyboard = _Keyboard()

        def locator(self, selector):
            if selector == DrawHandler.DRAW_MASK_SELECTOR:
                return _FakeLocator(count=1, visible=True, page=self)
            return _FakeLocator(count=0, visible=False, page=self)

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    assert DrawHandler.ensure_draw_ui_cleared(cast(Any, FakePage())) is True


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


def test_playwright_task_skips_automatic_run_before_preparing_data(monkeypatch):
    monkeypatch.setattr(bot_module.settings, "run_task", False)
    monkeypatch.setattr(
        bot_module,
        "prepare_mission_data",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("prepare_mission_data should not run")
        ),
    )

    bot_module.playwright_task()


def test_playwright_task_manual_run_bypasses_automatic_gate(monkeypatch):
    monkeypatch.setattr(bot_module.settings, "run_task", False)
    monkeypatch.setattr(
        bot_module,
        "prepare_mission_data",
        lambda *_args, **_kwargs: ({}, {}),
    )

    entered = {"value": False}

    class _StopManualRun(Exception):
        pass

    class _FakePlaywrightContext:
        def __enter__(self):
            entered["value"] = True
            raise _StopManualRun()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(bot_module, "sync_playwright", lambda: _FakePlaywrightContext())
    monkeypatch.setattr(
        bot_module.NotificationModule,
        "notify",
        lambda **_kwargs: None,
    )

    bot_module.playwright_task(manual_run=True)

    assert entered["value"] is True


def test_playwright_task_does_not_mark_failed_run_as_finished(monkeypatch):
    monkeypatch.setattr(bot_module.settings, "run_task", True)
    monkeypatch.setattr(
        bot_module,
        "prepare_mission_data",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    notifications = []
    last_run_calls = []
    monkeypatch.setattr(
        bot_module.NotificationModule,
        "notify",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(bot_module, "save_last_run", lambda: last_run_calls.append(True))

    bot_module.playwright_task()

    assert last_run_calls == []
    assert notifications[-1]["message"] == "Task finished"


def test_check_missed_runs_does_not_mark_failed_replay_as_finished(monkeypatch):
    monkeypatch.setattr(bot_module.settings, "run_task", True)
    monkeypatch.setattr(
        bot_module.settings,
        "schedule_times",
        [(datetime.now() - timedelta(minutes=1)).strftime("%H:%M")],
    )
    monkeypatch.setattr(data_store_module, "get_last_run", lambda: None)

    replay_calls = []
    last_run_calls = []
    monkeypatch.setattr(bot_module, "playwright_task", lambda: replay_calls.append("attempted"))
    monkeypatch.setattr(bot_module, "save_last_run", lambda: last_run_calls.append(True))

    bot_module.check_missed_runs()

    assert replay_calls == ["attempted"]
    assert last_run_calls == []


def test_asyncio_exception_handler_ignores_known_windows_transport_reset(monkeypatch):
    monkeypatch.setattr(bot_module.os, "name", "nt", raising=False)

    delegated_calls: list[dict[str, object]] = []

    def fallback(_loop, context):
        delegated_calls.append(context)

    error = ConnectionResetError("remote host closed the socket")
    error.winerror = 10054
    handler = bot_module._build_asyncio_exception_handler(fallback)

    handler(
        object(),
        {
            "exception": error,
            "message": "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)",
        },
    )

    assert delegated_calls == []


def test_asyncio_exception_handler_delegates_other_errors(monkeypatch):
    monkeypatch.setattr(bot_module.os, "name", "nt", raising=False)

    delegated_calls: list[dict[str, object]] = []

    def fallback(_loop, context):
        delegated_calls.append(context)

    handler = bot_module._build_asyncio_exception_handler(fallback)

    handler(
        object(),
        {
            "exception": RuntimeError("unexpected async failure"),
            "message": "Exception in callback something_else",
        },
    )

    assert len(delegated_calls) == 1


def test_configure_windows_asyncio_exception_handler_is_idempotent(monkeypatch):
    monkeypatch.setattr(bot_module.os, "name", "nt", raising=False)

    class FakeLoop:
        def __init__(self):
            self.handler = None
            self.set_calls = 0

        def get_exception_handler(self):
            return self.handler

        def set_exception_handler(self, handler):
            self.handler = handler
            self.set_calls += 1

    fake_loop = FakeLoop()

    bot_module._configure_windows_asyncio_exception_handler(fake_loop)
    bot_module._configure_windows_asyncio_exception_handler(fake_loop)

    assert fake_loop.set_calls == 1
    assert callable(fake_loop.handler)


def test_schedule_tasks_skips_registration_when_automatic_runs_disabled(monkeypatch):
    events: list[tuple[str, str | None]] = []

    class _FakeSchedule:
        def clear(self, tag=None):
            events.append(("clear", tag))

        def every(self):
            raise AssertionError("No scheduled jobs should be registered")

    monkeypatch.setattr(bot_module.settings, "run_task", False)
    monkeypatch.setattr(bot_module, "schedule", _FakeSchedule())

    bot_module.schedule_tasks()

    assert events == [("clear", None)]


def test_update_settings_skips_schedule_for_window_state_only_changes(monkeypatch):
    saved_payloads: list[dict[str, Any]] = []
    schedule_calls: list[str] = []

    class FakeRequest:
        def __init__(self, payload):
            self.payload = payload

        async def json(self):
            return self.payload

    monkeypatch.setattr(routes_module.settings, "window_x", 10)
    monkeypatch.setattr(routes_module.settings, "window_y", 20)
    monkeypatch.setattr(routes_module.settings, "window_width", 1200)
    monkeypatch.setattr(routes_module.settings, "window_height", 800)
    monkeypatch.setattr(routes_module.settings, "window_maximized", False)
    monkeypatch.setattr(routes_module.settings, "window_minimized", False)
    monkeypatch.setattr(
        routes_module.DataStore,
        "save_settings",
        lambda payload: saved_payloads.append(dict(payload)),
    )
    monkeypatch.setattr(bot_module, "schedule_tasks", lambda: schedule_calls.append("scheduled"))

    response = asyncio.run(
        routes_module.update_settings(
            FakeRequest(
                {
                    "window_x": 320,
                    "window_y": 180,
                    "window_width": 1440,
                    "window_height": 900,
                    "window_maximized": True,
                    "window_minimized": False,
                }
            )
        )
    )

    assert response.status_code == 200
    assert saved_payloads[-1]["window_x"] == 320
    assert saved_payloads[-1]["window_y"] == 180
    assert saved_payloads[-1]["window_width"] == 1440
    assert saved_payloads[-1]["window_height"] == 900
    assert saved_payloads[-1]["window_maximized"] is True
    assert saved_payloads[-1]["window_minimized"] is False
    assert schedule_calls == []


def test_update_settings_reschedules_for_non_window_changes(monkeypatch):
    saved_payloads: list[dict[str, Any]] = []
    schedule_calls: list[str] = []

    class FakeRequest:
        def __init__(self, payload):
            self.payload = payload

        async def json(self):
            return self.payload

    original_theme = routes_module.settings.theme
    updated_theme = "venom" if original_theme != "venom" else "glacier"

    monkeypatch.setattr(
        routes_module.DataStore,
        "save_settings",
        lambda payload: saved_payloads.append(dict(payload)),
    )
    monkeypatch.setattr(bot_module, "schedule_tasks", lambda: schedule_calls.append("scheduled"))

    response = asyncio.run(routes_module.update_settings(FakeRequest({"theme": updated_theme})))

    assert response.status_code == 200
    assert saved_payloads[-1]["theme"] == updated_theme
    assert schedule_calls == ["scheduled"]


def test_update_settings_reschedules_for_mixed_window_and_non_window_changes(
    monkeypatch,
):
    saved_payloads: list[dict[str, Any]] = []
    schedule_calls: list[str] = []

    class FakeRequest:
        def __init__(self, payload):
            self.payload = payload

        async def json(self):
            return self.payload

    original_theme = routes_module.settings.theme
    updated_theme = "venom" if original_theme != "venom" else "glacier"

    monkeypatch.setattr(routes_module.settings, "window_x", 10)
    monkeypatch.setattr(routes_module.settings, "window_y", 20)
    monkeypatch.setattr(routes_module.settings, "window_width", 1200)
    monkeypatch.setattr(routes_module.settings, "window_height", 800)
    monkeypatch.setattr(routes_module.settings, "window_maximized", False)
    monkeypatch.setattr(routes_module.settings, "window_minimized", False)
    monkeypatch.setattr(
        routes_module.DataStore,
        "save_settings",
        lambda payload: saved_payloads.append(dict(payload)),
    )
    monkeypatch.setattr(bot_module, "schedule_tasks", lambda: schedule_calls.append("scheduled"))

    response = asyncio.run(
        routes_module.update_settings(
            FakeRequest(
                {
                    "theme": updated_theme,
                    "window_x": 320,
                    "window_y": 180,
                    "window_width": 1440,
                    "window_height": 900,
                    "window_maximized": True,
                    "window_minimized": False,
                }
            )
        )
    )

    assert response.status_code == 200
    assert saved_payloads[-1]["theme"] == updated_theme
    assert saved_payloads[-1]["window_x"] == 320
    assert saved_payloads[-1]["window_y"] == 180
    assert saved_payloads[-1]["window_width"] == 1440
    assert saved_payloads[-1]["window_height"] == 900
    assert saved_payloads[-1]["window_maximized"] is True
    assert saved_payloads[-1]["window_minimized"] is False
    assert schedule_calls == ["scheduled"]


def test_schedule_hunt_tasks_skips_when_automatic_runs_disabled(monkeypatch):
    events: list[tuple[str, str | None]] = []

    class _FakeSchedule:
        def clear(self, tag=None):
            events.append(("clear", tag))

    monkeypatch.setattr(bot_module.settings, "run_task", False)
    monkeypatch.setattr(bot_module, "schedule", _FakeSchedule())
    monkeypatch.setattr(
        bot_module.HuntMode,
        "get_next_hunt_time",
        lambda: (_ for _ in ()).throw(
            AssertionError("Hunt scheduling should stop before reading hunt times")
        ),
    )

    target_dates: list[Any] = []
    monkeypatch.setattr(
        bot_module.HuntMode,
        "set_hunt_target_date",
        lambda value: target_dates.append(value),
    )

    bot_module.schedule_hunt_tasks()

    assert events == [("clear", "hunt")]
    assert target_dates == [None]


def test_replace_all_missions_replaces_existing_documents(sqlite_db):
    sqlite_db.save_mission_day({"day": "2026-03-10", "missions": []})
    sqlite_db.save_mission_day({"day": "2026-03-11", "missions": []})

    sqlite_db.replace_all_missions([{"day": "2026-03-12", "missions": [{"name": "Check-in"}]}])

    assert sqlite_db.get_missions() == [{"day": "2026-03-12", "missions": [{"name": "Check-in"}]}]


def test_resolve_redemption_indexed_at_uses_redeem_day():
    indexed_at = data_store_module._resolve_redemption_indexed_at(
        {"code": "TESTCODE123", "day": "21:51 12/11/2025", "state": True}
    )

    assert indexed_at == datetime(2025, 11, 12, 21, 51, tzinfo=timezone.utc)


def test_resolve_redemption_indexed_at_falls_back_to_now(monkeypatch):
    fallback_now = datetime(2026, 4, 1, 8, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(data_store_module, "_now_utc", lambda: fallback_now)

    indexed_at = data_store_module._resolve_redemption_indexed_at(
        {"code": "BADDATE", "day": "not-a-date", "state": False}
    )

    assert indexed_at == fallback_now


def test_replace_all_redemptions_round_trip(sqlite_db):
    sqlite_db.save_redemption({"code": "OLDCODE", "day": "21:51 12/11/2025", "state": True})

    sqlite_db.replace_all_redemptions(
        [{"code": "NEWCODE", "day": "10:00 01/01/2026", "state": False}]
    )

    assert sqlite_db.get_redemptions() == [
        {"code": "NEWCODE", "day": "10:00 01/01/2026", "state": False}
    ]


def test_repair_redemptions_indexed_at_once_is_a_noop(sqlite_db):
    report = sqlite_db.repair_redemptions_indexed_at_once()

    assert report == {
        "already_applied": True,
        "scanned": 0,
        "updated": 0,
        "skipped": 0,
    }
    assert sqlite_db.has_app_metadata_marker(sqlite_db.REDEMPTIONS_INDEXED_AT_REPAIR_MARKER)


def test_backup_export_filename_includes_timestamp():
    earlier = routes_module._build_backup_export_filename(datetime(2026, 3, 13, 8, 0, 0))
    later = routes_module._build_backup_export_filename(datetime(2026, 3, 13, 8, 0, 1))

    assert earlier == "zzz-bot-backup-2026-03-13_08-00-00-000000.json"
    assert later == "zzz-bot-backup-2026-03-13_08-00-01-000000.json"
    assert earlier != later


def test_backup_import_reschedules_hunt_tasks_when_shopping_restored(monkeypatch):
    events: list[str] = []

    class FakeRequest:
        async def json(self):
            return {
                "data": {"version": 1, "collections": {"shopping": {"Hunt": ["Item"]}}},
                "collections": ["shopping"],
            }

    monkeypatch.setattr(
        data_store_module,
        "import_data",
        lambda data, collections: {
            "restored": ["shopping"],
            "skipped": [],
            "errors": {},
        },
    )
    monkeypatch.setattr(
        bot_module,
        "schedule_tasks",
        lambda: (_ for _ in ()).throw(
            AssertionError("schedule_tasks should not run for shopping-only restores")
        ),
    )
    monkeypatch.setattr(bot_module, "schedule_hunt_tasks", lambda: events.append("hunt"))

    response = asyncio.run(routes_module.import_backup(FakeRequest()))

    assert response.status_code == 200
    assert response.body == b'{"restored":["shopping"],"skipped":[],"errors":{}}'
    assert events == ["hunt"]


def test_manual_run_route_starts_manual_override(monkeypatch):
    monkeypatch.setenv("ZZZ_DESKTOP_TOKEN", "expected-token")
    calls: list[bool] = []

    class FakeRequest:
        headers = {"x-desktop-token": "expected-token"}

    class FakeMain:
        pass

    fake_main = FakeMain()
    fake_main.run_playwright_task_async = lambda *, manual_run=False: calls.append(manual_run)

    monkeypatch.setitem(sys.modules, "__main__", fake_main)

    response = routes_module.run_playwright_now(FakeRequest())

    assert response.status_code == 200
    assert response.body == b'{"status":"started"}'
    assert calls == [True]


def test_resolve_bot_runtime_prefers_main_module(monkeypatch):
    class FakeMain:
        pass

    fake_main = FakeMain()
    fake_main.schedule_tasks = lambda: None
    fake_main.schedule_hunt_tasks = lambda: None

    monkeypatch.setitem(sys.modules, "__main__", fake_main)

    resolved = routes_module._resolve_bot_runtime("schedule_tasks", "schedule_hunt_tasks")

    assert resolved is fake_main


def test_extract_advanced_settings_returns_only_advanced_fields():
    full_settings = {
        "schedule_times": ["08:00", "20:00"],
        "show_window_on_startup": True,
        "window_x": 120,
        "window_y": 80,
        "window_width": 1440,
        "window_height": 900,
        "window_maximized": True,
        "window_minimized": False,
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
    assert "window_x" not in advanced_settings
    assert "window_y" not in advanced_settings
    assert "window_width" not in advanced_settings
    assert "window_height" not in advanced_settings
    assert "window_maximized" not in advanced_settings
    assert "window_minimized" not in advanced_settings


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
    assert settings["show_window_on_startup"] is True
    assert settings["window_x"] is None
    assert settings["window_y"] is None
    assert settings["window_width"] is None
    assert settings["window_height"] is None
    assert settings["window_maximized"] is False
    assert settings["window_minimized"] is False


def test_dynamic_routes_hide_internal_action_endpoints():
    assert routes_module._is_public_route("/shopping") is True
    assert routes_module._is_public_route("/overview/mission") is True
    assert routes_module._is_public_route("/shutdown") is False
    assert routes_module._is_public_route("/tasks/run-playwright") is False
    assert routes_module._is_public_route("/maintenance/local-cleanup") is False
    assert routes_module._is_public_route("/maintenance/legacy-migration") is False


def test_health_check_returns_phase_aware_startup_status(monkeypatch):
    payload = {
        "status": "starting",
        "ready": True,
        "phase": "warming",
    }
    monkeypatch.setattr(routes_module, "get_startup_status", lambda: payload)

    assert routes_module.health_check() == payload


def test_run_local_cleanup_runs_artifact_cleanup(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    cleanup_calls: list[dict[str, object]] = []

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("repositories.connection.get_runtime_mode", lambda: "dev")
    monkeypatch.setattr(
        "utils.local_artifact_maintenance.cleanup_local_artifacts_once",
        lambda **kwargs: cleanup_calls.append(kwargs) or {"status": "completed"},
    )

    response = routes_module.run_local_cleanup()

    assert response.status_code == 200
    assert json.loads(response.body) == {"status": "completed"}
    # The SQLite migration removed the Mongo log mirror and the db= argument.
    assert "db" not in cleanup_calls[0]
    assert "migration_report" not in cleanup_calls[0]
    assert cleanup_calls[0]["runtime_mode"] == "dev"


def test_run_mongo_migration_completed_refreshes_runtime_state(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeRequest:
        async def json(self):
            return {}

    migrate_calls: list[dict[str, object]] = []
    schedule_calls: list[str] = []

    def _fake_migrate(**kwargs):
        migrate_calls.append(kwargs)
        return {
            "status": "completed",
            "message": "Using database: zzz_bot",
            "summary": {"settings": 1, "missions": 3, "binary_assets": 2},
            "db_path": "/tmp/zzz_bot.db",
        }

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr("utils.migrate_mongo_to_sqlite.migrate", _fake_migrate)
    monkeypatch.setattr(data_store_module, "get_settings", lambda: None)
    monkeypatch.setattr(data_store_module, "get_account", lambda: None)
    monkeypatch.setattr(bot_module, "schedule_tasks", lambda: schedule_calls.append("all"))
    monkeypatch.setattr(bot_module, "schedule_hunt_tasks", lambda: schedule_calls.append("hunt"))

    response = asyncio.run(routes_module.run_mongo_migration(FakeRequest()))

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["status"] == "completed"
    assert payload["summary"] == {"settings": 1, "missions": 3, "binary_assets": 2}
    # Default URI when the request body omits mongo_uri.
    assert migrate_calls[0]["uri"] == "mongodb://localhost:27017"
    assert migrate_calls[0]["db_name"] is None
    # restored set is {"settings", "account", "shopping"} → schedule_tasks runs once;
    # schedule_hunt_tasks does not because "settings" is in the restored set.
    assert schedule_calls == ["all"]


def test_run_mongo_migration_no_source_skips_runtime_refresh(monkeypatch):
    class _NullSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeRequest:
        async def json(self):
            return {"mongo_uri": "mongodb://nowhere:27017", "mongo_db": "zzz_bot"}

    schedule_calls: list[str] = []

    monkeypatch.setattr("sentry_sdk.start_span", lambda *args, **kwargs: _NullSpan())
    monkeypatch.setattr(
        "utils.migrate_mongo_to_sqlite.migrate",
        lambda **kwargs: {
            "status": "no_source",
            "message": f"MongoDB not reachable at {kwargs['uri']}",
            "summary": {},
            "db_path": "/tmp/zzz_bot.db",
        },
    )
    monkeypatch.setattr(bot_module, "schedule_tasks", lambda: schedule_calls.append("all"))
    monkeypatch.setattr(bot_module, "schedule_hunt_tasks", lambda: schedule_calls.append("hunt"))

    response = asyncio.run(routes_module.run_mongo_migration(FakeRequest()))

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["status"] == "no_source"
    assert payload["summary"] == {}
    assert "MongoDB not reachable at mongodb://nowhere:27017" in payload["message"]
    assert schedule_calls == []


def test_deferred_startup_tasks_mark_ready(monkeypatch):
    schema_calls: list[str] = []
    repair_calls: list[str] = []
    original_phase = global_var_module._startup_phase
    original_error = global_var_module._startup_error

    monkeypatch.setattr(
        "repositories.DataStore.ensure_schema",
        lambda: schema_calls.append("schema"),
    )
    monkeypatch.setattr(
        "repositories.DataStore.repair_redemptions_indexed_at_once",
        lambda: (
            repair_calls.append("repair")
            or {
                "already_applied": True,
                "scanned": 0,
                "updated": 0,
                "skipped": 0,
            }
        ),
    )

    try:
        global_var_module._run_deferred_startup_tasks()

        assert schema_calls == ["schema"]
        assert repair_calls == ["repair"]
        assert global_var_module._startup_phase == global_var_module.STARTUP_PHASE_READY
        assert global_var_module._startup_error is None
    finally:
        global_var_module._startup_phase = original_phase
        global_var_module._startup_error = original_error


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
    assert fake_sentry.flush_calls == [routes_module.SHUTDOWN_SENTRY_FLUSH_TIMEOUT_SECONDS]
    assert exit_codes == [0]
