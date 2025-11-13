import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import schedule
import uvicorn
from PIL import Image
from fastapi import BackgroundTasks, HTTPException
from playwright.sync_api import sync_playwright
from pystray import Icon, Menu, MenuItem
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

import DrawHandler
import GlobalVar
import HuntMode
import ManualLogin
import Mission
import Notification
import NotificationHelper
import ShoppingHandler
from DataHandler import (
    load_shopping_data,
    prepare_mission_data,
    load_redeem_data,
)
from GlobalVar import app, accounts, CONFIG, settings, is_exe, RedeemItem
from Logger import Logger, NoImportFilter
from ManualLogin import run, playState_lock
from Win32Icon import Win32Icon

# Configure logger
logger = logging.getLogger(__name__)


@app.get("/routes")
async def get_routes():
    # Exclude specific internal routes and clean paths
    exclude_prefixes = {
        "/docs",
        "/openapi.json",
        "/redoc",
        "/manual",
        "/images",
        "/screenshot",
        "/playstate",
    }
    routes = [
        route.path.lstrip("/")
        for route in app.routes
        if not any(route.path.startswith(prefix) for prefix in exclude_prefixes)
        and route.path != "/routes"
    ]
    return {"routes": list(dict.fromkeys(routes))}  # Deduplicate and return


@app.get("/shopping")
def get_shopping_data():
    return load_shopping_data(Path(CONFIG["SHOPPING_FILE"]))


@app.post("/shopping")
def update_shopping_data(selected: dict):
    file_path = Path(CONFIG["SHOPPING_FILE"])

    # Load existing shopping data
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Shopping file not found")

    with open(file_path, "r", encoding="utf-8") as file:
        shopping_data = json.load(file)

    # Update or add the "Selected" key
    shopping_data["Selected"] = selected.get("Selected", [])

    # Update or add the "Hunt" key
    shopping_data["Hunt"] = selected.get("Hunt", [])

    # Save the updated shopping data back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(shopping_data, file, indent=4, ensure_ascii=False)

    return {"message": "Shopping data updated successfully"}


@app.get("/redeem")
def get_redeem_data():
    return load_redeem_data(Path(CONFIG["REDEEM_FILE"]))


@app.post("/redeem")
def update_redeem_data(redeem_data: list[RedeemItem]):
    file_path = CONFIG["REDEEM_FILE"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Redeem file not found")

    try:
        # Save data without 'id' and ensure UTF-8 encoding
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                [item.model_dump() for item in redeem_data],
                file,
                indent=4,
                ensure_ascii=False,
            )

        return {"message": "Redeem data updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update redeem data: {str(e)}"
        )


@app.get("/overview/mission")
def get_mission_report():
    _, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    return todays_data


@app.get("/overview/hunt")
def get_hunt_info():
    """Return hunt mode information including hunt items and next hunt time."""
    from datetime import datetime, timedelta
    from StringUtil import calculate_return_time

    hunt_items = HuntMode.get_hunt_items()
    next_hunt_time = HuntMode.get_next_hunt_time()
    hunt_enabled = settings.enable_hunt_mode

    # Get detailed item information including availability
    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)
    items_list = shopping_data.get("Item's list", {}) if shopping_data else {}

    # Build hunt items with scheduled hunt time
    hunt_items_with_info = []
    for item_name in hunt_items:
        item_data = items_list.get(item_name, {})
        availability = item_data.get("Available", "")

        # Calculate scheduled hunt time (availability time - buffer)
        scheduled_hunt_time = None
        try:
            # Check if availability is in countdown format (e.g., "153:03:27")
            if ":" in availability and "/" not in availability:
                # Convert countdown to return time format
                availability = calculate_return_time(availability)

            # Now parse the return time format "HH:MM DD/MM/YY"
            if "/" in availability and ":" in availability:
                return_time = datetime.strptime(availability, "%H:%M %d/%m/%y")
                # Schedule hunt WAIT_BUFFER_SECONDS before item becomes available
                hunt_time = return_time - timedelta(seconds=HuntMode.WAIT_BUFFER_SECONDS)
                scheduled_hunt_time = hunt_time.strftime("%H:%M %d/%m/%y")
            else:
                scheduled_hunt_time = "Not scheduled"
        except (ValueError, Exception):
            scheduled_hunt_time = "Invalid time"

        hunt_items_with_info.append({
            "name": item_name,
            "scheduled_time": scheduled_hunt_time,
            "price": item_data.get("Price", 0),
            "inventory": item_data.get("Inventory", 0),
        })

    return {
        "enabled": hunt_enabled,
        "hunt_items": hunt_items_with_info,
        "next_hunt_time": next_hunt_time,
    }


@app.get("/account")
def get_account():
    return asdict(accounts)


@app.post("/account")
async def get_account(request: Request):
    data = await request.json()
    for key, value in data.items():
        if hasattr(accounts, key):
            setattr(accounts, key, value)
    accounts.save(CONFIG["ACCOUNT_FILE"])
    return JSONResponse({"message": "Account updated"})


@app.post("/manual")
async def manual_task(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get("url")
    play_state = data.get("playState")

    with playState_lock:
        ManualLogin.playState = play_state

    if ManualLogin.playState:
        background_tasks.add_task(run, url)
        return {"message": "Task started"}
    else:
        return {"message": "Task stopped"}


@app.get("/playstate")
async def get_play_state():
    with playState_lock:
        return {"playState": ManualLogin.playState}


@app.get("/settings")
def get_settings():
    """Return all current settings as a dictionary."""
    return asdict(settings)


@app.post("/settings")
async def update_settings(request: Request):
    """Update settings dynamically from a JSON request."""
    data = await request.json()
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    # Save updated settings and reschedule tasks
    settings.save(CONFIG["SETTINGS_FILE"])
    schedule_tasks()
    update_tray_menu()

    # Update next_run in last_run.json when schedule_times change
    if "schedule_times" in data:
        if os.path.exists(CONFIG["LAST_RUN_FILE"]):
            with open(CONFIG["LAST_RUN_FILE"]) as f:
                run_data = json.load(f)

            # Recalculate next run with new schedule times
            next_run = calculate_next_run()
            run_data["next_run"] = next_run.strftime("%H:%M %d/%m/%y")

            # Save updated data
            with open(CONFIG["LAST_RUN_FILE"], "w") as f:
                json.dump(run_data, f)

            logger.info(f"Updated next run to: {run_data['next_run']}")

    return JSONResponse({"message": "Settings updated"})


@app.get("/check-run-status")
def check_run_status():
    """Check the last run status with dynamically calculated next run."""
    # Load last run data if exists
    last_run = None
    if os.path.exists(CONFIG["LAST_RUN_FILE"]):
        with open(CONFIG["LAST_RUN_FILE"]) as f:
            data = json.load(f)
            last_run = data.get("last_run")

    # Always calculate next run dynamically based on current time and settings
    next_run = calculate_next_run()

    return {
        "last_run": last_run,
        "next_run": next_run.strftime("%H:%M %d/%m/%y"),
    }


# Bot Logic
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
            NotificationHelper.notify(
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

        # Track if shopping screen was closed successfully
        shopping_screen_closed = True  # Default to True if shopping is disabled

        if settings.gather_shopping_data:
            ShoppingHandler.run(mino_page)

            # Close the shopping screen with retry logic
            shopping_screen = mino_page.locator(".wrapper-O3T67n")  # Shopping screen selector
            close_button = mino_page.locator(".panelBack--wW5qj")

            max_close_attempts = 3
            shopping_screen_closed = False

            for attempt in range(1, max_close_attempts + 1):
                try:
                    logger.info(f"Attempting to close shopping screen (attempt {attempt}/{max_close_attempts})")

                    # Check close button status
                    close_button_count = close_button.count()
                    logger.info(f"Close button count: {close_button_count}")

                    if close_button_count > 0:
                        is_visible = close_button.is_visible(timeout=2000)
                        logger.info(f"Close button visible: {is_visible}")

                        if is_visible:
                            # Get button position for debugging
                            box = close_button.bounding_box()
                            if box:
                                logger.info(f"Close button position: x={box['x']}, y={box['y']}, width={box['width']}, height={box['height']}")

                            close_button.click(force=True)
                            logger.info("Clicked shopping close button")
                            mino_page.wait_for_timeout(500)  # Wait for click to process
                        else:
                            logger.warning("Close button exists but not visible")
                    else:
                        logger.warning("Close button not found on page")

                    # Try Escape key as well
                    mino_page.keyboard.press("Escape")
                    mino_page.wait_for_timeout(500)

                    # Check if screen disappeared
                    if not shopping_screen.is_visible(timeout=2000):
                        logger.info("Shopping screen closed successfully")
                        shopping_screen_closed = True
                        break
                    else:
                        logger.warning(f"Shopping screen still visible after attempt {attempt}")
                        # Take screenshot for debugging
                        if attempt == max_close_attempts:
                            screenshot_path = os.path.join(CONFIG["SCREENSHOT_FOLDER"], f"shopping_wont_close_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                            mino_page.screenshot(path=screenshot_path)
                            logger.error(f"Final screenshot saved to: {screenshot_path}")

                except Exception as e:
                    logger.warning(f"Error during close attempt {attempt}: {e}")

            if not shopping_screen_closed:
                logger.error("Failed to close shopping screen after all attempts")
                logger.error("Skipping draw handler to avoid conflicts")
                # Reschedule hunt tasks and skip draw
                schedule_hunt_tasks()
                NotificationHelper.notify(
                    title="ZZZ Bot - Warning",
                    message="Shopping screen won't close, skipped prize draws",
                    app_icon=CONFIG["SAD_ICON"],
                )
                # Skip to saving state
                context.storage_state(path=CONFIG["STORAGE_PATH"])
                if not is_exe:
                    input("Press ENTER to exit...")
                browser.close()
                if settings.exit_after_run:
                    logger.info("Exiting after run as per the setting.")
                    sys.exit()
                return

            # Reschedule hunt tasks after shopping data is updated
            schedule_hunt_tasks()
        else:
            logger.info("Gather data cancelled due to setting.")

        if settings.draw_item and shopping_screen_closed:
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

        save_last_run()
        NotificationHelper.notify(
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
        schedule_datetime = hunt_datetime - timedelta(seconds=HuntMode.WAIT_BUFFER_SECONDS)
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
            logger.info(f"Hunt schedule time {schedule_datetime.strftime('%H:%M %d/%m/%y')} is in the past, skipping")

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


def setup_tray_icon():
    """Set up the system tray images."""
    if sys.platform == "win32":
        Icon = Win32Icon
    icon_image = Image.open(CONFIG["ICON_PATH"])
    GlobalVar.tray_icon = Icon(
        "ZZZ Bot",
        icon_image,
        menu=Menu(
            MenuItem("Run Playwright", lambda item: playwright_task()),
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
                ["npm", "run", "dev"], cwd="./../frontend", shell=True
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
