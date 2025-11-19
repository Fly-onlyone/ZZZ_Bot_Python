import json
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
from PIL import Image
from playwright.sync_api import sync_playwright
from pystray import Icon, Menu, MenuItem
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
from core import Notification
from utils.Win32Icon import Win32Icon
from api.routes import router

# Configure logger
logger = logging.getLogger(__name__)

# Include API routes from separate module
app.include_router(router)


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

            # Check close button status
            close_button_count = close_button.count()
            logger.info(f"Close button count: {close_button_count}")

            if close_button_count > 0:
                is_visible = close_button.is_visible(timeout=2000)
                logger.info(f"Close button visible: {is_visible}")

                if is_visible:
                    close_button.click(force=True)
                    logger.info("Clicked shopping close button")
                    page.wait_for_timeout(500)
                else:
                    logger.warning("Close button exists but not visible")
            else:
                logger.warning("Close button not found on page")

            # Try Escape key as well
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            # Check if screen disappeared
            if not shopping_screen.is_visible(timeout=2000):
                logger.info("Shopping screen closed successfully")
                return True
            else:
                logger.warning(
                    f"Shopping screen still visible after attempt {attempt}"
                )
                # Take screenshot for debugging
                if attempt == max_close_attempts:
                    screenshot_path = os.path.join(
                        CONFIG["SCREENSHOT_FOLDER"],
                        f"shopping_wont_close_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    )
                    page.screenshot(path=screenshot_path)
                    logger.error(f"Final screenshot saved to: {screenshot_path}")

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
        browser = p.firefox.launch(headless=settings.hide_browser)
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
        shopping_execution_success = True
        if settings.gather_shopping_data and settings.exchange_good:
            logger.info("=== PHASE 1: Shopping Execution (Before Draw) ===")
            shopping_execution_success = ShoppingHandler.execute_shopping_with_existing_data(mino_page)

            if shopping_execution_success:
                # Close shopping screen
                _close_shopping_screen_helper(mino_page)
            else:
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

            if gathering_success:
                # Close shopping screen
                _close_shopping_screen_helper(mino_page)
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
    now = datetime.now()
    next_run = calculate_next_run()

    # Save the last and next run times to the file
    with open(CONFIG["LAST_RUN_FILE"], "w") as f:
        json.dump(
            {
                "last_run": now.strftime("%H:%M %d/%m/%y"),
                "next_run": next_run.strftime("%H:%M %d/%m/%y"),
            },
            f,
        )


def check_missed_runs():
    """Check if any scheduled runs were missed."""
    last_run = datetime.min
    if os.path.exists(CONFIG["LAST_RUN_FILE"]):
        with open(CONFIG["LAST_RUN_FILE"]) as f:
            data = json.load(f)
            last_run = datetime.strptime(data["last_run"], "%H:%M %d/%m/%y")

    now = datetime.now()
    for scheduled_time in settings.schedule_times:
        today_scheduled = datetime.combine(
            now.date(), datetime.strptime(scheduled_time, "%H:%M").time()
        )
        if now > today_scheduled > last_run:
            playwright_task()
            save_last_run()  # Save the current run time
            break


def schedule_hunt_tasks():
    """Schedule hunt mode tasks based on item return times.

    This should only be called after shopping data has been refreshed.
    """
    # Clear existing hunt tasks before scheduling new ones
    schedule.clear("hunt")
    logger.info("Cleared old hunt schedules")

    if not settings.enable_hunt_mode:
        logger.info("Hunt mode is disabled, skipping hunt scheduling")
        return

    next_hunt_time = HuntMode.get_next_hunt_time()
    if not next_hunt_time:
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
            # Schedule at specific date and time (with buffer)
            schedule_time = schedule_datetime.strftime("%H:%M")
            schedule.every().day.at(schedule_time).do(HuntMode.run_hunt).tag("hunt")
            logger.info(
                f"Hunt mode scheduled at {schedule_datetime.strftime('%H:%M %d/%m/%y')} "
                f"(target item time: {next_hunt_time})"
            )
        else:
            logger.info(
                f"Hunt schedule time {schedule_datetime.strftime('%H:%M %d/%m/%y')} is in the past, skipping"
            )

    except ValueError as e:
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
    check_missed_runs()
    while True:
        schedule.run_pending()
        time.sleep(60)


# Tray Icon Logic
def update_tray_menu():
    """Update the tray images menu."""
    GlobalVar.tray_icon.update_menu()


def run_playwright_task_async():
    """Run playwright task in a background thread."""
    threading.Thread(target=playwright_task, daemon=False).start()


def setup_tray_icon():
    """Set up the system tray images."""
    if sys.platform == "win32":
        Icon = Win32Icon
    icon_image = Image.open(CONFIG["ICON_PATH"])
    GlobalVar.tray_icon = Icon(
        "ZZZ Bot",
        icon_image,
        menu=Menu(
            MenuItem("Run Playwright", lambda item: run_playwright_task_async()),
            MenuItem(
                "Toggle Web UI",
                lambda item: toggle_setting("open_web_ui"),
                checked=lambda item: settings.open_web_ui,
            ),
            MenuItem(
                "Exit After Run",
                lambda item: toggle_setting("exit_after_run"),
                checked=lambda item: settings.exit_after_run,
            ),
            MenuItem("Exit", lambda item: on_tray_exit(GlobalVar.tray_icon)),
        ),
        on_double_click=lambda icon, _: webbrowser.open_new_tab(CONFIG["WEB_UI_URL"]),
    )
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()
    GlobalVar.tray_icon.run()


def toggle_setting(setting_name):
    """Toggle a setting value."""
    current_value = getattr(settings, setting_name)
    setattr(settings, setting_name, not current_value)
    settings.save(CONFIG["SETTINGS_FILE"])
    print(f"{setting_name} set to {not current_value}")


def on_tray_exit(icon: Icon):
    """Handle tray images exit."""
    if not is_exe:
        react_server.send_signal(signal.CTRL_C_EVENT)
    icon.stop()


# Main Entry Point
if __name__ == "__main__":
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
        # Development mode - log to console
        print("Running in normal Python process (dev mode)")

        # Configure console logging for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        console_handler.addFilter(NoImportFilter())

        # Attach handler to root logger
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(console_handler)

    # === 2. Start React Dev Server (non-exe mode) ===
    if not is_exe:
        try:
            print("Starting React dev server...")
            react_server = subprocess.Popen(
                ["npm", "run", "dev"], cwd="./frontend", shell=True
            )
        except Exception as e:
            print(f"Error starting React server: {e}")

    # === 3. Mount Frontend (exe mode) ===
    else:
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

    # === 4. Start FastAPI Server ===
    print("Starting FastAPI server...")
    threading.Thread(
        target=lambda: uvicorn.run(app, log_config=None),
        daemon=True,
    ).start()

    # === 5. Open Web UI ===
    if settings.open_web_ui:
        print("Opening web UI...")
        webbrowser.open_new_tab(CONFIG["WEB_UI_URL"])

    # === 6. Setup Tray Icon ===
    try:
        print("Setting up tray icon...")
        setup_tray_icon()
    except Exception as e:
        print(f"Error setting up tray icon: {e}")
