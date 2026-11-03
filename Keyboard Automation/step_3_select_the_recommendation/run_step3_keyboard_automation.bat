@echo off
setlocal enabledelayedexpansion
title Step 3: Keyboard Automation Launcher - AutoSelect-Commander

:: ============================================================================
:: AutoSelect-Commander - Step 3: Keyboard Automation Standalone Runner
:: ============================================================================
:: Script: step3_keyboard_automation.py
:: Directory: step_3_select_the_recommendation (Step 3 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Executes Step 3 of the AutoSelect-Commander pipeline:
::   Automatically restores/maximizes Antigravity IDE window, bypasses OS
::   foreground lock, injects Ctrl+L -> Shift+Tab -> Option -> Enter with
::   support for dynamic multi-question quiz cards and safety abort gates.
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"
set "STEP3_SCRIPT=%SCRIPT_DIR%step3_keyboard_automation.py"

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
echo    [STEP 3 / 3] KEYBOARD AUTOMATION ^& OPTION SELECTION (STANDALONE RUNNER)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Target Script : %STEP3_SCRIPT%
echo   Target State  : %STATE_FILE%
echo ============================================================================
echo.

"%PYTHON_EXE%" "%STEP3_SCRIPT%" --state-file "%STATE_FILE%" %*
set "STEP3_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================================
if "%STEP3_EXIT%"=="0" (
    echo    [STEP 3 SUCCESS] Keyboard Automation completed successfully! [Exit: 0]
) else (
    echo   [!] [STEP 3 FAILED] Keyboard Automation encountered exit code: %STEP3_EXIT%
)
echo ============================================================================
echo.

exit /b %STEP3_EXIT%
