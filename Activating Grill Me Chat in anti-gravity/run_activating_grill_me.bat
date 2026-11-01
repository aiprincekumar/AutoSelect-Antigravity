@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Windows Runner
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Activating Grill Me Chat in anti-gravity
:: UTF-8 code page configuration for accurate emoji and Unicode output

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%activating_grill_me.py"

:: 1. Detect Python Executable
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
:: 2. If arguments are passed, forward them directly
if not "%~1"=="" (
    "%PY_CMD%" "%PYTHON_SCRIPT%" %*
    exit /b %errorlevel%
)

:: 3. Interactive Menu Mode
:MENU
cls
echo ============================================================================
echo   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (Method 1: Transcript Parsing)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Target Script : %PYTHON_SCRIPT%
echo ============================================================================
echo.
echo   [1] Scan ^& Identify Pending Grill Me Chats (Step 1)
echo   [2] Auto-Select Latest Pending Chat ^& Prepare Selection (Step 1 + 2)
echo   [3] Dry-Run Simulation (Inspect without modifying state)
echo   [4] Output Selection State in Structured JSON
echo   [5] Auto-Select ^& Focus Antigravity Window
echo   [6] Run Comprehensive Unit Test Suite
echo   [7] Exit
echo.
set /p "CHOICE=Enter selection [1-7] (default 2): "

if "%CHOICE%"=="" set "CHOICE=2"

if "%CHOICE%"=="1" (
    echo.
    echo [*] Scanning Antigravity transcripts for pending ask_question prompts...
    "%PY_CMD%" "%PYTHON_SCRIPT%" --scan
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="2" (
    echo.
    echo [*] Auto-selecting newest pending Grill Me chat...
    "%PY_CMD%" "%PYTHON_SCRIPT%" --auto-select
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="3" (
    echo.
    echo [*] Running dry-run simulation...
    "%PY_CMD%" "%PYTHON_SCRIPT%" --dry-run
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="4" (
    echo.
    echo [*] Exporting structured JSON envelope...
    "%PY_CMD%" "%PYTHON_SCRIPT%" --auto-select --json
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="5" (
    echo.
    echo [*] Auto-selecting and bringing Antigravity window to focus...
    "%PY_CMD%" "%PYTHON_SCRIPT%" --auto-select --focus
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="6" (
    echo.
    echo [*] Running Unit Tests for Activating Grill Me...
    "%PY_CMD%" -m unittest discover -s "%SCRIPT_DIR%..\tests" -p "test_activating_grill_me.py"
    echo.
    pause
    goto :MENU
)

if "%CHOICE%"=="7" (
    echo Goodbye.
    exit /b 0
)

echo [!] Invalid selection. Please enter a number between 1 and 7.
timeout /t 2 >nul
goto :MENU
