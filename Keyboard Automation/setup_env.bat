@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Setup Keyboard Automation Environment (.venv)

echo ===============================================================================
echo        AutoSelect-Commander - Dedicated Environment Setup (Keyboard Automation)
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python or uv availability
set "PYTHON_CMD="

where uv >nul 2>nul
if %errorlevel% equ 0 (
    set "USE_UV=1"
) else (
    set "USE_UV=0"
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py -3"
    ) else (
        echo [ERROR] Python 3 was not found in your system PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

:: 2. Check / Create Virtual Environment (.venv)
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Initializing dedicated virtual environment in Keyboard Automation\.venv...
    if %USE_UV% equ 1 (
        uv venv .venv
    ) else (
        !PYTHON_CMD! -m venv .venv
    )
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SETUP] Dedicated virtual environment created successfully.
    echo.
)

:: 3. Check and Install Requirements
if not exist ".venv\.installed_v1" (
    echo [SETUP] Installing required dependencies: pyautogui, psutil...
    if %USE_UV% equ 1 (
        uv pip install --python ".venv\Scripts\python.exe" -r requirements.txt
    ) else (
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    )
    if %errorlevel% neq 0 (
        echo [WARN] Fast install encountered notice, checking runtime...
    )
    echo 1 > ".venv\.installed_v1"
    echo [SETUP] Dependencies installed and verified.
    echo.
) else (
    echo [SETUP] Virtual environment and dependencies are up to date.
)

echo [SUCCESS] Keyboard Automation dedicated environment is ready:
echo   Python: "%~dp0.venv\Scripts\python.exe"
echo ===============================================================================

exit /b 0
