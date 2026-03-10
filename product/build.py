#!/usr/bin/env python3
"""
ZZZ Bot build script.

Build pipeline:
1. Build frontend (Vite)
2. Build backend sidecar for Tauri
3. Build Tauri desktop bundles (NSIS/MSI on Windows)

Optional: increment version before building.
"""

import json
import re
import subprocess
import sys
import time
import tomllib
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TAURI_DIR = PROJECT_ROOT / "src-tauri"
TAURI_CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
CARGO_TOML_PATH = TAURI_DIR / "Cargo.toml"
VERSION_FILE_PATH = Path(__file__).parent / "Bot version.txt"


def print_header(message: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}[ERR] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKCYAN}[..] {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def run_command(command, cwd: Path, step_name: str, shell: bool = False) -> bool:
    """Run a command and stream output to stdout."""
    print_info(f"Running ({step_name}): {command}")

    proc = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell,
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        print(line.rstrip())

    proc.wait()
    if proc.returncode != 0:
        print_error(f"{step_name} failed with exit code {proc.returncode}")
        return False

    print_success(f"{step_name} completed")
    return True


def get_current_version() -> str:
    """Read current version from Tauri config, then Cargo, then legacy metadata."""
    try:
        tauri_config = json.loads(TAURI_CONFIG_PATH.read_text(encoding="utf-8"))
        version = str(tauri_config.get("version", "")).strip()
        if version:
            return version
    except (OSError, json.JSONDecodeError):
        pass

    try:
        cargo_manifest = tomllib.loads(CARGO_TOML_PATH.read_text(encoding="utf-8"))
        package_meta = cargo_manifest.get("package")
        if isinstance(package_meta, dict):
            version = str(package_meta.get("version", "")).strip()
            if version:
                return version
    except (OSError, tomllib.TOMLDecodeError):
        pass

    try:
        content = VERSION_FILE_PATH.read_text(encoding="utf-8")
        match = re.search(r"StringStruct\('ProductVersion',\s*'([^']+)'\)", content)
        if match:
            return match.group(1)
    except OSError:
        pass

    return "0.1.0"


def increment_version(version: str) -> str:
    """Increment the trailing numeric version segment."""
    parts = version.split(".")
    if not parts:
        return "0.1.0"

    try:
        if len(parts) == 1:
            return f"{int(parts[0]) + 1}"

        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) >= 3 else 0
        return f"{major}.{minor}.{patch + 1}"
    except ValueError:
        return version


def update_version_files(new_version: str) -> None:
    """Update version metadata in legacy file, Tauri config, and Cargo manifest."""
    print_info(f"Updating version to {new_version}")

    parts = new_version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    version_tuple = f"({major}, {minor}, {patch}, 0)"

    version_content = VERSION_FILE_PATH.read_text(encoding="utf-8")
    version_content = re.sub(
        r"filevers=\([^)]+\)", f"filevers={version_tuple}", version_content
    )
    version_content = re.sub(
        r"prodvers=\([^)]+\)", f"prodvers={version_tuple}", version_content
    )
    version_content = re.sub(
        r"StringStruct\('ProductVersion',\s*'[^']+'\)",
        f"StringStruct('ProductVersion', '{new_version}')",
        version_content,
    )
    version_content = re.sub(
        r"StringStruct\('FileVersion',\s*'[^']+'\)",
        f"StringStruct('FileVersion', '{new_version}')",
        version_content,
    )
    VERSION_FILE_PATH.write_text(version_content, encoding="utf-8")
    print_success(f"Updated {VERSION_FILE_PATH}")

    tauri_config = json.loads(TAURI_CONFIG_PATH.read_text(encoding="utf-8"))
    tauri_config["version"] = new_version
    TAURI_CONFIG_PATH.write_text(
        json.dumps(tauri_config, indent=2) + "\n", encoding="utf-8"
    )
    print_success(f"Updated {TAURI_CONFIG_PATH}")

    cargo_content = CARGO_TOML_PATH.read_text(encoding="utf-8")
    cargo_updated, replacements = re.subn(
        r'(?ms)(^\[package]\s.*?^\s*version\s*=\s*")[^"]+(")',
        rf"\g<1>{new_version}\2",
        cargo_content,
    )
    if replacements:
        CARGO_TOML_PATH.write_text(cargo_updated, encoding="utf-8")
        print_success(f"Updated {CARGO_TOML_PATH}")
    else:
        print_warning(f"Could not locate [package].version in {CARGO_TOML_PATH}")


def build_frontend() -> bool:
    """Build frontend assets for Tauri embedding."""
    print_header("STEP 1: FRONTEND BUILD")
    return run_command(
        "bun run build", cwd=FRONTEND_DIR, step_name="frontend", shell=True
    )


def build_sidecar() -> bool:
    """Build and copy Python sidecar binary for Tauri externalBin."""
    print_header("STEP 2: SIDECAR BUILD")
    ok = run_command(
        "bun run tauri:prepare-sidecar",
        cwd=FRONTEND_DIR,
        step_name="tauri sidecar prepare",
        shell=True,
    )
    if not ok:
        return False

    binaries = sorted(TAURI_DIR.joinpath("binaries").glob("zzz-backend-*.exe"))
    if not binaries:
        print_error("No sidecar binary found in src-tauri/binaries")
        return False

    print_success(f"Sidecar ready: {binaries[-1]}")
    return True


def _collect_bundle_artifacts() -> list[Path]:
    bundle_dir = TAURI_DIR / "target" / "release" / "bundle"
    artifacts: list[Path] = []
    patterns = ["nsis/*.exe", "msi/*.msi", "app/*.exe"]
    for pattern in patterns:
        artifacts.extend(bundle_dir.glob(pattern))
    return sorted(artifacts, key=lambda path: path.stat().st_mtime, reverse=True)


def stop_conflicting_processes_for_bundle() -> int:
    """Stop running ZZZ processes that commonly lock Windows bundle outputs."""
    if sys.platform != "win32":
        return 0

    # WHY: Windows cannot overwrite bundle artifacts when app or stale build processes still hold files.
    script = (
        "$repoHint = 'ZZZ bot - Python'; "
        "$appTargets = @('ZZZ Bot.exe','zzz-bot.exe','zzz-backend.exe'); "
        "$toolTargets = @('cargo.exe','cargo-tauri.exe','makensis.exe','light.exe','candle.exe'); "
        "$appProcs = Get-CimInstance Win32_Process | Where-Object { "
        "($appTargets -contains $_.Name) -and $_.ExecutablePath -and "
        "(($_.ExecutablePath -like '*\\ZZZ Bot\\*') -or ($_.ExecutablePath -like '*\\ZZZ bot - Python\\*')) "
        "}; "
        "$toolProcs = Get-CimInstance Win32_Process | Where-Object { "
        "($toolTargets -contains $_.Name) -and $_.CommandLine -and ($_.CommandLine -like ('*' + $repoHint + '*')) "
        "}; "
        "$procs = @($appProcs + $toolProcs | Sort-Object ProcessId -Unique); "
        "$stopped = 0; "
        "foreach ($proc in $procs) { "
        "try { Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop; $stopped++ } catch {} "
        "}; "
        "Write-Output $stopped"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
    )

    stopped = 0
    if result.returncode == 0:
        value = result.stdout.strip().splitlines()
        if value:
            try:
                stopped = int(value[-1].strip())
            except ValueError:
                stopped = 0

    if stopped > 0:
        print_warning(
            f"Stopped {stopped} conflicting process(es) before bundling to avoid file locks"
        )
        time.sleep(1)

    return stopped


def build_tauri_bundle() -> bool:
    """Build native Tauri desktop bundles."""
    print_header("STEP 3: TAURI BUNDLE")

    stop_conflicting_processes_for_bundle()

    ok = run_command(
        ["cargo", "tauri", "build"],
        cwd=PROJECT_ROOT,
        step_name="tauri build",
    )
    if not ok:
        print_warning("Retrying tauri build once after another process cleanup")
        stop_conflicting_processes_for_bundle()
        ok = run_command(
            ["cargo", "tauri", "build"],
            cwd=PROJECT_ROOT,
            step_name="tauri build (retry)",
        )
        if not ok:
            return False

    artifacts = _collect_bundle_artifacts()
    if not artifacts:
        print_warning("No bundle artifacts found under src-tauri/target/release/bundle")
        return True

    print_success("Bundle artifacts:")
    for artifact in artifacts[:6]:
        size_mb = artifact.stat().st_size / (1024 * 1024)
        print(f"  - {artifact} ({size_mb:.1f} MB)")
    return True


def main() -> int:
    """Run interactive build flow."""
    print_header("ZZZ Bot Build Script")

    current_version = get_current_version()
    print_info(f"Current version: {current_version}")

    increment = (
        input(f"\n{Colors.BOLD}Increment version? (y/N): {Colors.ENDC}").strip().lower()
    )
    if increment in {"y", "yes"}:
        suggested = increment_version(current_version)
        user_version = input(
            f"{Colors.BOLD}New version [{suggested}]: {Colors.ENDC}"
        ).strip()
        new_version = user_version or suggested
        update_version_files(new_version)

    print_warning("Available build steps:")
    print("  1. Frontend (React + Vite)")
    print("  2. Sidecar (PyInstaller for Tauri)")
    print("  3. Desktop Bundle (cargo tauri build)")
    print()

    mode = (
        input(
            f"{Colors.BOLD}Run all steps or choose specific ones? (All/choose): {Colors.ENDC}"
        )
        .strip()
        .lower()
    )

    run_frontend = True
    run_sidecar = True
    run_bundle = True

    if mode in {"choose", "c", "select", "s"}:
        run_frontend = input(
            f"{Colors.BOLD}  Build frontend? (Y/n): {Colors.ENDC}"
        ).strip().lower() not in {"n", "no"}
        run_sidecar = input(
            f"{Colors.BOLD}  Build sidecar? (Y/n): {Colors.ENDC}"
        ).strip().lower() not in {"n", "no"}
        run_bundle = input(
            f"{Colors.BOLD}  Build Tauri desktop bundle? (Y/n): {Colors.ENDC}"
        ).strip().lower() not in {"n", "no"}

    steps = []
    if run_frontend:
        steps.append(("Frontend", build_frontend))
    if run_sidecar:
        steps.append(("Sidecar", build_sidecar))
    if run_bundle:
        steps.append(("Desktop Bundle", build_tauri_bundle))

    if not steps:
        print_error("No steps selected")
        return 1

    proceed = (
        input(f"\n{Colors.BOLD}Start build process? (Y/n): {Colors.ENDC}")
        .strip()
        .lower()
    )
    if proceed in {"n", "no"}:
        print_info("Build cancelled")
        return 0

    failed = []
    for step_name, step_func in steps:
        if not step_func():
            failed.append(step_name)
            cont = (
                input(f"\n{Colors.WARNING}Continue to next step? (y/N): {Colors.ENDC}")
                .strip()
                .lower()
            )
            if cont not in {"y", "yes"}:
                break

    print_header("Build Summary")
    if failed:
        print_warning(f"Completed with failures: {', '.join(failed)}")
        return 1

    print_success("All selected build steps completed successfully")
    artifacts = _collect_bundle_artifacts()
    if artifacts:
        print_info("Latest installer artifacts:")
        for artifact in artifacts[:4]:
            print(f"  - {artifact}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print_warning("Build cancelled by user")
        raise SystemExit(1)
