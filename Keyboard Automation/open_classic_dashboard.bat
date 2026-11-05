@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AutoSelect-Commander - Simple & Classic Dashboard

:: ============================================================================
:: AutoSelect-Commander - 1-Click Classic Dashboard Launcher
:: ============================================================================
:: Subsystem: Step 4: Simple & Classic Dashboard
:: Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
:: Description:
::   1-Click launcher to open the Simple & Classic Visual Dashboard.
::   - Connects to local server at http://127.0.0.1:8501/classic if running.
::   - Falls back to local file:// URL if server offline.
:: ============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "CLASSIC_FILE=%SCRIPT_DIR%step_4_reporting\Simple and Classic Dashboard\dashboard.html"

echo ============================================================================
echo   AUTOCONNECT / GRILL-ME • SIMPLE & CLASSIC DASHBOARD
echo ============================================================================
echo   Mode: Simple & Classic UI
echo   URL : http://127.0.0.1:8501/classic
echo   File: %CLASSIC_FILE%
echo ============================================================================
echo.

:: 1. Check if server on port 8501 is already running
powershell -NoProfile -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', 8501)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Control Server is ALREADY running on http://127.0.0.1:8501/
    echo [*] Opening Classic Dashboard in default browser...
    start http://127.0.0.1:8501/classic
    timeout /t 2 /nobreak >nul
    exit /b 0
)

:: 2. Fallback to direct file URL
if exist "%CLASSIC_FILE%" (
    echo [*] Opening Classic Dashboard static file in default browser...
    start "" "%CLASSIC_FILE%"
    exit /b 0
)

echo [ERROR] Classic Dashboard file not found at: "%CLASSIC_FILE%"
pause
exit /b 1
