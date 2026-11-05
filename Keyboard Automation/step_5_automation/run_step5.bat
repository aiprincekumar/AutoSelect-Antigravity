@echo off
setlocal enabledelayedexpansion
title Step 5: Lifecycle Sentinel Launcher - AutoSelect-Commander

:: ============================================================================
:: AutoSelect-Commander - Step 5: Antigravity Lifecycle Sentinel Standalone Runner
:: ============================================================================
:: Script: antigravity_lifecycle_sentinel.py
:: Directory: step_5_automation (Step 5 of 5)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Executes Step 5 of the AutoSelect-Commander suite:
::   Inspects Antigravity IDE process state and dashboard server port state,
::   records sentinel telemetry, and stops cleanly without cascading.
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP5_SCRIPT=%SCRIPT_DIR%antigravity_lifecycle_sentinel.py"
set "STATE_FILE=%SCRIPT_DIR%sentinel_state.json"

set "NO_PAUSE_ARG=0"
set "CMD_ARGS=%*"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--no-pause" set "NO_PAUSE_ARG=1"
    )
)

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%SCRIPT_DIR%..\setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        if "!NO_PAUSE_ARG!"=="0" pause
        exit /b 1
    )
)

set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: "%PYTHON_EXE%"
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b 1
)

:: 2. Verify Python interpreter is functional
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b 1
)

echo ============================================================================
echo   STEP 5: ANTIGRAVITY LIFECYCLE SENTINEL (STANDALONE RUNNER)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP5_SCRIPT%
echo   Target State  : %STATE_FILE%
echo ============================================================================
echo.

"%PYTHON_EXE%" "%STEP5_SCRIPT%" --check %*
set "STEP5_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================================
if "%STEP5_EXIT%"=="0" (
    echo   [STEP 5 COMPLETE] Antigravity Lifecycle Sentinel check finished cleanly.
    echo   Step 5 completed and stopped cleanly.
) else (
    echo   [STEP 5 FAILED] Sentinel check encountered exit code: %STEP5_EXIT%
)
echo ============================================================================
echo.

if "!NO_PAUSE_ARG!"=="0" (
    pause
)
exit /b %STEP5_EXIT%
