@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Antigravity 2.0 - Quiz Keyboard Automation Launcher

echo ====================================================================
echo   [*] ANTIGRAVITY 2.0 - QUIZ KEYBOARD AUTOMATION
echo   [*] Workspace: AutoSelect-Commander \ Quiz Automation
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

:: If arguments were passed from CLI, forward them immediately
if not "%~1"=="" (
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" %*
    exit /b %errorlevel%
)

:: Interactive Mode Selection Menu
echo Select Execution Mode:
echo   [1] Auto-Run (Load count from question_count.json)
echo   [2] Single Question Mode (N = 1)
echo   [3] 2-Question Quiz Mode (N = 2)
echo   [4] 3-Question Quiz Mode (N = 3)
echo   [5] Dry-Run Simulation (Safe test without sending keystrokes)
echo   [6] Custom Configuration...
echo   [7] Exit
echo.
set /p "CHOICE=Enter choice [1-7] (Default is 1): "

if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="1" (
    echo.
    echo [*] Executing Auto-Run from question_count.json...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions auto
) else if "%CHOICE%"=="2" (
    echo.
    echo [*] Executing Single Question Mode (N=1)...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions 1
) else if "%CHOICE%"=="3" (
    echo.
    echo [*] Executing 2-Question Quiz Mode (N=2)...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions 2
) else if "%CHOICE%"=="4" (
    echo.
    echo [*] Executing 3-Question Quiz Mode (N=3)...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions 3
) else if "%CHOICE%"=="5" (
    echo.
    echo [*] Running Safe Dry-Run Simulation...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions auto --dry-run
) else if "%CHOICE%"=="6" (
    echo.
    set /p "CUSTOM_Q=Enter number of questions: "
    set /p "CUSTOM_OPT=Enter option choices (default 1): "
    if "!CUSTOM_OPT!"=="" set "CUSTOM_OPT=1"
    echo [*] Executing with !CUSTOM_Q! questions and option !CUSTOM_OPT!...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions !CUSTOM_Q! --options !CUSTOM_OPT!
) else if "%CHOICE%"=="7" (
    echo Exiting.
    exit /b 0
) else (
    echo Invalid choice. Running Auto-Run...
    "%PYTHON_EXE%" "%~dp0quiz_automation.py" --questions auto
)

echo.
echo [DONE] Execution complete. Press any key to exit...
pause >nul
exit /b 0
