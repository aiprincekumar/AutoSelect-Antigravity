' ============================================================================
' AutoSelect-Commander - Persistent Background Dashboard & Server Launcher
' ============================================================================
' Subsystem: Step 4 Telemetry & Process Control Daemon
' Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
' Description:
'   Launches dashboard_server.py completely headless (window style 0, hidden).
'   Runs as a persistent background process detached from any console window.
'   If server on port 8501 is already running, reuses it and opens default browser.
' ============================================================================

Option Explicit

Dim fso, wshShell, scriptDir, workspaceDir, pythonExe, serverScript, runCmd, httpCheck, alreadyRunning

Set fso = CreateObject("Scripting.FileSystemObject")
Set wshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Dynamically resolve workspace root directory (Keyboard Automation)
If fso.FolderExists(fso.BuildPath(scriptDir, "Keyboard Automation")) Then
    workspaceDir = fso.BuildPath(scriptDir, "Keyboard Automation")
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "step_4_reporting\dashboard_server.py")) Then
    workspaceDir = scriptDir
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "dashboard_server.py")) Then
    workspaceDir = fso.GetParentFolderName(scriptDir)
Else
    workspaceDir = scriptDir
End If

' 2. Resolve Python Executable (Prefer .venv\Scripts\python.exe)
If fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")
ElseIf fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")
Else
    pythonExe = "python.exe"
End If

' 3. Resolve dashboard_server.py Path
If fso.FileExists(fso.BuildPath(workspaceDir, "step_4_reporting\dashboard_server.py")) Then
    serverScript = fso.BuildPath(workspaceDir, "step_4_reporting\dashboard_server.py")
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "dashboard_server.py")) Then
    serverScript = fso.BuildPath(scriptDir, "dashboard_server.py")
Else
    serverScript = fso.BuildPath(workspaceDir, "step_4_reporting\dashboard_server.py")
End If

' 4. Pre-Check: Is Server on Port 8501 Already Listening?
alreadyRunning = False
On Error Resume Next
Set httpCheck = CreateObject("MSXML2.ServerXMLHTTP.6.0")
If Not httpCheck Is Nothing Then
    httpCheck.setTimeouts 500, 500, 1000, 1000
    httpCheck.open "GET", "http://127.0.0.1:8501/api/automation/status", False
    httpCheck.send
    If httpCheck.status = 200 Then
        alreadyRunning = True
    End If
    Set httpCheck = Nothing
End If
On Error GoTo 0

' 5. Execution Logic
If alreadyRunning Then
    ' Server is already running: Open browser immediately without spawning duplicate
    wshShell.Run "cmd /c start http://127.0.0.1:8501/", 0, False
Else
    ' Server is not running: Launch dashboard_server.py completely hidden (style 0)
    wshShell.CurrentDirectory = workspaceDir
    runCmd = """" & pythonExe & """ """ & serverScript & """ --port 8501"
    wshShell.Run runCmd, 0, False

    ' Wait 1.2s for port binding, then launch browser
    WScript.Sleep 1200
    wshShell.Run "cmd /c start http://127.0.0.1:8501/", 0, False
End If

Set fso = Nothing
Set wshShell = Nothing
