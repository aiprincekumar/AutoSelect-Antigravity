@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Antigravity 2.0 - Chained Detection & Quiz Automation Launcher

echo ====================================================================
echo   [*] ANTIGRAVITY 2.0 - CHAINED DETECTION & QUIZ AUTOMATION
echo   [*] Step 1: Detect/Simulate Question Count (Question Detection)
echo   [*] Step 2: Execute Multi-Question Shortcut Loop (Quiz Automation)
echo ====================================================================
echo.

:: Resolve Python executable (prefer workspace .venv)
set "PYTHON_EXE="
if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERROR] Python not found on system PATH or virtual environment!
        pause
        exit /b 1
    )
)

set "DETECTION_SCRIPT=%~dp0..\Question Detection\detect_questions.py"
set "QUIZ_SCRIPT=%~dp0quiz_automation.py"

:: Check scripts existence
if not exist "%DETECTION_SCRIPT%" (
    echo [ERROR] Detection script not found at "%DETECTION_SCRIPT%"
    pause
    exit /b 1
)

:: Interactive Menu
echo Select Chained Execution Mode:
echo   [1] Live Auto-Detect from Antigravity Window + Execute Keystrokes
echo   [2] Live Auto-Detect + Dry-Run Simulation (Safe test)
echo   [3] Simulate 2 Questions + Execute Keystrokes
echo   [4] Simulate 2 Questions + Dry-Run Simulation
echo   [5] Simulate 3 Questions + Execute Keystrokes
echo   [6] Simulate 3 Questions + Dry-Run Simulation
echo   [7] Custom Simulation Count...
echo   [8] Exit
echo.
set /p "CHAIN_CHOICE=Enter choice [1-8] (Default is 1): "

if "%CHAIN_CHOICE%"=="" set "CHAIN_CHOICE=1"

set "SIM_FLAG="
set "DRY_FLAG="

if "%CHAIN_CHOICE%"=="1" (
    set "SIM_FLAG=--detect"
    set "DRY_FLAG="
) else if "%CHAIN_CHOICE%"=="2" (
    set "SIM_FLAG=--detect"
    set "DRY_FLAG=--dry-run"
) else if "%CHAIN_CHOICE%"=="3" (
    set "SIM_FLAG=--simulate 2"
    set "DRY_FLAG="
) else if "%CHAIN_CHOICE%"=="4" (
    set "SIM_FLAG=--simulate 2"
    set "DRY_FLAG=--dry-run"
) else if "%CHAIN_CHOICE%"=="5" (
    set "SIM_FLAG=--simulate 3"
    set "DRY_FLAG="
) else if "%CHAIN_CHOICE%"=="6" (
    set "SIM_FLAG=--simulate 3"
    set "DRY_FLAG=--dry-run"
) else if "%CHAIN_CHOICE%"=="7" (
    echo.
    set /p "CUSTOM_SIM=Enter number of questions to simulate (e.g. 4): "
    if "!CUSTOM_SIM!"=="" set "CUSTOM_SIM=2"
    set "SIM_FLAG=--simulate !CUSTOM_SIM!"
    set /p "DRY_CONFIRM=Run in Dry-Run mode? [y/N]: "
    if /i "!DRY_CONFIRM!"=="y" set "DRY_FLAG=--dry-run"
) else if "%CHAIN_CHOICE%"=="8" (
    echo Exiting.
    exit /b 0
) else (
    set "SIM_FLAG=--detect"
    set "DRY_FLAG="
)

echo.
echo ====================================================================
echo   [STAGE 1/2] RUNNING QUESTION DETECTION (%SIM_FLAG%)
echo ====================================================================
"%PYTHON_EXE%" "%DETECTION_SCRIPT%" %SIM_FLAG%
if %errorlevel% neq 0 (
    echo [ERROR] Question detection failed with exit code %errorlevel%!
    pause
    exit /b %errorlevel%
)

echo.
echo ====================================================================
echo   [STAGE 2/2] DISPATCHING QUIZ AUTOMATION LOOP (%DRY_FLAG%)
echo ====================================================================
"%PYTHON_EXE%" "%QUIZ_SCRIPT%" --questions auto %DRY_FLAG%
if %errorlevel% neq 0 (
    echo [ERROR] Quiz automation failed with exit code %errorlevel%!
    pause
    exit /b %errorlevel%
)

echo.
echo ====================================================================
echo   [COMPLETED] Chained Detection & Quiz Automation finished cleanly!
echo ====================================================================
echo Press any key to exit...
pause >nul
exit /b 0
