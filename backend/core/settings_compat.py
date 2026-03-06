import logging
from typing import Any, Callable

HUNT_EARLY_EXIT_RESET_MARKER = "compat:hunt_early_exit_default_reset:v1"


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
    if normalized_data and normalized_data.get("hunt_early_exit_on_unavailable") is True:
        normalized_data["hunt_early_exit_on_unavailable"] = False
        save_settings(normalized_data)
        if logger:
            logger.info(
                "Reset hunt_early_exit_on_unavailable to False for compatibility"
            )

    set_marker(HUNT_EARLY_EXIT_RESET_MARKER)
    return normalized_data
