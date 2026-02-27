use std::fs::{create_dir_all, read_to_string, File};
use std::path::{Path, PathBuf};

fn ensure_dev_sidecar_placeholder() {
    let profile = std::env::var("PROFILE").unwrap_or_default();
    if profile == "release" {
        return;
    }

    let target = std::env::var("TARGET").unwrap_or_default();
    if target.is_empty() {
        return;
    }

    let extension = if target.contains("windows") { ".exe" } else { "" };
    let filename = format!("zzz-backend-{target}{extension}");
    let path = PathBuf::from("binaries").join(filename);

    if let Some(parent) = path.parent() {
        let _ = create_dir_all(parent);
    }

    if !path.exists() {
        let _ = File::create(path);
    }
}

fn read_env_var_from_file(env_path: &Path, key: &str) -> Option<String> {
    let content = read_to_string(env_path).ok()?;

    for raw_line in content.lines() {
        let line = raw_line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let normalized_line = line.strip_prefix("export ").unwrap_or(line).trim();
        let Some((raw_key, raw_value)) = normalized_line.split_once('=') else {
            continue;
        };
        if raw_key.trim() != key {
            continue;
        }

        let value = raw_value.trim();
        if value.is_empty() {
            return None;
        }

        let unquoted = if (value.starts_with('"') && value.ends_with('"'))
            || (value.starts_with('\'') && value.ends_with('\''))
        {
            value[1..value.len() - 1].trim()
        } else {
            value
        };

        if unquoted.is_empty() {
            return None;
        }

        return Some(unquoted.to_string());
    }

    None
}

fn export_embedded_sentry_dsn() {
    let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_default());
    let root_env_path = manifest_dir.join("..").join(".env");

    println!("cargo:rerun-if-changed={}", root_env_path.display());

    if let Some(sentry_dsn) = read_env_var_from_file(&root_env_path, "SENTRY_DSN") {
        println!("cargo:rustc-env=ZZZ_SENTRY_DSN={sentry_dsn}");
    }
}

fn main() {
    ensure_dev_sidecar_placeholder();
    export_embedded_sentry_dsn();
    tauri_build::build();
}
