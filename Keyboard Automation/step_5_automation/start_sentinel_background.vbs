' ============================================================================
' AutoSelect-Commander - Antigravity Lifecycle Sentinel Background Launcher
' ============================================================================
' Subsystem: Step 5 Automation (Zero-Touch Lifecycle Sentinel & Task Orchestrator)
' Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
' Description:
'   Launches antigravity_lifecycle_sentinel.py completely headless (window style 0, hidden).
'   Runs as a persistent background process detached from any console window.
'   Auto-detects Pythonw from .venv\Scripts\pythonw.exe.
' ============================================================================

Option Explicit

Dim fso, wshShell, scriptDir, workspaceDir, pythonExe, sentinelScript, runCmd, alreadyRunning, procList, proc

Set fso = CreateObject("Scripting.FileSystemObject")
Set wshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Resolve workspace root directory (Keyboard Automation)
If fso.FolderExists(fso.BuildPath(scriptDir, "step_5_automation")) Then
    workspaceDir = scriptDir
Else
    workspaceDir = fso.GetParentFolderName(scriptDir)
End If

' 2. Resolve Python Executable (Prefer .venv\Scripts\pythonw.exe)
If fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\pythonw.exe")
ElseIf fso.FileExists(fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")) Then
    pythonExe = fso.BuildPath(workspaceDir, ".venv\Scripts\python.exe")
Else
    pythonExe = "pythonw.exe"
End If

' 3. Resolve antigravity_lifecycle_sentinel.py Path
If fso.FileExists(fso.BuildPath(scriptDir, "antigravity_lifecycle_sentinel.py")) Then
    sentinelScript = fso.BuildPath(scriptDir, "antigravity_lifecycle_sentinel.py")
Else
    sentinelScript = fso.BuildPath(workspaceDir, "step_5_automation\antigravity_lifecycle_sentinel.py")
End If

' 4. Check if Sentinel is already running to avoid duplicate instances
alreadyRunning = False
On Error Resume Next
Set procList = GetObject("winmgmts:").ExecQuery("SELECT ProcessId, CommandLine FROM Win32_Process WHERE CommandLine LIKE '%antigravity_lifecycle_sentinel.py%'")
If Not procList Is Nothing Then
    If procList.Count > 0 Then
        alreadyRunning = True
    End If
End If
On Error GoTo 0

' 5. Execution Logic
If alreadyRunning Then
    ' Already running, exit silently
    WScript.Quit 0
Else
    ' Launch sentinel completely hidden (window style 0)
    wshShell.CurrentDirectory = workspaceDir
    runCmd = """" & pythonExe & """ """ & sentinelScript & """ --daemon"
    wshShell.Run runCmd, 0, False
End If

Set fso = Nothing
Set wshShell = Nothing
