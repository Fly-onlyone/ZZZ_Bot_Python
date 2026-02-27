# ZZZ Bot Build Script

Build automation for the Tauri production app (with native tray icon).

## Pipeline

1. Frontend build (`bun run build`)
2. Backend sidecar build (`bun run tauri:prepare-sidecar`)
3. Desktop bundle build (`cargo tauri build`)

This replaces the old PyInstaller + Inno production installer flow.

## Requirements

- Python 3.11+
- Bun 1.3+
- Rust toolchain + Cargo
- Tauri CLI (`cargo install tauri-cli` if needed)
- uv

## Sentry DSN for Installed EXE

For release installer builds, the desktop binary embeds backend Sentry DSN from the repository root `.env` file.

Required before `cargo tauri build`:

- Add `SENTRY_DSN=...` to `../.env` (project root).
- Rebuild after changing the DSN value.

Runtime precedence for installed app:

1. Runtime environment variable `SENTRY_DSN` (if present)
2. Embedded fallback DSN from build time
3. Disabled Sentry when neither source exists

For profile visibility in installed app:

- Keep `sentry_traces_sample_rate` and `sentry_profiles_sample_rate` at `1.0` in Settings -> Monitoring, or set env vars
  `SENTRY_TRACES_SAMPLE_RATE=1.0` and `SENTRY_PROFILES_SAMPLE_RATE=1.0`.
- In Sentry, filter by `environment=production` and a recent time window.

## Usage

```bash
cd product
python build.py
```

Or run the GUI launcher:

```bash
cd product
build.bat
```

## Artifacts

After a successful bundle step, installers are created under:

- `src-tauri/target/release/bundle/nsis/*.exe`
- `src-tauri/target/release/bundle/msi/*.msi`

Use those installers for production releases if you need the Tauri tray icon.

## Version Update

When version increment is enabled, the script updates:

- `product/Bot version.txt`
- `src-tauri/tauri.conf.json`
- `src-tauri/Cargo.toml`
