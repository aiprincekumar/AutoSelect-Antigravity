@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AutoSelect-Commander - Live Telemetry & Control Dashboard

:: ============================================================================
:: AutoSelect-Commander - Step 4: Dashboard & Local Control Server Launcher
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: Keyboard Automation \ step_4_reporting \ run_dashboard.bat
:: Mission: Launches the local Python control daemon and opens visual dashboard.
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "ROOT_DIR=%SCRIPT_DIR%..\"

set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

set "SERVER_SCRIPT=%SCRIPT_DIR%dashboard_server.py"

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME • LIVE TELEMETRY DASHBOARD & CONTROL SERVER
echo ============================================================================
echo   Script       : %SERVER_SCRIPT%
echo   Python Engine: %PYTHON_EXE%
echo   Local URL    : http://127.0.0.1:8501/
echo ============================================================================
echo.
echo [*] Initializing control server and opening browser...
echo [*] Press Ctrl+C in this console window to gracefully stop the server.
echo.

"%PYTHON_EXE%" "%SERVER_SCRIPT%" %*

if errorlevel 1 (
    echo [ERROR] Dashboard server exited with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
