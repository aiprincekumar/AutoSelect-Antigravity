@echo off
REM ==============================================================================
REM AutoSelect-Commander - Simple and Classic Dashboard Launcher
REM ==============================================================================
TITLE AutoSelect-Commander - Simple and Classic Dashboard

SET "THIS_DIR=%~dp0"
SET "DASHBOARD_FILE=%THIS_DIR%dashboard.html"

echo ==============================================================================
echo [INFO] Launching Simple and Classic Dashboard...
echo [INFO] File: %DASHBOARD_FILE%
echo ==============================================================================

start "" "%DASHBOARD_FILE%"
exit /b 0
