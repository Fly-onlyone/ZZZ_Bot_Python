use std::fs::{create_dir_all, File};
use std::path::PathBuf;

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

fn main() {
    ensure_dev_sidecar_placeholder();
    tauri_build::build();
}
