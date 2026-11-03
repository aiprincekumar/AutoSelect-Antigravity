@echo off
setlocal enabledelayedexpansion
title AutoSelect-Commander - Complete 4-Step Automation Pipeline (All Steps)

:: ============================================================================
:: AutoSelect-Commander - Complete 4-Step Pipeline Runner (Root Master Launcher)
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Keyboard Automation (Root Master Launcher)
:: Architecture:
::   - Step 1 (step_1_chat_identifier\step1_find_and_focus.py): Scan Transcripts, Identify Chat, Focus Window, Save State
::   - Step 2 (step_2_chat_and_focus\step2_gui_chat_select.py): CDP/DOM Chat Search, Smooth Glide, GUI Selection & Focus
::   - Step 3 (step_3_select_the_recommendation\step3_keyboard_automation.py): Keyboard Automation, Option Selection & Confirmation
::   - Step 4 (step_4_reporting\step4_reporting.py): Reporting & Visual Dashboard (Two-Way Automation/Manual)
:: Virtual Environment: Dedicated, self-healing Keyboard Automation\.venv
:: UTF-8 code page configuration for accurate emoji and Unicode output
:: ============================================================================

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "STEP1_SCRIPT=%SCRIPT_DIR%step_1_chat_identifier\step1_find_and_focus.py"
set "STEP2_SCRIPT=%SCRIPT_DIR%step_2_chat_and_focus\step2_gui_chat_select.py"
set "STEP3_SCRIPT=%SCRIPT_DIR%step_3_select_the_recommendation\step3_keyboard_automation.py"
set "STEP4_SCRIPT=%SCRIPT_DIR%step_4_reporting\step4_reporting.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

:: 1. Dedicated Self-Healing Virtual Environment (.venv) Resolution
if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo [SETUP] Dedicated virtual environment not found in Keyboard Automation.
    echo [SETUP] Initializing self-healing .venv environment now...
    call "%SCRIPT_DIR%setup_env.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Keyboard Automation virtual environment.
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: "%PYTHON_EXE%"
    pause
    exit /b 1
)

:: 2. Verify Python interpreter is functional
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.8+ executable in .venv not working!
    echo Attempted: "%PYTHON_EXE%"
    pause
    exit /b 1
)

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME 4-STEP PIPELINE RUNNER (ALL STEPS)
echo   (1-Click Master Runner: Step 1 -^> Step 2 -^> Step 3 -^> Step 4)
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Step 1 Script : %STEP1_SCRIPT%
echo   Step 2 Script : %STEP2_SCRIPT%
echo   Step 3 Script : %STEP3_SCRIPT%
echo   Step 4 Script : %STEP4_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 3. Execute Step 1: Search, State Store & Window Focus
echo [*] [STEP 1 / 3] Scanning Brain Transcripts, Saving State and Focusing Window...
echo.

"%PYTHON_EXE%" "%STEP1_SCRIPT%" --state-file "%STATE_FILE%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if "%STEP1_EXIT%"=="10" (
    echo.
    echo ============================================================================
    echo   [INFO] NO PENDING GRILL ME / ASK_QUESTION CHATS FOUND
    echo   [*] All remaining steps [Step 2 and Step 3] cancelled automatically.
    echo   [*] Automation script closing now.
    echo ============================================================================
    goto :CLEAN_CLOSE
)

if not "%STEP1_EXIT%"=="0" goto :STEP1_FAILED

echo.
echo [*] Step 1 completed successfully!
echo [*] Settle delay (0.8s) before GUI selection...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 4. Execute Step 2: GUI Chat Selection & Chat Pane Activation
echo.
echo [*] [STEP 2 / 3] Locating Conversation Element in Antigravity GUI and Selecting...
echo.

"%PYTHON_EXE%" "%STEP2_SCRIPT%" --state-file "%STATE_FILE%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" goto :STEP2_FAILED

echo.
echo [*] Step 2 completed successfully!
echo [*] Settle delay (0.8s) before Keyboard Automation...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 5. Execute Step 3: Hybrid Keyboard Automation & Option Selection
echo.
echo [*] [STEP 3 / 3] Executing Keyboard Automation (Ctrl+L -^> Shift+Tab -^> Option -^> Enter)...
echo.

"%PYTHON_EXE%" "%STEP3_SCRIPT%" --state-file "%STATE_FILE%" --no-countdown %*
set "STEP3_EXIT=%ERRORLEVEL%"

if not "%STEP3_EXIT%"=="0" goto :STEP3_FAILED

echo.
echo [*] Step 3 completed successfully!
echo [*] Settle delay (0.8s) before Reporting & Telemetry...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 6. Execute Step 4: Reporting & Visual Dashboard
echo.
echo [*] [STEP 4 / 4] Recording Execution History & Scheduling Visual Dashboard...
echo.

if exist "%STEP4_SCRIPT%" (
    "%PYTHON_EXE%" "%STEP4_SCRIPT%" --state-file "%STATE_FILE%" %*
    set "STEP4_EXIT=!ERRORLEVEL!"
    if not "!STEP4_EXIT!"=="0" (
        echo [WARN] Step 4 reporting encountered warning (Exit Code: !STEP4_EXIT!).
    ) else (
        echo [*] Step 4 completed successfully. History stored in reports\automation_history.json.
    )
) else (
    echo [*] Step 4 script not found, skipping reporting.
)

echo.
echo ============================================================================
echo    [PIPELINE SUCCESS] 4-STEP GRILL ME WORKFLOW FULLY COMPLETED!
echo ============================================================================
echo   1. Pending Question Identified and State Saved to target_chat.json.
echo   2. Antigravity Window Safely Maximized/Preserved and Focused.
echo   3. Target Chat Selected via DevTools / DOM Precision Click.
echo   4. Chat Input Pane Focused and Option Selected via Keyboard Automation.
echo   5. Telemetry & Questions Recorded in reports\automation_history.json.
echo   6. Visual Dashboard primed to appear 10s after physical user movement.
echo ============================================================================
goto :CLEAN_CLOSE

:STEP1_FAILED
echo.
echo [ERROR] Step 1 encountered an issue (Exit Code: %STEP1_EXIT%).
echo Pipeline halted before GUI selection.
exit /b %STEP1_EXIT%

:STEP2_FAILED
echo.
echo [ERROR] Step 2 encountered an issue during GUI chat selection (Exit Code: %STEP2_EXIT%).
echo Pipeline halted before Keyboard Automation.
exit /b %STEP2_EXIT%

:STEP3_FAILED
echo.
echo [ERROR] Step 3 encountered an issue during Keyboard Automation (Exit Code: %STEP3_EXIT%).
exit /b %STEP3_EXIT%

:CLEAN_CLOSE
exit /b 0
