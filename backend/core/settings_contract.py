from typing import Any

ADVANCED_SETTINGS_KEYS = (
    "show_window_on_startup",
    "exit_after_run",
    "hunt_poll_max_wait_seconds",
    "hunt_poll_interval_seconds",
    "hunt_poll_backoff_enabled",
    "hunt_early_exit_on_unavailable",
    "sentry_dsn",
    "sentry_frontend_dsn",
    "sentry_send_test_event",
    "sentry_traces_sample_rate",
)


def extract_advanced_settings(settings_payload: dict[str, Any]) -> dict[str, Any]:
    """Return only the advanced settings fields exposed on the advanced page."""

    return {key: settings_payload[key] for key in ADVANCED_SETTINGS_KEYS if key in settings_payload}
