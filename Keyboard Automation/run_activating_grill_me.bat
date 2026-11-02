@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Activating Grill Me Chat in Antigravity - Two-Script Modular Runner
:: ============================================================================
:: Target: Antigravity AI Coding Agent Sessions
:: Directory: AutoSelect-Commander \ Keyboard Automation (Steps 1 & 2)
:: Architecture:
::   - Step 1 (step1_find_and_focus.py): Scan Transcripts, Identify Chat, Focus Window, Save State
::   - Step 2 (step2_gui_chat_select.py): CDP/DOM Chat Search, Smooth Glide, GUI Selection & Focus
:: UTF-8 code page configuration for accurate emoji and Unicode output

chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "STEP1_SCRIPT=%SCRIPT_DIR%step1_find_and_focus.py"
set "STEP2_SCRIPT=%SCRIPT_DIR%step2_gui_chat_select.py"
set "STATE_FILE=%SCRIPT_DIR%target_chat.json"

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

echo ============================================================================
echo   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (Two-Step Modular Runner)
echo   (2- :    + GUI  )
echo ============================================================================
echo   Python Engine : %PYTHON_EXE%
echo   Step 1 Script : %STEP1_SCRIPT%
echo   Step 2 Script : %STEP2_SCRIPT%
echo   State File    : %STATE_FILE%
echo ============================================================================
echo.

:: 3. Execute Step 1: Search, State Store & Window Focus
echo [*] [STEP 1 / 2] Scanning Brain Transcripts, Saving State and Focusing Window...
echo.

"%PYTHON_EXE%" "%STEP1_SCRIPT%" %*
set "STEP1_EXIT=%ERRORLEVEL%"

if not "%STEP1_EXIT%"=="0" goto :STEP1_FAILED

echo.
echo [*] Step 1 completed successfully!
echo [*] Settle delay (0.8s) before GUI selection...
ping 127.0.0.1 -n 2 >nul 2>nul

:: 4. Execute Step 2: GUI Chat Selection & Chat Pane Activation
echo.
echo [*] [STEP 2 / 2] Locating Conversation Element in Antigravity GUI and Selecting...
echo.

"%PYTHON_EXE%" "%STEP2_SCRIPT%" %*
set "STEP2_EXIT=%ERRORLEVEL%"

if not "%STEP2_EXIT%"=="0" goto :STEP2_FAILED

echo.
echo ============================================================================
echo    [SUCCESS] GRILL ME CHAT IDENTIFIED AND ACTIVATED!
echo ============================================================================
echo   1. Pending Question Identified and State Saved to target_chat.json.
echo   2. Antigravity Window Safely Maximized/Preserved and Focused.
echo   3. Target Chat Selected via DevTools / DOM Precision Click.
echo   4. Chat Input Pane Focused (Ready for Keyboard Automation - Step 3).
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
