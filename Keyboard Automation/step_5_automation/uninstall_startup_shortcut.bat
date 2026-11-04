@echo off
setlocal enabledelayedexpansion

echo ============================================================================
echo AutoSelect-Commander - Windows Startup Sentinel Uninstaller
echo Subsystem: Step 5 Automation
echo ============================================================================

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Antigravity_Lifecycle_Sentinel.lnk"

echo [1/2] Terminating any active background Sentinel instances...
call "%~dp0stop_sentinel.bat" >nul 2>&1

echo [2/2] Removing shortcut from Windows Startup folder...
if exist "%SHORTCUT_PATH%" (
    del /f /q "%SHORTCUT_PATH%"
    echo [SUCCESS] Removed "%SHORTCUT_PATH%".
) else (
    echo [INFO] Shortcut was not present in Windows Startup.
)

echo.
echo [DONE] Auto-start registration has been cleanly removed.
ping 127.0.0.1 -n 3 >nul
exit /b 0
