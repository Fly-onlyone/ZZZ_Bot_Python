import argparse
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Add src directory to Python path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import schedule
import uvicorn
from playwright.sync_api import Error as PlaywrightError, sync_playwright
from starlette.staticfiles import StaticFiles

from handlers import DrawHandler, ShoppingHandler
from handlers import MissionHandler as Mission
from handlers import HuntModeHandler as HuntMode
from utils.DataHandler import (
    prepare_mission_data,
)
from core.GlobalVar import app, CONFIG, settings, is_exe
from core import GlobalVar
from utils.Logger import StreamToLogger, NoImportFilter
from utils.NotificationHelper import NotificationModule
from utils.screenshot_store import save_page_screenshot
from utils.storage_state_store import (
    build_context_options,
    load_storage_state,
    save_context_storage_state,
)
from core import Notification
from api.routes import router

# Configure logger
logger = logging.getLogger(__name__)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _create_file_handler(log_path: str) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        filename=log_path,
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(NoImportFilter())
    return handler


class _SentryWarningHandler(logging.Handler):
    """Forward Python warnings captured via logging.captureWarnings() to Sentry as issues.

    Attached to the 'py.warnings' logger so that DeprecationWarning, RuntimeWarning,
    etc. create visible Sentry issues rather than only appearing in log files.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            import sentry_sdk

            if sentry_sdk.get_client().is_active():
                sentry_sdk.capture_message(self.format(record), level="warning")
        except Exception:
            self.handleError(record)


def _attach_sentry_warning_handler() -> None:
    """Attach _SentryWarningHandler to 'py.warnings' logger (idempotent)."""
    warnings_logger = logging.getLogger("py.warnings")
    if not any(isinstance(h, _SentryWarningHandler) for h in warnings_logger.handlers):
        warnings_logger.addHandler(_SentryWarningHandler())


# Include API routes from separate module
app.include_router(router)

# Hunt mode target date (used for date validation in run_hunt)
_hunt_target_date: datetime | None = None

# React dev server process (non-exe mode only)
react_server: subprocess.Popen | None = None

# Whether backend is hosted by the Tauri desktop shell.
hosted_by_tauri = False


# ============================================================================
# Bot Logic
# ============================================================================
def _close_shopping_screen_helper(page):
    """Helper function to close shopping screen with retry logic.

    Args:
        page: Playwright Page instance
    """
    shopping_screen = page.locator(".wrapper-O3T67n")
    close_button = page.locator(".panelBack--wW5qj")

    max_close_attempts = 3

    for attempt in range(1, max_close_attempts + 1):
        try:
            logger.info(
                f"Attempting to close shopping screen (attempt {attempt}/{max_close_attempts})"
            )

            # First, try to dismiss any lingering modals/dialogs that might block clicks
            try:
                draw_dialog_close = page.locator(".gainClose-7Q0hz8")
                if draw_dialog_close.count() > 0 and draw_dialog_close.is_visible(
                    timeout=1000
                ):
                    logger.info("Found open draw dialog, closing it first")
                    draw_dialog_close.click(force=True, timeout=2000)
                    page.wait_for_timeout(500)
            except Exception as modal_error:
                logger.debug(f"No draw dialog to dismiss: {modal_error}")

            # Check close button status
            close_button_count = close_button.count()
            logger.info(f"Close button count: {close_button_count}")

            if close_button_count > 0:
                is_visible = close_button.is_visible(timeout=2000)
                logger.info(f"Close button visible: {is_visible}")

                if is_visible:
                    # Try normal click first
                    try:
                        close_button.click(timeout=5000)
                        logger.info("Clicked shopping close button")
                    except Exception as click_error:
                        # If normal click fails (e.g., element intercepted), use force
                        logger.warning(
                            f"Normal click failed ({click_error}), trying force click"
                        )
                        close_button.click(force=True, timeout=2000)
                        logger.info("Force-clicked shopping close button")
                    # Wait longer for page transition/animation to complete
                    page.wait_for_timeout(1500)
                    # Wait for any network activity to settle
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        # Ignore timeout, continue anyway
                        pass
                else:
                    logger.warning("Close button exists but not visible")
            else:
                logger.warning("Close button not found on page")

            # Try Escape key as well
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

            # Check if screen disappeared
            if not shopping_screen.is_visible(timeout=2000):
                logger.info("Shopping screen closed successfully")
                return True
            else:
                logger.warning(f"Shopping screen still visible after attempt {attempt}")
                # Take screenshot for debugging
                if attempt == max_close_attempts:
                    screenshot_name = (
                        f"shopping_wont_close_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    asset_id = save_page_screenshot(page, screenshot_name)
                    logger.error("Final screenshot saved to MongoDB asset: %s", asset_id)

        except Exception as e:
            logger.warning(f"Error during close attempt {attempt}: {e}")

    logger.error("Failed to close shopping screen after all attempts")
    return False


def playwright_task():
    """Core logic for the bot task."""
    import sentry_sdk

    previous_data, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    with sentry_sdk.start_transaction(op="automation.run", name="playwright-task"):
        with sync_playwright() as p:
            with sentry_sdk.start_span(op="browser.launch", name="Launch browser"):
                try:
                    browser = p.firefox.launch(headless=settings.hide_browser)
                except PlaywrightError as firefox_error:
                    firefox_message = str(firefox_error)
                    logger.warning(f"Firefox launch failed: {firefox_message}")

                    if "Executable doesn't exist" not in firefox_message:
                        raise

                    logger.warning("Firefox browser binary is missing. Trying Chromium fallback.")
                    try:
                        browser = p.chromium.launch(headless=settings.hide_browser)
                        logger.info("Launched Chromium as fallback browser.")
                    except PlaywrightError as chromium_error:
                        logger.error(f"Chromium fallback failed: {chromium_error}")
                        NotificationModule.notify(
                            title="ZZZ Bot",
                            message=(
                                "Playwright browser binaries are missing. "
                                "Run 'playwright install' and try again."
                            ),
                            app_icon=CONFIG["SAD_ICON"],
                        )
                        return

            with sentry_sdk.start_span(op="auth.storage_state", name="Load auth state"):
                context_options = build_context_options(CONFIG["STORAGE_PATH"])
                context = browser.new_context(**context_options)
                mino_page = context.new_page()

                mino_page.goto(
                    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
                )

                # Handle manual login only when neither MongoDB nor file has auth state.
                has_auth_state = (
                    load_storage_state(CONFIG["STORAGE_PATH"]) is not None
                    or os.path.exists(CONFIG["STORAGE_PATH"])
                )
                if not has_auth_state:
                    NotificationModule.notify(
                        title="ZZZ Bot",
                        message="Please log in manually",
                        app_icon=CONFIG["SAD_ICON"],
                    )
                    return

            if settings.run_task:
                Mission.run(CONFIG["OUTPUT_FILE"], mino_page, previous_data, todays_data)
                close_button = mino_page.locator(".panelBack--wW5qj")
                close_button.click()
                Notification.send_mission_data_via_email_html(todays_data)
            else:
                logger.info("Task cancelled due to setting.")

            # Phase 1: Execute shopping with existing data (before draw)
            if settings.gather_shopping_data and settings.exchange_good:
                logger.info("=== PHASE 1: Shopping Execution (Before Draw) ===")
                shopping_execution_success = (
                    ShoppingHandler.execute_shopping_with_existing_data(mino_page)
                )

                # Always close shopping screen whether execution succeeded or failed
                # to prevent interference with subsequent tasks (draw, etc.)
                _close_shopping_screen_helper(mino_page)

                if not shopping_execution_success:
                    logger.warning("Shopping execution phase failed, continuing anyway")

            if settings.draw_item:
                DrawHandler.run(mino_page)
                # Wait briefly for any overlays to disappear
                mino_page.wait_for_timeout(1000)
                close_button = mino_page.locator(".panelBack--wW5qj")
                try:
                    close_button.click(
                        force=True
                    )  # Use force to bypass intercepting elements
                except Exception as e:
                    logger.warning(f"Could not click back button: {e}")
                    # Try alternative method - press Escape key
                    mino_page.keyboard.press("Escape")
            else:
                logger.info("Draw data cancelled due to setting.")

            # Phase 2: Gather shopping data (after draw)
            if settings.gather_shopping_data:
                logger.info("=== PHASE 2: Shopping Data Gathering (After Draw) ===")
                gathering_success = ShoppingHandler.gather_shopping_data_only(mino_page)

                # Always close shopping screen whether gathering succeeded or failed
                # to ensure browser state is clean for future operations
                _close_shopping_screen_helper(mino_page)

                if gathering_success:
                    # Reschedule hunt tasks after shopping data is updated
                    schedule_hunt_tasks()
                else:
                    logger.warning("Shopping data gathering phase failed")
            else:
                logger.info("Gather data cancelled due to setting.")

            save_last_run()
            NotificationModule.notify(
                title="ZZZ Bot", message="Task finished", app_icon=CONFIG["ICON_PATH"]
            )

            with sentry_sdk.start_span(op="auth.storage_state", name="save_storage_state"):
                save_context_storage_state(context, CONFIG["STORAGE_PATH"])
            if not is_exe:
                input("Press ENTER to exit...")
            browser.close()
            if settings.exit_after_run:
                logger.info("Exiting after run as per the setting.")
                sys.exit()


def calculate_next_run() -> datetime:
    """Calculate the next scheduled run time based on current settings.

    Returns:
        datetime object of next scheduled run
    """
    now = datetime.now()
    next_run = None

    # Determine the next scheduled run time
    for scheduled_time in sorted(settings.schedule_times):
        today_scheduled = datetime.combine(
            now.date(), datetime.strptime(scheduled_time, "%H:%M").time()
        )
        # Only schedule if the time is in the future (not equal to current time)
        if now < today_scheduled:
            next_run = today_scheduled
            break

    # If all today's runs are in the past, use the first run from the next day
    if next_run is None:
        next_run = datetime.combine(
            now.date() + timedelta(days=1),
            datetime.strptime(settings.schedule_times[0], "%H:%M").time(),
        )

    return next_run


def save_last_run():
    """Save the current time as last run and calculate the next run."""
    import repositories.MongoRepository as mongo

    now = datetime.now()
    next_run = calculate_next_run()
    mongo.save_last_run(
        {
            "last_run": now.strftime("%H:%M %d/%m/%y"),
            "next_run": next_run.strftime("%H:%M %d/%m/%y"),
        }
    )


def check_missed_runs():
    """Check if any scheduled runs were missed."""
    import repositories.MongoRepository as mongo

    last_run = datetime.min
    data = mongo.get_last_run()
    if data and data.get("last_run"):
        last_run = datetime.strptime(data["last_run"], "%H:%M %d/%m/%y")

    now = datetime.now()
    for scheduled_time in settings.schedule_times:
        today_scheduled = datetime.combine(
            now.date(), datetime.strptime(scheduled_time, "%H:%M").time()
        )
        if now > today_scheduled > last_run:
            playwright_task()
            save_last_run()
            break


def schedule_hunt_tasks():
    """Schedule hunt mode tasks based on item return times.

    This should only be called after shopping data has been refreshed.
    """
    global _hunt_target_date

    # Clear existing hunt tasks before scheduling new ones
    schedule.clear("hunt")
    logger.info("Cleared old hunt schedules")

    if not settings.enable_hunt_mode:
        _hunt_target_date = None
        logger.info("Hunt mode is disabled, skipping hunt scheduling")
        return

    next_hunt_time = HuntMode.get_next_hunt_time()
    if not next_hunt_time:
        _hunt_target_date = None
        logger.info("No hunt items with return times, skipping hunt scheduling")
        return

    try:
        # Parse the hunt time format "HH:MM DD/MM/YY"
        hunt_datetime = datetime.strptime(next_hunt_time, "%H:%M %d/%m/%y")

        # Schedule EARLIER to allow buffer time for opening shopping screen
        # Subtract buffer time (2 minutes by default)
        schedule_datetime = hunt_datetime - timedelta(
            seconds=HuntMode.WAIT_BUFFER_SECONDS
        )
        now = datetime.now()

        # Only schedule if the schedule time is in the future
        if schedule_datetime > now:
            # Store target date for validation in run_hunt
            _hunt_target_date = hunt_datetime
            # Schedule at specific date and time (with buffer)
            schedule_time = schedule_datetime.strftime("%H:%M")
            schedule.every().day.at(schedule_time).do(HuntMode.run_hunt).tag("hunt")
            logger.info(
                f"Hunt mode scheduled at {schedule_datetime.strftime('%H:%M %d/%m/%y')} "
                f"(target item time: {next_hunt_time})"
            )
        else:
            _hunt_target_date = None
            logger.info(
                f"Hunt schedule time {schedule_datetime.strftime('%H:%M %d/%m/%y')} is in the past, skipping"
            )

    except ValueError as e:
        _hunt_target_date = None
        logger.error(f"Failed to parse hunt time '{next_hunt_time}': {e}")


def schedule_tasks():
    """Reschedule tasks based on current settings."""
    schedule.clear()
    for scheduled_time in settings.schedule_times:
        schedule.every().day.at(scheduled_time).do(playwright_task)

    # Note: Hunt tasks are NOT scheduled here
    # They will be scheduled only after shopping data is refreshed in playwright_task()


def run_scheduled_tasks():
    """Run scheduled tasks in a loop."""
    schedule_tasks()
    schedule_hunt_tasks()  # Restore hunt schedule on startup
    check_missed_runs()
    while True:
        schedule.run_pending()
        time.sleep(60)


# Runtime Helpers
def run_playwright_task_async():
    """Run playwright task in a background thread."""
    threading.Thread(target=playwright_task, daemon=False).start()


def resolve_playwright_browsers_path() -> str | None:
    """Return first existing Playwright browser directory for packaged/runtime modes."""
    candidates: list[str] = []

    env_browser_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if env_browser_path:
        candidates.append(env_browser_path)

    configured_path = CONFIG.get("BROWSER")
    if configured_path:
        candidates.append(configured_path)

    candidates.extend(
        [
            GlobalVar.resource_path("./playwright-browsers"),
            GlobalVar.resource_path("./backend/playwright-browsers"),
            os.path.join(os.path.dirname(sys.executable), "playwright-browsers"),
            os.path.join(os.path.dirname(sys.executable), "backend", "playwright-browsers"),
        ]
    )

    checked: set[str] = set()
    for path in candidates:
        normalized = os.path.abspath(path)
        if normalized in checked:
            continue
        checked.add(normalized)
        if os.path.isdir(normalized):
            return normalized

    return None


def configure_sentry_runtime(
    *,
    trigger_source: str = "startup",
    force_reinit: bool = False,
) -> dict[str, object]:
    """Configure Sentry from environment + current settings values."""
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        return {
            "active": False,
            "dsn_source": "none",
            "dsn_present": False,
            "environment": "production" if is_exe else "development",
            "logs_enabled": False,
            "send_test_event": False,
            "send_test_event_source": "none",
            "traces_sample_rate": 0.0,
            "traces_sample_rate_source": "fallback",
            "profiles_sample_rate": 0.0,
            "profiles_sample_rate_source": "fallback",
            "trigger_source": trigger_source,
            "reconfigured": False,
            "error": "sentry_sdk unavailable",
        }

    env_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    settings_sentry_dsn = (settings.sentry_dsn or "").strip()
    sentry_dsn = env_sentry_dsn or settings_sentry_dsn
    if env_sentry_dsn:
        sentry_dsn_source = "env:SENTRY_DSN"
    elif settings_sentry_dsn:
        sentry_dsn_source = "settings.sentry_dsn"
    else:
        sentry_dsn_source = "none"

    raw_send_sentry_test_event = os.getenv("SENTRY_SEND_TEST_EVENT")
    if raw_send_sentry_test_event is None:
        send_sentry_test_event = bool(settings.sentry_send_test_event)
        sentry_test_event_source = "settings.sentry_send_test_event"
    else:
        send_sentry_test_event = raw_send_sentry_test_event.lower() in {
            "1",
            "true",
            "yes",
        }
        sentry_test_event_source = "env:SENTRY_SEND_TEST_EVENT"

    if is_exe and send_sentry_test_event:
        logger.warning(
            "Ignoring Sentry startup test event in production runtime (source=%s)",
            sentry_test_event_source,
        )
        send_sentry_test_event = False
        sentry_test_event_source = f"{sentry_test_event_source}:ignored_in_production"

    traces_sample_rate, traces_sample_rate_source = GlobalVar.resolve_sentry_sample_rate(
        env_name="SENTRY_TRACES_SAMPLE_RATE",
        settings_name="settings.sentry_traces_sample_rate",
        settings_value=getattr(settings, "sentry_traces_sample_rate", 1.0),
        fallback_value=1.0,
    )
    profiles_sample_rate, profiles_sample_rate_source = GlobalVar.resolve_sentry_sample_rate(
        env_name="SENTRY_PROFILES_SAMPLE_RATE",
        settings_name="settings.sentry_profiles_sample_rate",
        settings_value=getattr(settings, "sentry_profiles_sample_rate", 1.0),
        fallback_value=1.0,
    )

    if send_sentry_test_event:
        # Force deterministic visibility during verification runs.
        traces_sample_rate = 1.0
        profiles_sample_rate = 1.0
        traces_sample_rate_source = "forced:test_event"
        profiles_sample_rate_source = "forced:test_event"

    enable_sentry_logs = os.getenv("SENTRY_ENABLE_LOGS", "1").lower() not in {
        "0",
        "false",
        "no",
    }

    sentry_is_active = sentry_sdk.get_client().is_active()
    reconfigured = False

    try:
        if sentry_dsn:
            if force_reinit or not sentry_is_active:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment="production" if is_exe else "development",
                    integrations=[
                        FastApiIntegration(),
                        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                    ],
                    traces_sample_rate=traces_sample_rate,
                    profiles_sample_rate=profiles_sample_rate,
                    enable_logs=enable_sentry_logs,
                    send_default_pii=False,
                )
                sentry_is_active = sentry_sdk.get_client().is_active()
                reconfigured = True
                if sentry_is_active:
                    _attach_sentry_warning_handler()
            else:
                logger.info("Sentry already initialized during startup bootstrap")

            if send_sentry_test_event and sentry_is_active:
                event_id = sentry_sdk.capture_message(
                    "ZZZ Bot startup test event",
                    level="warning",
                )
                with sentry_sdk.start_transaction(
                    op="startup",
                    name="zzz-bot-startup-profile-test",
                    sampled=True,
                ):
                    with sentry_sdk.start_span(
                        op="test.work",
                        name="profile verification span",
                    ):
                        time.sleep(0.2)

                sentry_test_logger = logging.getLogger("zzz_bot.sentry_test")
                sentry_test_logger.info("ZZZ Bot startup info log integration test")
                sentry_test_logger.warning("ZZZ Bot startup warning log integration test")
                sentry_test_logger.error("ZZZ Bot startup error log integration test")

                sentry_sdk.flush(timeout=5.0)
                logger.info("Sent Sentry startup test event: %s", event_id)
        elif not sentry_is_active:
            logger.warning("Sentry DSN not configured. Monitoring is disabled.")
    except Exception as sentry_error:
        logger.error("Failed to configure Sentry runtime: %s", sentry_error)
        return {
            "active": sentry_is_active,
            "dsn_source": sentry_dsn_source,
            "dsn_present": bool(sentry_dsn),
            "environment": "production" if is_exe else "development",
            "logs_enabled": enable_sentry_logs,
            "send_test_event": send_sentry_test_event,
            "send_test_event_source": sentry_test_event_source,
            "traces_sample_rate": traces_sample_rate,
            "traces_sample_rate_source": traces_sample_rate_source,
            "profiles_sample_rate": profiles_sample_rate,
            "profiles_sample_rate_source": profiles_sample_rate_source,
            "trigger_source": trigger_source,
            "reconfigured": reconfigured,
            "error": str(sentry_error),
        }

    return {
        "active": sentry_is_active,
        "dsn_source": sentry_dsn_source,
        "dsn_present": bool(sentry_dsn),
        "environment": "production" if is_exe else "development",
        "logs_enabled": enable_sentry_logs,
        "send_test_event": send_sentry_test_event,
        "send_test_event_source": sentry_test_event_source,
        "traces_sample_rate": traces_sample_rate,
        "traces_sample_rate_source": traces_sample_rate_source,
        "profiles_sample_rate": profiles_sample_rate,
        "profiles_sample_rate_source": profiles_sample_rate_source,
        "trigger_source": trigger_source,
        "reconfigured": reconfigured,
        "error": None,
    }


# Main Entry Point
if __name__ == "__main__":
    # === 0. Parse Arguments ===
    _parser = argparse.ArgumentParser(description="ZZZ Bot")
    _parser.add_argument("--port", type=int, default=8001)
    _parser.add_argument("--no-frontend", action="store_true")
    _parser.add_argument("--hosted-by-tauri", action="store_true")
    args = _parser.parse_args()

    hosted_by_tauri = args.hosted_by_tauri

    # === 0.25. Load runtime env vars from .env files ===
    GlobalVar.load_runtime_env()

    # === 0.5. Initialize Sentry (before everything else) ===
    _sentry_status = configure_sentry_runtime(
        trigger_source="startup",
        force_reinit=False,
    )

    # === 1. Setup Log Path and Initialize Logger (only in EXE mode) ===
    if is_exe:
        log_dir = GlobalVar.resource_path("logs", outside_path=True)
        os.makedirs(log_dir, exist_ok=True)
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(_create_file_handler(os.path.join(log_dir, "app.log")))
        app_log = logging.getLogger(__name__)
        sys.stdout = StreamToLogger(app_log, logging.INFO)
        sys.stderr = StreamToLogger(app_log, logging.ERROR)
    else:
        # Development mode - log to both console and file
        os.makedirs("backend/logs", exist_ok=True)
        file_handler = _create_file_handler("backend/logs/app.log")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        console_handler.setLevel(logging.INFO)
        console_handler.addFilter(NoImportFilter())
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(file_handler)
        root.addHandler(console_handler)
        logger.info("Running in normal Python process (dev mode)")

    # Route Python warnings (DeprecationWarning, RuntimeWarning, etc.) through
    # the logging system so they appear in the log file and reach _SentryWarningHandler.
    logging.captureWarnings(True)

    logger.info(
        "Sentry startup status: active=%s, dsn_source=%s, dsn_present=%s, environment=%s, logs_enabled=%s, send_test_event=%s, send_test_event_source=%s, traces_sample_rate=%.3f, traces_sample_rate_source=%s, profiles_sample_rate=%.3f, profiles_sample_rate_source=%s, trigger_source=%s, reconfigured=%s, error=%s",
        _sentry_status["active"],
        _sentry_status["dsn_source"],
        _sentry_status["dsn_present"],
        _sentry_status["environment"],
        _sentry_status["logs_enabled"],
        _sentry_status["send_test_event"],
        _sentry_status["send_test_event_source"],
        _sentry_status["traces_sample_rate"],
        _sentry_status["traces_sample_rate_source"],
        _sentry_status["profiles_sample_rate"],
        _sentry_status["profiles_sample_rate_source"],
        _sentry_status["trigger_source"],
        _sentry_status["reconfigured"],
        _sentry_status["error"],
    )

    browser_path = resolve_playwright_browsers_path()
    if browser_path:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_path
        logger.info("Using Playwright browser path: %s", browser_path)
    else:
        logger.warning(
            "No packaged Playwright browser directory found. Falling back to default Playwright lookup."
        )

    # === 2. Start React Dev Server (non-exe mode) ===
    if not is_exe and not args.no_frontend:
        try:
            dev_backend_url = f"http://127.0.0.1:{args.port}"
            frontend_env = os.environ.copy()
            frontend_env["VITE_BACKEND_URL"] = dev_backend_url

            logger.info(
                "Starting React dev server with VITE_BACKEND_URL=%s",
                dev_backend_url,
            )
            react_server = subprocess.Popen(
                ["bun", "run", "dev"],
                cwd="./frontend",
                shell=True,
                env=frontend_env,
                stdout=sys.__stdout__,  # Use original stdout to see dev server output
                stderr=sys.__stderr__,  # Use original stderr
            )
        except Exception as e:
            logger.error("Error starting React server: %s", e)

    # === 3. Mount Frontend (exe mode) ===
    elif is_exe:
        if args.no_frontend or hosted_by_tauri:
            logger.info("Skipping frontend mount for Tauri sidecar or --no-frontend mode")
        else:
            try:
                logger.info("Mounting frontend build...")
                app.mount(
                    "/",
                    StaticFiles(directory=CONFIG["FRONTEND_BUILD"], html=True),
                    name="ui",
                )
            except Exception as e:
                logger.error("Error mounting frontend: %s", e)
    else:
        logger.info("Frontend mounting disabled via --no-frontend")

    # === 3.5. Validate MongoDB and migrate JSON backups on first run ===
    try:
        from repositories.connection import get_db
        from utils.migrate_json_to_mongo import migrate_if_needed

        get_db()
        migrate_if_needed(
            CONFIG["OUTPUT_FOLDER"],
            CONFIG["STORAGE_PATH"],
            CONFIG["SCREENSHOT_FOLDER"],
        )
    except Exception as mongo_exc:
        logger.critical("MongoDB is required but unavailable: %s", mongo_exc)
        raise SystemExit(1) from mongo_exc

    # === 4. Start Scheduler ===
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()

    # === 5. Open Web UI ===
    if settings.open_web_ui and not hosted_by_tauri:
        logger.info("Opening web UI...")
        webbrowser.open_new_tab(CONFIG["WEB_UI_URL"])

    # === 6. Start FastAPI Server ===
    logger.info("Starting FastAPI server...")
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=args.port,
            log_config=None,
            ws="wsproto",
        )
    finally:
        if not is_exe and react_server is not None:
            try:
                react_server.send_signal(signal.CTRL_C_EVENT)
            except Exception:
                react_server.terminate()
