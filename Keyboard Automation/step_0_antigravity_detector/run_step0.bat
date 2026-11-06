@echo off
setlocal enabledelayedexpansion
title Step 0: AntiGravity Detector - AutoSelect-Commander

REM ============================================================================
REM Step 0: AntiGravity Detector - Unified Canonical Runner
REM Script: step0_antigravity_detector.py
REM Directory: step_0_antigravity_detector (Step 0 of 4)
REM Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
REM Standard: Department 06 & Department 02 Clean Architecture
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP0_SCRIPT=%SCRIPT_DIR%step0_antigravity_detector.py"
if exist "%SCRIPT_DIR%..\state\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
) else if exist "%SCRIPT_DIR%..\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"
) else (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
)

set "NO_PAUSE_ARG=0"
set "CMD_ARGS=%*"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--no-pause" set "NO_PAUSE_ARG=1"
    )
)

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

"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    if "!NO_PAUSE_ARG!"=="0" pause
    exit /b 1
)

cls

set "BATCH_PAUSE_HANDLED=1"

set "HAS_MODE=0"
if defined CMD_ARGS (
    for %%A in (%*) do (
        if "%%~A"=="--mode" set "HAS_MODE=1"
    )
)

if "!HAS_MODE!"=="1" (
    "%PYTHON_EXE%" "%STEP0_SCRIPT%" %*
) else (
    "%PYTHON_EXE%" "%STEP0_SCRIPT%" --mode production %*
)
set "STEP0_EXIT=%ERRORLEVEL%"

if not "%STEP0_EXIT%"=="0" (
    if "!NO_PAUSE_ARG!"=="0" (
        echo.
        pause >nul
    )
    exit /b !STEP0_EXIT!
)

if "!NO_PAUSE_ARG!"=="0" (
    echo.
    pause >nul
)
exit /b 0
