@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Streamlined 1-Click Runner
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Activating Grill Me Chat in anti-gravity
:: UTF-8 code page configuration for accurate emoji and Unicode output

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%activating_grill_me.py"

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
:: 2. Forward arguments if provided (e.g. --dry-run, --json, --scan)
if not "%~1"=="" (
    "%PY_CMD%" "%PYTHON_SCRIPT%" %*
    exit /b %errorlevel%
)

:: 3. Streamlined 1-Click Execution (No "taam-jhaam" / unnecessary menu prompts)
echo ============================================================================
echo   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (1-Click Automation Runner)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %PYTHON_SCRIPT%
echo ============================================================================
echo.
echo   [*] Executing 1-Click Grill Me Detection, Focus ^& GUI Chat Selection...
echo.

"%PY_CMD%" "%PYTHON_SCRIPT%"

echo.
echo ============================================================================
echo   Press any key to close this runner window...
pause >nul
exit /b 0
