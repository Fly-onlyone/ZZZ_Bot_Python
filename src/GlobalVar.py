import os
import sys
from dataclasses import dataclass, field
from typing import List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from DataHandler import Serializable
from Logger import Logger
from StringUtil import clean_leading_dots


def is_exe():
    if os.getenv("SIMULATE_EXE", "0") == "1":
        sys.frozen = True
    if getattr(sys, "frozen", False):
        sys.stdout = Logger(resource_path("./../log.txt", outside_path=True))
        sys.stderr = sys.stdout
        print("running in a PyInstaller bundle")
        return True
    else:
        print("running in a normal Python process")
        return False


def resource_path(relative_path, outside_path=False):
    normalized_path = clean_leading_dots(relative_path)

    if is_exe:
        if os.getenv("SIMULATE_EXE", "0") == "1":
            return relative_path
        if outside_path:
            final_path = os.path.abspath(
                os.path.join(os.path.dirname(sys.executable), normalized_path)
            )
        else:
            final_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), normalized_path)
            )

        return final_path
    else:
        return relative_path


def generate_config(outside_folder, exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = []

    base_config = {
        "FRONTEND_BUILD": "./../frontend/dist",
        "BROWSER": "./playwright-browsers",
        "ICON_PATH": "./../images/Qingyi02.ico",
        "SAD_ICON": "./../images/Qingyi01.ico",
        "STORAGE_PATH": "./../authentication data/hoyo.json",
        "ICON_FOLDER": "./../images",
        "OUTPUT_FOLDER": "./../output",
        "SCREENSHOT_FOLDER": "./../screenshot",
        "SAMPLE_FOLDER": "./../sample",
        "MISSION_BUTTON_FOLDER": "./../mission button",
        "MISSION_NOTIFICATION": "./message/mission.html.jinja",
        "ZZZ_ICON": "./../sample/ZZZ Avatar.png",
        "OUTPUT_FILE": "./../output/missions.json",
        "LAST_RUN_FILE": "./../output/last_run.json",
        "SETTINGS_FILE": "./../output/settings.json",
        "ACCOUNT_FILE": "./../output/account.json",
        "SHOPPING_FILE": "./../output/shopping.json",
        "REDEEM_FILE": "./../output/redeem.json",
        "WEB_UI_URL": None,
    }

    # Resolve absolute paths for outside_folder values
    outside_folder_paths = {
        key: os.path.abspath(base_config[key])
        for key in outside_folder
        if key in base_config
    }

    # Apply resource_path conditionally
    def should_use_outside_folder(path):
        abs_path = os.path.abspath(path)
        return any(
            abs_path.startswith(folder_path)
            for folder_path in outside_folder_paths.values()
        )

    return {
        key: (
            (
                resource_path(value, outside_path=True)
                if should_use_outside_folder(value)
                else resource_path(value)
            )
            if key not in exclude_keys and value
            else value
        )
        for key, value in base_config.items()
    }


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
    draw_item: bool = False


@dataclass
class Account(Serializable):
    username: str = "***REMOVED***"
    password: str = ""
    app_password: str = "***REMOVED***"


is_exe = is_exe()

CONFIG = generate_config(
    ["STORAGE_PATH", "OUTPUT_FOLDER", "SCREENSHOT_FOLDER"], ["WEB_UI_URL"]
)
CONFIG["WEB_UI_URL"] = (
    "http://127.0.0.1:3000" if not is_exe else "http://127.0.0.1:8000"
)
print(CONFIG)


settings = AppSettings.load(CONFIG["SETTINGS_FILE"])
accounts = Account.load(CONFIG["ACCOUNT_FILE"])
tray_icon = None
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory=CONFIG["ICON_FOLDER"]), name="images")
app.mount(
    "/screenshot",
    StaticFiles(directory=CONFIG["SCREENSHOT_FOLDER"]),
    name="screenshots",
)
