use std::process::Command as ProcessCommand;
use std::fs;
use std::net::TcpListener;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use reqwest::blocking::Client;
use serde_json::{json, Value};
use tauri::{
    menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, PhysicalPosition, PhysicalSize, Position, RunEvent, Size,
    WebviewUrl, WebviewWindowBuilder, WindowEvent,
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
const WINDOW_STATE_PERSIST_DEBOUNCE_MS: u64 = 500;
const WINDOW_STATE_FILE_NAME: &str = "window-state.json";
const WINDOW_MAXIMIZED_KEY: &str = "window_maximized";
const WINDOW_MINIMIZED_KEY: &str = "window_minimized";
const WINDOW_STATE_KEYS: [&str; 6] = [
    "window_x",
    "window_y",
    "window_width",
    "window_height",
    WINDOW_MAXIMIZED_KEY,
    WINDOW_MINIMIZED_KEY,
];

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
    backend_port: u16,
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

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum StartupWindowAction {
    ShowFocused,
    KeepHidden,
}

#[derive(Debug, Default, Clone, Copy)]
struct WindowGeometry {
    position: Option<(i32, i32)>,
    size: Option<(u32, u32)>,
    persist_revision: u64,
    persist_worker_running: bool,
}

#[derive(Debug, Default)]
struct WindowStateCache(Mutex<WindowGeometry>);

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

fn port_is_available(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

fn allocate_free_port() -> Option<u16> {
    TcpListener::bind(("127.0.0.1", 0))
        .ok()
        .and_then(|listener| listener.local_addr().ok())
        .map(|addr| addr.port())
}

/// Preferred backend port if free, otherwise an OS-allocated free port.
///
/// Mirrors the dev fallback in `backend/Bot.py`: a lingering instance or another
/// process on the default port must not stop the app from coming up.
fn resolve_backend_port() -> u16 {
    let preferred = backend_port();
    if port_is_available(preferred) {
        return preferred;
    }

    match allocate_free_port() {
        Some(free) => {
            log::warn!("Port {preferred} is in use; falling back to free port {free}");
            free
        }
        None => preferred,
    }
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

#[cfg(test)]
fn determine_startup_window_action(
    show_window_on_startup: bool,
    started_minimized: bool,
) -> StartupWindowAction {
    determine_startup_window_action_with_saved_state(
        show_window_on_startup,
        started_minimized,
        false,
    )
}

fn determine_startup_window_action_with_saved_state(
    show_window_on_startup: bool,
    started_minimized: bool,
    _restore_minimized: bool,
) -> StartupWindowAction {
    if !show_window_on_startup || started_minimized {
        StartupWindowAction::KeepHidden
    } else {
        StartupWindowAction::ShowFocused
    }
}

fn spans_intersect(start_a: i32, length_a: u32, start_b: i32, length_b: u32) -> bool {
    let end_a = i64::from(start_a) + i64::from(length_a);
    let end_b = i64::from(start_b) + i64::from(length_b);

    i64::from(start_a) < end_b && i64::from(start_b) < end_a
}

fn window_rect_intersects_monitor(
    window_position: (i32, i32),
    window_size: Option<(u32, u32)>,
    monitor_position: (i32, i32),
    monitor_size: (u32, u32),
) -> bool {
    match window_size {
        Some((window_width, window_height)) => {
            spans_intersect(
                window_position.0,
                window_width,
                monitor_position.0,
                monitor_size.0,
            ) && spans_intersect(
                window_position.1,
                window_height,
                monitor_position.1,
                monitor_size.1,
            )
        }
        None => {
            let monitor_right = i64::from(monitor_position.0) + i64::from(monitor_size.0);
            let monitor_bottom = i64::from(monitor_position.1) + i64::from(monitor_size.1);

            i64::from(window_position.0) >= i64::from(monitor_position.0)
                && i64::from(window_position.0) < monitor_right
                && i64::from(window_position.1) >= i64::from(monitor_position.1)
                && i64::from(window_position.1) < monitor_bottom
        }
    }
}

fn saved_window_rect_intersects_any_monitor(
    settings: &Value,
    monitors: &[tauri::Monitor],
) -> bool {
    let Some(window_position) = saved_window_position(settings) else {
        return true;
    };
    let window_size = saved_window_size(settings);

    monitors.iter().any(|monitor| {
        window_rect_intersects_monitor(
            window_position,
            window_size,
            (monitor.position().x, monitor.position().y),
            (monitor.size().width, monitor.size().height),
        )
    })
}

fn should_persist_window_geometry(is_maximized: bool) -> bool {
    !is_maximized
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

fn merge_window_state(settings: &mut Value, override_state: &Value) {
    let Some(settings_object) = settings.as_object_mut() else {
        return;
    };
    let Some(override_object) = override_state.as_object() else {
        return;
    };

    for key in WINDOW_STATE_KEYS {
        if let Some(value) = override_object.get(key) {
            settings_object.insert(key.to_string(), value.clone());
        }
    }
}

fn resolved_window_state_for_restore(
    settings: Option<Value>,
    local_state: Option<Value>,
) -> Option<Value> {
    match (settings, local_state) {
        (Some(mut settings), Some(local_state)) => {
            merge_window_state(&mut settings, &local_state);
            Some(settings)
        }
        (Some(settings), None) => Some(settings),
        (None, Some(local_state)) => Some(local_state),
        (None, None) => None,
    }
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

fn update_window_flag_payload(settings: &mut Value, key: &str, value: bool) -> Result<bool, String> {
    let current_value = settings.get(key).and_then(Value::as_bool);

    if current_value == Some(value) {
        return Ok(false);
    }

    let Some(object) = settings.as_object_mut() else {
        return Err(format!("Settings payload is not an object while saving {key}"));
    };

    object.insert(key.to_string(), Value::from(value));
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

fn saved_window_flag(settings: &Value, key: &str) -> Option<bool> {
    settings.get(key).and_then(Value::as_bool)
}

fn saved_window_maximized(settings: &Value) -> bool {
    saved_window_flag(settings, WINDOW_MAXIMIZED_KEY).unwrap_or(false)
}

fn saved_window_minimized(settings: &Value) -> bool {
    saved_window_flag(settings, WINDOW_MINIMIZED_KEY).unwrap_or(false)
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
        match window.available_monitors() {
            Ok(monitors)
                if !monitors.is_empty()
                    && !saved_window_rect_intersects_any_monitor(settings, &monitors) =>
            {
                log::warn!(
                    "Saved window position {x},{y} is outside the available monitors; centering window instead"
                );
                let _ = window.center();
                return;
            }
            Ok(_) => {}
            Err(error) => {
                log::warn!("Failed to inspect available monitors before restoring position: {error}");
            }
        }

        if let Err(error) =
            window.set_position(Position::Physical(PhysicalPosition::new(x, y)))
        {
            log::warn!("Failed to restore saved window position {x},{y}: {error}");
        }
    }
}

fn restore_main_window_geometry(app: &AppHandle, settings: &Value) {
    restore_main_window_position(app, settings);
    restore_main_window_size(app, settings);
}

fn apply_startup_window_state(
    app: &AppHandle,
    settings: &Value,
    action: StartupWindowAction,
) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    if saved_window_maximized(settings) {
        if let Err(error) = window.maximize() {
            log::warn!("Failed to restore maximized window state: {error}");
        }
    }

    match action {
        StartupWindowAction::ShowFocused => {
            let _ = window.unminimize();
            let _ = window.show();
            let _ = window.set_focus();
        }
        StartupWindowAction::KeepHidden => {}
    }
}

fn cache_window_size(app: &AppHandle, width: u32, height: u32) {
    match app.state::<WindowStateCache>().0.lock() {
        Ok(mut cache) => {
            cache.size = Some((width, height));
        }
        Err(error) => {
            log::warn!("Failed to cache window size before shutdown: {error}");
        }
    }
}

fn cache_window_position(app: &AppHandle, x: i32, y: i32) {
    match app.state::<WindowStateCache>().0.lock() {
        Ok(mut cache) => {
            cache.position = Some((x, y));
        }
        Err(error) => {
            log::warn!("Failed to cache window position before shutdown: {error}");
        }
    }
}

fn persist_updated_settings<FUpdate, FWrite>(
    settings: &mut Value,
    update: FUpdate,
    write: FWrite,
    write_error_message: &str,
) where
    FUpdate: FnOnce(&mut Value) -> Result<bool, String>,
    FWrite: FnOnce(&Value) -> Result<(), String>,
{
    match update(settings) {
        Ok(true) => {
            if let Err(error) = write(settings) {
                log::warn!("{write_error_message}: {error}");
            }
        }
        Ok(false) => {}
        Err(error) => {
            log::warn!("{error}");
        }
    }
}

fn persist_window_size(app: &AppHandle, width: u32, height: u32) {
    let runtime = app.state::<AppRuntime>();
    match read_settings(&runtime) {
        Ok(mut settings) => persist_updated_settings(
            &mut settings,
            |settings| update_window_size_payload(settings, width, height),
            |settings| write_settings(&runtime, settings),
            "Failed to persist saved window size to backend",
        ),
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

    persist_updated_settings(
        &mut local_settings,
        |settings| update_window_size_payload(settings, width, height),
        |settings| write_local_window_state(app, settings),
        "Failed to persist saved window size locally",
    );
}

fn persist_window_position(app: &AppHandle, x: i32, y: i32) {
    let runtime = app.state::<AppRuntime>();
    match read_settings(&runtime) {
        Ok(mut settings) => persist_updated_settings(
            &mut settings,
            |settings| update_window_position_payload(settings, x, y),
            |settings| write_settings(&runtime, settings),
            "Failed to persist saved window position to backend",
        ),
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

    persist_updated_settings(
        &mut local_settings,
        |settings| update_window_position_payload(settings, x, y),
        |settings| write_local_window_state(app, settings),
        "Failed to persist saved window position locally",
    );
}

fn persist_window_flag(
    app: &AppHandle,
    key: &str,
    value: bool,
    backend_error_message: &str,
    local_error_message: &str,
) {
    let runtime = app.state::<AppRuntime>();
    match read_settings(&runtime) {
        Ok(mut settings) => persist_updated_settings(
            &mut settings,
            |settings| update_window_flag_payload(settings, key, value),
            |settings| write_settings(&runtime, settings),
            backend_error_message,
        ),
        Err(error) => {
            log::info!("Skipping backend {key} persistence: {error}");
        }
    }

    let mut local_settings = match read_local_window_state(app) {
        Ok(settings) => settings,
        Err(error) => {
            log::warn!("Failed to read local window state before saving {key}: {error}");
            json!({})
        }
    };

    persist_updated_settings(
        &mut local_settings,
        |settings| update_window_flag_payload(settings, key, value),
        |settings| write_local_window_state(app, settings),
        local_error_message,
    );
}

fn schedule_runtime_window_state_persist(app: &AppHandle) {
    let should_spawn = match app.state::<WindowStateCache>().0.lock() {
        Ok(mut cache) => {
            cache.persist_revision = cache.persist_revision.saturating_add(1);
            if cache.persist_worker_running {
                false
            } else {
                cache.persist_worker_running = true;
                true
            }
        }
        Err(error) => {
            log::warn!("Failed to schedule runtime window state persistence: {error}");
            false
        }
    };

    if !should_spawn {
        return;
    }

    let app_handle = app.clone();
    std::thread::spawn(move || loop {
        let observed_revision = match app_handle.state::<WindowStateCache>().0.lock() {
            Ok(cache) => cache.persist_revision,
            Err(error) => {
                log::warn!("Failed to inspect pending window state persistence: {error}");
                return;
            }
        };

        std::thread::sleep(Duration::from_millis(WINDOW_STATE_PERSIST_DEBOUNCE_MS));

        let should_persist = match app_handle.state::<WindowStateCache>().0.lock() {
            Ok(mut cache) => {
                if cache.persist_revision == observed_revision {
                    cache.persist_worker_running = false;
                    true
                } else {
                    false
                }
            }
            Err(error) => {
                log::warn!("Failed to finalize runtime window state persistence: {error}");
                return;
            }
        };

        if should_persist {
            persist_current_window_state(&app_handle);
            return;
        }
    });
}

fn cached_window_geometry<T, F>(app: &AppHandle, select: F) -> Option<T>
where
    T: Copy,
    F: FnOnce(&WindowGeometry) -> Option<T>,
{
    app.state::<WindowStateCache>()
        .0
        .lock()
        .ok()
        .and_then(|cache| select(&cache))
}

fn persist_cached_window_size(app: &AppHandle) {
    if !should_persist_window_geometry(main_window_is_maximized(app)) {
        return;
    }

    let cached_size = cached_window_geometry(app, |cache| cache.size);

    if let Some((width, height)) = cached_size {
        persist_window_size(app, width, height);
    } else {
        persist_main_window_size(app);
    }
}

fn persist_cached_window_position(app: &AppHandle) {
    if !should_persist_window_geometry(main_window_is_maximized(app)) {
        return;
    }

    let cached_position = cached_window_geometry(app, |cache| cache.position);

    if let Some((x, y)) = cached_position {
        persist_window_position(app, x, y);
    } else {
        persist_main_window_position(app);
    }
}

fn persist_main_window_display_state(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    let is_maximized = window.is_maximized().unwrap_or(false);
    let is_minimized = window.is_minimized().unwrap_or(false);

    persist_window_flag(
        app,
        WINDOW_MAXIMIZED_KEY,
        is_maximized,
        "Failed to persist maximized window state to backend",
        "Failed to persist maximized window state locally",
    );
    persist_window_flag(
        app,
        WINDOW_MINIMIZED_KEY,
        is_minimized,
        "Failed to persist minimized window state to backend",
        "Failed to persist minimized window state locally",
    );
}

fn persist_current_window_state(app: &AppHandle) {
    persist_main_window_display_state(app);
    persist_cached_window_position(app);
    persist_cached_window_size(app);
}

fn should_persist_display_state_on_window_event(event: &WindowEvent) -> bool {
    matches!(event, WindowEvent::Focused(_))
}

fn should_schedule_runtime_window_state_persist(event: &WindowEvent) -> bool {
    matches!(event, WindowEvent::Moved(_) | WindowEvent::Resized(_))
}

fn persist_main_window_size(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    if !should_persist_window_geometry(window.is_maximized().unwrap_or(false)) {
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

    if !should_persist_window_geometry(window.is_maximized().unwrap_or(false)) {
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

fn main_window_is_maximized(app: &AppHandle) -> bool {
    app.get_webview_window("main")
        .and_then(|window| window.is_maximized().ok())
        .unwrap_or(false)
}

fn reconcile_startup_window_visibility(app: AppHandle) {
    let started_hidden = started_minimized();
    if started_hidden {
        log::info!("Autostart launch detected; keeping main window hidden");
    }

    std::thread::spawn(move || {
        for attempt in 1..=STARTUP_WINDOW_RECONCILE_ATTEMPTS {
            let runtime = app.state::<AppRuntime>();
            let local_state = read_local_window_state(&app).ok();

            match read_settings(&runtime) {
                Ok(settings) => {
                    let show_window_on_startup = settings
                        .get("show_window_on_startup")
                        .and_then(Value::as_bool)
                        .unwrap_or(true);
                    if let Some(settings) =
                        resolved_window_state_for_restore(Some(settings), local_state)
                    {
                        restore_main_window_geometry(&app, &settings);
                        apply_startup_window_state(
                            &app,
                            &settings,
                            determine_startup_window_action_with_saved_state(
                                show_window_on_startup,
                                started_hidden,
                                saved_window_minimized(&settings),
                            ),
                        );
                    }
                    if !show_window_on_startup && !started_hidden {
                        log::info!("Startup settings requested a background-only launch");
                    }
                    return;
                }
                Err(error) => {
                    if let Some(settings) =
                        resolved_window_state_for_restore(None, local_state)
                    {
                        restore_main_window_geometry(&app, &settings);
                        apply_startup_window_state(
                            &app,
                            &settings,
                            determine_startup_window_action_with_saved_state(
                                false,
                                started_hidden,
                                saved_window_minimized(&settings),
                            ),
                        );
                    }
                    if attempt == STARTUP_WINDOW_RECONCILE_ATTEMPTS {
                        if started_hidden {
                            log::warn!(
                                "Failed to load startup window preference after {} attempts: {}. Keeping autostart launch hidden.",
                                STARTUP_WINDOW_RECONCILE_ATTEMPTS,
                                error
                            );
                        } else {
                            log::warn!(
                                "Failed to load startup window preference after {} attempts: {}. Showing window by default.",
                                STARTUP_WINDOW_RECONCILE_ATTEMPTS,
                                error
                            );
                            show_main_window(&app);
                        }
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
    let port = runtime.backend_port.to_string();

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
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            show_main_window(app);
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_autostart::Builder::new()
                .args(["--minimized"])
                .build(),
        )
        .setup(|app| {
            let desktop_token = std::env::var("ZZZ_DESKTOP_TOKEN")
                .unwrap_or_else(|_| generate_desktop_token());
            // In debug (`cargo tauri dev`) the dev runner fixes the port and starts
            // the backend itself, so bind exactly that. In release the bundled
            // sidecar is ours to launch, so fall back to a free port if needed.
            let port = if cfg!(debug_assertions) {
                backend_port()
            } else {
                resolve_backend_port()
            };
            let backend_url = format!("http://127.0.0.1:{port}");

            // Build the main window in Rust (instead of tauri.conf.json) so we can
            // attach an initialization script. It runs after the global object is
            // created but before the page is parsed or any frontend script runs, so
            // the WebView learns the actual backend URL even when it isn't 8000.
            let init_script = format!(
                "if (window.location.protocol.startsWith('tauri') || \
                 window.location.protocol.startsWith('http')) {{ \
                 window.__ZZZ_BACKEND_URL__ = \"{backend_url}\"; }}"
            );
            WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title("ZZZ Bot")
                .inner_size(1200.0, 800.0)
                .resizable(true)
                .visible(false)
                .initialization_script(init_script)
                .build()?;

            app.manage(AppRuntime {
                backend_url,
                backend_port: port,
                desktop_token,
                backend_child: Mutex::new(None),
                backend_terminated: Mutex::new(false),
                shutdown_in_progress: Mutex::new(false),
            });
            app.manage(WindowStateCache::default());

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
            if should_persist_display_state_on_window_event(event) {
                persist_main_window_display_state(&window.app_handle());
            }
            if should_schedule_runtime_window_state_persist(event) {
                schedule_runtime_window_state_persist(&window.app_handle());
            }

            match event {
                WindowEvent::Moved(position) => {
                    cache_window_position(&window.app_handle(), position.x, position.y);
                }
                WindowEvent::Resized(size) => {
                    cache_window_size(&window.app_handle(), size.width, size.height);
                }
                WindowEvent::CloseRequested { api, .. } => {
                    api.prevent_close();
                    persist_current_window_state(&window.app_handle());
                    let _ = window.hide();
                }
                _ => {}
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| match event {
        RunEvent::ExitRequested { .. } => {
            persist_current_window_state(app_handle);
            stop_backend_sidecar(app_handle, "exit_requested", "app_run_event");
        }
        RunEvent::Exit => {
            persist_current_window_state(app_handle);
            stop_backend_sidecar(app_handle, "exit", "app_run_event");
        }
        _ => {}
    });
}

#[cfg(test)]
mod tests {
    use super::{
        determine_autostart_sync_action, determine_shutdown_escalation,
        determine_startup_window_action, determine_startup_window_action_with_saved_state,
        merge_window_state, resolved_window_state_for_restore, saved_window_flag,
        saved_window_position, saved_window_size, spans_intersect,
        should_persist_display_state_on_window_event, should_persist_window_geometry,
        should_schedule_runtime_window_state_persist, update_window_flag_payload,
        update_window_position_payload, update_window_size_payload,
        window_rect_intersects_monitor, AutostartSyncAction, ShutdownEscalation,
        StartupWindowAction, WINDOW_MAXIMIZED_KEY, WINDOW_MINIMIZED_KEY,
    };
    use serde_json::json;
    use tauri::{PhysicalPosition, PhysicalSize, WindowEvent};

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
        assert_eq!(
            determine_startup_window_action(true, false),
            StartupWindowAction::ShowFocused
        );
    }

    #[test]
    fn startup_window_visibility_hides_when_setting_disabled() {
        assert_eq!(
            determine_startup_window_action(false, false),
            StartupWindowAction::KeepHidden
        );
    }

    #[test]
    fn startup_window_visibility_hides_for_minimized_launches() {
        assert_eq!(
            determine_startup_window_action(true, true),
            StartupWindowAction::KeepHidden
        );
    }

    #[test]
    fn startup_window_action_ignores_saved_minimized_state_for_manual_launches() {
        assert_eq!(
            determine_startup_window_action_with_saved_state(true, false, true),
            StartupWindowAction::ShowFocused
        );
    }

    #[test]
    fn spans_intersect_when_ranges_overlap() {
        assert!(spans_intersect(100, 300, 250, 200));
        assert!(!spans_intersect(100, 100, 200, 100));
    }

    #[test]
    fn window_rect_intersects_monitor_when_top_left_is_offscreen_but_window_is_visible() {
        assert!(window_rect_intersects_monitor(
            (-200, 120),
            Some((800, 600)),
            (0, 0),
            (1920, 1080),
        ));
    }

    #[test]
    fn window_rect_does_not_intersect_monitor_when_completely_offscreen() {
        assert!(!window_rect_intersects_monitor(
            (2600, 200),
            Some((800, 600)),
            (0, 0),
            (1920, 1080),
        ));
    }

    #[test]
    fn maximized_windows_skip_geometry_persistence() {
        assert!(!should_persist_window_geometry(true));
        assert!(should_persist_window_geometry(false));
    }

    #[test]
    fn merge_window_state_overrides_only_window_state_keys() {
        let mut settings = json!({
            "window_x": 120,
            "window_y": 80,
            "window_width": 1280,
            "window_height": 720,
            "window_maximized": false,
            "theme": "nebula",
        });

        merge_window_state(
            &mut settings,
            &json!({
                "window_x": 320,
                "window_height": 900,
                "window_maximized": true,
                "theme": "venom",
            }),
        );

        assert_eq!(
            settings,
            json!({
                "window_x": 320,
                "window_y": 80,
                "window_width": 1280,
                "window_height": 900,
                "window_maximized": true,
                "theme": "nebula",
            })
        );
    }

    #[test]
    fn resolved_window_state_prefers_local_geometry_over_backend() {
        assert_eq!(
            resolved_window_state_for_restore(
                Some(json!({
                    "window_x": 120,
                    "window_y": 80,
                    "window_width": 1280,
                    "window_height": 720,
                    "window_maximized": false,
                    "show_window_on_startup": true,
                })),
                Some(json!({
                    "window_x": 320,
                    "window_width": 1440,
                    "window_minimized": true,
                })),
            ),
            Some(json!({
                "window_x": 320,
                "window_y": 80,
                "window_width": 1440,
                "window_height": 720,
                "window_maximized": false,
                "window_minimized": true,
                "show_window_on_startup": true,
            }))
        );
    }

    #[test]
    fn resolved_window_state_uses_local_fallback_without_backend_settings() {
        assert_eq!(
            resolved_window_state_for_restore(
                None,
                Some(json!({
                    "window_x": 320,
                    "window_y": 180,
                    "window_width": 1440,
                    "window_height": 900,
                    "window_maximized": true,
                    "window_minimized": false,
                })),
            ),
            Some(json!({
                "window_x": 320,
                "window_y": 180,
                "window_width": 1440,
                "window_height": 900,
                "window_maximized": true,
                "window_minimized": false,
            }))
        );
    }

    #[test]
    fn update_window_size_payload_is_noop_for_unchanged_dimensions() {
        let mut settings = json!({
            "window_width": 1440,
            "window_height": 900,
        });

        assert_eq!(
            update_window_size_payload(&mut settings, 1440, 900),
            Ok(false)
        );
        assert_eq!(
            settings,
            json!({
                "window_width": 1440,
                "window_height": 900,
            })
        );
    }

    #[test]
    fn update_window_flag_payload_is_noop_for_unchanged_value() {
        let mut settings = json!({
            "window_maximized": true,
        });

        assert_eq!(
            update_window_flag_payload(&mut settings, WINDOW_MAXIMIZED_KEY, true),
            Ok(false)
        );
        assert_eq!(
            settings,
            json!({
                "window_maximized": true,
            })
        );
    }

    #[test]
    fn saved_window_flag_reads_boolean_values() {
        let settings = json!({
            "window_maximized": true,
            "window_minimized": false,
        });

        assert_eq!(saved_window_flag(&settings, WINDOW_MAXIMIZED_KEY), Some(true));
        assert_eq!(saved_window_flag(&settings, WINDOW_MINIMIZED_KEY), Some(false));
    }

    #[test]
    fn display_state_persists_on_resize_and_focus_events() {
        assert!(should_persist_display_state_on_window_event(
            &WindowEvent::Focused(false)
        ));
        assert!(!should_persist_display_state_on_window_event(
            &WindowEvent::Resized(PhysicalSize::new(1440, 900))
        ));
        assert!(!should_persist_display_state_on_window_event(
            &WindowEvent::Moved(PhysicalPosition::new(320, 180))
        ));
    }

    #[test]
    fn runtime_window_state_persist_schedules_on_move_and_resize_events() {
        assert!(should_schedule_runtime_window_state_persist(
            &WindowEvent::Moved(PhysicalPosition::new(320, 180))
        ));
        assert!(should_schedule_runtime_window_state_persist(
            &WindowEvent::Resized(PhysicalSize::new(1440, 900))
        ));
        assert!(!should_schedule_runtime_window_state_persist(
            &WindowEvent::Focused(false)
        ));
    }

    #[test]
    fn update_window_position_payload_is_noop_for_unchanged_coordinates() {
        let mut settings = json!({
            "window_x": 320,
            "window_y": 180,
        });

        assert_eq!(
            update_window_position_payload(&mut settings, 320, 180),
            Ok(false)
        );
        assert_eq!(
            settings,
            json!({
                "window_x": 320,
                "window_y": 180,
            })
        );
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
