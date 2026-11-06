@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AutoSelect-Commander - Check Windows Auto-Start Status

:: ============================================================================
:: AutoSelect-Commander - Check Windows Auto-Start Status
:: ============================================================================
:: Subsystem: Step 4: Reporting & Dashboard Local Control Server
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Checks and displays whether Windows Auto-Start is currently enabled or disabled.
:: ============================================================================

set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Keyboard_Automation_Dashboard.lnk"

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME - WINDOWS AUTO-START STATUS CHECK
echo ============================================================================

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%ROOT_DIR%\step_4_reporting\dashboard_server.py" --status-autostart
    goto FINISH
)

if exist "%SHORTCUT_PATH%" (
    echo [STATUS] Windows Auto-Start: [ENABLED]
    echo   Shortcut : "%SHORTCUT_PATH%"
    echo   Target   : wscript.exe
) else (
    echo [STATUS] Windows Auto-Start: [DISABLED]
    echo   Shortcut : Not present in Startup folder.
)

:FINISH
echo ============================================================================
echo.
exit /b 0
