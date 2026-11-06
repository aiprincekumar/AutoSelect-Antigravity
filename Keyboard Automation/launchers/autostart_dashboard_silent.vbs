' ============================================================================
' AutoSelect-Commander - Silent Auto-Start Dashboard & Server Launcher
' ============================================================================
' Subsystem: Step 4: Reporting & Dashboard Local Control Server
' Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
' Description:
'   Launches the Dashboard Server 100% headlessly in the background on Windows
'   login/boot without flashing a console window or popping up a web browser.
'   Forwards --no-browser flag to start_dashboard_background.vbs.
' ============================================================================

Option Explicit

Dim fso, wshShell, scriptDir, launcherScript, runCmd

Set fso = CreateObject("Scripting.FileSystemObject")
Set wshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

If fso.FileExists(fso.BuildPath(scriptDir, "start_dashboard_background.vbs")) Then
    launcherScript = fso.BuildPath(scriptDir, "start_dashboard_background.vbs")
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "launchers\start_dashboard_background.vbs")) Then
    launcherScript = fso.BuildPath(scriptDir, "launchers\start_dashboard_background.vbs")
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "step_4_reporting\start_dashboard_background.vbs")) Then
    launcherScript = fso.BuildPath(scriptDir, "step_4_reporting\start_dashboard_background.vbs")
Else
    launcherScript = fso.BuildPath(scriptDir, "start_dashboard_background.vbs")
End If

runCmd = "wscript.exe """ & launcherScript & """ --no-browser"
wshShell.Run runCmd, 0, False

Set fso = Nothing
Set wshShell = Nothing
