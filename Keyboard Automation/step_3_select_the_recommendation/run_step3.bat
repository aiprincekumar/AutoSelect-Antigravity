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
:: Environment: Dedicated, self-healing Keyboard Automation\.venv
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
if exist "%SCRIPT_DIR%..\state\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
) else if exist "%SCRIPT_DIR%..\target_chat.json" (
    set "STATE_FILE=%SCRIPT_DIR%..\target_chat.json"
) else (
    set "STATE_FILE=%SCRIPT_DIR%..\state\target_chat.json"
)
set "STEP3_SCRIPT=%SCRIPT_DIR%step3_keyboard_automation.py"

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
