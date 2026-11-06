@echo off
setlocal enabledelayedexpansion
title Step 1: Chat Identifier Launcher - AutoSelect-Commander

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 1 Standalone Runner
:: ============================================================================
:: Script: step1_find_and_focus.py
:: Directory: step_1_chat_identifier (Step 1 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Scans Antigravity brain transcripts for pending Grill-Me (ask_question) chats,
::   extracts questions & choices, persists state to target_chat.json in root, and
::   safely focuses/maximizes the Antigravity IDE window without restoring down.
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"

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
echo   STEP 1: SCAN TRANSCRIPTS, PERSIST STATE ^& FOCUS WINDOW
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP1_SCRIPT%
echo   Target State  : %STATE_FILE%
echo ============================================================================
echo.

"%PYTHON_EXE%" "%STEP1_SCRIPT%" --state-file "%STATE_FILE%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if "%STEP1_EXIT%"=="10" (
    echo.
    echo ============================================================================
    echo   [INFO] NO PENDING GRILL ME / ASK_QUESTION CHATS FOUND
    echo   [*] Step 1 finished and closed cleanly.
    echo ============================================================================
    exit /b 0
)

if not "%STEP1_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 1 failed with exit code: %STEP1_EXIT%
    exit /b %STEP1_EXIT%
)

echo.
echo [SUCCESS] Step 1 finished successfully!
exit /b 0
