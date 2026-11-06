@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AutoSelect-Commander - Enable Windows Auto-Start

:: ============================================================================
:: AutoSelect-Commander - 1-Click Windows Auto-Start Installer
:: ============================================================================
:: Subsystem: Step 4: Reporting & Dashboard Local Control Server
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Registers the Dashboard Control Server into Windows Startup folder.
::   On user login, server starts 100% silently in background (headless daemon).
:: ============================================================================

set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Keyboard_Automation_Dashboard.lnk"
set "VBS_LAUNCHER=%LAUNCHER_DIR%autostart_dashboard_silent.vbs"
if not exist "%VBS_LAUNCHER%" (
    set "VBS_LAUNCHER=%LAUNCHER_DIR%start_dashboard_background.vbs"
)

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME - ENABLE WINDOWS AUTO-START
echo ============================================================================
echo   Subsystem: Step 4 Visual Telemetry ^& Automation Control Server
echo   Target   : %SHORTCUT_PATH%
echo ============================================================================
echo.

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    echo [1/2] Invoking Auto-Start manager via Python engine...
    "%PYTHON_EXE%" "%ROOT_DIR%\step_4_reporting\dashboard_server.py" --enable-autostart
) else (
    echo [1/2] Registering background shortcut into Windows Startup via PowerShell...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%SHORTCUT_PATH%'); $sc.TargetPath = 'wscript.exe'; $sc.Arguments = [char]34 + '%VBS_LAUNCHER%' + [char]34 + ' --no-browser'; $sc.WorkingDirectory = '%ROOT_DIR%'; $sc.Description = 'Keyboard Automation Dashboard Server - Background Auto-Start'; $sc.WindowStyle = 7; $sc.Save();"
)

echo.
if not exist "%SHORTCUT_PATH%" goto FAILED

echo [2/2] [VERIFIED] Auto-Start shortcut is ACTIVE in Windows Startup:
echo       "%SHORTCUT_PATH%"
echo.
echo ============================================================================
echo [SUCCESS] Dashboard Server will now launch automatically on Windows login!
echo   - Runs silently in background: windowless daemon on port 8501.
echo   - No flashing console windows, no browser popups on login.
echo   - To disable anytime, run: launchers\disable_autostart.bat
echo ============================================================================
echo.
exit /b 0

:FAILED
echo [ERROR] Failed to verify shortcut creation in:
echo         "%SHORTCUT_PATH%"
echo.
exit /b 1
