@echo off
setlocal enabledelayedexpansion
title Complete Automation (Testing Mode - 10s Timer Dashboard)

:: ============================================================================
:: Complete Automation - Testing Mode Launcher (10-Second Timer & Clean Box)
:: ============================================================================
:: Subsystem: Complete Automation
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   1-Click testing launcher featuring 100% Screen Purity live dashboard.
::   - Checks Antigravity & Grill-Me status every 10 seconds
::   - On condition match, triggers enabled steps (1 -> 2 -> 3 -> 4)
::   - Shows execution results with zero technical clutter
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\"
cd /d "%SCRIPT_DIR%"

set "MASTER_SCRIPT=%SCRIPT_DIR%complete_automation.py"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"

set "NO_PAUSE_ARG=0"
set "CMD_ARGS=%*"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--no-pause" set "NO_PAUSE_ARG=1"
    )
)

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%ROOT_DIR%.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%ROOT_DIR%setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        if "!NO_PAUSE_ARG!"=="0" pause
        exit /b 1
    )
)

set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: "%PYTHON_EXE%"
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b 1
)

:: 2. Verify Python interpreter
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b 1
)

cls

"%PYTHON_EXE%" "%MASTER_SCRIPT%" --mode test --interactive %*
set "AUTO_EXIT=%ERRORLEVEL%"

if not "%AUTO_EXIT%"=="0" (
    echo.
    echo [ERROR] Complete Automation test finished with exit code: %AUTO_EXIT%
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b !AUTO_EXIT!
)

if "!NO_PAUSE_ARG!"=="0" (
    echo.
    echo [INFO] Complete Automation test cycle finished. Press any key to exit.
    pause >nul
)
exit /b 0
