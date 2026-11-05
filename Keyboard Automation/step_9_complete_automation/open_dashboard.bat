@echo off

chcp 65001 >nul

setlocal enabledelayedexpansion

title Visual Reporting Dashboard - AutoSelect-Commander



:: ============================================================================

:: Step 9: Complete Automation - Visual Reporting Dashboard 1-Click Launcher

:: ============================================================================

:: Subsystem: Step 9: Complete Automation

:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

:: Description:

::   1-Click launcher to view the execution history and visual HTML dashboard.

::   - Checks if control daemon is already active on port 8501 and reuses it.

::   - Starts headless persistent server in background if not already active.

::   - Opens interactive dashboard immediately in default browser.

:: ============================================================================



set "SCRIPT_DIR=%~dp0"

set "ROOT_DIR=%SCRIPT_DIR%..\"

cd /d "%SCRIPT_DIR%"



set "DASHBOARD_FILE=%ROOT_DIR%step_4_reporting\Modern and Interactive Dashboard\dashboard.html"

if not exist "%DASHBOARD_FILE%" (

    set "DASHBOARD_FILE=%ROOT_DIR%step_4_reporting\reports\modern_dashboard.html"

)

if not exist "%DASHBOARD_FILE%" (

    set "DASHBOARD_FILE=%ROOT_DIR%step_4_reporting\reports\dashboard.html"

)

set "STEP4_SCRIPT=%ROOT_DIR%step_4_reporting\step4_reporting.py"

set "SERVER_SCRIPT=%ROOT_DIR%step_4_reporting\dashboard_server.py"

set "VBS_LAUNCHER=%ROOT_DIR%start_dashboard_background.vbs"



:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution

if not exist "%ROOT_DIR%.venv\Scripts\python.exe" (

    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.

    echo [SETUP] Initializing self-healing .venv environment now...

    call "%ROOT_DIR%setup_env.bat"

    if errorlevel 1 (

        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.

        pause

        exit /b 1

    )

)



set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"



echo ============================================================================

echo   VISUAL REPORTING DASHBOARD ^& CONTROL SERVER - 1-CLICK LAUNCHER

echo ============================================================================

echo   Server Port    : http://127.0.0.1:8501/

echo   Dashboard File : %DASHBOARD_FILE%

echo ============================================================================

echo.



:: 2. Pre-Check: Is Control Server Already Running on Port 8501?

powershell -NoProfile -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 8501)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1

if not errorlevel 1 (

    echo [INFO] Control Server is ALREADY running on http://127.0.0.1:8501/

    echo [*] Opening visual dashboard in default browser...

    start http://127.0.0.1:8501/

    exit /b 0

)



:: 3. Launch Persistent Background Control Server via VBScript

if exist "%VBS_LAUNCHER%" (

    echo [*] Starting persistent headless Control Server in background...

    wscript //nologo "%VBS_LAUNCHER%"

    echo [SUCCESS] Control Server started on http://127.0.0.1:8501/ (Persistent Background).

    exit /b 0

)



:: 4. Fallback to direct Python server or static file

if exist "%SERVER_SCRIPT%" (

    echo [*] Starting local control server in background and opening dashboard...

    start "" /b "%PYTHON_EXE%" "%SERVER_SCRIPT%" %*

    ping 127.0.0.1 -n 3 >nul

    start http://127.0.0.1:8501/

    exit /b 0

)



if exist "%DASHBOARD_FILE%" (

    echo [*] Opening existing visual dashboard in default browser...

    start "" "%DASHBOARD_FILE%"

    echo [SUCCESS] Dashboard opened successfully!

    exit /b 0

)



echo [*] Dashboard file not yet generated. Building from history now...

if exist "%STEP4_SCRIPT%" (

    "%PYTHON_EXE%" "%STEP4_SCRIPT%" --open %*

    if errorlevel 1 (

        echo [ERROR] Failed to generate dashboard from Step 4.

        pause

        exit /b 1

    )

    echo [SUCCESS] Dashboard generated and opened!

    exit /b 0

) else (

    echo [ERROR] Step 4 reporting script not found at: "%STEP4_SCRIPT%"

    pause

    exit /b 1

)

