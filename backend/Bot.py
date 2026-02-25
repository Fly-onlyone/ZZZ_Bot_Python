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
from utils.Logger import Logger, NoImportFilter
from utils.NotificationHelper import NotificationModule
from utils.screenshot_store import save_page_screenshot
from core import Notification
from api.routes import router

# Configure logger
logger = logging.getLogger(__name__)

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

    previous_data, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    with sync_playwright() as p:
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

        context_options = (
            {"storage_state": CONFIG["STORAGE_PATH"]}
            if os.path.exists(CONFIG["STORAGE_PATH"])
            else {}
        )
        context = browser.new_context(**context_options)
        mino_page = context.new_page()

        mino_page.goto(
            "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
        )

        # Handle manual login if storage path doesn't exist
        if not os.path.exists(CONFIG["STORAGE_PATH"]):
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

        context.storage_state(path=CONFIG["STORAGE_PATH"])
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


# Main Entry Point
if __name__ == "__main__":
    # === 0. Parse Arguments ===
    _parser = argparse.ArgumentParser(description="ZZZ Bot")
    _parser.add_argument("--port", type=int, default=8000)
    _parser.add_argument("--no-frontend", action="store_true")
    _parser.add_argument("--hosted-by-tauri", action="store_true")
    args = _parser.parse_args()

    hosted_by_tauri = args.hosted_by_tauri

    # === 0.25. Load runtime env vars from .env files ===
    GlobalVar.load_runtime_env()

    # === 0.5. Initialize Sentry (before everything else) ===
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    _sentry_dsn = (
        os.getenv("SENTRY_DSN")
        or (settings.sentry_dsn if settings.sentry_dsn else "")
    )
    _send_sentry_test_event = os.getenv("SENTRY_SEND_TEST_EVENT", "0") == "1"
    _default_sample_rate = "0.1" if is_exe else "1.0"
    _traces_sample_rate = float(
        os.getenv("SENTRY_TRACES_SAMPLE_RATE", _default_sample_rate)
    )
    _profiles_sample_rate = float(
        os.getenv("SENTRY_PROFILES_SAMPLE_RATE", _default_sample_rate)
    )
    if _send_sentry_test_event:
        # Force deterministic visibility during verification runs.
        _traces_sample_rate = 1.0
        _profiles_sample_rate = 1.0

    _enable_sentry_logs = os.getenv("SENTRY_ENABLE_LOGS", "1").lower() not in {
        "0",
        "false",
        "no",
    }

    if _sentry_dsn:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            environment="production" if is_exe else "development",
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            traces_sample_rate=_traces_sample_rate,
            profiles_sample_rate=_profiles_sample_rate,
            enable_logs=_enable_sentry_logs,
            send_default_pii=False,
        )

        if _send_sentry_test_event:
            # Send an explicit startup message event.
            event_id = sentry_sdk.capture_message(
                "ZZZ Bot startup test event",
                level="warning",
            )

            # Create a sampled transaction so traces/profiles can be verified.
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

            # Emit multiple log levels to verify log ingestion.
            sentry_test_logger = logging.getLogger("zzz_bot.sentry_test")
            sentry_test_logger.info("ZZZ Bot startup info log integration test")
            sentry_test_logger.warning("ZZZ Bot startup warning log integration test")
            sentry_test_logger.error("ZZZ Bot startup error log integration test")

            sentry_sdk.flush(timeout=5.0)
            logger.info(f"Sent Sentry startup test event: {event_id}")
    else:
        logger.warning("Sentry DSN not configured. Monitoring is disabled.")

    # === 1. Setup Log Path and Initialize Logger (only in EXE mode) ===
    if is_exe:
        # ensure logs dir exists
        os.makedirs("logs", exist_ok=True)

        # configure root logger *only* with your rotating handler
        handler = TimedRotatingFileHandler(
            filename="logs/app.log",
            when="D",  # rollover every day
            interval=1,  # 1-day interval
            backupCount=7,  # KEEP only 7 days of logs
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handler.addFilter(NoImportFilter())

        # attach handler to root logger
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(handler)

        app_log = logging.getLogger(__name__)
        sys.stdout = Logger(app_log, logging.INFO)
        sys.stderr = Logger(app_log, logging.ERROR)
    else:
        # Development mode - log to both console and file
        print("Running in normal Python process (dev mode)")

        # Ensure logs directory exists
        os.makedirs("backend/logs", exist_ok=True)

        # Configure file logging for development
        file_handler = TimedRotatingFileHandler(
            filename="backend/logs/app.log",
            when="D",  # rollover every day
            interval=1,  # 1-day interval
            backupCount=7,  # Keep only 7 days of logs
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        file_handler.addFilter(NoImportFilter())

        # Configure console logging for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        console_handler.addFilter(NoImportFilter())

        # Attach both handlers to root logger
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    # === 2. Start React Dev Server (non-exe mode) ===
    if not is_exe and not args.no_frontend:
        try:
            dev_backend_url = f"http://127.0.0.1:{args.port}"
            frontend_env = os.environ.copy()
            frontend_env["VITE_BACKEND_URL"] = dev_backend_url

            print("Starting React dev server...")
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
            print(f"Error starting React server: {e}")

    # === 3. Mount Frontend (exe mode) ===
    elif is_exe:
        try:
            print("Mounting frontend build and setting browser path...")
            app.mount(
                "/",
                StaticFiles(directory=CONFIG["FRONTEND_BUILD"], html=True),
                name="ui",
            )
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = CONFIG["BROWSER"]
        except Exception as e:
            print(f"Error mounting frontend: {e}")
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
        print("Opening web UI...")
        webbrowser.open_new_tab(CONFIG["WEB_UI_URL"])

    # === 6. Start FastAPI Server ===
    print("Starting FastAPI server...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_config=None)
    finally:
        if not is_exe and react_server is not None:
            try:
                react_server.send_signal(signal.CTRL_C_EVENT)
            except Exception:
                react_server.terminate()
