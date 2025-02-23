import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

import schedule
import uvicorn
from PIL import Image
from fastapi import BackgroundTasks, HTTPException
from playwright.sync_api import sync_playwright
from plyer import notification
from pystray import Icon, Menu, MenuItem
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

import DrawHandler
import GlobalVar
import ManualLogin
import Mission
import Notification
import ShoppingHandler
from DataHandler import (
    load_shopping_data,
    prepare_mission_data,
    load_redeem_data,
)
from GlobalVar import app, accounts, CONFIG, settings, is_exe, RedeemItem
from ManualLogin import run, playState_lock
from Win32Icon import Win32Icon


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
    return JSONResponse({"message": "Settings updated"})


@app.get("/check-run-status")
def check_run_status():
    """Check the last run status."""
    if os.path.exists(CONFIG["LAST_RUN_FILE"]):
        with open(CONFIG["LAST_RUN_FILE"]) as f:
            data = json.load(f)
        return data
    return None


# Bot Logic
def playwright_task():
    """Core logic for the bot task."""

    previous_data, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=settings.headless_mode)
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
            notification.notify(
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
            print("Task cancelled due to setting.")

        if settings.gather_shopping_data:
            ShoppingHandler.run(mino_page)
            close_button = mino_page.locator(".panelBack--wW5qj")
            close_button.click()
        else:
            print("Gather data cancelled due to setting.")

        if settings.draw_item:
            DrawHandler.run(mino_page)
            close_button = mino_page.locator(".panelBack--wW5qj")
            close_button.click()
        else:
            print("Draw data cancelled due to setting.")

        save_last_run()
        notification.notify(
            title="ZZZ Bot", message="Task finished", app_icon=CONFIG["ICON_PATH"]
        )

        context.storage_state(path=CONFIG["STORAGE_PATH"])
        if not is_exe:
            input("Press ENTER to exit...")
        browser.close()
        if settings.exit_after_run:
            print("Exiting after run as per the setting.")
            sys.exit()


def save_last_run():
    """Save the current time as last run and calculate the next run."""
    now = datetime.now()
    next_run = None

    # Determine the next scheduled run time
    for scheduled_time in sorted(settings.schedule_times):
        today_scheduled = datetime.combine(
            now.date(), datetime.strptime(scheduled_time, "%H:%M").time()
        )
        if now <= today_scheduled:
            next_run = today_scheduled
            break

    # If all today's runs are in the past, use the first run from the next day
    if next_run is None:
        next_run = datetime.combine(
            now.date() + timedelta(days=1),
            datetime.strptime(settings.schedule_times[0], "%H:%M").time(),
        )

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


def schedule_tasks():
    """Reschedule tasks based on current settings."""
    schedule.clear()
    for scheduled_time in settings.schedule_times:
        schedule.every().day.at(scheduled_time).do(playwright_task)


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
            MenuItem("Exit", on_tray_exit),
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
    if not is_exe:
        react_server = subprocess.Popen(
            ["npm", "run", "dev"], cwd="./../frontend", shell=True
        )
    else:
        app.mount(
            "/", StaticFiles(directory=CONFIG["FRONTEND_BUILD"], html=True), name="ui"
        )
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = CONFIG["BROWSER"]

    threading.Thread(
        target=lambda: uvicorn.run(app, log_config=None), daemon=True
    ).start()

    if settings.open_web_ui:
        webbrowser.open_new_tab(CONFIG["WEB_UI_URL"])
    setup_tray_icon()
