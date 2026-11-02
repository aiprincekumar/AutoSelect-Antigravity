@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 1 Standalone Runner
:: ============================================================================
:: Script: step1_find_and_focus.py
:: Workspace: AutoSelect-Commander \ Keyboard Automation (Step 1 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Scans Antigravity brain transcripts for pending Grill-Me (ask_question) chats,
::   extracts questions & choices, persists state to target_chat.json, and
::   safely focuses/maximizes the Antigravity IDE window without restoring down.
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

:: 1. Detect Python Executable (.venv prioritized)
set "PY_CMD="

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :PYTHON_FOUND
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :PYTHON_FOUND
)

where uv >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=uv run python"
    goto :PYTHON_FOUND
)

echo [ERROR] Python environment not found! Please install Python 3.10+ or configure a virtualenv.
pause
exit /b 1

:PYTHON_FOUND
echo ============================================================================
echo   STEP 1: SCAN TRANSCRIPTS, PERSIST STATE ^& FOCUS WINDOW
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %STEP1_SCRIPT%
echo   Target State  : %STATE_FILE%
echo ============================================================================
echo.

"%PY_CMD%" "%STEP1_SCRIPT%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if not "%STEP1_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 1 failed with exit code: %STEP1_EXIT%
    exit /b %STEP1_EXIT%
)

echo.
echo [SUCCESS] Step 1 finished successfully!
exit /b 0
