@echo off
setlocal enabledelayedexpansion

echo ============================================================================
echo AutoSelect-Commander - Windows Startup Auto-Boot Installer
echo Subsystem: Step 5 Automation (Zero-Touch Lifecycle Sentinel)
echo ============================================================================

set "SCRIPT_DIR=%~dp0"
set "VBS_LAUNCHER=%SCRIPT_DIR%start_sentinel_background.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Antigravity_Lifecycle_Sentinel.lnk"

if not exist "%VBS_LAUNCHER%" (
    echo [ERROR] Launcher file not found at: "%VBS_LAUNCHER%"
    pause
    exit /b 1
)

echo [1/3] Registering background sentinel into Windows Startup folder:
echo       Destination: "%SHORTCUT_PATH%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$sc = $ws.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$sc.TargetPath = 'wscript.exe'; " ^
    "$sc.Arguments = [char]34 + '%VBS_LAUNCHER%' + [char]34; " ^
    "$sc.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$sc.Description = 'Antigravity Lifecycle Sentinel - Auto Start Server & Automation'; " ^
    "$sc.WindowStyle = 7; " ^
    "$sc.Save();"

if exist "%SHORTCUT_PATH%" (
    echo [2/3] Verified shortcut creation in Windows Startup successfully!
) else (
    echo [ERROR] Failed to create shortcut in Startup folder.
    pause
    exit /b 1
)

echo [3/3] Starting Sentinel daemon immediately in background...
cscript //nologo "%VBS_LAUNCHER%"

echo.
echo ============================================================================
echo [SUCCESS] Full Automation is now ACTIVE!
echo   - Whenever Windows starts, this Sentinel will launch automatically.
echo   - Whenever Antigravity opens, it will start the Server + Auto-Run Tasks.
echo   - Whenever Antigravity closes, it will automatically shut them down.
echo   - No clicks or commands required ever again!
echo ============================================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
