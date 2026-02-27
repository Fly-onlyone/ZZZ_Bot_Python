@echo off
REM ZZZ Bot Build GUI Launcher
REM Opens the Tkinter build GUI (build_gui.py)

echo Starting ZZZ Bot Build GUI...
echo.

python build_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build GUI exited with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

