@echo off

chcp 65001 >nul

setlocal enabledelayedexpansion

title AutoSelect-Commander - Modern ^& Interactive Dashboard



:: ============================================================================

:: AutoSelect-Commander - 1-Click Modern Dashboard Launcher

:: ============================================================================

:: Subsystem: Step 4: Modern & Interactive Dashboard

:: Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

:: Description:

::   1-Click launcher to open the Modern & Interactive Visual Dashboard.

::   - Connects to local server at http://127.0.0.1:8501/ if running.

::   - If server not running, starts it in background and opens http://127.0.0.1:8501/

::   - Falls back to local file:// URL if offline.

:: ============================================================================



set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "MODERN_FILE=%ROOT_DIR%\step_4_reporting\Modern and Interactive Dashboard\dashboard.html"
set "VBS_LAUNCHER=%LAUNCHER_DIR%start_dashboard_background.vbs"



echo ============================================================================

echo   AUTOCONNECT / GRILL-ME • MODERN ^& INTERACTIVE DASHBOARD

echo ============================================================================

echo   Mode: Modern ^& Interactive UI/UX

echo   URL : http://127.0.0.1:8501/

echo   File: %MODERN_FILE%

echo ============================================================================

echo.



:: 1. Check if server on port 8501 is already running

powershell -NoProfile -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 8501)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1

if not errorlevel 1 (

    echo [INFO] Control Server is ALREADY running on http://127.0.0.1:8501/

    echo [*] Opening Modern Dashboard in default browser...

    start http://127.0.0.1:8501/

    ping 127.0.0.1 -n 3 >nul

    exit /b 0

)



:: 2. Launch persistent background server if VBScript launcher exists

if exist "%VBS_LAUNCHER%" (

    echo [*] Starting persistent headless Control Server in background...

    wscript //nologo "%VBS_LAUNCHER%"

    ping 127.0.0.1 -n 3 >nul

    exit /b 0

)



:: 3. Fallback to direct file URL

if exist "%MODERN_FILE%" (

    echo [*] Opening Modern Dashboard static file in default browser...

    start "" "%MODERN_FILE%"

    exit /b 0

)



echo [ERROR] Modern Dashboard file not found at: "%MODERN_FILE%"

pause

exit /b 1

