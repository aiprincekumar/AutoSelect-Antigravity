@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 1 Standalone Runner
:: ============================================================================
:: Script: step1_find_and_focus.py
:: Workspace: AutoSelect-Commander \ Activating Grill Me Chat in anti-gravity
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

if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
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
echo   🚀 [STEP 1 / 2] SCAN, STATE STORE & WINDOW FOCUS (STANDALONE RUNNER)
echo   (स्टेप 1: ट्रांसक्रिप्ट स्कैनिंग, स्टेट सेविंग और विंडो मैक्सिमाइज़/फोकस)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %STEP1_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 2. Execute Step 1 Script
"%PY_CMD%" "%STEP1_SCRIPT%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if not "%STEP1_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 1 failed with exit code: %STEP1_EXIT%
    exit /b %STEP1_EXIT%
)

echo.
echo ============================================================================
echo   ✅ [STEP 1 SUCCESS] Transcripts scanned & Antigravity window focused!
echo      State saved to: %STATE_FILE%
echo ============================================================================
echo.
if not "%1"=="--no-pause" (
    echo Press any key to close this runner window...
    pause >nul
)
exit /b 0
