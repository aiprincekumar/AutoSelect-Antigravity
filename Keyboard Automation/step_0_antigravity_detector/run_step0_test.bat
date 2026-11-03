@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Step 0: AntiGravity Detector Testing - AutoSelect-Commander

:: ============================================================================
:: Step 0: AntiGravity Detector - Testing Runner (10-Second Telemetry)
:: ============================================================================
:: Script: step0_antigravity_detector_test.py
:: Directory: step_0_antigravity_detector (Step 0 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Manual inspection testing runner checking every 10 seconds if Google
::   Antigravity is running/open with clean console telemetry. When detected,
::   automatically triggers Step 1 (step_1_chat_identifier/step1_find_and_focus.py).
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP0_SCRIPT=%SCRIPT_DIR%step0_antigravity_detector_test.py"
set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%SCRIPT_DIR%..\setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: "%PYTHON_EXE%"
    pause
    exit /b 1
)

:: 2. Verify Python interpreter is functional
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    pause
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

"%PYTHON_EXE%" "%STEP0_SCRIPT%" %*
set "STEP0_EXIT=%ERRORLEVEL%"

if not "%STEP0_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 0 Test Runner exited with error code: %STEP0_EXIT%
    exit /b %STEP0_EXIT%
)

echo.
echo [SUCCESS] Step 0 testing session completed successfully!
exit /b 0
