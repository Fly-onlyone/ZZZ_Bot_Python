"""API route definitions for ZZZ Bot.

Separates API logic from application bootstrapping for better maintainability.
"""

import logging
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path
from secrets import compare_digest

from fastapi import APIRouter, BackgroundTasks, Query
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import repositories.MongoRepository as mongo
from core.GlobalVar import CONFIG, RedeemItem, accounts, is_exe, resource_path, settings
from core.ManualLogin import run

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


def _has_valid_desktop_token(request: Request) -> bool:
    """Verify local desktop token for privileged loopback-only endpoints."""
    expected = os.getenv("ZZZ_DESKTOP_TOKEN", "")
    provided = request.headers.get("x-desktop-token", "")

    if not expected or not provided:
        return False

    return compare_digest(expected, provided)


# ============================================================================
# METADATA ROUTES
# ============================================================================


@router.get("/routes")
async def get_routes():
    """Return list of available API routes (excluding internal endpoints)."""
    from core.GlobalVar import app

    exclude_prefixes = {
        "/docs",
        "/openapi.json",
        "/redoc",
        "/manual",
        "/images",
        "/screenshot",
        "/assets",
        "/playstate",
        "/logs",
    }
    routes = [
        route.path.lstrip("/")
        for route in app.routes
        if not any(route.path.startswith(prefix) for prefix in exclude_prefixes)
        and route.path != "/routes"
    ]
    return {"routes": list(dict.fromkeys(routes))}  # Deduplicate


@router.get("/assets/screenshot/{filename}")
def get_screenshot_asset(filename: str):
    """Serve screenshot assets from MongoDB storage."""
    from utils.screenshot_store import get_screenshot_bytes

    safe_name = Path(filename).name
    if not safe_name:
        return JSONResponse({"message": "Invalid screenshot filename"}, status_code=400)

    image_bytes = get_screenshot_bytes(safe_name)
    if image_bytes is None:
        return JSONResponse({"message": "Screenshot not found"}, status_code=404)

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


# ============================================================================
# SHOPPING ROUTES
# ============================================================================


@router.get("/shopping")
def get_shopping_data():
    """Retrieve current shopping data from storage."""
    return mongo.get_shopping()


@router.post("/shopping")
def update_shopping_data(selected: dict):
    """Update shopping selections and reschedule hunt tasks.

    Args:
        selected: Dictionary containing 'Selected' and 'Hunt' item lists

    Returns:
        Success message
    """
    shopping_data = mongo.get_shopping() or {}
    shopping_data["Selected"] = selected.get("Selected", [])
    shopping_data["Hunt"] = selected.get("Hunt", [])
    mongo.save_shopping(shopping_data)

    from Bot import schedule_hunt_tasks

    schedule_hunt_tasks()

    return {"message": "Shopping data updated successfully"}


# ============================================================================
# REDEEM ROUTES
# ============================================================================


@router.get("/redeem")
def get_redeem_data():
    """Retrieve redemption code history."""
    return mongo.get_redemptions()


@router.post("/redeem")
def update_redeem_data(redeem_data: list[RedeemItem]):
    """Update redemption code data.

    Args:
        redeem_data: List of RedeemItem objects

    Returns:
        Success message
    """
    mongo.replace_all_redemptions([item.model_dump() for item in redeem_data])
    return {"message": "Redeem data updated successfully"}


# ============================================================================
# OVERVIEW ROUTES
# ============================================================================


@router.get("/overview/mission")
def get_mission_report():
    """Retrieve today's mission completion report."""
    from datetime import datetime

    today_str = datetime.now().strftime("%d/%m/%Y")
    todays_data = mongo.get_today_mission(today_str) or {
        "day": today_str,
        "check_in": "Link isn't opened",
        "missions": [],
    }
    return todays_data


@router.get("/overview/hunt")
def get_hunt_info():
    """Return hunt mode information including items and next hunt time."""
    from datetime import datetime, timedelta

    from handlers import HuntModeHandler as HuntMode
    from utils.StringUtil import calculate_return_time

    hunt_items = HuntMode.get_hunt_items()
    next_hunt_time = HuntMode.get_next_hunt_time()
    hunt_enabled = settings.enable_hunt_mode

    # Get detailed item information
    shopping_data = mongo.get_shopping()
    items_list = shopping_data.get("Item's list", {}) if shopping_data else {}

    # Build hunt items with scheduled times
    hunt_items_with_info = []
    for item_name in hunt_items:
        item_data = items_list.get(item_name, {})
        availability = item_data.get("Available", "")

        # Calculate scheduled hunt time
        try:
            # Convert countdown to return time if needed
            if ":" in availability and "/" not in availability:
                availability = calculate_return_time(availability)

            # Parse return time format
            if "/" in availability and ":" in availability:
                return_time = datetime.strptime(availability, "%H:%M %d/%m/%y")
                hunt_time = return_time - timedelta(
                    seconds=HuntMode.WAIT_BUFFER_SECONDS
                )
                scheduled_hunt_time = hunt_time.strftime("%H:%M %d/%m/%y")
            else:
                scheduled_hunt_time = "Not scheduled"
        except (ValueError, Exception):
            scheduled_hunt_time = "Invalid time"

        hunt_items_with_info.append(
            {
                "name": item_name,
                "scheduled_time": scheduled_hunt_time,
                "price": item_data.get("Price", 0),
                "inventory": item_data.get("Inventory", 0),
            }
        )

    return {
        "enabled": hunt_enabled,
        "hunt_items": hunt_items_with_info,
        "next_hunt_time": next_hunt_time,
    }


# ============================================================================
# ACCOUNT ROUTES
# ============================================================================


@router.get("/account")
def get_account():
    """Retrieve account credentials for email notifications."""
    return asdict(accounts)


@router.post("/account")
async def update_account(request: Request):
    """Update account credentials.

    Args:
        request: HTTP request with account data

    Returns:
        Success message
    """
    data = await request.json()
    for key, value in data.items():
        if hasattr(accounts, key):
            setattr(accounts, key, value)
    mongo.save_account(asdict(accounts))
    return JSONResponse({"message": "Account updated"})


# ============================================================================
# MANUAL CONTROL ROUTES
# ============================================================================


@router.post("/manual")
async def manual_task(request: Request, background_tasks: BackgroundTasks):
    """Start or stop manual browser control.

    Args:
        request: HTTP request with 'url' and 'playState' fields
        background_tasks: FastAPI background task manager

    Returns:
        Status message with current state
    """
    from core.ManualLogin import get_manager

    data = await request.json()
    url = data.get("url")
    play_state = data.get("playState")

    manager = get_manager()

    if play_state:
        # Start session
        if not url:
            return {"message": "URL is required", "success": False}

        if manager.is_running:
            return {
                "message": "Session already running",
                "success": False,
                "state": manager.state.value,
            }

        if manager.start_session(url):
            background_tasks.add_task(run, url)
            return {
                "message": "Manual login session started",
                "success": True,
                "state": manager.state.value,
            }
        else:
            return {
                "message": "Failed to start session (invalid URL or already running)",
                "success": False,
                "state": manager.state.value,
            }
    else:
        # Stop session
        if manager.stop_session():
            return {
                "message": "Stop signal sent",
                "success": True,
                "state": manager.state.value,
            }
        else:
            return {
                "message": "No active session to stop",
                "success": False,
                "state": manager.state.value,
            }


@router.get("/playstate")
async def get_play_state():
    """Get current manual browser control state.

    Returns:
        Current session state and whether it's running
    """
    from core.ManualLogin import get_manager

    manager = get_manager()
    return {
        "playState": manager.is_running,
        "state": manager.state.value,
    }


# ============================================================================
# TASK ROUTES
# ============================================================================


@router.post("/shutdown")
def shutdown(request: Request):
    """Gracefully shut down the backend process.

    Requires a desktop token header — only callable from the Tauri shell.
    """
    if not _has_valid_desktop_token(request):
        return JSONResponse({"status": "rejected"}, status_code=401)

    logger.info("Graceful shutdown requested by desktop shell.")
    os._exit(0)


@router.post("/tasks/run-playwright")
def run_playwright_now(request: Request):
    """Start a manual automation run in the background.

    Requires a desktop token header for local shell integrations.
    """
    if not _has_valid_desktop_token(request):
        return JSONResponse({"status": "rejected"}, status_code=401)

    from Bot import run_playwright_task_async

    run_playwright_task_async()
    return JSONResponse({"status": "started"})


# ============================================================================
# SETTINGS ROUTES
# ============================================================================


@router.post("/maintenance/local-cleanup")
def run_local_cleanup():
    """Run local artifact cleanup on demand from the UI."""
    from repositories.connection import get_db, get_runtime_mode
    from utils.local_artifact_maintenance import cleanup_local_artifacts_once
    from utils.migrate_json_to_mongo import migrate_if_needed

    migration_report = migrate_if_needed(
        CONFIG["OUTPUT_FOLDER"],
        CONFIG["STORAGE_PATH"],
        CONFIG["SCREENSHOT_FOLDER"],
    )
    cleanup_report = cleanup_local_artifacts_once(
        db=get_db(),
        config=CONFIG,
        is_exe_mode=is_exe,
        runtime_mode=get_runtime_mode(),
        migration_report=migration_report,
        exe_base_dir=os.path.dirname(sys.executable) if is_exe else None,
    )
    return JSONResponse(cleanup_report)


@router.get("/settings")
def get_settings():
    """Return all current application settings."""
    return asdict(settings)


@router.post("/settings")
async def update_settings(request: Request):
    """Update application settings dynamically.

    Args:
        request: HTTP request with settings data

    Returns:
        Success message
    """
    from Bot import calculate_next_run, configure_sentry_runtime, schedule_tasks
    from repositories.connection import get_db, set_runtime_uri

    data = await request.json()

    applied_updates: dict[str, tuple[object, object]] = {}
    for key, value in data.items():
        if hasattr(settings, key):
            applied_updates[key] = (getattr(settings, key), value)
            setattr(settings, key, value)

    try:
        if "mongodb_uri" in applied_updates:
            set_runtime_uri(settings.mongodb_uri)
            get_db()

        # Save and reschedule
        mongo.save_settings(asdict(settings))
    except Exception as exc:
        # Roll back in-memory settings.
        for key, (old_value, _) in applied_updates.items():
            setattr(settings, key, old_value)

        # Restore previous Mongo connection if URI update failed.
        if "mongodb_uri" in applied_updates:
            previous_uri = applied_updates["mongodb_uri"][0]
            try:
                set_runtime_uri(previous_uri if isinstance(previous_uri, str) else "")
                get_db()
            except Exception as restore_exc:
                logger.error(
                    "Failed to restore previous MongoDB URI after update failure: %s",
                    restore_exc,
                )

        logger.error("Failed to update settings: %s", exc)
        return JSONResponse(
            {
                "message": "Settings update failed",
                "error": str(exc),
            },
            status_code=400,
        )

    schedule_tasks()

    sentry_setting_keys = {
        "sentry_dsn",
        "sentry_send_test_event",
        "sentry_traces_sample_rate",
        "sentry_profiles_sample_rate",
    }
    if any(key in applied_updates for key in sentry_setting_keys):
        sentry_status = configure_sentry_runtime(
            trigger_source="settings_update",
            force_reinit=True,
        )
        logger.info(
            "Applied Sentry runtime settings from UI: active=%s, dsn_source=%s, traces_sample_rate=%.3f, profiles_sample_rate=%.3f, reconfigured=%s, error=%s",
            sentry_status["active"],
            sentry_status["dsn_source"],
            sentry_status["traces_sample_rate"],
            sentry_status["profiles_sample_rate"],
            sentry_status["reconfigured"],
            sentry_status["error"],
        )

    # Update next_run when schedule_times change
    if "schedule_times" in applied_updates:
        run_data = mongo.get_last_run() or {}
        next_run = calculate_next_run()
        run_data["next_run"] = next_run.strftime("%H:%M %d/%m/%y")
        mongo.save_last_run(run_data)
        logger.info("Updated next run to: %s", run_data["next_run"])

    return JSONResponse({"message": "Settings updated"})


@router.get("/check-run-status")
def check_run_status():
    """Check last run status with dynamically calculated next run."""
    from Bot import calculate_next_run

    data = mongo.get_last_run() or {}
    return {
        "last_run": data.get("last_run"),
        "next_run": calculate_next_run().strftime("%H:%M %d/%m/%y"),
    }


# ============================================================================
# LOGS ROUTES
# ============================================================================

_LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.+?) - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - (.*)"
)


def _get_log_dir() -> Path:
    """Return the log directory for the current run mode."""
    if is_exe:
        return Path(resource_path("logs", outside_path=True))
    # Development: logs are written to backend/logs/ relative to project root
    return Path(__file__).parent.parent / "logs"


@router.get("/logs")
def get_logs(
    log_date: str = Query(None, alias="date"),
    level: str = Query(None),
    search: str = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    """Return parsed log entries with optional filtering and pagination.

    Args:
        log_date: Date suffix of rotated log file (e.g. "2026-02-25"). Omit for current log.
        level: Comma-separated level filter (e.g. "ERROR,WARNING").
        search: Case-insensitive text search across message and logger fields.
        limit: Max entries to return.
        offset: Entries to skip (for pagination).

    Returns:
        { entries: [...], total: int, files: [str] }
    """
    log_dir = _get_log_dir()

    if not log_dir.exists():
        return {"entries": [], "total": 0, "files": []}

    # Build sorted list of available log files (current first, then rotated)
    log_files = sorted(log_dir.glob("app.log*"), reverse=True)
    file_names = [f.name for f in log_files]

    # Determine which file to read
    if log_date:
        target_file = (log_dir / f"app.log.{log_date}").resolve()
        # Security: resolved path must stay inside the log directory
        try:
            target_file.relative_to(log_dir.resolve())
        except ValueError:
            return JSONResponse({"message": "Invalid date"}, status_code=400)
        if not target_file.exists():
            return {"entries": [], "total": 0, "files": file_names}
        log_file = target_file
    else:
        log_file = log_dir / "app.log"
        if not log_file.exists():
            return {"entries": [], "total": 0, "files": file_names}

    # Parse log file line-by-line, collecting multiline (traceback) entries
    entries = []
    current_entry: dict | None = None

    with open(log_file, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n\r")
            match = _LOG_PATTERN.match(line)
            if match:
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "timestamp": match.group(1),
                    "logger": match.group(2),
                    "level": match.group(3),
                    "message": match.group(4),
                }
            elif current_entry is not None:
                # Continuation line (e.g. traceback)
                current_entry["message"] += "\n" + line

    if current_entry:
        entries.append(current_entry)

    # Apply level filter
    if level:
        level_set = {lv.strip().upper() for lv in level.split(",") if lv.strip()}
        entries = [e for e in entries if e["level"] in level_set]

    # Apply search filter (message + logger)
    if search:
        search_lower = search.lower()
        entries = [
            e
            for e in entries
            if search_lower in e["message"].lower()
            or search_lower in e["logger"].lower()
        ]

    # Newest-first
    entries = list(reversed(entries))

    total = len(entries)
    entries = entries[offset : offset + limit]

    return {"entries": entries, "total": total, "files": file_names}
