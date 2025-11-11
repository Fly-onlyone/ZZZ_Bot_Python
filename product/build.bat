@echo off
REM ZZZ Bot Build Script Launcher
REM Runs the Python build script

echo Starting ZZZ Bot Build Script...
echo.

python build.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Build completed!
pause
