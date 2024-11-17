import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime

import schedule
import uvicorn
from PIL import Image
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from playwright.sync_api import sync_playwright
from plyer import notification
from pystray import Icon, Menu, MenuItem

import Mission
import Notification
from DataHandler import prepare_data

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ICON_PATH = "./../Qingyi02.ico"
STORAGE_PATH = './../authentication data/hoyo.json'
OUTPUT_FOLDER = './../bot data'
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, 'missions.json')

LAST_RUN_FILE = os.path.join(OUTPUT_FOLDER, 'last_run.json')
EXIT_AFTER_RUN = False
OPEN_WEB_UI = True
SCHEDULE_TIMES = ["08:00", "20:00"]
WEB_UI_URL = "http://127.0.0.1:8000"
SETTINGS_FILE = os.path.join(OUTPUT_FOLDER, 'settings.json')


def playwright_task():
    previous_data, todays_data = prepare_data(OUTPUT_FOLDER, OUTPUT_FILE)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context_options = {"storage_state": STORAGE_PATH} if os.path.exists(STORAGE_PATH) else {}
        context = browser.new_context(**context_options)
        page = context.new_page()

        page.goto(
            'https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?from=zzz&hyl_presentation_style=fullscreen&hyl_auth_required=true&hyl_portrait=true&hyl_hide_status_bar=true&lang=en-us&bbs_theme=dark&bbs_theme_device=1')

        # If storage path doesn't exist, prompt the user to log in manually
        if not os.path.exists(STORAGE_PATH):
            print('Please log in manually...')
            page.wait_for_timeout(120000)  # Wait 2 minutes for manual login
            context.storage_state(path=STORAGE_PATH)
            print('Login session saved.')

        Mission.run(OUTPUT_FILE, page, previous_data, todays_data)
        Notification.send_mission_data_via_email_html(todays_data)

        notification.notify(title='ZZZ Bot', message='Task finished!', app_icon=ICON_PATH)

        # Save the current run timestamp
        with open(LAST_RUN_FILE, 'w') as f:
            json.dump({"last_run": datetime.now().isoformat()}, f)

    # Exit the app if exit_after_run is set to True
    if EXIT_AFTER_RUN:
        print("Exiting after run as per the setting.")
        sys.exit()


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html.jinja", {"request": request, "schedule_times": SCHEDULE_TIMES,
                                                           "exit_after_run": EXIT_AFTER_RUN})


def load_settings():
    global SCHEDULE_TIMES, EXIT_AFTER_RUN, OPEN_WEB_UI
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
            SCHEDULE_TIMES = settings.get("schedule_times", SCHEDULE_TIMES)
            EXIT_AFTER_RUN = settings.get("exit_after_run", EXIT_AFTER_RUN)
            OPEN_WEB_UI = settings.get("open_web_ui", OPEN_WEB_UI)


def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({"schedule_times": SCHEDULE_TIMES, "exit_after_run": EXIT_AFTER_RUN, "open_web_ui": OPEN_WEB_UI}, f)


@app.post("/update-settings")
async def update_settings(schedule_times: str = Form(...), exit_after_run: str = Form("off")):
    global SCHEDULE_TIMES, EXIT_AFTER_RUN
    SCHEDULE_TIMES = schedule_times.split(",")
    EXIT_AFTER_RUN = exit_after_run == "on"

    # Save settings to persist changes
    save_settings()

    schedule.clear()  # Clear existing schedule
    schedule_tasks()  # Re-schedule tasks with updated times
    return RedirectResponse(url="/", status_code=303)


def check_missed_runs():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE) as f:
            data = json.load(f)
            last_run = datetime.fromisoformat(data["last_run"])
    else:
        last_run = datetime.min  # Never run before

    now = datetime.now()
    for scheduled_time in SCHEDULE_TIMES:
        today_scheduled = datetime.combine(now.date(), datetime.strptime(scheduled_time, "%H:%M").time())

        if now > today_scheduled > last_run:
            playwright_task()
            break  # Run only once if missed


def schedule_tasks():
    for scheduled_time in SCHEDULE_TIMES:
        schedule.every().day.at(scheduled_time).do(playwright_task)


def run_scheduled_tasks():
    check_missed_runs()
    while True:
        schedule.run_pending()
        time.sleep(60)


def on_tray_exit(icon):
    icon.stop()


def setup_tray_icon():
    icon_image = Image.open(ICON_PATH)
    tray_icon: Icon = Icon("ZZZ Bot", icon_image, menu=Menu(
        MenuItem(
            "Close after run",
            lambda item: toggle_value("exit_after_run", "Close after run"),
            lambda item: EXIT_AFTER_RUN
        ),
        MenuItem(
            "Toggle web UI",
            lambda item: toggle_value("open_web_ui", "Toggle Web UI"),
            lambda item: OPEN_WEB_UI,
        ),
        MenuItem("Open web UI", lambda item: webbrowser.open_new_tab(WEB_UI_URL), visible=False, default=True),
        MenuItem("Exit", on_tray_exit)
    ))
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()
    tray_icon.run()


def toggle_value(global_var_name, text):
    # Access the global variable by its name
    global_vars = globals()

    if global_var_name in global_vars:
        current_value = global_vars[global_var_name]
        new_value = not current_value
        global_vars[global_var_name] = new_value  # Update the global variable
        print(f"{text} set to {new_value}")
    else:
        print(f"Error: Global variable '{global_var_name}' not found.")

    save_settings()


if __name__ == "__main__":
    load_settings()
    threading.Thread(target=lambda: uvicorn.run(app), daemon=True).start()
    if OPEN_WEB_UI:
        webbrowser.open_new_tab(WEB_UI_URL)
    setup_tray_icon()
