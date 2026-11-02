@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Step 2 Standalone Runner
:: ============================================================================
:: Script: step2_gui_chat_select.py
:: Workspace: AutoSelect-Commander \ Keyboard Automation (Step 2 of 3)
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

:: 1. Bulletproof Python Executable Resolution
set "PYTHON_EXE="

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe"
) else if exist "%USERPROFILE%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.venv\Scripts\python.exe"
) else if exist "%USERPROFILE%\.local\bin\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.local\bin\python.exe"
) else (
    for /f "delims=" %%I in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
    )
    if not defined PYTHON_EXE (
        for /f "delims=" %%I in ('where py.exe 2^>nul') do (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
        )
    )
)

if not defined PYTHON_EXE set "PYTHON_EXE=python"

:: 2. Verify Python interpreter is functional
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable not found or not working!
    echo Attempted: "%PYTHON_EXE%"
    echo Please install Python 3.10+ or configure a virtual environment.
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

"%PYTHON_EXE%" "%STEP2_SCRIPT%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" (
    echo.
    echo [ERROR] Step 2 failed with exit code: %STEP2_EXIT%
    exit /b %STEP2_EXIT%
)

echo.
echo [SUCCESS] Step 2 finished successfully!
exit /b 0
