import glob
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


PRODUCT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PRODUCT_DIR.parent


def get_environment():
    env = os.getenv("MODE")
    print(f"MODE: {env}")
    return env


def _set_full_permissions(path):
    try:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not set permissions on {path}: {e}")


def grant_permissions(directory_path):
    """
    Grant full permissions (read, write, execute) to a directory and its contents.
    """
    directory_path = Path(directory_path)

    if not directory_path.exists():
        print(f"Directory does not exist: {directory_path}")
        return

    # Windows reserved device names that should be skipped
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }

    for root, dirs, files in os.walk(directory_path):
        for dir_name in dirs:
            if dir_name.lower() not in reserved_names:
                _set_full_permissions(Path(root) / dir_name)

        for file_name in files:
            if file_name.lower() not in reserved_names:
                _set_full_permissions(Path(root) / file_name)

    _set_full_permissions(directory_path)
    print(f"Permissions granted to {directory_path}")


def process_directory(base_dir, copy_sources):
    """
    Process the base directory (`dist` or `build`), find `.exe` files, and copy required directories.
    """
    base_dir = Path(base_dir)
    exe_files = glob.glob(str(base_dir / "**" / "*.exe"), recursive=True)
    if exe_files:
        # Assuming the first `.exe` file found is the main one
        exe_path = Path(exe_files[0])
        exe_dir = exe_path.parent
        print(f"Detected exe path: {exe_path}")

        # Copy the specified directories to the same relative path as the exe
        for directory in copy_sources:
            src = Path(directory).resolve()
            dst = exe_dir / src.name
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print(f"Copied {src} to {dst}")
            else:
                print(f"Source directory does not exist: {src}")
    else:
        print(f"No .exe file was found in the directory: {base_dir}")


mode = get_environment()

# Paths to the directories you want to copy
COPY_SOURCE_DIRS = [
    PROJECT_ROOT / "authentication data",
    PROJECT_ROOT / "screenshot",
    PROJECT_ROOT / "output",
]
spec_file_path = (
    PRODUCT_DIR / "SpecStandalone.py"
    if mode == "MAKE_EXE_STANDALONE"
    else PRODUCT_DIR / "SpecOnefile.py"
)
bot_spec_path = PRODUCT_DIR / "Bot.spec"
dist_dir = PRODUCT_DIR / "dist"

previous_cwd = Path.cwd()
os.chdir(PRODUCT_DIR)
try:
    # Read Spec.py and write its content to Bot.spec
    with open(spec_file_path, "r", encoding="utf-8") as spec_file:
        spec_content = spec_file.read()

    with open(bot_spec_path, "w", encoding="utf-8") as bot_spec_file:
        bot_spec_file.write(spec_content)

    # Grant permissions to dist directory
    grant_permissions(dist_dir)

    # Run PyInstaller to build the exe
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(bot_spec_path),
            "--noconfirm",
            "--clean",
        ],
        check=True,
    )
finally:
    os.chdir(previous_cwd)

# Process dist directory
process_directory(dist_dir, COPY_SOURCE_DIRS)
