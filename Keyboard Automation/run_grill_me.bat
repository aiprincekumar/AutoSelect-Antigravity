@echo off
setlocal enabledelayedexpansion
title Grill Me Automation Launcher - AutoSelect-Commander

echo =====================================================================
echo            GRILL ME KEYBOARD AUTOMATION LAUNCHER
echo                 AutoSelect-Commander Suite
echo =====================================================================
echo.

:: Detect Python interpreter
set "PYTHON_CMD="
if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0..\.venv\Scripts\python.exe"
    echo [*] Using project virtualenv: !PYTHON_CMD!
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
echo Key Sequence to execute:
echo   1. Ctrl + L    ^> Focus chat input prompt
echo   2. Shift + Tab ^> Shift focus to option selection buttons
echo   3. 1           ^> Select Option 1 (Recommended answer)
echo   4. Enter       ^> Confirm and submit
echo.
echo A 5-second countdown will start after launch.
echo Switch to or click on your target chat window during countdown.
echo =====================================================================
echo.

"%PYTHON_CMD%" "%~dp0grill_me_automation.py" %*

set EXITCODE=%errorlevel%
echo.
echo =====================================================================
if !EXITCODE! equ 0 (
    echo [*] Automation finished successfully. [Exit Code: 0]
) else (
    echo [!] Automation encountered an error or non-zero exit code: !EXITCODE!
)
echo =====================================================================
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXITCODE%
