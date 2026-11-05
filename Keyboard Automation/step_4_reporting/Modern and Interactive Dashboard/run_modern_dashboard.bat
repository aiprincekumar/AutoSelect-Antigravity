@echo off
REM ==============================================================================
REM AutoSelect-Commander - Modern and Interactive Dashboard Launcher
REM ==============================================================================
TITLE AutoSelect-Commander - Modern and Interactive Dashboard

SET "THIS_DIR=%~dp0"
SET "DASHBOARD_FILE=%THIS_DIR%dashboard.html"

echo ==============================================================================
echo [INFO] Generating / Refreshing Modern and Interactive Dashboard...
python "%THIS_DIR%generate_modern_dashboard.py"
echo ==============================================================================
echo [INFO] Launching Modern and Interactive Dashboard in Browser...
echo [INFO] File: %DASHBOARD_FILE%
echo ==============================================================================

start "" "%DASHBOARD_FILE%"
exit /b 0
