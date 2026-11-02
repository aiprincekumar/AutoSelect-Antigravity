@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Two-Script Modular Runner
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Activating Grill Me Chat in anti-gravity
:: Architecture:
::   - Step 1 (step1_find_and_focus.py): Scan Transcripts, Identify Chat, Focus Window, Save State
::   - Step 2 (step2_gui_chat_select.py): CDP/DOM Chat Search, Smooth Glide, GUI Selection & Focus
:: UTF-8 code page configuration for accurate emoji and Unicode output

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STEP2_SCRIPT=%SCRIPT_DIR%step2_gui_chat_select.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

:: 1. Detect Python Executable (.venv prioritized)
set "PY_CMD="

if exist "%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%..\Mouse Automation\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
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
echo   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (Two-Script Modular Pipeline)
echo ============================================================================
echo   Python Engine : %PY_CMD%
echo   Step 1 Script : %STEP1_SCRIPT%
echo   Step 2 Script : %STEP2_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 2. Execute Step 1: Search, State Store & Window Focus
echo [*] [STEP 1 / 2] Scanning Brain Transcripts, Saving State and Focusing Window...
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
echo [*] [STEP 2 / 2] Locating Conversation Element in Antigravity GUI and Selecting...
echo.

"%PY_CMD%" "%STEP2_SCRIPT%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" goto :STEP2_FAILED

echo.
echo ============================================================================
echo   🎉 [PIPELINE SUCCESS] GRILL ME CHAT IS FULLY ACTIVATED IN ANTIGRAVITY!
echo ============================================================================
echo   1. Pending Question Identified and State Saved to target_chat.json.
echo   2. Antigravity Window Safely Maximized/Preserved (No Restore-Down) and Focused.
echo   3. Target Chat Selected via DevTools / DOM Precision Click.
echo   4. Chat Input Pane Focused (Ctrl + L) and Ready for Response.
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
exit /b %STEP2_EXIT%

:END_PROMPT
echo.
echo %* | findstr /i "no-pause" >nul
if errorlevel 1 (
    echo Press any key to close this runner window...
    pause >nul
)
exit /b 0
