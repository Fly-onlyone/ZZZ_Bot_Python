import os
import sys
from dataclasses import dataclass, field
from typing import List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from DataHandler import Serializable

if os.getenv("SIMULATE_EXE", "0") == "1":
    sys.frozen = True
    sys._MEIPASS = os.path.abspath(".")

if os.getenv("SIMULATE_EXE", "0") == "1":
    sys.frozen = True
    sys._MEIPASS = os.path.abspath(".")


def is_development_mode():
    if getattr(sys, "frozen", False):
        print("Running as an executable")
        return False
    else:
        print("Running in development mode")
        return True


def resource_path(relative_path):
    """
    Get the absolute path to a resource. Handles both development and executable modes.
    Resolves paths like ./../ to absolute paths.
    """
    normalized_path = os.path.normpath(
        relative_path
    )  # Normalize path (removes ./ and ../)
    if hasattr(sys, "_MEIPASS"):
        return os.path.abspath(os.path.join(sys._MEIPASS,normalized_path))
    return os.path.abspath(normalized_path)  # Resolve absolute path


def generate_config(exclude_keys=None):
    """
    Generate CONFIG dictionary with resource_path applied conditionally.

    Args:
        exclude_keys (list): Keys to exclude from applying resource_path.

    Returns:
        dict: Generated CONFIG dictionary.
    """
    if exclude_keys is None:
        exclude_keys = []

    base_config = {
        "FRONTEND_BUILD": "./../frontend/dist",
        "ICON_PATH": "./../images/Qingyi02.ico",
        "SAD_ICON": "./../images/Qingyi01.ico",
        "STORAGE_PATH": "./../authentication data/hoyo.json",
        "ICON_FOLDER": "./../images",
        "OUTPUT_FOLDER": "./../output",
        "SCREENSHOT_FOLDER": "./../screenshot",
        "SAMPLE_FOLDER": "./../sample",
        "MISSION_BUTTON_FOLDER": "./../mission button",
        "MISSION_NOTIFICATION": "message/mission.html.jinja",
        "ZZZ_ICON": "./../sample/ZZZ Avatar.png",
        "OUTPUT_FILE": "./../output/missions.json",
        "LAST_RUN_FILE": "./../output/last_run.json",
        "SETTINGS_FILE": "./../output/settings.json",
        "ACCOUNT_FILE": "./../output/account.json",
        "SHOPPING_FILE": "./../output/shopping.json",
        "REDEEM_FILE": "./../output/redeem.json",
        "WEB_UI_URL": None,
    }

    # Apply resource_path only to keys not in the exclude list
    return {
        key: resource_path(value) if key not in exclude_keys and value else value
        for key, value in base_config.items()
    }


CONFIG = generate_config(["WEB_UI_URL"])
CONFIG["WEB_UI_URL"] = (
    "http://127.0.0.1:3000" if is_development_mode() else "http://127.0.0.1:8000"
)
print(CONFIG)


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
    username: str = "galevan61"
    password: str = ""
    app_password: str = "jlqrqxxtaggvnuce"


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
