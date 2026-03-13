import logging
from typing import Any, Callable

HUNT_EARLY_EXIT_RESET_MARKER = "compat:hunt_early_exit_default_reset:v1"
SHOW_WINDOW_ON_STARTUP_RENAME_MARKER = "compat:show_window_on_startup_rename:v1"


def normalize_hunt_early_exit_default(
    settings_data: dict[str, Any] | None,
    *,
    has_marker: Callable[[str], bool],
    set_marker: Callable[[str], None],
    save_settings: Callable[[dict[str, Any]], None],
    logger: logging.Logger | None = None,
) -> dict[str, Any] | None:
    """Apply the one-time compatibility reset for the hunt early-exit default."""

    if has_marker(HUNT_EARLY_EXIT_RESET_MARKER):
        return settings_data

    normalized_data = dict(settings_data) if settings_data else None
    if (
        normalized_data
        and normalized_data.get("hunt_early_exit_on_unavailable") is True
    ):
        normalized_data["hunt_early_exit_on_unavailable"] = False
        save_settings(normalized_data)
        if logger:
            logger.info(
                "Reset hunt_early_exit_on_unavailable to False for compatibility"
            )

    set_marker(HUNT_EARLY_EXIT_RESET_MARKER)
    return normalized_data


def normalize_show_window_on_startup_setting(
    settings_data: dict[str, Any] | None,
    *,
    has_marker: Callable[[str], bool],
    set_marker: Callable[[str], None],
    save_settings: Callable[[dict[str, Any]], None],
    logger: logging.Logger | None = None,
) -> dict[str, Any] | None:
    """Rename the legacy browser startup setting to the Tauri window setting."""

    normalized_data = dict(settings_data) if settings_data else None
    already_marked = has_marker(SHOW_WINDOW_ON_STARTUP_RENAME_MARKER)
    if normalized_data and "open_web_ui" in normalized_data:
        normalized_data.setdefault(
            "show_window_on_startup", normalized_data["open_web_ui"]
        )
        normalized_data.pop("open_web_ui", None)
        save_settings(normalized_data)
        if logger:
            logger.info(
                "Renamed open_web_ui to show_window_on_startup for compatibility"
            )

    if not already_marked:
        set_marker(SHOW_WINDOW_ON_STARTUP_RENAME_MARKER)
    return normalized_data
