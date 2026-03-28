"""API route definitions for ZZZ Bot.

Separates API logic from application bootstrapping for better maintainability.
"""

import asyncio
import importlib
import json
import logging
import os
import re
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from secrets import compare_digest

from fastapi import APIRouter, BackgroundTasks, Query
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

import repositories.MongoRepository as MongoRepository
from core.GlobalVar import (
    CONFIG,
    RedeemItem,
    accounts,
    ensure_accounts_loaded,
    get_startup_status,
    is_exe,
    resource_path,
    settings,
)
from core.ManualLogin import run
from core.settings_contract import extract_advanced_settings

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()
WINDOW_STATE_SETTING_KEYS = {
    "window_x",
    "window_y",
    "window_width",
    "window_height",
    "window_maximized",
    "window_minimized",
}

INTERNAL_ROUTE_PREFIXES = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/manual",
    "/images",
    "/screenshot",
    "/assets",
    "/playstate",
    "/logs",
    "/health",
    "/shutdown",
    "/tasks",
    "/maintenance",
    "/backup",
    "/events",
    "/locator-tracker",
}
SHUTDOWN_RESPONSE_DELAY_SECONDS = 0.2
SHUTDOWN_SENTRY_FLUSH_TIMEOUT_SECONDS = 2.0
LEGACY_MIGRATION_COLLECTIONS_BY_FILE = {
    "settings.json": "settings",
    "account.json": "account",
    "shopping.json": "shopping",
    "missions.json": "missions",
    "redeem.json": "redemptions",
    "last_run.json": "last_run",
}


def _resolve_bot_runtime(*required_attrs: str):
    """Return the live backend runtime module, preferring packaged __main__."""
    main_module = sys.modules.get("__main__")
    if main_module is not None and all(
        hasattr(main_module, attr) for attr in required_attrs
    ):
        return main_module
    return importlib.import_module("Bot")


def _build_backup_export_filename(exported_at: datetime | None = None) -> str:
    """Generate a timestamped backup filename so repeated exports stay distinct."""
    timestamp = (exported_at or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S-%f")
    return f"zzz-bot-backup-{timestamp}.json"


def _collect_migrated_collections_from_report(
    migration_report: dict[str, object],
) -> set[str]:
    """Map migrated legacy artifacts to their runtime collection names."""
    migrated_collections: set[str] = set()
    artifact_status = migration_report.get("artifact_status", {})
    if not isinstance(artifact_status, dict):
        return migrated_collections

    for filename, collection_name in LEGACY_MIGRATION_COLLECTIONS_BY_FILE.items():
        status = artifact_status.get(filename, {})
        if not isinstance(status, dict):
            continue
        action = status.get("action")
        if isinstance(action, str) and action.startswith("migrated"):
            migrated_collections.add(collection_name)

    return migrated_collections


def _migration_report_has_warnings(migration_report: dict[str, object]) -> bool:
    """Detect partial or invalid legacy migration results."""
    artifact_status = migration_report.get("artifact_status", {})
    if not isinstance(artifact_status, dict):
        return False

    for status in artifact_status.values():
        if not isinstance(status, dict):
            continue
        action = status.get("action")
        if action in {"skipped_invalid", "migrated_partial"}:
            return True
        parse_error = status.get("parse_error")
        if isinstance(parse_error, str) and parse_error:
            return True

    return False


def _refresh_runtime_state_after_restore(
    restored_collections: set[str],
) -> dict[str, str]:
    """Reload shared in-memory state after restore-style operations."""
    from repositories.connection import get_db, set_runtime_uri

    bot_runtime = _resolve_bot_runtime("schedule_hunt_tasks", "schedule_tasks")

    runtime_errors: dict[str, str] = {}

    if "settings" in restored_collections:
        previous_mongodb_uri = getattr(settings, "mongodb_uri", "")
        restored_settings = MongoRepository.get_settings()
        if restored_settings:
            for key, value in restored_settings.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            restored_mongodb_uri = restored_settings.get("mongodb_uri")
            if restored_mongodb_uri != previous_mongodb_uri:
                try:
                    set_runtime_uri(
                        restored_mongodb_uri
                        if isinstance(restored_mongodb_uri, str)
                        else ""
                    )
                    get_db()
                except Exception as exc:
                    logger.error(
                        "Failed to reconnect MongoDB after runtime restore: %s",
                        exc,
                        exc_info=True,
                    )
                    runtime_errors[
                        "settings_runtime"
                    ] = f"Settings restored but MongoDB reconnect failed: {exc}"

        bot_runtime.schedule_tasks()

    if "account" in restored_collections:
        restored_account = MongoRepository.get_account()
        if restored_account:
            for key, value in restored_account.items():
                if hasattr(accounts, key):
                    setattr(accounts, key, value)

    if "settings" not in restored_collections and "shopping" in restored_collections:
        bot_runtime.schedule_hunt_tasks()

    return runtime_errors


def _has_valid_desktop_token(request: Request) -> bool:
    """Verify local desktop token for privileged loopback-only endpoints."""
    expected = os.getenv("ZZZ_DESKTOP_TOKEN", "")
    provided = request.headers.get("x-desktop-token", "")

    if not expected or not provided:
        return False

    return compare_digest(expected, provided)


def _is_public_route(path: str) -> bool:
    """Filter out internal endpoints from dynamic frontend route discovery."""
    return path != "/routes" and not any(
        path.startswith(prefix) for prefix in INTERNAL_ROUTE_PREFIXES
    )


def _build_shutdown_context(payload: object) -> dict[str, object]:
    """Normalize desktop shutdown metadata into a trace-safe payload."""
    raw_payload = payload if isinstance(payload, dict) else {}

    tracked_pid = raw_payload.get("tracked_pid")
    if not isinstance(tracked_pid, int):
        tracked_pid = None

    shutdown_started_at = raw_payload.get("shutdown_started_at")
    if not isinstance(shutdown_started_at, str):
        shutdown_started_at = ""

    return {
        "source": str(raw_payload.get("source") or "tauri"),
        "run_event": str(raw_payload.get("run_event") or "unknown"),
        "reason": str(raw_payload.get("reason") or "desktop_shell"),
        "tracked_pid": tracked_pid,
        "shutdown_started_at": shutdown_started_at,
        "hosted_by_tauri": True,
        "is_exe": bool(is_exe),
    }


def _perform_desktop_shutdown(
    shutdown_context: dict[str, object],
    *,
    sentry_sdk_module=None,
    exit_func=os._exit,
    sleep_func=time.sleep,
) -> None:
    """Trace desktop-triggered shutdown and flush telemetry before exiting."""
    transaction = None
    sentry_active = False

    try:
        if sentry_sdk_module is None:
            try:
                import sentry_sdk as sentry_sdk_module
            except ImportError:
                sentry_sdk_module = None

        if sentry_sdk_module is not None:
            sentry_active = sentry_sdk_module.get_client().is_active()

        if sentry_active:
            transaction = sentry_sdk_module.start_transaction(
                op="app.shutdown",
                name="desktop-sidecar-shutdown",
                sampled=True,
            )
            transaction.set_tag("shutdown.source", str(shutdown_context["source"]))
            transaction.set_tag(
                "shutdown.run_event", str(shutdown_context["run_event"])
            )
            transaction.set_tag("shutdown.reason", str(shutdown_context["reason"]))
            for key, value in shutdown_context.items():
                transaction.set_data(key, value)

            with transaction.start_child(
                op="shutdown.request.accepted",
                description="desktop shutdown accepted",
            ):
                logger.info(
                    "Graceful shutdown accepted by backend "
                    "(source=%s, run_event=%s, reason=%s, tracked_pid=%s)",
                    shutdown_context["source"],
                    shutdown_context["run_event"],
                    shutdown_context["reason"],
                    shutdown_context["tracked_pid"],
                )

            sleep_func(SHUTDOWN_RESPONSE_DELAY_SECONDS)
            transaction.set_status("ok")
        else:
            logger.info(
                "Graceful shutdown accepted by backend "
                "(source=%s, run_event=%s, reason=%s, tracked_pid=%s)",
                shutdown_context["source"],
                shutdown_context["run_event"],
                shutdown_context["reason"],
                shutdown_context["tracked_pid"],
            )
            sleep_func(SHUTDOWN_RESPONSE_DELAY_SECONDS)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        logger.exception("Desktop shutdown trace failed")
        if transaction is not None:
            transaction.set_status("internal_error")
        if sentry_active:
            sentry_sdk_module.capture_exception()
    finally:
        try:
            if transaction is not None:
                transaction.finish()
            if sentry_active:
                sentry_sdk_module.flush(timeout=SHUTDOWN_SENTRY_FLUSH_TIMEOUT_SECONDS)
        finally:
            exit_func(0)


def _start_shutdown_worker(
    shutdown_context: dict[str, object],
    *,
    thread_factory=threading.Thread,
):
    """Start the deferred shutdown worker so the HTTP response can complete."""
    worker = thread_factory(
        target=_perform_desktop_shutdown,
        args=(shutdown_context,),
        name="desktop-shutdown-worker",
        daemon=True,
    )
    worker.start()
    return worker


# ============================================================================
# METADATA ROUTES
# ============================================================================


@router.get("/health")
def health_check():
    """Return backend readiness status for frontend startup gating."""
    return get_startup_status()


@router.get("/routes")
async def get_routes():
    """Return list of available API routes (excluding internal endpoints)."""
    from core.GlobalVar import app

    routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if path and _is_public_route(path):
            routes.append(path.lstrip("/"))
    return {"routes": list(dict.fromkeys(routes))}  # Deduplicate


@router.get("/assets/screenshot/{filename}")
def get_screenshot_asset(filename: str):
    """Serve screenshot assets from MongoDB storage."""
    from utils.screenshot_store import get_screenshot_asset as load_screenshot_asset

    safe_name = Path(filename).name
    if not safe_name:
        return JSONResponse({"message": "Invalid screenshot filename"}, status_code=400)

    asset = load_screenshot_asset(safe_name)
    if asset is None:
        return JSONResponse({"message": "Screenshot not found"}, status_code=404)

    return Response(
        content=asset["payload"],
        media_type=asset["content_type"],
        headers={"Cache-Control": "no-store"},
    )


# ============================================================================
# LOCATOR TRACKER ROUTES
# ============================================================================


@router.get("/locator-tracker")
def get_locator_tracker():
    """Return all locator tracking entries."""
    from automation.LocatorTracker import get_all_entries

    return get_all_entries()


@router.get("/locator-tracker/failures")
def get_locator_tracker_failures(
    limit: int = Query(100, ge=1, le=500),
    summary_id: str | None = Query(None),
):
    """Return recent locator tracker failure events."""
    from automation.LocatorTracker import get_failure_events

    return get_failure_events(limit=limit, summary_id=summary_id)


@router.get("/locator-tracker/child-scan/{summary_id:path}")
def get_locator_child_scan(summary_id: str):
    """Return child scan data for a specific locator summary entry."""
    from repositories.connection import get_db

    entry = get_db().locator_tracker.find_one({"_id": summary_id}, {"child_scan": 1})
    if not entry:
        return JSONResponse({"message": "Summary not found"}, status_code=404)
    return {"child_scan": entry.get("child_scan", [])}


@router.post("/locator-tracker/clear")
def clear_locator_tracker():
    """Clear all locator tracking entries."""
    from automation.LocatorTracker import clear_entries

    clear_entries()
    return {"message": "Locator tracker cleared"}


# ============================================================================
# SHOPPING ROUTES
# ============================================================================


@router.get("/shopping")
def get_shopping_data():
    """Retrieve current shopping data from storage."""
    return MongoRepository.get_shopping()


@router.post("/shopping")
def update_shopping_data(selected: dict):
    """Update shopping selections and reschedule hunt tasks.

    Args:
        selected: Dictionary containing 'Selected' and 'Hunt' item lists

    Returns:
        Success message
    """
    shopping_data = MongoRepository.get_shopping() or {}
    shopping_data["Selected"] = selected.get("Selected", [])
    shopping_data["Hunt"] = selected.get("Hunt", [])
    MongoRepository.save_shopping(shopping_data)

    _resolve_bot_runtime("schedule_hunt_tasks").schedule_hunt_tasks()

    return {"message": "Shopping data updated successfully"}


# ============================================================================
# REDEEM ROUTES
# ============================================================================


@router.get("/redeem")
def get_redeem_data():
    """Retrieve redemption code history."""
    return MongoRepository.get_redemptions()


@router.post("/redeem")
def update_redeem_data(redeem_data: list[RedeemItem]):
    """Update redemption code data.

    Args:
        redeem_data: List of RedeemItem objects

    Returns:
        Success message
    """
    MongoRepository.replace_all_redemptions([item.model_dump() for item in redeem_data])
    return {"message": "Redeem data updated successfully"}


# ============================================================================
# OVERVIEW ROUTES
# ============================================================================


@router.get("/overview/mission")
def get_mission_report():
    """Retrieve today's mission completion report."""
    from datetime import datetime

    today_str = datetime.now().strftime("%d/%m/%Y")
    todays_data = MongoRepository.get_today_mission(today_str) or {
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
    shopping_data = MongoRepository.get_shopping()
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
    ensure_accounts_loaded()
    return asdict(accounts)


@router.post("/account")
async def update_account(request: Request):
    """Update account credentials.

    Args:
        request: HTTP request with account data

    Returns:
        Success message
    """
    ensure_accounts_loaded()
    data = await request.json()
    for key, value in data.items():
        if hasattr(accounts, key):
            setattr(accounts, key, value)
    MongoRepository.save_account(asdict(accounts))
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
async def shutdown(request: Request):
    """Gracefully shut down the backend process.

    Requires a desktop token header — only callable from the Tauri shell.
    """
    if not _has_valid_desktop_token(request):
        return JSONResponse({"status": "rejected"}, status_code=401)

    raw_body = await request.body()
    payload: object = {}
    if raw_body:
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.warning("Desktop shutdown request included invalid JSON payload")

    shutdown_context = _build_shutdown_context(payload)
    _start_shutdown_worker(shutdown_context)
    return JSONResponse({"status": "accepted"}, status_code=202)


@router.post("/tasks/run-playwright")
def run_playwright_now(request: Request):
    """Start a manual automation run in the background.

    Requires a desktop token header for local shell integrations.
    """
    if not _has_valid_desktop_token(request):
        return JSONResponse({"status": "rejected"}, status_code=401)

    _resolve_bot_runtime("run_playwright_task_async").run_playwright_task_async(
        manual_run=True
    )
    return JSONResponse({"status": "started"})


# ============================================================================
# SETTINGS ROUTES
# ============================================================================


@router.post("/maintenance/local-cleanup")
def run_local_cleanup():
    """Run local artifact cleanup on demand from the UI."""
    from repositories.connection import get_db, get_runtime_mode
    from utils.local_artifact_maintenance import cleanup_local_artifacts_once

    import sentry_sdk

    with sentry_sdk.start_span(
        op="maintenance.cleanup", name="local-cleanup-artifacts"
    ):
        cleanup_report = cleanup_local_artifacts_once(
            db=get_db(),
            config=CONFIG,
            is_exe_mode=is_exe,
            runtime_mode=get_runtime_mode(),
            migration_report={},
            exe_base_dir=os.path.dirname(sys.executable) if is_exe else None,
        )
    return JSONResponse(cleanup_report)


@router.post("/maintenance/legacy-migration")
def run_legacy_migration():
    """Import legacy local JSON and binary artifacts into Mongo on demand."""
    from utils.migrate_json_to_mongo import migrate_if_needed

    import sentry_sdk

    with sentry_sdk.start_span(
        op="maintenance.legacy_migration", name="legacy-migration"
    ):
        migration_report = migrate_if_needed(
            CONFIG["OUTPUT_FOLDER"],
            CONFIG["STORAGE_PATH"],
            CONFIG["SCREENSHOT_FOLDER"],
        )

    restored_collections = _collect_migrated_collections_from_report(migration_report)
    runtime_errors = _refresh_runtime_state_after_restore(restored_collections)

    response_payload = dict(migration_report)
    response_payload["status"] = (
        "completed_with_warnings"
        if runtime_errors or _migration_report_has_warnings(migration_report)
        else "completed"
    )
    if runtime_errors:
        response_payload["errors"] = runtime_errors
    return JSONResponse(response_payload)


@router.get("/settings")
def get_settings():
    """Return all current application settings."""
    return asdict(settings)


@router.get("/settings/advanced")
def get_advanced_settings():
    """Return only the advanced settings edited on the advanced page."""
    return extract_advanced_settings(asdict(settings))


async def _update_settings_payload(request: Request) -> JSONResponse:
    """Persist settings updates to the shared settings document."""
    import sentry_sdk

    from repositories.connection import get_db, set_runtime_uri

    bot_runtime = _resolve_bot_runtime(
        "calculate_next_run",
        "configure_sentry_runtime",
        "schedule_tasks",
    )

    data = await request.json()
    current_settings = asdict(settings)
    updated_settings = dict(current_settings)

    for key, value in data.items():
        if key in current_settings:
            updated_settings[key] = value

    applied_updates = {
        key: (current_settings[key], updated_settings[key])
        for key in current_settings
        if current_settings[key] != updated_settings[key]
    }

    for key, value in updated_settings.items():
        setattr(settings, key, value)

    with sentry_sdk.start_span(op="settings.update", name="update-settings-payload"):
        try:
            if "mongodb_uri" in applied_updates:
                with sentry_sdk.start_span(
                    op="settings.mongo_uri_switch", name="mongo-uri-switch"
                ):
                    set_runtime_uri(settings.mongodb_uri)
                    get_db()

            MongoRepository.save_settings(asdict(settings))
        except Exception as exc:
            with sentry_sdk.start_span(
                op="settings.rollback", name="settings-rollback"
            ):
                for key, value in current_settings.items():
                    setattr(settings, key, value)

                if "mongodb_uri" in applied_updates:
                    previous_uri = current_settings["mongodb_uri"]
                    try:
                        set_runtime_uri(
                            previous_uri if isinstance(previous_uri, str) else ""
                        )
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

    non_window_updates = {
        key: change
        for key, change in applied_updates.items()
        if key not in WINDOW_STATE_SETTING_KEYS
    }
    if non_window_updates:
        bot_runtime.schedule_tasks()

    sentry_setting_keys = {
        "sentry_dsn",
        "sentry_send_test_event",
        "sentry_traces_sample_rate",
    }
    if any(key in applied_updates for key in sentry_setting_keys):
        sentry_status = bot_runtime.configure_sentry_runtime(
            trigger_source="settings_update",
            force_reinit=True,
        )
        logger.info(
            "Applied Sentry runtime settings from UI: active=%s, dsn_source=%s, traces_sample_rate=%.3f, reconfigured=%s, error=%s",
            sentry_status["active"],
            sentry_status["dsn_source"],
            sentry_status["traces_sample_rate"],
            sentry_status["reconfigured"],
            sentry_status["error"],
        )

    if "schedule_times" in applied_updates:
        run_data = MongoRepository.get_last_run() or {}
        next_run = bot_runtime.calculate_next_run()
        run_data["next_run"] = next_run.strftime("%H:%M %d/%m/%y")
        MongoRepository.save_last_run(run_data)
        logger.info("Updated next run to: %s", run_data["next_run"])

    return JSONResponse({"message": "Settings updated"})


@router.post("/settings")
async def update_settings(request: Request):
    """Update application settings dynamically.

    Args:
        request: HTTP request with settings data

    Returns:
        Success message
    """
    return await _update_settings_payload(request)


@router.post("/settings/advanced")
async def update_advanced_settings(request: Request):
    """Update advanced settings using the shared settings storage."""
    return await _update_settings_payload(request)


@router.get("/check-run-status")
def check_run_status():
    """Check last run status with dynamically calculated next run."""
    data = MongoRepository.get_last_run() or {}
    calculate_next_run = _resolve_bot_runtime("calculate_next_run").calculate_next_run
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


# ============================================================================
# SSE EVENTS
# ============================================================================


@router.get("/events")
async def sse_events():
    """Server-Sent Events stream for real-time task completion notifications."""
    from core.event_bus import subscribe, unsubscribe

    client_queue = subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    event_type, payload = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, client_queue.get, True, 30.0
                        ),
                        timeout=35.0,
                    )
                    yield f"event: {event_type}\ndata: {payload}\n\n"
                except (asyncio.TimeoutError, Exception):
                    # Send keepalive comment every ~30 seconds
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# BACKUP ROUTES
# ============================================================================


@router.get("/backup/summary")
def get_backup_summary():
    """Return metadata summary of all collections for the backup page."""
    return MongoRepository.get_data_summary()


@router.get("/backup/config")
def get_backup_config():
    """Return backup configuration (export path, etc.)."""
    return MongoRepository.get_backup_config()


@router.post("/backup/config")
async def update_backup_config(request: Request):
    """Update backup configuration."""
    data = await request.json()
    MongoRepository.save_backup_config(data)
    return JSONResponse({"message": "Backup config updated"})


@router.post("/backup/browse")
def browse_export_folder():
    """Open a native folder picker dialog and return the selected path."""
    import tkinter as tk
    from tkinter import filedialog

    # Get current config to use as initial directory
    config = MongoRepository.get_backup_config()
    initial_dir = (config.get("export_path") or "").strip() or None

    root = tk.Tk()
    root.withdraw()
    # Bring the dialog to front on Windows
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(
        title="Choose Backup Folder",
        initialdir=initial_dir,
    )
    root.destroy()

    if not selected:
        return JSONResponse({"path": None, "cancelled": True})

    # Normalize to OS-native separators
    selected = str(Path(selected))
    return {"path": selected, "cancelled": False}


@router.post("/backup/export")
def export_backup():
    """Write backup JSON to the configured export path.

    Returns:
        Success message with the file path written, or error
    """
    config = MongoRepository.get_backup_config()
    export_path = (config.get("export_path") or "").strip()

    if not export_path:
        return JSONResponse(
            {"message": "Export path not configured. Set a folder first."},
            status_code=400,
        )

    export_dir = Path(export_path)
    if not export_dir.is_dir():
        return JSONResponse(
            {"message": f"Export folder does not exist: {export_path}"},
            status_code=400,
        )

    data = MongoRepository.export_all_data()

    file_name = _build_backup_export_filename()
    file_path = export_dir / file_name

    try:
        file_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("Backup exported to %s", file_path)
    except Exception as exc:
        logger.error("Backup export failed: %s", exc, exc_info=True)
        return JSONResponse(
            {"message": f"Failed to write backup: {exc}"}, status_code=500
        )

    return {"message": "Backup exported", "file": str(file_path)}


@router.post("/backup/import")
async def import_backup(request: Request):
    """Import data from a backup JSON file with selective collection restore.

    Args:
        request: HTTP request with {data: <backup JSON>, collections: [str]}

    Returns:
        Import report with restored/skipped/errors
    """
    body = await request.json()
    backup_data = body.get("data")
    collections = body.get("collections", [])

    if not backup_data or not isinstance(backup_data, dict):
        return JSONResponse({"message": "Invalid backup data"}, status_code=400)

    if not collections or not isinstance(collections, list):
        return JSONResponse(
            {"message": "No collections selected for import"}, status_code=400
        )

    report = MongoRepository.import_data(backup_data, collections)
    runtime_errors = _refresh_runtime_state_after_restore(set(report.get("restored", [])))
    if runtime_errors:
        report.setdefault("errors", {}).update(runtime_errors)

    return JSONResponse(report)
