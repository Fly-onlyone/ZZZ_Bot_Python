import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from utils.DataHandler import Serializable
from utils.StringUtil import clean_leading_dots

logger = logging.getLogger(__name__)


def is_exe():
    if os.getenv("SIMULATE_EXE", "0") == "1":
        sys.frozen = True
    return getattr(sys, "frozen", False)


is_exe = is_exe()


def resource_path(relative_path, outside_path=False):
    normalized_path = clean_leading_dots(relative_path)

    if is_exe:
        if os.getenv("SIMULATE_EXE", "0") == "1":
            # In SIMULATE_EXE mode, use absolute paths from current directory
            # This simulates exe behavior in dev environment
            return os.path.abspath(relative_path)
        if outside_path:
            # For user data that persists outside the exe (output, screenshots, etc.)
            final_path = os.path.abspath(
                os.path.join(os.path.dirname(sys.executable), normalized_path)
            )
        else:
            # For bundled resources inside the exe (frontend, images, etc.)
            # Use sys._MEIPASS which points to the PyInstaller temporary folder
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            final_path = os.path.abspath(os.path.join(base_path, normalized_path))

        return final_path
    else:
        # Development mode: resolve paths relative to project root
        if outside_path:
            # For user data (output, screenshots, etc.)
            # Get project root: __file__ is backend/core/GlobalVar.py
            # .parent = backend/core, .parent.parent = backend, .parent.parent.parent = project root
            project_root = Path(__file__).parent.parent.parent
            return str(project_root / normalized_path)
        else:
            # For bundled resources, keep relative to allow normal imports
            return relative_path


def generate_config(outside_folder, exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = []

    base_config = {
        "FRONTEND_BUILD": "./frontend/dist",
        "BROWSER": "./backend/playwright-browsers",
        "ICON_PATH": "./images/Qingyi02.ico",
        "SAD_ICON": "./images/Qingyi01.ico",
        "STORAGE_PATH": "./authentication data/hoyo.json",
        "ICON_FOLDER": "./images",
        "OUTPUT_FOLDER": "./output",
        "SCREENSHOT_FOLDER": "./screenshot",
        "SAMPLE_FOLDER": "./sample",
        "REWARD_FOLDER": "./reward image",
        "MISSION_NOTIFICATION": "./backend/message/mission.html.jinja",
        "ZZZ_ICON": "./sample/ZZZ Avatar.png",
        "OUTPUT_FILE": "./output/missions.json",
        "LAST_RUN_FILE": "./output/last_run.json",
        "SETTINGS_FILE": "./output/settings.json",
        "ACCOUNT_FILE": "./output/account.json",
        "SHOPPING_FILE": "./output/shopping.json",
        "REDEEM_FILE": "./output/redeem.json",
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
                if not folder_path.endswith(
                    (".json", ".ico", ".png", ".html", ".jinja")
                ):
                    # It's a folder
                    if (
                        os.path.commonpath([abs_path, folder_path_normalized])
                        == folder_path_normalized
                    ):
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
    exchange_good: bool = False
    buy_all: bool = False
    draw_item: bool = False
    enable_hunt_mode: bool = False
    stop_on_failed_exchange: bool = False
    theme: str = "purple"  # purple, green, blue
    sentry_dsn: str = ""  # Override SENTRY_DSN env var if set
    mongodb_uri: str = ""  # Override MONGODB_URI env var if set


@dataclass
class Account(Serializable):
    """Account credentials for email notifications stored in MongoDB."""

    username: str = ""
    password: str = ""
    app_password: str = ""


class RedeemItem(BaseModel):
    item_name: str
    code: str
    day: str
    state: bool


CONFIG = generate_config(
    [
        "STORAGE_PATH",
        "OUTPUT_FOLDER",
        "SCREENSHOT_FOLDER",
    ],
    ["WEB_UI_URL"],
)
CONFIG["WEB_UI_URL"] = (
    "http://127.0.0.1:3000/" if not is_exe else "http://127.0.0.1:8000"
)
# Config loaded successfully (removed print to avoid exposing paths)


def load_runtime_env() -> None:
    """Load local .env files before any MongoDB initialization."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    if is_exe:
        candidates.append(Path(sys.executable).resolve().parent / ".env")

    loaded_any = False
    checked_paths = set()
    for env_path in candidates:
        resolved = env_path.resolve()
        if resolved in checked_paths:
            continue
        checked_paths.add(resolved)
        if resolved.is_file():
            load_dotenv(dotenv_path=resolved, override=False)
            loaded_any = True

    if loaded_any:
        logger.info("Loaded runtime .env configuration")


def _bootstrap_mongo() -> None:
    """Ensure Mongo is reachable and run one-time JSON migration check."""
    import sentry_sdk

    from repositories.connection import get_connection_debug_info, get_db
    from utils.migrate_json_to_mongo import migrate_if_needed

    with sentry_sdk.start_transaction(
        op="startup.mongo_bootstrap",
        name="mongo-bootstrap",
        sampled=True,
    ) as transaction:
        with sentry_sdk.start_span(op="mongo.connect", description="Connect and ping"):
            db = get_db()

        with sentry_sdk.start_span(
            op="mongo.migrate",
            description="Migrate JSON backups if needed",
        ):
            report = migrate_if_needed(
                CONFIG["OUTPUT_FOLDER"],
                CONFIG["STORAGE_PATH"],
                CONFIG["SCREENSHOT_FOLDER"],
            )

        transaction.set_tag("mongo.db_name", db.name)
        transaction.set_data("mongo.connection", get_connection_debug_info())
        transaction.set_data("mongo.migration_report", report)


def _load_settings() -> "AppSettings":
    """Load settings from MongoDB only and persist defaults when missing."""
    import sentry_sdk

    from repositories import MongoRepository
    from repositories.connection import (
        get_connection_debug_info,
        get_db,
        set_runtime_uri,
    )
    from utils.migrate_json_to_mongo import migrate_if_needed

    data = MongoRepository.get_settings()
    if data:
        valid = AppSettings.__annotations__.keys()
        loaded = AppSettings(**{k: v for k, v in data.items() if k in valid})
    else:
        loaded = AppSettings()

    # settings.mongodb_uri is the primary runtime source after bootstrap.
    set_runtime_uri(loaded.mongodb_uri)

    with sentry_sdk.start_transaction(
        op="startup.mongo_runtime_uri_sync",
        name="mongo-runtime-uri-sync",
        sampled=True,
    ) as transaction:
        with sentry_sdk.start_span(
            op="mongo.connect",
            description="Reconnect with settings.mongodb_uri",
        ):
            active_db = get_db()

        with sentry_sdk.start_span(
            op="mongo.migrate",
            description="Migrate JSON backups into active runtime DB if needed",
        ):
            runtime_report = migrate_if_needed(
                CONFIG["OUTPUT_FOLDER"],
                CONFIG["STORAGE_PATH"],
                CONFIG["SCREENSHOT_FOLDER"],
            )

        transaction.set_tag("mongo.db_name", active_db.name)
        transaction.set_data("mongo.connection", get_connection_debug_info())
        transaction.set_data("mongo.runtime_migration_report", runtime_report)

    # Read settings from the active database after applying runtime URI.
    active_data = MongoRepository.get_settings()
    if active_data:
        valid = AppSettings.__annotations__.keys()
        return AppSettings(**{k: v for k, v in active_data.items() if k in valid})

    # Ensure settings document exists in the active database.
    MongoRepository.save_settings(asdict(loaded))
    return loaded


def _load_accounts() -> "Account":
    """Load account from MongoDB only and persist defaults when missing."""
    from repositories import MongoRepository

    data = MongoRepository.get_account()
    if data:
        valid = Account.__annotations__.keys()
        return Account(**{k: v for k, v in data.items() if k in valid})

    default_account = Account()
    MongoRepository.save_account(asdict(default_account))
    return default_account


load_runtime_env()
_bootstrap_mongo()

settings = _load_settings()
accounts = _load_accounts()
tray_icon = None
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # Allow desktop/web UI origins on localhost and WebView protocols.
    allow_origins=[
        "tauri://localhost",
        "https://tauri.localhost",
        "null",  # file:// origin in some desktop webviews
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure screenshot directory exists (it's an outside path that needs creation)
os.makedirs(CONFIG["SCREENSHOT_FOLDER"], exist_ok=True)

# ICON_FOLDER is bundled with the exe, no need to create it
app.mount("/images", StaticFiles(directory=CONFIG["ICON_FOLDER"]), name="images")
app.mount(
    "/screenshot",
    StaticFiles(directory=CONFIG["SCREENSHOT_FOLDER"]),
    name="screenshots",
)
