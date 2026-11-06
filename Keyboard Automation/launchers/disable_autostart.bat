@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AutoSelect-Commander - Disable Windows Auto-Start

:: ============================================================================
:: AutoSelect-Commander - 1-Click Windows Auto-Start Uninstaller
:: ============================================================================
:: Subsystem: Step 4: Reporting & Dashboard Local Control Server
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Removes the Dashboard Server shortcut from Windows Startup folder.
:: ============================================================================

set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Keyboard_Automation_Dashboard.lnk"

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME - DISABLE WINDOWS AUTO-START
echo ============================================================================
echo   Removing: %SHORTCUT_PATH%
echo ============================================================================
echo.

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%ROOT_DIR%\step_4_reporting\dashboard_server.py" --disable-autostart
    goto DONE
)

if exist "%SHORTCUT_PATH%" (
    del /f /q "%SHORTCUT_PATH%"
    echo [SUCCESS] Removed Windows Auto-Start shortcut successfully.
) else (
    echo [INFO] Auto-Start shortcut was not present.
)

:DONE
echo.
echo ============================================================================
echo [DONE] Dashboard Server Auto-Start has been disabled cleanly.
echo ============================================================================
echo.
exit /b 0
