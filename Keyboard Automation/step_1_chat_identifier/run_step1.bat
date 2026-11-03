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
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"

:: 1. Bulletproof Python Executable Resolution
set "PYTHON_EXE="

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\..\.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\..\Mouse Automation\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\..\Mouse Automation\.venv\Scripts\python.exe"
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
