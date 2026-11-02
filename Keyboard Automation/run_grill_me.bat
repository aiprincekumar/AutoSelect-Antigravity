@echo off
setlocal enabledelayedexpansion
title Step 3: Keyboard Automation (Grill-Me) Launcher - AutoSelect-Commander

echo =====================================================================
echo       [+] STEP 3: KEYBOARD AUTOMATION LAUNCHER (Grill-Me Mode)
echo                     AutoSelect-Commander Suite
echo =====================================================================
echo.

:: Detect Python interpreter
set "PYTHON_CMD="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo [*] Using local virtualenv: !PYTHON_CMD!
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0..\.venv\Scripts\python.exe"
    echo [*] Using parent virtualenv: !PYTHON_CMD!
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
        echo [*] Using system Python
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=py -3"
            echo [*] Using Windows py launcher
        ) else (
            echo [!] ERROR: Python could not be found on your PATH or in .venv.
            echo [!] Please install Python 3.8+ or configure your environment.
            echo.
            pause
            exit /b 1
        )
    )
)

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

set "TARGET_SCRIPT=%~dp0step3_keyboard_automation.py"
if not exist "!TARGET_SCRIPT!" set "TARGET_SCRIPT=%~dp0grill_me_automation.py"

"%PYTHON_CMD%" "!TARGET_SCRIPT!" %*

set EXITCODE=%errorlevel%
echo.
echo =====================================================================
if !EXITCODE! equ 0 (
    echo [*] Step 3: Keyboard Automation finished successfully. [Exit Code: 0]
) else (
    echo [!] Step 3: Keyboard Automation encountered exit code: !EXITCODE!
)
echo =====================================================================
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXITCODE%
