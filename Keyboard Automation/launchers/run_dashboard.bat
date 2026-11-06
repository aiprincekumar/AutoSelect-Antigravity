@echo off

chcp 65001 >nul

setlocal enabledelayedexpansion

title AutoSelect-Commander - Live Telemetry ^& Control Dashboard



:: ============================================================================

:: AutoSelect-Commander - 1-Click Dashboard & Local Control Server Launcher

:: ============================================================================

:: Subsystem: Step 4: Reporting & Dashboard Local Control Server

:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

:: Description:

::   1-Click launcher to host the visual dashboard and OS automation control daemon.

::   - Pre-check: If server is already running on http://127.0.0.1:8501, reuses it immediately.

::   - If not running, launches persistent background server via start_dashboard_background.vbs.

::   - Pass --fg or --foreground to run server attached to this console window.

:: ============================================================================



set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

set "SERVER_SCRIPT=%ROOT_DIR%\step_4_reporting\dashboard_server.py"
set "VBS_LAUNCHER=%LAUNCHER_DIR%start_dashboard_background.vbs"



echo ============================================================================

echo   AUTOCONNECT / GRILL-ME • LIVE TELEMETRY DASHBOARD ^& CONTROL SERVER

echo ============================================================================

echo   Server Port  : http://127.0.0.1:8501/

echo   Server Script: %SERVER_SCRIPT%

echo ============================================================================

echo.



:: 1. Check if server on port 8501 is already running

powershell -NoProfile -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 8501)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1

if not errorlevel 1 (

    echo [INFO] Control Server is ALREADY running on http://127.0.0.1:8501/

    echo [INFO] Opening visual dashboard in default browser...

    start http://127.0.0.1:8501/

    ping 127.0.0.1 -n 3 >nul

    exit /b 0

)



:: 2. If user requested foreground console execution

if /i "%~1"=="--fg" goto RUN_FOREGROUND

if /i "%~1"=="--foreground" goto RUN_FOREGROUND



:: 3. Launch persistent background server via VBScript

if exist "%VBS_LAUNCHER%" (

    echo [*] Starting persistent headless Control Server in background...

    wscript //nologo "%VBS_LAUNCHER%"

    echo [SUCCESS] Control Server started on http://127.0.0.1:8501/ (Persistent Background).

    echo [*] Opening visual dashboard in default browser...

    ping 127.0.0.1 -n 3 >nul

    exit /b 0

)



:RUN_FOREGROUND

echo [*] Initializing control server in foreground mode...

echo [*] Press Ctrl+C in this console window to gracefully stop the server.

echo.



"%PYTHON_EXE%" "%SERVER_SCRIPT%" %*



if errorlevel 1 (

    echo [ERROR] Dashboard server exited with error code %ERRORLEVEL%.

    pause

    exit /b %ERRORLEVEL%

)



exit /b 0

