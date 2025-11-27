"""API route definitions for ZZZ Bot.

Separates API logic from application bootstrapping for better maintainability.
"""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from core import ManualLogin
from core.GlobalVar import accounts, CONFIG, settings, RedeemItem
from core.ManualLogin import run, playState_lock
from utils.DataHandler import load_shopping_data, prepare_mission_data, load_redeem_data

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


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
        "/playstate",
    }
    routes = [
        route.path.lstrip("/")
        for route in app.routes
        if not any(route.path.startswith(prefix) for prefix in exclude_prefixes)
        and route.path != "/routes"
    ]
    return {"routes": list(dict.fromkeys(routes))}  # Deduplicate


# ============================================================================
# SHOPPING ROUTES
# ============================================================================


@router.get("/shopping")
def get_shopping_data():
    """Retrieve current shopping data from storage."""
    return load_shopping_data(Path(CONFIG["SHOPPING_FILE"]))


@router.post("/shopping")
def update_shopping_data(selected: dict):
    """Update shopping selections and reschedule hunt tasks.

    Args:
        selected: Dictionary containing 'Selected' and 'Hunt' item lists

    Returns:
        Success message

    Raises:
        HTTPException: If shopping file not found
    """
    file_path = Path(CONFIG["SHOPPING_FILE"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Shopping file not found")

    # Load existing data
    with open(file_path, "r", encoding="utf-8") as file:
        shopping_data = json.load(file)

    # Update selected and hunt items
    shopping_data["Selected"] = selected.get("Selected", [])
    shopping_data["Hunt"] = selected.get("Hunt", [])

    # Save updated data
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(shopping_data, file, indent=4, ensure_ascii=False)

    # Reschedule hunt tasks to reflect updated items
    from Bot import schedule_hunt_tasks

    schedule_hunt_tasks()

    return {"message": "Shopping data updated successfully"}


# ============================================================================
# REDEEM ROUTES
# ============================================================================


@router.get("/redeem")
def get_redeem_data():
    """Retrieve redemption code history."""
    return load_redeem_data(Path(CONFIG["REDEEM_FILE"]))


@router.post("/redeem")
def update_redeem_data(redeem_data: list[RedeemItem]):
    """Update redemption code data.

    Args:
        redeem_data: List of RedeemItem objects

    Returns:
        Success message

    Raises:
        HTTPException: If file not found or save fails
    """
    file_path = CONFIG["REDEEM_FILE"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Redeem file not found")

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                [item.model_dump() for item in redeem_data],
                file,
                indent=4,
                ensure_ascii=False,
            )
        return {"message": "Redeem data updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update redeem data: {str(e)}"
        )


# ============================================================================
# OVERVIEW ROUTES
# ============================================================================


@router.get("/overview/mission")
def get_mission_report():
    """Retrieve today's mission completion report."""
    _, todays_data = prepare_mission_data(
        CONFIG["OUTPUT_FOLDER"], CONFIG["OUTPUT_FILE"]
    )
    return todays_data


@router.get("/overview/hunt")
def get_hunt_info():
    """Return hunt mode information including items and next hunt time."""
    from datetime import datetime, timedelta
    from utils.StringUtil import calculate_return_time
    from handlers import HuntModeHandler as HuntMode

    hunt_items = HuntMode.get_hunt_items()
    next_hunt_time = HuntMode.get_next_hunt_time()
    hunt_enabled = settings.enable_hunt_mode

    # Get detailed item information
    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)
    items_list = shopping_data.get("Item's list", {}) if shopping_data else {}

    # Build hunt items with scheduled times
    hunt_items_with_info = []
    for item_name in hunt_items:
        item_data = items_list.get(item_name, {})
        availability = item_data.get("Available", "")

        # Calculate scheduled hunt time
        scheduled_hunt_time = None
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
    accounts.save(CONFIG["ACCOUNT_FILE"])
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
        Status message
    """
    data = await request.json()
    url = data.get("url")
    play_state = data.get("playState")

    with playState_lock:
        ManualLogin.playState = play_state

    if ManualLogin.playState:
        background_tasks.add_task(run, url)
        return {"message": "Task started"}
    else:
        return {"message": "Task stopped"}


@router.get("/playstate")
async def get_play_state():
    """Get current manual browser control state."""
    with playState_lock:
        return {"playState": ManualLogin.playState}


# ============================================================================
# SETTINGS ROUTES
# ============================================================================


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
    from Bot import schedule_tasks, update_tray_menu, calculate_next_run

    data = await request.json()
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    # Save and reschedule
    settings.save(CONFIG["SETTINGS_FILE"])
    schedule_tasks()
    update_tray_menu()

    # Update next_run when schedule_times change
    if "schedule_times" in data:
        if os.path.exists(CONFIG["LAST_RUN_FILE"]):
            with open(CONFIG["LAST_RUN_FILE"]) as f:
                run_data = json.load(f)

            next_run = calculate_next_run()
            run_data["next_run"] = next_run.strftime("%H:%M %d/%m/%y")

            with open(CONFIG["LAST_RUN_FILE"], "w") as f:
                json.dump(run_data, f)

            logger.info(f"Updated next run to: {run_data['next_run']}")

    return JSONResponse({"message": "Settings updated"})


@router.get("/check-run-status")
def check_run_status():
    """Check last run status with dynamically calculated next run."""
    from Bot import calculate_next_run

    last_run = None
    if os.path.exists(CONFIG["LAST_RUN_FILE"]):
        with open(CONFIG["LAST_RUN_FILE"]) as f:
            data = json.load(f)
            last_run = data.get("last_run")

    # Calculate next run dynamically
    next_run = calculate_next_run()

    return {
        "last_run": last_run,
        "next_run": next_run.strftime("%H:%M %d/%m/%y"),
    }
