@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Antigravity 2.0 - Question Detection Launcher

echo ====================================================================
echo   [*] ANTIGRAVITY 2.0 - QUESTION DETECTION SYSTEM
echo   [*] Workspace: AutoSelect-Commander \ Question Detection
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
        echo Please run setup or install Python 3.10+.
        pause
        exit /b 1
    )
)

:: If arguments were passed from CLI, forward them immediately
if not "%~1"=="" (
    "%PYTHON_EXE%" "%~dp0detect_questions.py" %*
    exit /b %errorlevel%
)

:: Interactive Mode Selection Menu
echo Select Detection Mode:
echo   [1] Auto-Detect Questions from live Antigravity window
echo   [2] Simulate Single Question (N = 1)
echo   [3] Simulate 2 Questions (N = 2)
echo   [4] Simulate 3 Questions (N = 3)
echo   [5] Enter Custom Question Count...
echo   [6] Exit
echo.
set /p "CHOICE=Enter choice [1-6] (Default is 1): "

if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="1" (
    echo.
    echo [*] Running Auto-Detection...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --detect
) else if "%CHOICE%"=="2" (
    echo.
    echo [*] Simulating 1 Question...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --simulate 1
) else if "%CHOICE%"=="3" (
    echo.
    echo [*] Simulating 2 Questions...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --simulate 2
) else if "%CHOICE%"=="4" (
    echo.
    echo [*] Simulating 3 Questions...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --simulate 3
) else if "%CHOICE%"=="5" (
    echo.
    set /p "CUSTOM_COUNT=Enter number of questions to simulate (e.g. 4): "
    if "!CUSTOM_COUNT!"=="" set "CUSTOM_COUNT=1"
    echo [*] Simulating !CUSTOM_COUNT! Questions...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --simulate !CUSTOM_COUNT!
) else if "%CHOICE%"=="6" (
    echo Exiting.
    exit /b 0
) else (
    echo Invalid choice. Defaulting to Auto-Detection...
    "%PYTHON_EXE%" "%~dp0detect_questions.py" --detect
)

echo.
echo [DONE] Detection output saved in 'question_count.json'.
echo Press any key to exit...
pause >nul
exit /b 0
