@echo off
setlocal enabledelayedexpansion
title Step 3: Keyboard Automation Launcher - AutoSelect-Commander

:: ============================================================================
:: AutoSelect-Commander - Step 3: Keyboard Automation Standalone Runner
:: ============================================================================
:: Script: step3_keyboard_automation.py
:: Workspace: AutoSelect-Commander \ Keyboard Automation (Step 3 of 3)
:: Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   Executes Step 3 of the AutoSelect-Commander pipeline:
::   Automatically restores/maximizes Antigravity IDE window, bypasses OS
::   foreground lock, injects Ctrl+L -> Shift+Tab -> Option -> Enter with
::   support for dynamic multi-question quiz cards and safety abort gates.
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP3_SCRIPT=%SCRIPT_DIR%step3_keyboard_automation.py"

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

echo [ERROR] Python environment not found! Please install Python 3.8+ or configure a virtualenv.
pause
exit /b 1

:PYTHON_FOUND
echo ============================================================================
echo   ⌨️ [STEP 3 / 3] KEYBOARD AUTOMATION ^& OPTION SELECTION (STANDALONE RUNNER)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %STEP3_SCRIPT%
echo ============================================================================
echo.

"%PY_CMD%" "%STEP3_SCRIPT%" %*
set "STEP3_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================================
if "%STEP3_EXIT%"=="0" (
    echo   🎉 [STEP 3 SUCCESS] Keyboard Automation completed successfully! [Exit: 0]
) else (
    echo   [!] [STEP 3 FAILED] Keyboard Automation encountered exit code: %STEP3_EXIT%
)
echo ============================================================================
echo.

exit /b %STEP3_EXIT%
