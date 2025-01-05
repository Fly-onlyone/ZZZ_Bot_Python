import PyInstaller.__main__
import shutil
import os
import glob
import stat


def get_environment():
    env = os.getenv("MODE")
    print(f"MODE: {env}")
    return env


def grant_permissions(directory_path):
    """
    Grant full permissions (read, write, execute) to a directory and its contents.
    """
    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
        return

    for root, dirs, files in os.walk(directory_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Full permissions
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Full permissions

    os.chmod(directory_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Root directory
    print(f"Full permissions granted to {directory_path}")


def process_directory(base_dir, directories_to_copy):
    """
    Process the base directory (`dist` or `build`), find `.exe` files, and copy required directories.
    """
    exe_files = glob.glob(os.path.join(base_dir, "**", "*.exe"), recursive=True)
    if exe_files:
        # Assuming the first `.exe` file found is the main one
        exe_path = exe_files[0]
        exe_dir = os.path.dirname(exe_path)
        print(f"Detected exe path: {exe_path}")

        # Copy the specified directories to the same relative path as the exe
        for directory in directories_to_copy:
            src = os.path.abspath(directory)
            dst = os.path.join(exe_dir, os.path.basename(directory))  # Match relative path to exe
            if os.path.exists(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print(f"Copied {src} to {dst}")
            else:
                print(f"Source directory does not exist: {src}")
    else:
        print(f"No .exe file was found in the directory: {base_dir}")


mode = get_environment()

# Paths to the directories you want to copy
directories_to_copy = ["./../authentication data", "./../screenshot", "./../output"]
spec_file_path="SpecStandalone.py" if mode =="MAKE_EXE_STANDALONE" else "SpecOnefile.py"
# Read Spec.py and write its content to Bot.spec
with open(spec_file_path, "r") as spec_file:
    spec_content = spec_file.read()

with open("Bot.spec", "w") as bot_spec_file:
    bot_spec_file.write(spec_content)

# Paths to `dist` and `build` directories
dist_dir = os.path.abspath("./dist")

# Grant permissions to both directories
grant_permissions(dist_dir)

# Run PyInstaller to build the exe
PyInstaller.__main__.run(["Bot.spec", "--noconfirm"])

# Process both `dist` and `build` directories
for base_dir in [dist_dir]:
    process_directory(base_dir, directories_to_copy)
