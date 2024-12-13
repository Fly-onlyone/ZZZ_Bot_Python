from dataclasses import dataclass, field
from typing import List
import sys
import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.DataHandler import Serializable

CONFIG = {
    "ICON_PATH": "./../images/Qingyi02.ico",
    "SAD_ICON": "./../images/Qingyi01.ico",
    "STORAGE_PATH": "./../authentication data/hoyo.json",
    "ICON_FOLDER": "./../images",
    "OUTPUT_FOLDER": "./../output",
    "OUTPUT_FILE": "./../output/missions.json",
    "LAST_RUN_FILE": "./../output/last_run.json",
    "SETTINGS_FILE": "./../output/settings.json",
    "ACCOUNT_FILE": "./../output/account.json",
    "SHOPPING_FILE": "./../output/shopping.json",
    "REDEEM_FILE": "./../output/redeem.json",
    "WEB_UI_URL": None,
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
app.mount("/screenshot", StaticFiles(directory="./../screenshot"), name="screenshots")


def is_development_mode():
    if os.getenv("SIMULATE_EXE", "0") == "1":
        sys.frozen = True
        sys._MEIPASS = os.path.abspath(".")
    else:
        sys.frozen = False

    if getattr(sys, "frozen", False):
        print("Running as an executable")
        return False
    else:
        print("Running in development mode")
        return True


CONFIG["WEB_UI_URL"] = (
    "http://127.0.0.1:3000" if is_development_mode() else "http://127.0.0.1:8000"
)
