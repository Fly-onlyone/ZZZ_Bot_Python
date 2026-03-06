from typing import Any

ADVANCED_SETTINGS_KEYS = (
    "open_web_ui",
    "exit_after_run",
    "hunt_poll_max_wait_seconds",
    "hunt_poll_interval_seconds",
    "hunt_poll_backoff_enabled",
    "hunt_early_exit_on_unavailable",
    "sentry_send_test_event",
    "sentry_traces_sample_rate",
    "sentry_profiles_sample_rate",
)


def extract_advanced_settings(settings_payload: dict[str, Any]) -> dict[str, Any]:
    """Return only the advanced settings fields exposed on the advanced page."""

    return {
        key: settings_payload[key]
        for key in ADVANCED_SETTINGS_KEYS
        if key in settings_payload
    }
