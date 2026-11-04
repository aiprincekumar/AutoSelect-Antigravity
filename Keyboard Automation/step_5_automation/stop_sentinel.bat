@echo off
setlocal enabledelayedexpansion

echo ============================================================================
echo AutoSelect-Commander - Stop Sentinel & Automation
echo Subsystem: Step 5 Automation
echo ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo [1/3] Terminating Antigravity Lifecycle Sentinel background processes...
wmic process where "CommandLine like '%%antigravity_lifecycle_sentinel.py%%'" call terminate >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AntigravitySentinel*" >nul 2>&1

echo [2/3] Terminating Dashboard Server & Port 8501...
if exist "step_5_automation\antigravity_lifecycle_sentinel.py" (
    call ".venv\Scripts\python.exe" "step_5_automation\antigravity_lifecycle_sentinel.py" --stop >nul 2>&1
)

echo [3/3] Cleaning up any dangling complete_automation instances...
wmic process where "CommandLine like '%%complete_automation.py%%'" call terminate >nul 2>&1

echo.
echo [SUCCESS] Antigravity Sentinel, Server, and Automation stopped cleanly.
ping 127.0.0.1 -n 3 >nul
exit /b 0
