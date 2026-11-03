@echo off
setlocal enabledelayedexpansion
title Step 0: AntiGravity Detector Testing - AutoSelect-Commander

REM ============================================================================
REM Step 0: AntiGravity Detector - Testing Runner (10-Second Telemetry)
REM Script: step0_antigravity_detector_test.py
REM Directory: step_0_antigravity_detector (Step 0 of 3)
REM Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP0_SCRIPT=%SCRIPT_DIR%step0_antigravity_detector_test.py"
set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"

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

echo ============================================================================
echo   STEP 0: ANTIGRAVITY DETECTOR - TESTING RUNNER (10-SEC INTERVAL)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP0_SCRIPT%
echo   Polling Rate  : Every 10 seconds
echo   Target Step 1 : step_1_chat_identifier\step1_find_and_focus.py
echo ============================================================================
echo.

set "BATCH_PAUSE_HANDLED=1"

"%PYTHON_EXE%" "%STEP0_SCRIPT%" %*
set "STEP0_EXIT=%ERRORLEVEL%"

if not "%STEP0_EXIT%"=="0" (
    echo.
    echo ============================================================================
    echo   [ERROR] Step 0 Test Runner exited with error code: !STEP0_EXIT!
    echo   Please inspect the error messages and stack traces displayed above.
    echo   Window is kept open for diagnosis.
    echo ============================================================================
    echo.
    if "!NO_PAUSE_ARG!"=="0" (
        echo Press any key to close this window...
        pause >nul
    )
    exit /b !STEP0_EXIT!
)

echo.
echo ============================================================================
echo   [SUCCESS] Step 0 Testing Session Completed Successfully!
echo   AntiGravity detection and telemetry execution finished cleanly.
echo   This window remains open so you can inspect the full report above.
echo ============================================================================
echo.
if "!NO_PAUSE_ARG!"=="0" (
    echo Press any key to close this window...
    pause >nul
)
exit /b 0
