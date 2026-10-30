@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title AutoSelect-Commander Launcher

echo ===============================================================================
echo                AutoSelect-Commander for Antigravity (1-Click)
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
    echo [SETUP] Initializing virtual environment in .venv...
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
    echo [SETUP] Virtual environment created successfully.
    echo.
)

:: 3. Check and Install Requirements
if not exist ".venv\.installed_v2" (
    echo [SETUP] Installing required dependencies (pyautogui, opencv-python, pillow, pynput, pygetwindow, uiautomation, winsdk)...
    if %USE_UV% equ 1 (
        uv pip install --python ".venv\Scripts\python.exe" -r requirements.txt
    ) else (
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    )
    if %errorlevel% neq 0 (
        echo [WARN] Fast install encountered notice, checking runtime...
    )
    echo 2 > ".venv\.installed_v2"
    echo [SETUP] Dependencies verified.
    echo.
)

:: 4. If command-line arguments are provided, bypass menu and run directly
if not "%~1"=="" (
    ".venv\Scripts\python.exe" auto_commander.py %*
    goto FINISH
)

:: 5. Interactive Mode Selection Menu (5s Default to Demo Mode)
echo.
echo  =============================================================================
echo                              SELECT EXECUTION MODE
echo  =============================================================================
echo.
echo    [1] Live Visual Demo / Test Mode (Recommended)
echo        -^> Spawns mock question card, floating countdown HUD ^& glides mouse!
echo.
echo    [2] Active Background Sentinel
echo        -^> Monitors live screen for Antigravity decision modals.
echo.
echo    [3] Screen ^& Window Diagnostics
echo        -^> Scans screen, tests OCR, lists detected windows and text.
echo.
echo  -----------------------------------------------------------------------------
echo  Auto-launching [1] Demo Mode in 5 seconds (Press 1, 2, or 3 to choose now)...
echo  -----------------------------------------------------------------------------
echo.

choice /c 123 /t 5 /d 1 /m "Your selection"

if %errorlevel% equ 3 goto RUN_DIAGNOSTICS
if %errorlevel% equ 2 goto RUN_SENTINEL
goto RUN_DEMO

:RUN_DEMO
echo.
echo [LAUNCH] Starting Live Visual Demo Mode...
echo ───────────────────────────────────────────────────────────────────────────────
".venv\Scripts\python.exe" auto_commander.py --simulate
goto FINISH

:RUN_SENTINEL
echo.
echo [LAUNCH] Starting Active Background Sentinel...
echo ───────────────────────────────────────────────────────────────────────────────
".venv\Scripts\python.exe" auto_commander.py
goto FINISH

:RUN_DIAGNOSTICS
echo.
echo [LAUNCH] Running Screen ^& Window Diagnostics...
echo ───────────────────────────────────────────────────────────────────────────────
".venv\Scripts\python.exe" auto_commander.py --diagnostics
goto FINISH

:FINISH
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Process terminated with code %errorlevel%.
    pause
)

exit /b 0
