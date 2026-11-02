@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 2 Standalone Runner
:: ============================================================================
:: Script: step2_gui_chat_select.py
:: Workspace: AutoSelect-Commander \ Activating Grill Me Chat in anti-gravity
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Reads target chat state saved by Step 1, ensures window is foregrounded
::   without restoring down, locates the conversation in the Antigravity GUI
::   via Chrome DevTools Protocol / DOM glide, clicks it, and focuses the chat pane.
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP2_SCRIPT=%SCRIPT_DIR%step2_gui_chat_select.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

:: 1. Detect Python Executable (.venv prioritized)
set "PY_CMD="

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
echo   🚀 [STEP 2 / 2] CHAT SEARCH ^& GUI SELECTION (STANDALONE RUNNER)
echo   (स्टेप 2: एंटी-ग्रैविटी GUI में चैट खोजना, माउस ग्लाइड व सक्रिय करना)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %STEP2_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 2. Execute Step 2 Script
"%PY_CMD%" "%STEP2_SCRIPT%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 2 failed with exit code: %STEP2_EXIT%
    exit /b %STEP2_EXIT%
)

echo.
echo ============================================================================
echo   ✅ [STEP 2 SUCCESS] Target conversation selected and chat pane focused!
echo ============================================================================
echo.
echo %* | findstr /i "no-pause" >nul
if errorlevel 1 (
    echo Press any key to close this runner window...
    pause >nul
)
exit /b 0
