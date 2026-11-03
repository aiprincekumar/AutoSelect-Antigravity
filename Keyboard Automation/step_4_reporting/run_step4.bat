@echo off
setlocal enabledelayedexpansion
title AutoSelect-Commander - Step 4: Visual Dashboard Launcher

:: ============================================================================
:: AutoSelect-Commander - Step 4: Visual Dashboard Launcher (Manual Mode)
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: Keyboard Automation \ step_4_reporting \ run_step4.bat
:: Mission: Instantly opens the visual reporting dashboard in the default browser.
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "ROOT_DIR=%SCRIPT_DIR%..\"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME • STEP 4 VISUAL DASHBOARD (MANUAL MODE)
echo ============================================================================
echo   Script       : %SCRIPT_DIR%step4_reporting.py
echo   Python Engine: %PYTHON_EXE%
echo   Action       : Launching Visual Dashboard in Default Web Browser...
echo ============================================================================
echo.

"%PYTHON_EXE%" "%SCRIPT_DIR%step4_reporting.py" --show %*

if errorlevel 1 (
    echo [ERROR] Failed to open visual dashboard.
    pause
    exit /b 1
)

echo [*] Dashboard opened successfully in browser.
exit /b 0
