use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use reqwest::blocking::Client;
use serde_json::Value;
use tauri::{
    menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, WindowEvent,
};
use tauri_plugin_shell::{process::CommandChild, process::CommandEvent, ShellExt};

#[derive(Debug)]
struct AppRuntime {
    backend_url: String,
    desktop_token: String,
    backend_child: Mutex<Option<CommandChild>>,
}

#[derive(Debug, Clone, Copy)]
struct TraySettings {
    open_web_ui: bool,
    exit_after_run: bool,
}

impl Default for TraySettings {
    fn default() -> Self {
        Self {
            open_web_ui: true,
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

fn get_tray_settings(runtime: &AppRuntime) -> TraySettings {
    if let Ok(settings) = read_settings(runtime) {
        let open_web_ui = settings
            .get("open_web_ui")
            .and_then(Value::as_bool)
            .unwrap_or(true);
        let exit_after_run = settings
            .get("exit_after_run")
            .and_then(Value::as_bool)
            .unwrap_or(false);

        return TraySettings {
            open_web_ui,
            exit_after_run,
        };
    }

    TraySettings::default()
}

fn toggle_backend_setting(runtime: &AppRuntime, key: &str) -> Result<bool, String> {
    let client = http_client()?;
    let mut payload = read_settings(runtime)?;

    let current_value = payload
        .get(key)
        .and_then(Value::as_bool)
        .ok_or_else(|| format!("Setting '{key}' is not a boolean"))?;
    let next_value = !current_value;

    if let Some(object) = payload.as_object_mut() {
        object.insert(key.to_string(), Value::Bool(next_value));
    } else {
        return Err("Settings payload is not a JSON object".to_string());
    }

    client
        .post(format!("{}/settings", runtime.backend_url))
        .json(&payload)
        .send()
        .map_err(|error| error.to_string())?
        .error_for_status()
        .map_err(|error| error.to_string())?;

    Ok(next_value)
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

fn stop_backend_sidecar(app: &AppHandle) {
    let runtime = app.state::<AppRuntime>();
    let mut child_guard = match runtime.backend_child.lock() {
        Ok(guard) => guard,
        Err(_) => return,
    };

    if let Some(child) = child_guard.take() {
        let _ = child.kill();
    }
}

fn spawn_backend_sidecar(app: &tauri::App) {
    if cfg!(debug_assertions) {
        return;
    }

    let runtime = app.state::<AppRuntime>();
    let port = backend_port().to_string();

    let spawn_result = app
        .shell()
        .sidecar("zzz-backend")
        .map(|command| {
            command
                .arg("--port")
                .arg(port)
                .arg("--no-frontend")
                .arg("--hosted-by-tauri")
                .env("ZZZ_DESKTOP_TOKEN", runtime.desktop_token.clone())
                .spawn()
        })
        .map_err(|error| error.to_string())
        .and_then(|result| result.map_err(|error| error.to_string()));

    match spawn_result {
        Ok((mut rx, child)) => {
            if let Ok(mut child_guard) = runtime.backend_child.lock() {
                child_guard.replace(child);
            }

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(_) | CommandEvent::Stderr(_) => {}
                        CommandEvent::Terminated(payload) => {
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
    let toggle_open_web_ui_item = CheckMenuItemBuilder::with_id(
        "toggle_open_web_ui",
        "Toggle Web UI",
    )
    .checked(tray_settings.open_web_ui)
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
            &toggle_open_web_ui_item,
            &toggle_exit_after_run_item,
            &exit_item,
        ])
        .build()?;

    let toggle_open_web_ui_item_handle = toggle_open_web_ui_item.clone();
    let toggle_exit_after_run_item_handle = toggle_exit_after_run_item.clone();

    TrayIconBuilder::new()
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "run_playwright" => {
                let runtime = app.state::<AppRuntime>();
                if let Err(error) = trigger_playwright_run(&runtime) {
                    log::error!("Failed to trigger Run Playwright: {error}");
                }
            }
            "toggle_open_web_ui" => {
                let runtime = app.state::<AppRuntime>();
                match toggle_backend_setting(&runtime, "open_web_ui") {
                    Ok(value) => {
                        let _ = toggle_open_web_ui_item_handle.set_checked(value);
                    }
                    Err(error) => {
                        log::error!("Failed to toggle open_web_ui: {error}");
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
                stop_backend_sidecar(app);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| match event {
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
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let desktop_token = std::env::var("ZZZ_DESKTOP_TOKEN")
                .unwrap_or_else(|_| generate_desktop_token());
            let backend_url = format!("http://127.0.0.1:{}", backend_port());

            app.manage(AppRuntime {
                backend_url,
                desktop_token,
                backend_child: Mutex::new(None),
            });

            spawn_backend_sidecar(app);
            build_tray(app)?;

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
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
