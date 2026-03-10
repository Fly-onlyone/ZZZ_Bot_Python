from collections.abc import Mapping


def resolve_frontend_sentry_dsn(
    runtime_env: Mapping[str, str],
    settings_frontend_dsn: str,
) -> tuple[str, str]:
    """Resolve the frontend Sentry DSN for Vite startup and builds.

    Prefer explicit Vite input first, then the root env variable, then the
    persisted settings value so the advanced settings UI survives restarts.
    """

    vite_dsn = runtime_env.get("VITE_SENTRY_DSN", "").strip()
    if vite_dsn:
        return vite_dsn, "env:VITE_SENTRY_DSN"

    frontend_env_dsn = runtime_env.get("SENTRY_FRONTEND_DSN", "").strip()
    if frontend_env_dsn:
        return frontend_env_dsn, "env:SENTRY_FRONTEND_DSN"

    saved_dsn = settings_frontend_dsn.strip()
    if saved_dsn:
        return saved_dsn, "settings.sentry_frontend_dsn"

    return "", "disabled"
