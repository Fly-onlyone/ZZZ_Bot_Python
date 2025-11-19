#!/usr/bin/env python3
"""
ZZZ Bot Build Script
====================
Automates the complete build process:
1. Build frontend (React + Vite)
2. Build executable (PyInstaller)
3. Build installer (Inno Setup)

Optional: Increment version number before building
"""

import os
import re
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(msg):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(msg):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def print_info(msg):
    """Print an info message"""
    print(f"{Colors.OKCYAN}→ {msg}{Colors.ENDC}")


def print_warning(msg):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def get_current_version():
    """Read current version from Bot version.txt"""
    version_file = Path(__file__).parent / "Bot version.txt"

    with open(version_file, "r") as f:
        content = f.read()

    # Extract version from ProductVersion
    match = re.search(r"StringStruct\('ProductVersion',\s*'([^']+)'\)", content)
    if match:
        return match.group(1)

    return "1.0"


def increment_version(version_str):
    """Increment the minor version number (e.g., 1.5 -> 1.6)"""
    parts = version_str.split(".")
    if len(parts) >= 2:
        major = int(parts[0])
        minor = int(parts[1])
        return f"{major}.{minor + 1}"
    return version_str


def update_version_files(new_version):
    """Update version in all relevant files"""
    print_info(f"Updating version to {new_version}...")

    # Convert version string to tuple (e.g., "1.5" -> (1, 5, 0, 0))
    parts = new_version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 1
    minor = int(parts[1]) if len(parts) > 1 else 0
    version_tuple = f"({major}, {minor}, 0, 0)"

    # Update Bot version.txt
    version_file = Path(__file__).parent / "Bot version.txt"
    with open(version_file, "r") as f:
        content = f.read()

    # Update filevers and prodvers tuples
    content = re.sub(r"filevers=\([^)]+\)", f"filevers={version_tuple}", content)
    content = re.sub(r"prodvers=\([^)]+\)", f"prodvers={version_tuple}", content)

    # Update ProductVersion and FileVersion strings
    content = re.sub(
        r"StringStruct\('ProductVersion',\s*'[^']+'\)",
        f"StringStruct('ProductVersion', '{new_version}')",
        content,
    )
    content = re.sub(
        r"StringStruct\('FileVersion',\s*'[^']+'\)",
        f"StringStruct('FileVersion', '{new_version}')",
        content,
    )

    with open(version_file, "w") as f:
        f.write(content)

    print_success(f"Updated {version_file.name}")

    # Update installer.iss
    installer_file = Path(__file__).parent.parent / "installer.iss"
    with open(installer_file, "r") as f:
        content = f.read()

    content = re.sub(
        r'#define MyAppVersion\s+"[^"]+"',
        f'#define MyAppVersion "{new_version}"',
        content,
    )

    with open(installer_file, "w") as f:
        f.write(content)

    print_success(f"Updated {installer_file.name}")


def build_frontend():
    """Build the React frontend with Vite"""
    print_header("STEP 1: Building Frontend")

    frontend_dir = Path(__file__).parent.parent / "frontend"

    if not frontend_dir.exists():
        print_error("Frontend directory not found!")
        return False

    print_info("Running: npm run build")

    try:
        # Use shell=True on Windows to find npm.cmd
        result = subprocess.run(
            "npm run build",
            cwd=frontend_dir,
            check=True,
            capture_output=True,
            text=True,
            shell=True,
        )

        print_success("Frontend build completed successfully!")

        # Verify dist folder exists
        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            print_success(f"Build output: {dist_dir}")
        else:
            print_warning("dist folder not found after build")

        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Frontend build failed!")
        print(e.stderr)
        return False


def build_executable():
    """Build the executable using BuildExe.py (ensures onefile mode)"""
    print_header("STEP 2: Building Executable")

    product_dir = Path(__file__).parent
    build_exe_script = product_dir / "BuildExe.py"

    if not build_exe_script.exists():
        print_error("BuildExe.py not found!")
        return False

    print_info("Running: python BuildExe.py (onefile mode)")

    try:
        # Run BuildExe.py without MODE env var to ensure onefile build
        env = os.environ.copy()
        env.pop("MODE", None)  # Remove MODE if it exists to ensure onefile

        result = subprocess.run(
            [sys.executable, "BuildExe.py"],
            cwd=product_dir,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        print_success("Executable build completed successfully!")

        # Verify exe exists
        exe_file = product_dir / "dist" / "ZZZ Bot.exe"
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print_success(f"Executable created: {exe_file.name} ({size_mb:.1f} MB)")
        else:
            print_warning("Executable not found after build")

        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Executable build failed!")
        if e.stderr:
            print(e.stderr)
        return False


def find_iscc():
    """Find iscc.exe in common Inno Setup installation locations"""
    # Common Inno Setup installation paths
    common_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"),
        Path(r"C:\Program Files\Inno Setup 6\iscc.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\iscc.exe"),
        Path(r"C:\Program Files\Inno Setup 5\iscc.exe"),
    ]

    for iscc_path in common_paths:
        if iscc_path.exists():
            return iscc_path

    return None


def build_installer():
    """Build the installer with Inno Setup"""
    print_header("STEP 3: Building Installer")

    installer_script = Path(__file__).parent.parent / "installer.iss"

    if not installer_script.exists():
        print_error("installer.iss not found!")
        return False

    # Find iscc.exe without relying on PATH
    iscc_path = find_iscc()

    if not iscc_path:
        print_error("Inno Setup Compiler (iscc.exe) not found!")
        print_warning("Searched in:")
        print_warning("  - C:\\Program Files (x86)\\Inno Setup 6\\")
        print_warning("  - C:\\Program Files\\Inno Setup 6\\")
        print_warning("Install Inno Setup from: https://jrsoftware.org/isinfo.php")
        return False

    print_info(f"Found iscc.exe at: {iscc_path}")
    print_info(f"Running: iscc installer.iss")

    try:
        result = subprocess.run(
            [str(iscc_path), str(installer_script)],
            check=True,
            capture_output=True,
            text=True,
        )

        print_success("Installer build completed successfully!")

        # Verify installer exists
        installer_file = Path(__file__).parent / "ZZZ Bot Installer.exe"
        if installer_file.exists():
            size_mb = installer_file.stat().st_size / (1024 * 1024)
            print_success(
                f"Installer created: {installer_file.name} ({size_mb:.1f} MB)"
            )
        else:
            print_warning("Installer not found after build")

        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Installer build failed!")
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Main build process"""
    print_header("ZZZ Bot Build Script v1.0")

    # Get current version
    current_version = get_current_version()
    print_info(f"Current version: {current_version}")

    # Ask about version increment
    increment = (
        input(f"\n{Colors.BOLD}Increment version? (y/N): {Colors.ENDC}").strip().lower()
    )

    if increment == "y" or increment == "yes":
        new_version = increment_version(current_version)
        print_info(f"New version will be: {new_version}")

        confirm = (
            input(
                f"{Colors.BOLD}Proceed with version {new_version}? (Y/n): {Colors.ENDC}"
            )
            .strip()
            .lower()
        )
        if confirm == "n" or confirm == "no":
            custom = input(
                f"{Colors.BOLD}Enter custom version (or press Enter to skip): {Colors.ENDC}"
            ).strip()
            if custom:
                new_version = custom
            else:
                print_info("Skipping version increment")
                new_version = None

        if new_version:
            update_version_files(new_version)
            print_success(f"Version updated to {new_version}\n")
    else:
        print_info("Skipping version increment\n")

    # Ask which steps to run
    print_warning("Available build steps:")
    print("  1. Frontend (React + Vite)")
    print("  2. Executable (BuildExe.py - onefile)")
    print("  3. Installer (Inno Setup)")
    print()

    build_choice = (
        input(
            f"{Colors.BOLD}Run all steps or choose specific ones? (All/choose): {Colors.ENDC}"
        )
        .strip()
        .lower()
    )

    # Determine which steps to run
    run_frontend = True
    run_executable = True
    run_installer = True

    if build_choice in ["choose", "c", "select", "s"]:
        print()
        print_info("Select which steps to run:")

        frontend_choice = (
            input(f"{Colors.BOLD}  Build frontend? (Y/n): {Colors.ENDC}")
            .strip()
            .lower()
        )
        run_frontend = frontend_choice not in ["n", "no"]

        executable_choice = (
            input(f"{Colors.BOLD}  Build executable? (Y/n): {Colors.ENDC}")
            .strip()
            .lower()
        )
        run_executable = executable_choice not in ["n", "no"]

        installer_choice = (
            input(f"{Colors.BOLD}  Build installer? (Y/n): {Colors.ENDC}")
            .strip()
            .lower()
        )
        run_installer = installer_choice not in ["n", "no"]

        print()

        # Show selected steps
        selected_steps = []
        if run_frontend:
            selected_steps.append("Frontend")
        if run_executable:
            selected_steps.append("Executable")
        if run_installer:
            selected_steps.append("Installer")

        if not selected_steps:
            print_error("No steps selected! Exiting...")
            return 0

        print_success(f"Selected steps: {', '.join(selected_steps)}")
        print()
    else:
        print_info("Running all steps\n")

    # Final confirmation
    proceed = (
        input(f"{Colors.BOLD}Start build process? (Y/n): {Colors.ENDC}").strip().lower()
    )
    if proceed == "n" or proceed == "no":
        print_info("Build cancelled")
        return 0

    # Build list of steps to execute
    steps = []
    if run_frontend:
        steps.append(("Frontend", build_frontend))
    if run_executable:
        steps.append(("Executable", build_executable))
    if run_installer:
        steps.append(("Installer", build_installer))

    failed_steps = []

    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)

            # Ask if we should continue after failure
            cont = (
                input(f"\n{Colors.WARNING}Continue to next step? (y/N): {Colors.ENDC}")
                .strip()
                .lower()
            )
            if cont != "y" and cont != "yes":
                print_error("Build process aborted")
                return 1

    # Final summary
    print_header("Build Summary")

    completed_steps = [name for name, _ in steps if name not in failed_steps]

    if not failed_steps:
        print_success(
            f"All {len(completed_steps)} build step(s) completed successfully!"
        )
        print()
        print_info("Completed steps:")
        for step in completed_steps:
            print(f"  ✓ {step}")
        print()
        print_info("Build artifacts:")
        if run_frontend:
            print(f"  • Frontend: frontend/dist/")
        if run_executable:
            print(f"  • Executable: product/dist/ZZZ Bot.exe")
        if run_installer:
            print(f"  • Installer: product/ZZZ Bot Installer.exe")
        return 0
    else:
        print_warning(
            f"Build completed: {len(completed_steps)} succeeded, {len(failed_steps)} failed"
        )
        print()
        if completed_steps:
            print_success("Completed steps:")
            for step in completed_steps:
                print(f"  ✓ {step}")
            print()
        print_error("Failed steps:")
        for step in failed_steps:
            print(f"  ✗ {step}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Build cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
