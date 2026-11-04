@echo off
setlocal enabledelayedexpansion

echo ============================================================================
echo AutoSelect-Commander - Stop Sentinel and Automation
echo Subsystem: Step 5 Automation
echo ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo [1/3] Terminating Antigravity Lifecycle Sentinel background processes...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'antigravity_lifecycle_sentinel' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [2/3] Terminating Dashboard Server and Port 8501...
if exist "step_5_automation\antigravity_lifecycle_sentinel.py" (
    call ".venv\Scripts\python.exe" "step_5_automation\antigravity_lifecycle_sentinel.py" --stop >nul 2>&1
)

echo [3/3] Cleaning up any dangling complete_automation instances...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'complete_automation.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo.
echo [SUCCESS] Antigravity Sentinel, Server, and Automation stopped cleanly.
ping 127.0.0.1 -n 2 >nul
exit /b 0
