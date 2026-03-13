import asyncio
import logging
import sys
import threading
from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

image_processor_module = import_module("automation.ImageProcessor")
routes_module = import_module("api.routes")
bot_module = import_module("Bot")
mongo_module = import_module("repositories.MongoRepository")
from automation import EventNavigator
from handlers import DrawHandler, HuntModeHandler, MissionHandler, ShoppingHandler
from core.frontend_env import resolve_frontend_sentry_dsn
from core.mission_email import schedule_mission_email_delivery
from core.settings_compat import (
    HUNT_EARLY_EXIT_RESET_MARKER,
    SHOW_WINDOW_ON_STARTUP_RENAME_MARKER,
    normalize_hunt_early_exit_default,
    normalize_show_window_on_startup_setting,
)
from core.settings_contract import ADVANCED_SETTINGS_KEYS, extract_advanced_settings
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
                    click_action=lambda: (_ for _ in ()).throw(
                        RuntimeError("detached")
                    ),
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


def test_run_hunt_skips_mismatched_target_date_without_backend_import(caplog):
    caplog.set_level(logging.INFO)
    HuntModeHandler.set_hunt_target_date(datetime.now() + timedelta(days=1))

    try:
        HuntModeHandler.run_hunt()
    finally:
        HuntModeHandler.set_hunt_target_date(None)

    assert "Skipping until correct date." in caplog.text


def test_stream_to_logger_buffers_partial_lines(caplog):
    stream_logger = logging.getLogger("test.stream_to_logger")
    caplog.set_level(logging.ERROR, logger=stream_logger.name)

    stream = StreamToLogger(stream_logger, logging.ERROR)
    stream.write("Exception in thread ")
    stream.write("Thread-2\nTraceback")
    stream.write(" (most recent call last):")
    stream.flush()

    messages = [
        record.message for record in caplog.records if record.name == stream_logger.name
    ]
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
        message.startswith("Screenshot saved to MongoDB asset:")
        for message in warning_messages
    )


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

    monkeypatch.setattr(
        DrawHandler, "_wait_for_success_dialog", lambda page, draw_number: None
    )
    monkeypatch.setattr(
        DrawHandler,
        "_capture_missing_draw_result_event",
        lambda page, draw_number, total_draws: reported.append(
            (draw_number, total_draws)
        ),
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
        notifications[0]["message"]
        == "Draw button clicked but no result - draws may be exhausted"
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
            return FakeRewardLocator(succeeds=selector == "img")

    result = DrawHandler._find_reward_image(cast(Any, FakeSuccessDialog()), 1)

    assert result is not None


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


def test_normalize_show_window_on_startup_setting_renames_legacy_key_once():
    markers: set[str] = set()
    saved_payloads: list[dict] = []

    normalized = normalize_show_window_on_startup_setting(
        {"open_web_ui": False, "theme": "venom"},
        has_marker=lambda marker: marker in markers,
        set_marker=markers.add,
        save_settings=lambda payload: saved_payloads.append(dict(payload)),
    )

    assert normalized == {
        "show_window_on_startup": False,
        "theme": "venom",
    }
    assert saved_payloads == [normalized]
    assert SHOW_WINDOW_ON_STARTUP_RENAME_MARKER in markers

    preserved = normalize_show_window_on_startup_setting(
        {"open_web_ui": True, "theme": "venom"},
        has_marker=lambda marker: marker in markers,
        set_marker=markers.add,
        save_settings=lambda payload: saved_payloads.append(dict(payload)),
    )

    assert preserved == {
        "show_window_on_startup": True,
        "theme": "venom",
    }
    assert saved_payloads == [normalized, preserved]


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

    class _StopManualRun(Exception):
        pass

    class _FakePlaywrightContext:
        def __enter__(self):
            raise _StopManualRun()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(bot_module, "sync_playwright", lambda: _FakePlaywrightContext())

    try:
        bot_module.playwright_task(manual_run=True)
    except _StopManualRun:
        pass
    else:
        raise AssertionError("Manual run should enter the Playwright context")


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
    monkeypatch.setattr(
        routes_module.MongoRepository,
        "save_settings",
        lambda payload: saved_payloads.append(dict(payload)),
    )
    monkeypatch.setattr(
        bot_module, "schedule_tasks", lambda: schedule_calls.append("scheduled")
    )

    response = asyncio.run(
        routes_module.update_settings(
            FakeRequest(
                {
                    "window_x": 320,
                    "window_y": 180,
                    "window_width": 1440,
                    "window_height": 900,
                }
            )
        )
    )

    assert response.status_code == 200
    assert saved_payloads[-1]["window_x"] == 320
    assert saved_payloads[-1]["window_y"] == 180
    assert saved_payloads[-1]["window_width"] == 1440
    assert saved_payloads[-1]["window_height"] == 900
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
        routes_module.MongoRepository,
        "save_settings",
        lambda payload: saved_payloads.append(dict(payload)),
    )
    monkeypatch.setattr(
        bot_module, "schedule_tasks", lambda: schedule_calls.append("scheduled")
    )

    response = asyncio.run(
        routes_module.update_settings(FakeRequest({"theme": updated_theme}))
    )

    assert response.status_code == 200
    assert saved_payloads[-1]["theme"] == updated_theme
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


def test_replace_all_missions_replaces_existing_documents(monkeypatch):
    indexed_at = datetime(2026, 3, 13, 8, 0, 0)

    class _FakeMissionCollection:
        def __init__(self):
            self.docs = [
                {"day": "2026-03-10", "indexed_at": "old"},
                {"day": "2026-03-11", "indexed_at": "old"},
            ]

        def count_documents(self, _query):
            return len(self.docs)

        def delete_many(self, _query):
            self.docs = []

        def find_one_and_replace(self, query, record, upsert=False):
            day = query["day"]
            self.docs = [doc for doc in self.docs if doc["day"] != day]
            self.docs.append(record)

    class _FakeDb:
        def __init__(self):
            self.missions = _FakeMissionCollection()

    fake_db = _FakeDb()
    monkeypatch.setattr(mongo_module, "get_db", lambda: fake_db)
    monkeypatch.setattr(mongo_module, "_ensure_indexes", lambda: None)
    monkeypatch.setattr(mongo_module, "_now_utc", lambda: indexed_at)

    mongo_module.replace_all_missions(
        [{"day": "2026-03-12", "missions": [{"name": "Check-in"}]}]
    )

    assert fake_db.missions.docs == [
        {
            "day": "2026-03-12",
            "missions": [{"name": "Check-in"}],
            "indexed_at": indexed_at,
        }
    ]


def test_backup_export_filename_includes_timestamp():
    earlier = routes_module._build_backup_export_filename(
        datetime(2026, 3, 13, 8, 0, 0)
    )
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
        mongo_module,
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
    monkeypatch.setattr(
        bot_module, "schedule_hunt_tasks", lambda: events.append("hunt")
    )

    response = asyncio.run(routes_module.import_backup(FakeRequest()))

    assert response.status_code == 200
    assert response.body == b'{"restored":["shopping"],"skipped":[],"errors":{}}'
    assert events == ["hunt"]


def test_manual_run_route_starts_manual_override(monkeypatch):
    monkeypatch.setenv("ZZZ_DESKTOP_TOKEN", "expected-token")
    calls: list[bool] = []

    class FakeRequest:
        headers = {"x-desktop-token": "expected-token"}

    monkeypatch.setattr(
        bot_module,
        "run_playwright_task_async",
        lambda *, manual_run=False: calls.append(manual_run),
    )

    response = routes_module.run_playwright_now(FakeRequest())

    assert response.status_code == 200
    assert response.body == b'{"status":"started"}'
    assert calls == [True]


def test_extract_advanced_settings_returns_only_advanced_fields():
    full_settings = {
        "schedule_times": ["08:00", "20:00"],
        "show_window_on_startup": True,
        "window_x": 120,
        "window_y": 80,
        "window_width": 1440,
        "window_height": 900,
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
