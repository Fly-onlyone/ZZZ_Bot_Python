import json
import os
import sys
import threading
import time
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
import webbrowser

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

ICON_PATH = "./Qingyi02.ico"
STORAGE_PATH = './authentication data/hoyo.json'
OUTPUT_FOLDER = './bot data'
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, 'missions.json')
LAST_RUN_FILE = os.path.join(OUTPUT_FOLDER, 'last_run.json')
exit_after_run = False
open_web_ui = True
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
    if exit_after_run:
        print("Exiting after run as per the setting.")
        sys.exit()


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html.jinja", {"request": request, "schedule_times": SCHEDULE_TIMES,
                                                           "exit_after_run": exit_after_run})


def load_settings():
    global SCHEDULE_TIMES, exit_after_run_value
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            SCHEDULE_TIMES = settings.get("schedule_times", SCHEDULE_TIMES)
            exit_after_run_value = settings.get("exit_after_run", exit_after_run)


def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({"schedule_times": SCHEDULE_TIMES, "exit_after_run": exit_after_run_value}, f)


@app.post("/update-settings")
async def update_settings(schedule_times: str = Form(...), exit_after_run: str = Form("off")):
    global SCHEDULE_TIMES, exit_after_run_value
    SCHEDULE_TIMES = schedule_times.split(",")
    exit_after_run_value = exit_after_run == "on"

    # Save settings to persist changes
    save_settings()

    schedule.clear()  # Clear existing schedule
    schedule_tasks()  # Re-schedule tasks with updated times
    return RedirectResponse(url="/", status_code=303)


def check_missed_runs():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            last_run = datetime.fromisoformat(data["last_run"])
    else:
        last_run = datetime.min  # Never run before

    now = datetime.now()
    for scheduled_time in SCHEDULE_TIMES:
        today_scheduled = datetime.combine(now.date(), datetime.strptime(scheduled_time, "%H:%M").time())

        # Check if scheduled time has passed and the bot hasn't run since then
        if today_scheduled < now and last_run < today_scheduled:
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


def on_tray_exit(icon, item):
    icon.stop()


def setup_tray_icon():
    icon_image = Image.open(ICON_PATH)
    icon = Icon("ZZZ Bot", icon_image, menu=Menu(
        MenuItem("Exit", on_tray_exit),
        MenuItem("Close after run", lambda icon, item: toggle_exit_after_run()),
        MenuItem("Toggle Web UI", lambda icon, item: toggle_open_web_ui())
    ))
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()
    icon.run()


def toggle_exit_after_run():
    global exit_after_run
    exit_after_run = not exit_after_run
    print(f"Exit after run set to {exit_after_run}")


def toggle_open_web_ui():
    global open_web_ui
    open_web_ui = not open_web_ui
    print(f"Open Web UI set to {open_web_ui}")


if __name__ == "__main__":
    load_settings()
    if open_web_ui:
        webbrowser.open_new_tab(WEB_UI_URL)
        threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000), daemon=True).start()
    setup_tray_icon()
