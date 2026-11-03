@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Step 9: Complete Automation (Production Runner) - AutoSelect-Commander

:: ============================================================================
:: Step 9: Complete Automation - Production Launcher (5-Minute Background Runner)
:: ============================================================================
:: Subsystem: Step 9: Complete Automation
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   1-Click launcher for the complete autonomous background lifecycle.
::   - Reads step_9_complete_automation\config.json
::   - Monitors Antigravity & pending Grill-Me chats (every 5 minutes / 300s)
::   - Automatically executes Step 1 -> Step 2 -> Step 3 -> Step 4 sequentially
::   - Respects configured settle delays and enabled steps
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\"
cd /d "%SCRIPT_DIR%"

set "MASTER_SCRIPT=%SCRIPT_DIR%complete_automation.py"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"

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

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: "%PYTHON_EXE%"
    pause
    exit /b 1
)

:: 2. Verify Python interpreter
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    pause
    exit /b 1
)

echo ============================================================================
echo   COMPLETE AUTOMATION - PRODUCTION RUNNER (AUTONOMOUS BACKGROUND MODE)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Master Script : %MASTER_SCRIPT%
echo   Config File   : %CONFIG_FILE%
echo   Polling Rate  : Configured in config.json (Default: 5 Minutes)
echo   Target Steps  : Step 1 -^> Step 2 -^> Step 3 -^> Step 4
echo ============================================================================
echo.
echo [*] Starting Complete Automation production runner in background...

"%PYTHON_EXE%" "%MASTER_SCRIPT%" --mode production %*
set "AUTO_EXIT=%ERRORLEVEL%"

if not "%AUTO_EXIT%"=="0" (
    echo [ERROR] Complete Automation exited with code: %AUTO_EXIT%
    exit /b %AUTO_EXIT%
)

echo.
echo [SUCCESS] Complete Automation cycle finished cleanly!
exit /b 0
