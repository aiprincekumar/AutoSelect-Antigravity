@echo off
setlocal enabledelayedexpansion
title Step 2: GUI Chat Select Launcher - AutoSelect-Commander

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 2 Standalone Runner
:: ============================================================================
:: Script: step2_gui_chat_select.py
:: Directory: step_2_chat_and_focus (Step 2 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Reads target chat state saved by Step 1 from root target_chat.json,
::   ensures window is foregrounded without restoring down, locates the conversation
::   in the Antigravity GUI via Chrome DevTools Protocol / DOM glide, clicks it,
::   and focuses the chat pane.
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP2_SCRIPT=%SCRIPT_DIR%step2_gui_chat_select.py"
if exist "%SCRIPT_DIR%..\state\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
) else if exist "%SCRIPT_DIR%..\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"
) else (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
)

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
echo   STEP 2: GUI CHAT SELECTION ^& CHAT PANE ACTIVATION
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP2_SCRIPT%
echo   Target State  : %STATE_FILE%
echo ============================================================================
echo.

"%PYTHON_EXE%" "%STEP2_SCRIPT%" --state-file "%STATE_FILE%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 2 failed with exit code: %STEP2_EXIT%
    exit /b %STEP2_EXIT%
)

echo.
echo [SUCCESS] Step 2 finished successfully!
exit /b 0
