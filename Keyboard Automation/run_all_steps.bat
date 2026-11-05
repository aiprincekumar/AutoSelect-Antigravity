@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Complete Automation - Run All Steps (1 -> 2 -> 3 -> 4)

:: ============================================================================
:: Complete Automation - Direct Pipeline Runner (Run All Steps)
:: Subsystem: AutoSelect Antigravity Automation Suite
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Standard: Department 06 (Backend & API) & Department 02 (Solution Architecture)
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "MASTER_SCRIPT=%SCRIPT_DIR%step_9_complete_automation\complete_automation.py"

set "NO_PAUSE_ARG=0"
set "CMD_ARGS=%*"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--no-pause" set "NO_PAUSE_ARG=1"
    )
)

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%SCRIPT_DIR%setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        if "!NO_PAUSE_ARG!"=="0" pause
        exit /b 1
    )
)

set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

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

echo ============================================================================
echo   AUTORUN: COMPLETE PIPELINE (STEP 1 -^> STEP 2 -^> STEP 3 -^> STEP 4)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Master Script : %MASTER_SCRIPT%
echo ============================================================================
echo.

"%PYTHON_EXE%" "%MASTER_SCRIPT%" --run-pipeline --interactive %*
set "PIPELINE_EXIT=%ERRORLEVEL%"

if not "%PIPELINE_EXIT%"=="0" (
    echo.
    echo [ERROR] Pipeline execution finished with exit code: %PIPELINE_EXIT%
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b !PIPELINE_EXIT!
)

echo.
echo [SUCCESS] Complete Automation pipeline completed successfully!
if "!NO_PAUSE_ARG!"=="0" pause
exit /b 0
