import asyncio
import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List

import schedule
import uvicorn
from PIL import Image
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from playwright.sync_api import sync_playwright
from plyer import notification
from pystray import Icon, Menu, MenuItem
from starlette.middleware.cors import CORSMiddleware

import Mission
import Notification
from DataHandler import prepare_mission_data
from src import ShoppingHandler, RedeemAutofill, ManualLogin
from src.DataHandler import Serializable, load_shopping_data


# Data Classes
@dataclass
class AppSettings(Serializable):

    schedule_times: List[str] = field(default_factory=lambda: ["08:00", "20:00"])
    exit_after_run: bool = False
    open_web_ui: bool = True
    headless_mode: bool = False
    run_task: bool = True
    gather_shopping_data: bool = True
    redeem_after_gather_data: bool = False
    buy_all: bool = False


@dataclass
class Account(Serializable):
    username: str = "galevan61"
    password: str = ""
    app_password: str = "jlqrqxxtaggvnuce"


# Configuration
CONFIG = {
    "ICON_PATH": "./../Qingyi02.ico",
    "SAD_ICON": "./../Qingyi01.ico",
    "STORAGE_PATH": "./../authentication data/hoyo.json",
    "OUTPUT_FOLDER": "./../output",
    "OUTPUT_FILE": "./../output/missions.json",
    "LAST_RUN_FILE": "./../output/last_run.json",
    "SETTINGS_FILE": "./../output/settings.json",
    "ACCOUNT_FILE": "./../output/account.json",
    "SHOPPING_FILE": "./../output/shopping.json",
    "REDEEM_FILE": "./../output/redeem.json",
    "WEB_UI_URL": "http://127.0.0.1:3000",
}

# Initialize global state
settings = AppSettings.load(CONFIG["SETTINGS_FILE"])
accounts = Account.load(CONFIG["ACCOUNT_FILE"])
tray_icon = None

# App Initialization
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/overview/mission")
def get_mission_report():
    _, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    return todays_data


# FastAPI Endpoints
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
    background_tasks.add_task(ManualLogin.run, data["url"])
    return JSONResponse({"message": "Handle login in the background"})


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
            last_run = datetime.fromisoformat(data["last_run"])
        return {"last_run": last_run}
    return {"last_run": None}


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
            print("Please log in manually...")
            mino_page.wait_for_timeout(120000)
            context.storage_state(path=CONFIG["STORAGE_PATH"])
            print("Login session saved.")

        if settings.run_task:
            Mission.run(CONFIG["OUTPUT_FILE"], mino_page, previous_data, todays_data)
            close_button = mino_page.locator(".panelBack--wW5qj")
            close_button.click()
            Notification.send_mission_data_via_email_html(todays_data)
        else:
            print("Task cancelled due to setting.")

        if settings.gather_shopping_data:
            ShoppingHandler.run(mino_page)
        else:
            print("Gather data cancelled due to setting.")

        # RedeemAutofill.run(context)

        save_last_run()
        notification.notify(
            title="ZZZ Bot", message="Task finished", app_icon=CONFIG["ICON_PATH"]
        )

        input("Press ENTER to exit...")
        if settings.exit_after_run:
            print("Exiting after run as per the setting.")
            sys.exit()


def save_last_run():
    """Save the timestamp of the last run."""
    with open(CONFIG["LAST_RUN_FILE"], "w") as f:
        json.dump({"last_run": datetime.now().isoformat()}, f)


# Scheduling Logic
def check_missed_runs():
    """Check if any scheduled runs were missed."""
    last_run = datetime.min
    if os.path.exists(CONFIG["LAST_RUN_FILE"]):
        with open(CONFIG["LAST_RUN_FILE"]) as f:
            data = json.load(f)
            last_run = datetime.fromisoformat(data["last_run"])

    now = datetime.now()
    for scheduled_time in settings.schedule_times:
        today_scheduled = datetime.combine(
            now.date(), datetime.strptime(scheduled_time, "%H:%M").time()
        )
        if now > today_scheduled > last_run:
            playwright_task()
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
    """Update the tray icon menu."""
    tray_icon.update_menu()


def setup_tray_icon():
    """Set up the system tray icon."""
    icon_image = Image.open(CONFIG["ICON_PATH"])
    global tray_icon
    tray_icon = Icon(
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
    )
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()
    tray_icon.run()


def toggle_setting(setting_name):
    """Toggle a setting value."""
    current_value = getattr(settings, setting_name)
    setattr(settings, setting_name, not current_value)
    settings.save(CONFIG["SETTINGS_FILE"])
    print(f"{setting_name} set to {not current_value}")


def on_tray_exit(icon: Icon):
    """Handle tray icon exit."""
    react_server.send_signal(signal.CTRL_C_EVENT)
    icon.stop()


# Main Entry Point
if __name__ == "__main__":
    react_server = subprocess.Popen(
        ["npm", "run", "dev"], cwd="./../frontend", shell=True
    )
    threading.Thread(target=lambda: uvicorn.run(app), daemon=True).start()
    if settings.open_web_ui:
        webbrowser.open_new_tab(CONFIG["WEB_UI_URL"])
    setup_tray_icon()
