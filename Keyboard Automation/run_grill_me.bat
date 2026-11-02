@echo off
setlocal enabledelayedexpansion
title Step 3: Keyboard Automation (Grill-Me) Launcher - AutoSelect-Commander

echo =====================================================================
echo       [+] STEP 3: KEYBOARD AUTOMATION LAUNCHER (Grill-Me Mode)
echo                     AutoSelect-Commander Suite
echo =====================================================================
echo.

set "SCRIPT_DIR=%~dp0"

:: 1. Bulletproof Python Executable Resolution
set "PYTHON_EXE="

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe"
) else if exist "%USERPROFILE%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.venv\Scripts\python.exe"
) else if exist "%USERPROFILE%\.local\bin\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.local\bin\python.exe"
) else (
    for /f "delims=" %%I in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
    )
    if not defined PYTHON_EXE (
        for /f "delims=" %%I in ('where py.exe 2^>nul') do (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
        )
    )
)

if not defined PYTHON_EXE set "PYTHON_EXE=python"

:: 2. Verify Python interpreter is functional
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable not found or not working!
    echo Attempted: "%PYTHON_EXE%"
    echo Please install Python 3.10+ or configure a virtual environment.
    pause
    exit /b 1
)

echo [*] Using Python interpreter: %PYTHON_EXE%
echo.
echo Intelligent Auto-Targeting (Step 3: Keyboard Automation):
echo   - Auto-Detects target window (Antigravity 2.0 Harness / IDE / Chat)
echo   - Process-level detection: Antigravity.exe, Chrome_WidgetWin_1, and Titles
echo   - If minimized -^> Restores automatically (SW_RESTORE / OpenIcon)
echo   - If small/normal -^> Maximizes to full screen (SW_MAXIMIZE)
echo   - Brings window to foreground focus with Windows 10/11 OS lock bypass
echo.
echo Key Sequence to execute:
echo   1. Ctrl + L    ^> Focus chat input prompt
echo   2. Shift + Tab ^> Shift focus to option selection buttons
echo   3. 1           ^> Select Option 1 (Recommended answer)
echo   4. Enter       ^> Confirm and submit
echo.
echo A countdown will start after launch. Target window will be
echo automatically maximized and focused before keystrokes are sent.
echo =====================================================================
echo.

set "TARGET_SCRIPT=%SCRIPT_DIR%step3_keyboard_automation.py"
if not exist "%TARGET_SCRIPT%" set "TARGET_SCRIPT=%SCRIPT_DIR%grill_me_automation.py"

"%PYTHON_EXE%" "%TARGET_SCRIPT%" %*

set EXITCODE=%errorlevel%
echo.
echo =====================================================================
if %EXITCODE% equ 0 (
    echo [*] Step 3: Keyboard Automation finished successfully. [Exit Code: 0]
) else (
    echo [!] Step 3: Keyboard Automation encountered exit code: %EXITCODE%
)
echo =====================================================================
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXITCODE%
