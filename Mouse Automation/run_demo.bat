@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title AutoSelect-Commander - Standalone Demo

echo ===============================================================================
echo            AutoSelect-Commander - Standalone Visual Demo Simulator
echo ===============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv!
    echo Please run run.bat first to set up the environment.
    pause
    exit /b 1
)

echo [LAUNCH] Starting Standalone Visual Demo Simulator...
echo -------------------------------------------------------------------------------
".venv\Scripts\python.exe" standalone_demo.py %*

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Demo finished with code %errorlevel%.
    pause
)

exit /b 0
