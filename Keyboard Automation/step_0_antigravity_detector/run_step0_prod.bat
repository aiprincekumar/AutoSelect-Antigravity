@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Step 0: AntiGravity Detector Production - AutoSelect-Commander

:: ============================================================================
:: Step 0: AntiGravity Detector - Production Runner (5-Minute Polling)
:: ============================================================================
:: Script: step0_antigravity_detector_prod.py
:: Directory: step_0_antigravity_detector (Step 0 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Headless background daemon checking every 5 minutes (300 seconds) if Google
::   Antigravity is running/open. When detected, automatically triggers Step 1
::   (step_1_chat_identifier/step1_find_and_focus.py) and exits cleanly.
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP0_SCRIPT=%SCRIPT_DIR%step0_antigravity_detector_prod.py"
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
echo   STEP 0: ANTIGRAVITY DETECTOR - PRODUCTION RUNNER (5-MIN INTERVAL)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP0_SCRIPT%
echo   Polling Rate  : Every 5 minutes (300 seconds)
echo   Target Pipeline : Steps 1 -^> 2 -^> 3 (and future Step 4)
echo ============================================================================
echo.
echo [*] Starting silent background detection loop...

"%PYTHON_EXE%" "%STEP0_SCRIPT%" %*
set "STEP0_EXIT=%ERRORLEVEL%"

if not "%STEP0_EXIT%"=="0" (
    echo [ERROR] Step 0 Detector exited with error code: %STEP0_EXIT%
    exit /b %STEP0_EXIT%
)

echo.
echo [SUCCESS] Step 0 finished and automation pipeline triggered successfully!
exit /b 0
