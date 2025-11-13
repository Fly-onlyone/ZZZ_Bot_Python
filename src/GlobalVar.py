import os
import sys
from dataclasses import dataclass, field
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from DataHandler import Serializable
from StringUtil import clean_leading_dots


def is_exe():
    if os.getenv("SIMULATE_EXE", "0") == "1":
        sys.frozen = True
    return getattr(sys, "frozen", False)


is_exe = is_exe()


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
        "REWARD_FOLDER": "./../reward image",
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

    # Apply resource_path conditionally with secure path checking
    def should_use_outside_folder(path):
        abs_path = os.path.abspath(os.path.normpath(path))
        # Use normalized paths to prevent traversal attacks
        for folder_path in outside_folder_paths.values():
            try:
                # Normalize folder_path to handle both files and folders
                folder_path_normalized = os.path.normpath(folder_path)
                # If folder_path is a file, use its directory
                if not folder_path.endswith(('.json', '.ico', '.png', '.html', '.jinja')):
                    # It's a folder
                    if os.path.commonpath([abs_path, folder_path_normalized]) == folder_path_normalized:
                        return True
                else:
                    # It's a file, check if paths match
                    if abs_path == folder_path_normalized:
                        return True
            except ValueError:
                # Paths are on different drives on Windows, skip
                continue
        return False

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
    hide_browser: bool = False
    run_task: bool = True
    gather_shopping_data: bool = True
    redeem_after_gather_data: bool = False
    buy_all: bool = False
    draw_item: bool = False
    enable_hunt_mode: bool = False
    stop_on_failed_exchange: bool = False


@dataclass
class Account(Serializable):
    """Account credentials for email notifications. Load from output/account.json."""
    username: str = ""
    password: str = ""
    app_password: str = ""


class RedeemItem(BaseModel):
    item_name: str
    code: str
    day: str
    state: bool


CONFIG = generate_config(
    ["STORAGE_PATH", "OUTPUT_FOLDER", "SCREENSHOT_FOLDER"], ["WEB_UI_URL"]
)
CONFIG["WEB_UI_URL"] = (
    "http://127.0.0.1:3000/" if not is_exe else "http://127.0.0.1:8000"
)
# Config loaded successfully (removed print to avoid exposing paths)


settings = AppSettings.load(CONFIG["SETTINGS_FILE"])
accounts = Account.load(CONFIG["ACCOUNT_FILE"])
tray_icon = None
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # Restrict to localhost only for security (desktop app)
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow needed methods
    allow_headers=["Content-Type"],  # Only allow needed headers
)
app.mount("/images", StaticFiles(directory=CONFIG["ICON_FOLDER"]), name="images")
app.mount(
    "/screenshot",
    StaticFiles(directory=CONFIG["SCREENSHOT_FOLDER"]),
    name="screenshots",
)
