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
Dim pollCount, isBound

Set fso = CreateObject("Scripting.FileSystemObject")
Set wshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Dynamically resolve workspace root directory (Keyboard Automation)
If fso.FolderExists(fso.BuildPath(scriptDir, "Keyboard Automation")) Then
    workspaceDir = fso.BuildPath(scriptDir, "Keyboard Automation")
ElseIf fso.FileExists(fso.BuildPath(fso.GetParentFolderName(scriptDir), "step_4_reporting\dashboard_server.py")) Then
    workspaceDir = fso.GetParentFolderName(scriptDir)
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "step_4_reporting\dashboard_server.py")) Then
    workspaceDir = scriptDir
ElseIf fso.FileExists(fso.BuildPath(scriptDir, "dashboard_server.py")) Then
    workspaceDir = fso.GetParentFolderName(scriptDir)
Else
    workspaceDir = fso.GetParentFolderName(scriptDir)
End If

' 2. Resolve Python Executable (Prefer .venv\Scripts\pythonw.exe for true windowless daemon)
If fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")
ElseIf fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")
Else
    pythonExe = "pythonw.exe"
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
If Err.Number <> 0 Or httpCheck Is Nothing Then
    Err.Clear
    Set httpCheck = CreateObject("MSXML2.ServerXMLHTTP")
End If
If Err.Number <> 0 Or httpCheck Is Nothing Then
    Err.Clear
    Set httpCheck = CreateObject("WinHttp.WinHttpRequest.5.1")
End If

If Not httpCheck Is Nothing Then
    httpCheck.setTimeouts 500, 500, 1000, 1000
    httpCheck.open "GET", "http://127.0.0.1:8501/api/automation/status", False
    httpCheck.send
    If Err.Number = 0 Then
        If httpCheck.status = 200 Then
            alreadyRunning = True
        End If
    Else
        Err.Clear
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
    runCmd = """" & pythonExe & """ """ & serverScript & """ --port 8501 --no-browser"
    wshShell.Run runCmd, 0, False

    ' Wait for server port binding (up to 3 seconds) before opening browser
    isBound = False
    For pollCount = 1 To 15
        WScript.Sleep 200
        On Error Resume Next
        Set httpCheck = CreateObject("MSXML2.ServerXMLHTTP.6.0")
        If Not httpCheck Is Nothing Then
            httpCheck.setTimeouts 200, 200, 400, 400
            httpCheck.open "GET", "http://127.0.0.1:8501/api/automation/status", False
            httpCheck.send
            If Err.Number = 0 Then
                If httpCheck.status = 200 Then
                    isBound = True
                End If
            Else
                Err.Clear
            End If
            Set httpCheck = Nothing
        End If
        On Error GoTo 0
        If isBound Then Exit For
    Next

    wshShell.Run "cmd /c start http://127.0.0.1:8501/", 0, False
End If

Set fso = Nothing
Set wshShell = Nothing
