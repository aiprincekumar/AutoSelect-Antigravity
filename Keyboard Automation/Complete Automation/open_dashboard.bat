@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Visual Reporting Dashboard - AutoSelect-Commander

:: ============================================================================
:: Complete Automation - Visual Reporting Dashboard 1-Click Launcher
:: ============================================================================
:: Subsystem: Complete Automation
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   1-Click launcher to view the execution history and visual HTML dashboard.
::   Opens the interactive dashboard immediately in the default browser.
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\"
cd /d "%SCRIPT_DIR%"

set "DASHBOARD_FILE=%ROOT_DIR%step_4_reporting\reports\dashboard.html"
set "STEP4_SCRIPT=%ROOT_DIR%step_4_reporting\step4_reporting.py"

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
echo   VISUAL REPORTING DASHBOARD - 1-CLICK LAUNCHER
echo ============================================================================
echo   Dashboard Path : %DASHBOARD_FILE%
echo ============================================================================
echo.

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
