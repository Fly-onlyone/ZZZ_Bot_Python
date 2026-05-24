import logging
import os
import sys
import threading
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

STARTUP_PHASE_BOOTING = "booting"
STARTUP_PHASE_WARMING = "warming"
STARTUP_PHASE_READY = "ready"
STARTUP_PHASE_ERROR = "error"


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
        key: os.path.abspath(base_config[key]) for key in outside_folder if key in base_config
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
                if not folder_path.endswith((".json", ".ico", ".png", ".html", ".jinja")):
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
    show_window_on_startup: bool = True
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None
    window_maximized: bool = False
    window_minimized: bool = False
    autostart_on_login: bool | None = None
    hide_browser: bool = False
    run_task: bool = True
    gather_shopping_data: bool = True
    exchange_good: bool = False
    buy_all: bool = False
    draw_item: bool = False
    enable_hunt_mode: bool = False
    stop_on_failed_exchange: bool = False
    hunt_poll_max_wait_seconds: int = 180
    hunt_poll_interval_seconds: int = 1
    hunt_poll_backoff_enabled: bool = True
    hunt_early_exit_on_unavailable: bool = False
    theme: str = "nebula"
    sentry_dsn: str = ""  # Backend DSN (overrides SENTRY_DSN env var)
    sentry_frontend_dsn: str = ""  # Frontend DSN fallback when Vite env is unset
    sentry_send_test_event: bool = False
    sentry_traces_sample_rate: float = 1.0


@dataclass
class Account(Serializable):
    """Account credentials for HoYoLab login and email notifications."""

    # HoYo Account
    hoyo_username: str = ""
    hoyo_password: str = ""
    # Apprise Notification (Gmail SMTP)
    username: str = ""
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
CONFIG["WEB_UI_URL"] = "http://127.0.0.1:3000/" if not is_exe else "http://127.0.0.1:8000"
# Config loaded successfully (removed print to avoid exposing paths)


def load_runtime_env() -> None:
    """Load local .env files before any storage initialization."""
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


def parse_sample_rate_value(raw_value: object, source_name: str) -> float | None:
    if raw_value is None:
        return None

    value_text = str(raw_value).strip()
    if not value_text:
        return None

    try:
        parsed_value = float(value_text)
    except ValueError:
        logger.warning("Invalid %s='%s'; ignoring value", source_name, value_text)
        return None

    if not 0.0 <= parsed_value <= 1.0:
        logger.warning(
            "Out-of-range %s=%.3f; expected 0.0-1.0, ignoring value",
            source_name,
            parsed_value,
        )
        return None

    return parsed_value


def parse_sample_rate(env_name: str, default_value: float) -> float:
    parsed_value = parse_sample_rate_value(os.getenv(env_name), env_name)
    if parsed_value is None:
        return default_value
    return parsed_value


def resolve_sentry_sample_rate(
    *,
    env_name: str,
    settings_name: str,
    settings_value: object,
    fallback_value: float = 1.0,
) -> tuple[float, str]:
    env_value = parse_sample_rate_value(os.getenv(env_name), env_name)
    if env_value is not None:
        return env_value, f"env:{env_name}"

    settings_rate = parse_sample_rate_value(settings_value, settings_name)
    if settings_rate is not None:
        return settings_rate, f"settings:{settings_name}"

    return fallback_value, "fallback"


def _env_flag_enabled(env_name: str, default_value: bool = True) -> bool:
    raw_value = os.getenv(env_name)
    if raw_value is None:
        return default_value
    return raw_value.lower() not in {"0", "false", "no"}


def default_sentry_logs_enabled() -> bool:
    """Keep Sentry Logs on in both dev and installed builds."""
    return True


def sentry_logs_enabled_from_env() -> bool:
    """Resolve Sentry log collection using the runtime default for the current mode."""
    return _env_flag_enabled(
        "SENTRY_ENABLE_LOGS",
        default_value=default_sentry_logs_enabled(),
    )


def _init_startup_sentry_if_configured() -> None:
    """Initialize Sentry early so startup transactions are captured."""
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        return

    if sentry_sdk.get_client().is_active():
        return

    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if not sentry_dsn:
        return

    default_sample_rate = 1.0
    traces_sample_rate = parse_sample_rate(
        "SENTRY_TRACES_SAMPLE_RATE",
        default_sample_rate,
    )
    enable_logs = sentry_logs_enabled_from_env()

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment="production" if is_exe else "development",
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            auto_enabling_integrations=False,
            traces_sample_rate=traces_sample_rate,
            enable_logs=enable_logs,
            send_default_pii=False,
        )
        logger.info("Initialized Sentry during startup bootstrap")
    except Exception as exc:
        logger.warning("Failed to initialize startup Sentry: %s", exc)


def _bootstrap_storage() -> None:
    """Open the SQLite database and create the schema before loading state."""
    import sentry_sdk
    from repositories import DataStore
    from repositories.connection import get_connection_debug_info

    with sentry_sdk.start_span(
        op="startup.storage_bootstrap",
        name="storage-bootstrap",
    ) as span:
        DataStore.ensure_schema()
        span.set_data("storage.connection", get_connection_debug_info())


def _load_settings() -> "AppSettings":
    """Load settings from the database, persisting defaults when missing."""
    from repositories import DataStore

    valid = AppSettings.__annotations__.keys()
    data = DataStore.get_settings()
    if data:
        loaded = AppSettings(**{k: v for k, v in data.items() if k in valid})
        # Re-persist when the stored document carried unknown or legacy keys.
        if any(key not in valid for key in data):
            DataStore.save_settings(asdict(loaded))
        return loaded

    default_settings = AppSettings()
    DataStore.save_settings(asdict(default_settings))
    return default_settings


def _load_accounts() -> "Account":
    """Load account from the database, persisting defaults when missing."""
    from repositories import DataStore

    data = DataStore.get_account()
    if data:
        # Migrate old-format documents to new hoyo_username/hoyo_password fields
        migrated = False
        if "password" in data and not data.get("hoyo_password"):
            data["hoyo_password"] = data["password"]
            migrated = True
        if not data.get("hoyo_username") and data.get("username"):
            data["hoyo_username"] = data["username"] + "@gmail.com"
            migrated = True
        if migrated:
            DataStore.save_account(data)

        valid = Account.__annotations__.keys()
        return Account(**{k: v for k, v in data.items() if k in valid})

    default_account = Account()
    DataStore.save_account(asdict(default_account))
    return default_account


settings = AppSettings()
accounts = Account()
app = FastAPI()
_startup_lock = threading.RLock()
_startup_phase = STARTUP_PHASE_BOOTING
_startup_ready = False
_startup_error: str | None = None
_settings_loaded = False
_accounts_loaded = False
_deferred_startup_started = False


def _apply_dataclass_values(target, source) -> None:
    """Copy dataclass field values into a shared runtime instance."""
    for field_name in target.__dataclass_fields__:
        setattr(target, field_name, getattr(source, field_name))


def initialize_runtime_state() -> AppSettings:
    """Load runtime configuration needed before the API starts serving."""
    global _settings_loaded, _startup_phase, _startup_ready, _startup_error

    with _startup_lock:
        if _settings_loaded:
            return settings

        _startup_phase = STARTUP_PHASE_BOOTING
        _startup_ready = False
        _startup_error = None

        try:
            load_runtime_env()
            _init_startup_sentry_if_configured()
            import sentry_sdk

            with sentry_sdk.start_transaction(
                op="startup",
                name="critical-bootstrap",
                sampled=True,
            ):
                _bootstrap_storage()
                loaded_settings = _load_settings()

            _apply_dataclass_values(settings, loaded_settings)
            _settings_loaded = True
            _startup_ready = True
            _startup_phase = STARTUP_PHASE_WARMING
            return settings
        except Exception as exc:
            _startup_phase = STARTUP_PHASE_ERROR
            _startup_error = str(exc)
            logger.error("Critical startup bootstrap failed: %s", exc)
            raise


def ensure_accounts_loaded() -> Account:
    """Lazily load persisted account credentials on first use."""
    global _accounts_loaded

    initialize_runtime_state()

    with _startup_lock:
        if _accounts_loaded:
            return accounts

        loaded_accounts = _load_accounts()
        _apply_dataclass_values(accounts, loaded_accounts)
        _accounts_loaded = True
        return accounts


def _run_deferred_startup_tasks() -> None:
    """Warm non-critical state after the backend is already usable."""
    global _startup_phase, _startup_error

    try:
        from repositories import DataStore

        DataStore.ensure_schema()
        redemption_repair_report = DataStore.repair_redemptions_indexed_at_once()
        _startup_phase = STARTUP_PHASE_READY
        _startup_error = None
        logger.info(
            "Deferred startup warmup completed: redemptions_updated=%s",
            redemption_repair_report["updated"],
        )
    except Exception as exc:
        _startup_phase = STARTUP_PHASE_READY
        _startup_error = str(exc)
        logger.exception("Deferred startup warmup failed")


def start_deferred_startup_tasks() -> None:
    """Start deferred startup work once the critical path is complete."""
    global _deferred_startup_started

    initialize_runtime_state()

    with _startup_lock:
        if _deferred_startup_started:
            return
        _deferred_startup_started = True

    threading.Thread(
        target=_run_deferred_startup_tasks,
        name="startup-warmup",
        daemon=True,
    ).start()


def get_startup_status() -> dict[str, object]:
    """Return a phase-aware readiness snapshot for local clients."""
    with _startup_lock:
        if _startup_phase == STARTUP_PHASE_ERROR and not _startup_ready:
            status = "error"
        elif _startup_phase == STARTUP_PHASE_READY:
            status = "ok"
        else:
            status = "starting"

        payload = {
            "status": status,
            "ready": _startup_ready,
            "phase": _startup_phase,
        }
        if _startup_error:
            payload["detail"] = _startup_error
        return payload


app.add_middleware(
    CORSMiddleware,
    # Allow desktop/web UI origins on localhost and WebView protocols.
    allow_origins=[
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "null",  # file:// origin in some desktop webviews
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure outside-path runtime directories exist for first run in packaged app.
os.makedirs(CONFIG["SCREENSHOT_FOLDER"], exist_ok=True)
storage_parent = os.path.dirname(CONFIG["STORAGE_PATH"])
if storage_parent:
    os.makedirs(storage_parent, exist_ok=True)

# ICON_FOLDER is bundled with the exe, no need to create it
app.mount("/images", StaticFiles(directory=CONFIG["ICON_FOLDER"]), name="images")
app.mount(
    "/screenshot",
    StaticFiles(directory=CONFIG["SCREENSHOT_FOLDER"]),
    name="screenshots",
)
