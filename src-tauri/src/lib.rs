use std::process::Command as ProcessCommand;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use reqwest::blocking::Client;
use serde_json::{json, Value};
use tauri::{
    menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, PhysicalPosition, PhysicalSize, Position, RunEvent, Size,
    WindowEvent,
};
use tauri_plugin_shell::{process::CommandChild, process::CommandEvent, ShellExt};
use tauri_plugin_autostart::ManagerExt as _;

const AUTOSTART_RECONCILE_ATTEMPTS: u32 = 20;
const AUTOSTART_RECONCILE_DELAY_MS: u64 = 500;
const APP_NAME: &str = "ZZZ Bot";
const APP_NAME_DEV: &str = "ZZZ Bot Dev";
const BACKEND_SHUTDOWN_GRACEFUL_WAIT_MS: u64 = 2000;
const BACKEND_SHUTDOWN_POST_KILL_WAIT_MS: u64 = 500;
const BACKEND_SHUTDOWN_POLL_INTERVAL_MS: u64 = 100;
const STARTUP_WINDOW_RECONCILE_ATTEMPTS: u32 = 20;
const STARTUP_WINDOW_RECONCILE_DELAY_MS: u64 = 250;
const WINDOW_STATE_FILE_NAME: &str = "window-state.json";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AutostartSyncAction {
    None,
    Persist(bool),
    Enable,
    Disable,
}

#[derive(Debug)]
struct AppRuntime {
    backend_url: String,
    desktop_token: String,
    backend_child: Mutex<Option<CommandChild>>,
    backend_terminated: Mutex<bool>,
    shutdown_in_progress: Mutex<bool>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ShutdownEscalation {
    Graceful,
    DirectKill,
    ForceTaskkill,
}

#[derive(Debug, Clone, Copy)]
struct TraySettings {
    show_window_on_startup: bool,
    exit_after_run: bool,
}

impl Default for TraySettings {
    fn default() -> Self {
        Self {
            show_window_on_startup: true,
            exit_after_run: false,
        }
    }
}

fn backend_port() -> u16 {
    std::env::var("ZZZ_DEV_BACKEND_PORT")
        .ok()
        .and_then(|v| v.parse::<u16>().ok())
        .filter(|port| *port > 0)
        .unwrap_or(8000)
}

fn tray_tooltip() -> &'static str {
    if cfg!(debug_assertions) {
        APP_NAME_DEV
    } else {
        APP_NAME
    }
}

fn generate_desktop_token() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|value| value.as_nanos())
        .unwrap_or(0);
    format!("zzz-desktop-{}-{nanos}", std::process::id())
}

fn http_client() -> Result<Client, String> {
    Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .map_err(|error| error.to_string())
}

fn read_settings(runtime: &AppRuntime) -> Result<Value, String> {
    let client = http_client()?;
    let response = client
        .get(format!("{}/settings", runtime.backend_url))
        .send()
        .map_err(|error| error.to_string())?
        .error_for_status()
        .map_err(|error| error.to_string())?;

    response.json::<Value>().map_err(|error| error.to_string())
}

fn write_settings(runtime: &AppRuntime, payload: &Value) -> Result<(), String> {
    let client = http_client()?;
    client
        .post(format!("{}/settings", runtime.backend_url))
        .json(payload)
        .send()
        .map_err(|error| error.to_string())?
        .error_for_status()
        .map_err(|error| error.to_string())?;

    Ok(())
}

fn update_setting_value(runtime: &AppRuntime, key: &str, value: Value) -> Result<(), String> {
    let mut payload = read_settings(runtime)?;

    if let Some(object) = payload.as_object_mut() {
        object.insert(key.to_string(), value);
    } else {
        return Err("Settings payload is not a JSON object".to_string());
    }

    write_settings(runtime, &payload)
}

fn get_tray_settings(runtime: &AppRuntime) -> TraySettings {
    if let Ok(settings) = read_settings(runtime) {
        let show_window_on_startup = settings
            .get("show_window_on_startup")
            .and_then(Value::as_bool)
            .unwrap_or(true);
        let exit_after_run = settings
            .get("exit_after_run")
            .and_then(Value::as_bool)
            .unwrap_or(false);

        return TraySettings {
            show_window_on_startup,
            exit_after_run,
        };
    }

    TraySettings::default()
}

fn toggle_backend_setting(runtime: &AppRuntime, key: &str) -> Result<bool, String> {
    let payload = read_settings(runtime)?;

    let current_value = payload
        .get(key)
        .and_then(Value::as_bool)
        .ok_or_else(|| format!("Setting '{key}' is not a boolean"))?;
    let next_value = !current_value;

    update_setting_value(runtime, key, Value::Bool(next_value))?;
    Ok(next_value)
}

fn determine_autostart_sync_action(
    persisted_preference: Option<bool>,
    live_enabled: bool,
) -> AutostartSyncAction {
    match (persisted_preference, live_enabled) {
        (None, value) => AutostartSyncAction::Persist(value),
        (Some(true), false) => AutostartSyncAction::Enable,
        (Some(false), true) => AutostartSyncAction::Disable,
        _ => AutostartSyncAction::None,
    }
}

fn reconcile_autostart_preference_once(app: &AppHandle) -> Result<AutostartSyncAction, String> {
    let runtime = app.state::<AppRuntime>();
    let settings = read_settings(&runtime)?;
    let persisted_preference = settings.get("autostart_on_login").and_then(Value::as_bool);
    let autolaunch = app.autolaunch();
    let live_enabled = autolaunch.is_enabled().map_err(|error| error.to_string())?;
    let action = determine_autostart_sync_action(persisted_preference, live_enabled);

    match action {
        AutostartSyncAction::Persist(value) => {
            update_setting_value(&runtime, "autostart_on_login", Value::Bool(value))?;
        }
        AutostartSyncAction::Enable => {
            autolaunch.enable().map_err(|error| error.to_string())?;
        }
        AutostartSyncAction::Disable => {
            autolaunch.disable().map_err(|error| error.to_string())?;
        }
        AutostartSyncAction::None => {}
    }

    Ok(action)
}

fn reconcile_autostart_preference(app: AppHandle) {
    std::thread::spawn(move || {
        for attempt in 1..=AUTOSTART_RECONCILE_ATTEMPTS {
            match reconcile_autostart_preference_once(&app) {
                Ok(AutostartSyncAction::None) => return,
                Ok(AutostartSyncAction::Persist(value)) => {
                    log::info!(
                        "Persisted current autostart state during compatibility migration: {}",
                        value
                    );
                    return;
                }
                Ok(AutostartSyncAction::Enable) => {
                    log::info!("Re-enabled autostart from persisted preference");
                    return;
                }
                Ok(AutostartSyncAction::Disable) => {
                    log::info!("Disabled autostart to match persisted preference");
                    return;
                }
                Err(error) => {
                    if attempt == AUTOSTART_RECONCILE_ATTEMPTS {
                        log::warn!(
                            "Failed to reconcile autostart preference after {} attempts: {}",
                            AUTOSTART_RECONCILE_ATTEMPTS,
                            error
                        );
                        return;
                    }
                    std::thread::sleep(Duration::from_millis(
                        AUTOSTART_RECONCILE_DELAY_MS,
                    ));
                }
            }
        }
    });
}

fn determine_startup_window_visibility(
    show_window_on_startup: bool,
    started_minimized: bool,
) -> bool {
    show_window_on_startup && !started_minimized
}

fn window_state_file_path(app: &AppHandle) -> Result<PathBuf, String> {
    let mut dir = app.path().app_config_dir().map_err(|error| error.to_string())?;
    fs::create_dir_all(&dir).map_err(|error| error.to_string())?;
    dir.push(WINDOW_STATE_FILE_NAME);
    Ok(dir)
}

fn read_local_window_state(app: &AppHandle) -> Result<Value, String> {
    let path = window_state_file_path(app)?;
    match fs::read_to_string(&path) {
        Ok(contents) => serde_json::from_str::<Value>(&contents).map_err(|error| error.to_string()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(json!({})),
        Err(error) => Err(error.to_string()),
    }
}

fn write_local_window_state(app: &AppHandle, payload: &Value) -> Result<(), String> {
    let path = window_state_file_path(app)?;
    let serialized = serde_json::to_string_pretty(payload).map_err(|error| error.to_string())?;
    fs::write(path, serialized).map_err(|error| error.to_string())
}

fn merge_local_window_state(app: &AppHandle, mut settings: Value) -> Value {
    let Ok(local_state) = read_local_window_state(app) else {
        return settings;
    };

    let Some(settings_object) = settings.as_object_mut() else {
        return settings;
    };
    let Some(local_object) = local_state.as_object() else {
        return settings;
    };

    for key in ["window_x", "window_y", "window_width", "window_height"] {
        if let Some(value) = local_object.get(key) {
            settings_object.insert(key.to_string(), value.clone());
        }
    }

    settings
}

fn update_window_size_payload(settings: &mut Value, width: u32, height: u32) -> Result<bool, String> {
    let current_width = settings
        .get("window_width")
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok());
    let current_height = settings
        .get("window_height")
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok());

    if current_width == Some(width) && current_height == Some(height) {
        return Ok(false);
    }

    let Some(object) = settings.as_object_mut() else {
        return Err("Settings payload is not an object while saving window size".to_string());
    };

    object.insert("window_width".to_string(), Value::from(width));
    object.insert("window_height".to_string(), Value::from(height));
    Ok(true)
}

fn update_window_position_payload(settings: &mut Value, x: i32, y: i32) -> Result<bool, String> {
    let current_x = settings
        .get("window_x")
        .and_then(Value::as_i64)
        .and_then(|value| i32::try_from(value).ok());
    let current_y = settings
        .get("window_y")
        .and_then(Value::as_i64)
        .and_then(|value| i32::try_from(value).ok());

    if current_x == Some(x) && current_y == Some(y) {
        return Ok(false);
    }

    let Some(object) = settings.as_object_mut() else {
        return Err("Settings payload is not an object while saving window position".to_string());
    };

    object.insert("window_x".to_string(), Value::from(x));
    object.insert("window_y".to_string(), Value::from(y));
    Ok(true)
}

fn saved_window_size(settings: &Value) -> Option<(u32, u32)> {
    let width = settings
        .get("window_width")
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .filter(|value| *value > 0);
    let height = settings
        .get("window_height")
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .filter(|value| *value > 0);

    width.zip(height)
}

fn saved_window_position(settings: &Value) -> Option<(i32, i32)> {
    let x = settings
        .get("window_x")
        .and_then(Value::as_i64)
        .and_then(|value| i32::try_from(value).ok());
    let y = settings
        .get("window_y")
        .and_then(Value::as_i64)
        .and_then(|value| i32::try_from(value).ok());

    x.zip(y)
}

fn restore_main_window_size(app: &AppHandle, settings: &Value) {
    let Some((width, height)) = saved_window_size(settings) else {
        return;
    };

    if let Some(window) = app.get_webview_window("main") {
        if let Err(error) = window.set_size(Size::Physical(PhysicalSize::new(width, height)))
        {
            log::warn!("Failed to restore saved window size {width}x{height}: {error}");
        }
    }
}

fn restore_main_window_position(app: &AppHandle, settings: &Value) {
    let Some((x, y)) = saved_window_position(settings) else {
        return;
    };

    if let Some(window) = app.get_webview_window("main") {
        if let Err(error) =
            window.set_position(Position::Physical(PhysicalPosition::new(x, y)))
        {
            log::warn!("Failed to restore saved window position {x},{y}: {error}");
        }
    }
}

fn persist_window_size(app: &AppHandle, width: u32, height: u32) {
    let runtime = app.state::<AppRuntime>();
    match read_settings(&runtime) {
        Ok(mut settings) => match update_window_size_payload(&mut settings, width, height) {
            Ok(true) => {
                if let Err(error) = write_settings(&runtime, &settings) {
                    log::warn!("Failed to persist saved window size to backend: {error}");
                }
            }
            Ok(false) => {}
            Err(error) => {
                log::warn!("{error}");
            }
        },
        Err(error) => {
            log::info!("Skipping backend window size persistence: {error}");
        }
    }

    let mut local_settings = match read_local_window_state(app) {
        Ok(settings) => settings,
        Err(error) => {
            log::warn!("Failed to read local window state before saving size: {error}");
            json!({})
        }
    };

    match update_window_size_payload(&mut local_settings, width, height) {
        Ok(true) => {
            if let Err(error) = write_local_window_state(app, &local_settings) {
                log::warn!("Failed to persist saved window size locally: {error}");
            }
        }
        Ok(false) => {}
        Err(error) => {
            log::warn!("{error}");
        }
    }
}

fn persist_window_position(app: &AppHandle, x: i32, y: i32) {
    let runtime = app.state::<AppRuntime>();
    match read_settings(&runtime) {
        Ok(mut settings) => match update_window_position_payload(&mut settings, x, y) {
            Ok(true) => {
                if let Err(error) = write_settings(&runtime, &settings) {
                    log::warn!("Failed to persist saved window position to backend: {error}");
                }
            }
            Ok(false) => {}
            Err(error) => {
                log::warn!("{error}");
            }
        },
        Err(error) => {
            log::info!("Skipping backend window position persistence: {error}");
        }
    }

    let mut local_settings = match read_local_window_state(app) {
        Ok(settings) => settings,
        Err(error) => {
            log::warn!("Failed to read local window state before saving position: {error}");
            json!({})
        }
    };

    match update_window_position_payload(&mut local_settings, x, y) {
        Ok(true) => {
            if let Err(error) = write_local_window_state(app, &local_settings) {
                log::warn!("Failed to persist saved window position locally: {error}");
            }
        }
        Ok(false) => {}
        Err(error) => {
            log::warn!("{error}");
        }
    }
}

fn persist_main_window_size(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    if window.is_maximized().unwrap_or(false) {
        return;
    }

    let Ok(size) = window.inner_size() else {
        return;
    };

    persist_window_size(app, size.width, size.height);
}

fn persist_main_window_position(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    if window.is_maximized().unwrap_or(false) {
        return;
    }

    let Ok(position) = window.outer_position() else {
        return;
    };

    persist_window_position(app, position.x, position.y);
}

fn started_minimized() -> bool {
    std::env::args().any(|arg| arg == "--minimized")
}

fn reconcile_startup_window_visibility(app: AppHandle) {
    if started_minimized() {
        log::info!("Autostart launch detected; keeping main window hidden");
        return;
    }

    std::thread::spawn(move || {
        for attempt in 1..=STARTUP_WINDOW_RECONCILE_ATTEMPTS {
            let runtime = app.state::<AppRuntime>();
            match read_settings(&runtime) {
                Ok(settings) => {
                    let settings = merge_local_window_state(&app, settings);
                    restore_main_window_position(&app, &settings);
                    restore_main_window_size(&app, &settings);
                    let show_window_on_startup = settings
                        .get("show_window_on_startup")
                        .and_then(Value::as_bool)
                        .unwrap_or(true);
                    if determine_startup_window_visibility(show_window_on_startup, false) {
                        show_main_window(&app);
                    } else {
                        log::info!("Startup settings requested a background-only launch");
                    }
                    return;
                }
                Err(error) => {
                    if let Ok(settings) = read_local_window_state(&app) {
                        restore_main_window_position(&app, &settings);
                        restore_main_window_size(&app, &settings);
                    }
                    if attempt == STARTUP_WINDOW_RECONCILE_ATTEMPTS {
                        log::warn!(
                            "Failed to load startup window preference after {} attempts: {}. Showing window by default.",
                            STARTUP_WINDOW_RECONCILE_ATTEMPTS,
                            error
                        );
                        show_main_window(&app);
                        return;
                    }
                    std::thread::sleep(Duration::from_millis(
                        STARTUP_WINDOW_RECONCILE_DELAY_MS,
                    ));
                }
            }
        }
    });
}

fn trigger_playwright_run(runtime: &AppRuntime) -> Result<(), String> {
    let client = http_client()?;
    client
        .post(format!("{}/tasks/run-playwright", runtime.backend_url))
        .header("x-desktop-token", runtime.desktop_token.clone())
        .send()
        .map_err(|error| error.to_string())?
        .error_for_status()
        .map_err(|error| error.to_string())?;

    Ok(())
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn is_backend_terminated(runtime: &AppRuntime) -> bool {
    runtime
        .backend_terminated
        .lock()
        .map(|guard| *guard)
        .unwrap_or(false)
}

fn set_backend_terminated(runtime: &AppRuntime, terminated: bool) {
    if let Ok(mut guard) = runtime.backend_terminated.lock() {
        *guard = terminated;
    }
}

fn begin_shutdown(runtime: &AppRuntime) -> bool {
    if let Ok(mut guard) = runtime.shutdown_in_progress.lock() {
        if *guard {
            return false;
        }
        *guard = true;
        return true;
    }

    false
}

fn wait_for_backend_termination(runtime: &AppRuntime, timeout_ms: u64) -> bool {
    let mut waited_ms = 0;
    while waited_ms <= timeout_ms {
        if is_backend_terminated(runtime) {
            return true;
        }
        std::thread::sleep(Duration::from_millis(BACKEND_SHUTDOWN_POLL_INTERVAL_MS));
        waited_ms += BACKEND_SHUTDOWN_POLL_INTERVAL_MS;
    }

    is_backend_terminated(runtime)
}

fn determine_shutdown_escalation(
    terminated_after_graceful_wait: bool,
    tracked_child_available: bool,
    terminated_after_direct_kill_wait: bool,
) -> ShutdownEscalation {
    if terminated_after_graceful_wait {
        ShutdownEscalation::Graceful
    } else if tracked_child_available && terminated_after_direct_kill_wait {
        ShutdownEscalation::DirectKill
    } else {
        ShutdownEscalation::ForceTaskkill
    }
}

#[cfg(target_os = "windows")]
fn run_taskkill(args: &[&str], label: &str) {
    use std::os::windows::process::CommandExt;
    // Suppress the console window that would flash for each taskkill call in a GUI app.
    const CREATE_NO_WINDOW: u32 = 0x08000000;

    match ProcessCommand::new("taskkill")
        .args(args)
        .creation_flags(CREATE_NO_WINDOW)
        .output()
    {
        Ok(output) => {
            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                log::warn!("taskkill failed ({label}): {}", stderr.trim());
            }
        }
        Err(error) => {
            log::warn!("Failed to run taskkill ({label}): {error}");
        }
    }
}

#[cfg(target_os = "windows")]
fn force_kill_backend_processes(tracked_pid: Option<u32>) {
    if let Some(pid) = tracked_pid {
        let pid_str = pid.to_string();

        run_taskkill(&["/F", "/T", "/PID", &pid_str], "tracked-pid");
    }

    // Exact image-name attempts for known sidecar naming variants.
    for image in [
        "zzz-backend.exe",
        "zzz-backend-x86_64-pc-windows-msvc.exe",
        "zzz-backend-aarch64-pc-windows-msvc.exe",
        "zzz-backend-i686-pc-windows-msvc.exe",
    ] {
        run_taskkill(&["/F", "/T", "/IM", image], image);
    }

    // Final fallback using filter wildcard to catch any suffix variants.
    run_taskkill(
        &["/F", "/T", "/FI", "IMAGENAME eq zzz-backend*", "/IM", "*"],
        "filtered-wildcard",
    );
}

#[cfg(not(target_os = "windows"))]
fn force_kill_backend_processes(_tracked_pid: Option<u32>) {}

fn resolve_sidecar_sentry_dsn() -> Option<(String, &'static str)> {
    if let Ok(runtime_dsn) = std::env::var("SENTRY_DSN") {
        let trimmed = runtime_dsn.trim();
        if !trimmed.is_empty() {
            return Some((trimmed.to_string(), "env:SENTRY_DSN"));
        }
    }

    if let Some(embedded_dsn) = option_env!("ZZZ_SENTRY_DSN") {
        let trimmed = embedded_dsn.trim();
        if !trimmed.is_empty() {
            return Some((trimmed.to_string(), "embedded:ZZZ_SENTRY_DSN"));
        }
    }

    None
}

fn stop_backend_sidecar(app: &AppHandle, run_event: &str, reason: &str) {
    let runtime = app.state::<AppRuntime>();
    if !begin_shutdown(&runtime) {
        return;
    }

    let mut tracked_pid: Option<u32> = None;

    // Grab PID before taking the child so force_kill can use it as a fallback.
    if let Ok(child_guard) = runtime.backend_child.lock() {
        if let Some(child) = child_guard.as_ref() {
            tracked_pid = Some(child.pid());
        }
    }

    let shutdown_started_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|value| value.as_millis())
        .unwrap_or(0)
        .to_string();

    // Send graceful shutdown request (best-effort, 1 s timeout).
    if let Ok(client) = Client::builder()
        .timeout(Duration::from_millis(1000))
        .build()
    {
        if let Err(error) = client
            .post(format!("{}/shutdown", runtime.backend_url))
            .header("x-desktop-token", runtime.desktop_token.clone())
            .json(&json!({
                "source": "tauri",
                "run_event": run_event,
                "reason": reason,
                "tracked_pid": tracked_pid,
                "shutdown_started_at": shutdown_started_at,
            }))
            .send()
        {
            log::warn!("Failed to request graceful backend shutdown: {error}");
        }
    }

    let terminated_after_graceful_wait =
        wait_for_backend_termination(&runtime, BACKEND_SHUTDOWN_GRACEFUL_WAIT_MS);
    let mut tracked_child_available = false;
    let mut terminated_after_direct_kill_wait = false;

    if !terminated_after_graceful_wait {
        if let Ok(mut child_guard) = runtime.backend_child.lock() {
            if let Some(child) = child_guard.take() {
                tracked_child_available = true;
                if let Err(error) = child.kill() {
                    log::warn!("Failed to kill tracked backend sidecar: {error}");
                } else {
                    log::warn!(
                        "Graceful backend shutdown timed out; killed tracked sidecar process"
                    );
                }
            }
        }

        if tracked_child_available {
            terminated_after_direct_kill_wait =
                wait_for_backend_termination(&runtime, BACKEND_SHUTDOWN_POST_KILL_WAIT_MS);
        }
    }

    match determine_shutdown_escalation(
        terminated_after_graceful_wait,
        tracked_child_available,
        terminated_after_direct_kill_wait,
    ) {
        ShutdownEscalation::Graceful => {
            log::info!("Backend sidecar exited after graceful shutdown request");
        }
        ShutdownEscalation::DirectKill => {
            log::warn!("Backend sidecar exited after tracked child kill");
        }
        ShutdownEscalation::ForceTaskkill => {
            log::warn!("Backend sidecar still running; using taskkill fallback");
            force_kill_backend_processes(tracked_pid);
        }
    }
}

fn spawn_backend_sidecar(app: &tauri::App) {
    if cfg!(debug_assertions) {
        return;
    }

    let runtime = app.state::<AppRuntime>();
    let port = backend_port().to_string();

    let sentry_dsn = resolve_sidecar_sentry_dsn();
    if let Some((_, source)) = sentry_dsn.as_ref() {
        log::info!("Sidecar Sentry DSN source: {source}");
    } else {
        log::info!("Sidecar Sentry DSN source: none");
    }

    let spawn_result = app
        .shell()
        .sidecar("zzz-backend")
        .map(|command| {
            let command = command
                .arg("--port")
                .arg(port)
                .arg("--no-frontend")
                .arg("--hosted-by-tauri")
                .env("ZZZ_DESKTOP_TOKEN", runtime.desktop_token.clone());

            let command = if let Some((dsn, _)) = sentry_dsn.as_ref() {
                command.env("SENTRY_DSN", dsn)
            } else {
                command
            };

            command.spawn()
        })
        .map_err(|error| error.to_string())
        .and_then(|result| result.map_err(|error| error.to_string()));

    match spawn_result {
        Ok((mut rx, child)) => {
            set_backend_terminated(&runtime, false);
            if let Ok(mut child_guard) = runtime.backend_child.lock() {
                child_guard.replace(child);
            }

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(_) | CommandEvent::Stderr(_) => {}
                        CommandEvent::Terminated(payload) => {
                            let runtime = app_handle.state::<AppRuntime>();
                            set_backend_terminated(&runtime, true);
                            log::info!(
                                "Backend sidecar terminated with code {:?}",
                                payload.code
                            );
                        }
                        CommandEvent::Error(error) => {
                            log::error!("Backend sidecar error: {error}");
                        }
                        _ => {}
                    }
                }
            });
        }
        Err(error) => {
            log::error!("Failed to start backend sidecar: {error}");
        }
    }
}

fn build_tray(app: &tauri::App) -> tauri::Result<()> {
    let runtime = app.state::<AppRuntime>();
    let tray_settings = get_tray_settings(&runtime);

    let run_playwright_item =
        MenuItemBuilder::with_id("run_playwright", "Run Playwright").build(app)?;
    let toggle_show_window_on_startup_item = CheckMenuItemBuilder::with_id(
        "toggle_show_window_on_startup",
        "Show Window on Startup",
    )
    .checked(tray_settings.show_window_on_startup)
    .build(app)?;
    let toggle_exit_after_run_item = CheckMenuItemBuilder::with_id(
        "toggle_exit_after_run",
        "Exit After Run",
    )
    .checked(tray_settings.exit_after_run)
    .build(app)?;
    let exit_item = MenuItemBuilder::with_id("exit", "Exit").build(app)?;

    let menu = MenuBuilder::new(app)
        .items(&[
            &run_playwright_item,
            &toggle_show_window_on_startup_item,
            &toggle_exit_after_run_item,
            &exit_item,
        ])
        .build()?;

    let toggle_show_window_on_startup_item_handle =
        toggle_show_window_on_startup_item.clone();
    let toggle_exit_after_run_item_handle = toggle_exit_after_run_item.clone();

    TrayIconBuilder::with_id("main")
        .menu(&menu)
        .tooltip(tray_tooltip())
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "run_playwright" => {
                let runtime = app.state::<AppRuntime>();
                if let Err(error) = trigger_playwright_run(&runtime) {
                    log::error!("Failed to trigger Run Playwright: {error}");
                }
            }
            "toggle_show_window_on_startup" => {
                let runtime = app.state::<AppRuntime>();
                match toggle_backend_setting(&runtime, "show_window_on_startup") {
                    Ok(value) => {
                        let _ = toggle_show_window_on_startup_item_handle
                            .set_checked(value);
                    }
                    Err(error) => {
                        log::error!(
                            "Failed to toggle show_window_on_startup: {error}"
                        );
                    }
                }
            }
            "toggle_exit_after_run" => {
                let runtime = app.state::<AppRuntime>();
                match toggle_backend_setting(&runtime, "exit_after_run") {
                    Ok(value) => {
                        let _ = toggle_exit_after_run_item_handle.set_checked(value);
                    }
                    Err(error) => {
                        log::error!("Failed to toggle exit_after_run: {error}");
                    }
                }
            }
            "exit" => {
                stop_backend_sidecar(app, "menu_exit", "tray_menu");
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray: &TrayIcon, event: TrayIconEvent| match event {
            TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            }
            | TrayIconEvent::DoubleClick {
                button: MouseButton::Left,
                ..
            } => {
                show_main_window(&tray.app_handle());
            }
            _ => {}
        })
        .icon(
            app.default_window_icon()
                .cloned()
                .expect("missing default window icon for tray"),
        )
        .build(app)?;

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_autostart::Builder::new()
                .args(["--minimized"])
                .build(),
        )
        .setup(|app| {
            let desktop_token = std::env::var("ZZZ_DESKTOP_TOKEN")
                .unwrap_or_else(|_| generate_desktop_token());
            let backend_url = format!("http://127.0.0.1:{}", backend_port());

            app.manage(AppRuntime {
                backend_url,
                desktop_token,
                backend_child: Mutex::new(None),
                backend_terminated: Mutex::new(false),
                shutdown_in_progress: Mutex::new(false),
            });

            if let Some(window) = app.get_webview_window("main") {
                if let Some(icon) = app.default_window_icon().cloned() {
                    let _ = window.set_icon(icon);
                }
            }

            spawn_backend_sidecar(app);
            reconcile_autostart_preference(app.handle().clone());
            build_tray(app)?;
            reconcile_startup_window_visibility(app.handle().clone());

            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            match event {
                WindowEvent::CloseRequested { api, .. } => {
                    api.prevent_close();
                    persist_main_window_position(&window.app_handle());
                    persist_main_window_size(&window.app_handle());
                    let _ = window.hide();
                }
                _ => {}
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| match event {
        RunEvent::ExitRequested { .. } => {
            persist_main_window_position(app_handle);
            persist_main_window_size(app_handle);
            stop_backend_sidecar(app_handle, "exit_requested", "app_run_event");
        }
        RunEvent::Exit => {
            persist_main_window_position(app_handle);
            persist_main_window_size(app_handle);
            stop_backend_sidecar(app_handle, "exit", "app_run_event");
        }
        _ => {}
    });
}

#[cfg(test)]
mod tests {
    use super::{
        determine_autostart_sync_action, determine_shutdown_escalation,
        determine_startup_window_visibility, saved_window_position, saved_window_size,
        AutostartSyncAction, ShutdownEscalation,
    };
    use serde_json::json;

    #[test]
    fn autostart_sync_persists_existing_enabled_state() {
        assert_eq!(
            determine_autostart_sync_action(None, true),
            AutostartSyncAction::Persist(true)
        );
    }

    #[test]
    fn autostart_sync_persists_existing_disabled_state() {
        assert_eq!(
            determine_autostart_sync_action(None, false),
            AutostartSyncAction::Persist(false)
        );
    }

    #[test]
    fn autostart_sync_enables_when_preference_requires_it() {
        assert_eq!(
            determine_autostart_sync_action(Some(true), false),
            AutostartSyncAction::Enable
        );
    }

    #[test]
    fn autostart_sync_disables_when_preference_requires_it() {
        assert_eq!(
            determine_autostart_sync_action(Some(false), true),
            AutostartSyncAction::Disable
        );
    }

    #[test]
    fn autostart_sync_noops_when_state_matches_preference() {
        assert_eq!(
            determine_autostart_sync_action(Some(true), true),
            AutostartSyncAction::None
        );
        assert_eq!(
            determine_autostart_sync_action(Some(false), false),
            AutostartSyncAction::None
        );
    }

    #[test]
    fn startup_window_visibility_shows_for_normal_launches() {
        assert!(determine_startup_window_visibility(true, false));
    }

    #[test]
    fn startup_window_visibility_hides_when_setting_disabled() {
        assert!(!determine_startup_window_visibility(false, false));
    }

    #[test]
    fn startup_window_visibility_hides_for_minimized_launches() {
        assert!(!determine_startup_window_visibility(true, true));
    }

    #[test]
    fn saved_window_size_reads_valid_dimensions() {
        assert_eq!(
            saved_window_size(&json!({
                "window_width": 1440,
                "window_height": 900,
            })),
            Some((1440, 900))
        );
    }

    #[test]
    fn saved_window_size_rejects_missing_or_invalid_dimensions() {
        assert_eq!(saved_window_size(&json!({"window_width": 1440})), None);
        assert_eq!(
            saved_window_size(&json!({
                "window_width": 0,
                "window_height": 900,
            })),
            None
        );
        assert_eq!(
            saved_window_size(&json!({
                "window_width": u64::from(u32::MAX) + 1,
                "window_height": 900,
            })),
            None
        );
    }

    #[test]
    fn saved_window_position_reads_valid_coordinates() {
        assert_eq!(
            saved_window_position(&json!({
                "window_x": -640,
                "window_y": 120,
            })),
            Some((-640, 120))
        );
    }

    #[test]
    fn saved_window_position_rejects_missing_or_invalid_coordinates() {
        assert_eq!(saved_window_position(&json!({"window_x": 12})), None);
        assert_eq!(
            saved_window_position(&json!({
                "window_x": i64::from(i32::MAX) + 1,
                "window_y": 120,
            })),
            None
        );
        assert_eq!(
            saved_window_position(&json!({
                "window_x": 12,
                "window_y": i64::from(i32::MIN) - 1,
            })),
            None
        );
    }

    #[test]
    fn shutdown_escalation_prefers_graceful_exit() {
        assert_eq!(
            determine_shutdown_escalation(true, true, false),
            ShutdownEscalation::Graceful
        );
    }

    #[test]
    fn shutdown_escalation_accepts_direct_kill_exit() {
        assert_eq!(
            determine_shutdown_escalation(false, true, true),
            ShutdownEscalation::DirectKill
        );
    }

    #[test]
    fn shutdown_escalation_uses_force_kill_when_tracked_child_survives() {
        assert_eq!(
            determine_shutdown_escalation(false, true, false),
            ShutdownEscalation::ForceTaskkill
        );
    }

    #[test]
    fn shutdown_escalation_uses_force_kill_without_tracked_child() {
        assert_eq!(
            determine_shutdown_escalation(false, false, false),
            ShutdownEscalation::ForceTaskkill
        );
    }
}
