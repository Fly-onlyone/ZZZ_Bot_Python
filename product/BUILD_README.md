# ZZZ Bot Build Script

Automated build script that handles the complete build process for ZZZ Bot.

## Features

✅ **Automated Build Pipeline**

- Builds React frontend (Vite)
- Creates executable (PyInstaller onefile)
- Generates installer (Inno Setup)

✅ **Version Management**

- Optional version increment (default: no)
- Auto-updates both exe and installer versions
- Supports custom version numbers

✅ **User-Friendly**

- Interactive prompts
- Colored output
- Progress tracking
- Error handling with option to continue

## Requirements

- Python 3.7+
- Node.js & npm (for frontend)
- PyInstaller (`pip install pyinstaller`)
- Inno Setup (for installer creation)
    - Download: https://jrsoftware.org/isinfo.php
    - Make sure `iscc.exe` is in your PATH

## Usage

### Option 1: Run with Python

```bash
cd product
python build.py
```

### Option 2: Run with Batch File (Windows)

```bash
cd product
build.bat
```

## Interactive Prompts

The script will ask you:

1. **Increment version?** (y/N)
    - Default: No
    - If yes: auto-increments minor version (1.5 → 1.6)
    - Option to enter custom version

2. **Run all steps or choose specific ones?** (All/choose)
    - Default: All (runs all 3 steps)
    - If "choose": asks which steps to run individually
        - Build frontend? (Y/n)
        - Build executable? (Y/n)
        - Build installer? (Y/n)

3. **Start build process?** (Y/n)
    - Default: Yes
    - Final confirmation before building

4. **Continue after failure?** (y/N)
    - Only shown if a build step fails
    - Allows you to continue to next step

## Build Steps

### 1. Frontend Build

- Runs: `npm run build` in `frontend/` directory
- Output: `frontend/dist/`
- Bundled into the executable by PyInstaller

### 2. Executable Build

- Runs: `python BuildExe.py` in `product/` directory
- Uses BuildExe.py to ensure onefile mode (not standalone)
- MODE environment variable is explicitly removed to force onefile
- Output: `product/dist/ZZZ Bot.exe`
- Creates single-file executable (onefile mode)
- Includes all dependencies and resources

### 3. Installer Build

- Finds: `iscc.exe` in common Inno Setup installation locations
- Does NOT rely on PATH environment variable
- Searches in:
    - C:\Program Files (x86)\Inno Setup 6\
    - C:\Program Files\Inno Setup 6\
    - C:\Program Files (x86)\Inno Setup 5\
    - C:\Program Files\Inno Setup 5\
- Runs: `iscc installer.iss`
- Output: `product/ZZZ Bot Installer.exe`
- Creates Windows installer with auto-start option

## Output Files

After successful build:

```
product/
├── dist/
│   └── ZZZ Bot.exe          # Single executable file
└── ZZZ Bot Installer.exe    # Windows installer
```

## Version Files Updated

When incrementing version, these files are automatically updated:

1. **product/Bot version.txt**
    - `filevers` tuple
    - `prodvers` tuple
    - `ProductVersion` string
    - `FileVersion` string

2. **installer.iss**
    - `MyAppVersion` define

## Examples

### Build without version increment

```bash
python build.py
# Answer 'N' to version increment
# Answer 'Y' to start build
```

### Build with version increment

```bash
python build.py
# Answer 'y' to version increment
# Confirm auto version or enter custom
# Answer 'Y' to start build
```

### Build with custom version

```bash
python build.py
# Answer 'y' to version increment
# Answer 'n' to auto version
# Enter custom version (e.g., "2.0")
# Answer 'all' to run all steps
# Answer 'Y' to start build
```

### Build only frontend

```bash
python build.py
# Answer 'N' to version increment
# Answer 'choose' to select steps
# Answer 'Y' to build frontend
# Answer 'N' to build executable
# Answer 'N' to build installer
# Answer 'Y' to start build
```

### Build only executable

```bash
python build.py
# Answer 'N' to version increment
# Answer 'choose' to select steps
# Answer 'N' to build frontend
# Answer 'Y' to build executable
# Answer 'N' to build installer
# Answer 'Y' to start build
```

### Build executable and installer (skip frontend)

```bash
python build.py
# Answer 'N' to version increment
# Answer 'choose' to select steps
# Answer 'N' to build frontend
# Answer 'Y' to build executable
# Answer 'Y' to build installer
# Answer 'Y' to start build
```

## Troubleshooting

### Frontend build fails

- Check if `npm` is installed: `npm --version`
- Try manual build: `cd frontend && npm run build`
- Check for errors in frontend code

### Executable build fails

- Check if BuildExe.py exists in product/ directory
- Check if PyInstaller is installed: `pip install pyinstaller`
- Try manual build: `cd product && python BuildExe.py`
- Check Python dependencies are installed
- Ensure MODE environment variable is not set to "MAKE_EXE_STANDALONE"

### Installer build fails

- Check if Inno Setup is installed in one of these locations:
    - C:\Program Files (x86)\Inno Setup 6\
    - C:\Program Files\Inno Setup 6\
- Script does NOT use PATH, it searches directly
- Install from: https://jrsoftware.org/isinfo.php
- Try manual build: `"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer.iss`

### Version update doesn't work

- Check if version files exist:
    - `product/Bot version.txt`
    - `installer.iss`
- Ensure files are not read-only

## Exit Codes

- `0` - Success
- `1` - Build failed or user cancelled

## Notes

- The script uses colored terminal output for better readability
- Each build step can be retried individually if it fails
- Version files are updated before the build starts
- All builds use optimized settings (bytecode optimization, onefile, etc.)

## Support

For issues or questions, check the main project documentation or log files in `src/logs/`.
