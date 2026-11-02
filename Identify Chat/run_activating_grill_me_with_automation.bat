@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Complete 3-Step Pipeline Runner
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Identify Chat
:: Architecture:
::   - Step 1 (step1_find_and_focus.py): Scan Transcripts, Identify Chat, Focus Window, Save State
::   - Step 2 (step2_gui_chat_select.py): CDP/DOM Chat Search, Smooth Glide, GUI Selection & Focus
::   - Step 3 (step3_keyboard_automation.py): Step 3: Keyboard Automation, Option Selection & Confirmation
:: UTF-8 code page configuration for accurate emoji and Unicode output

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STEP2_SCRIPT=%SCRIPT_DIR%step2_gui_chat_select.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

:: Resolve absolute path for Keyboard Automation
for %%I in ("%SCRIPT_DIR%..\Keyboard Automation") do set "KEYBOARD_DIR=%%~fI"
if exist "%KEYBOARD_DIR%\step3_keyboard_automation.py" (
    set "STEP3_SCRIPT=%KEYBOARD_DIR%\step3_keyboard_automation.py"
) else (
    set "STEP3_SCRIPT=%KEYBOARD_DIR%\grill_me_automation.py"
)

:: 1. Detect Python Executable (.venv prioritized)
set "PY_CMD="

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%KEYBOARD_DIR%\.venv\Scripts\python.exe" (
    set "PY_CMD=%KEYBOARD_DIR%\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :PYTHON_FOUND
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :PYTHON_FOUND
)

where uv >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=uv run python"
    goto :PYTHON_FOUND
)

echo [ERROR] Python environment not found! Please install Python 3.10+ or configure a virtualenv.
pause
exit /b 1

:PYTHON_FOUND
echo ============================================================================
echo   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (Three-Step Pipeline Runner)
echo   (3-स्टेप ऑटोमेशन: स्कैन और फोकस + GUI चैट सेलेक्ट + कीबोर्ड ऑटोमेशन)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Step 1 Script : %STEP1_SCRIPT%
echo   Step 2 Script : %STEP2_SCRIPT%
echo   Step 3 Script : %STEP3_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 2. Execute Step 1: Search, State Store & Window Focus
echo [*] [STEP 1 / 3] Scanning Brain Transcripts, Saving State and Focusing Window...
echo.

"%PY_CMD%" "%STEP1_SCRIPT%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if not "%STEP1_EXIT%"=="0" goto :STEP1_FAILED

echo.
echo [*] Step 1 completed successfully!
echo [*] Settle delay (0.8s) before GUI selection...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 3. Execute Step 2: GUI Chat Selection & Chat Pane Activation
echo.
echo [*] [STEP 2 / 3] Locating Conversation Element in Antigravity GUI and Selecting...
echo.

"%PY_CMD%" "%STEP2_SCRIPT%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" goto :STEP2_FAILED

echo.
echo [*] Step 2 completed successfully!
echo [*] Settle delay (0.8s) before Keyboard Automation...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 4. Execute Step 3: Hybrid Keyboard Automation & Option Selection
echo.
echo [*] [STEP 3 / 3] Executing Keyboard Automation (Ctrl+L -^> Shift+Tab -^> Option -^> Enter)...
echo.

"%PY_CMD%" "%STEP3_SCRIPT%" %*
set "STEP3_EXIT=%ERRORLEVEL%"

if not "%STEP3_EXIT%"=="0" goto :STEP3_FAILED

echo.
echo ============================================================================
echo   🎉 [PIPELINE SUCCESS] 3-STEP GRILL ME WORKFLOW FULLY COMPLETED!
echo ============================================================================
echo   1. Pending Question Identified and State Saved to target_chat.json.
echo   2. Antigravity Window Safely Maximized/Preserved and Focused.
echo   3. Target Chat Selected via DevTools / DOM Precision Click.
echo   4. Chat Input Pane Focused and Option Selected via Keyboard Automation.
echo ============================================================================
goto :END_PROMPT

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

:END_PROMPT
echo.
echo %* | findstr /i "no-pause" >nul
if errorlevel 1 (
    echo Press any key to close this runner window...
    pause >nul
)
exit /b 0
