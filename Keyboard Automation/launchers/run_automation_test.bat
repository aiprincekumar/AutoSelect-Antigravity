@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Complete Automation - Testing Mode (10s Timer Dashboard)

:: ============================================================================
:: Complete Automation - Testing Mode Launcher (10-Second Timer & Clean Box)
:: Subsystem: AutoSelect Antigravity Automation Suite
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Standard: Department 06 (Backend & API) & Department 02 (Solution Architecture)
:: ============================================================================

set "LAUNCHER_DIR=%~dp0"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

set "MASTER_SCRIPT=%ROOT_DIR%\step_9_complete_automation\complete_automation.py"

set "NO_PAUSE_ARG=0"
set "CMD_ARGS=%*"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--no-pause" set "NO_PAUSE_ARG=1"
    )
)

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%LAUNCHER_DIR%setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        if "!NO_PAUSE_ARG!"=="0" pause
        exit /b 1
    )
)

set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"

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
    echo [INFO] Complete Automation test cycle finished.
    pause >nul
)
exit /b 0
