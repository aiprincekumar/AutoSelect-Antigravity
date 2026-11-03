<#
.SYNOPSIS
    PowerShell runner for the Step 3: Keyboard Automation (Grill Me) suite.

.DESCRIPTION
    Runs step3_keyboard_automation.py (or grill_me_automation.py) with configurable parameters,
    automatically locating the local project virtual environment or system Python.
    Features automatic window detection, un-minimizing, full-screen maximizing, and foreground focus.
    Pipeline Step: Step 3 of 3 (Option Selection & Confirmation).

.PARAMETER TargetWindow
    Window title or process keywords to identify and auto-maximize (default: "Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander"). Supports comma-separated keywords and Antigravity 2.0 Harness process signature.

.PARAMETER Countdown
    Seconds to count down before sending keystrokes (default: 5).

.PARAMETER StepDelay
    Delay in seconds between keystrokes (default: 0.35s / 350ms).

.PARAMETER Option
    Option number to choose (default: "1").

.PARAMETER SettleDelay
    Delay in seconds after window maximize/focus before keystroke sequence (default: 0.5s).

.PARAMETER SkipCtrlL
    Skip sending Ctrl + L.

.PARAMETER SkipEnter
    Skip sending Enter.

.PARAMETER NoAutoFocus
    Disable automatic foreground window focus.

.PARAMETER NoAutoMaximize
    Disable automatic window maximization.

.PARAMETER NoCountdown
    Execute immediately without countdown.

.PARAMETER DryRun
    Simulate execution without sending keystrokes.

.PARAMETER Engine
    Simulation engine ('auto', 'ctypes', or 'pyautogui').

.PARAMETER Repeat
    Number of times to run sequence (default: 1).

.EXAMPLE
    .\run_grill_me.ps1 -Countdown 5 -Option "1"

.EXAMPLE
    .\run_grill_me.ps1 -TargetWindow "Antigravity" -DryRun
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [int]$Countdown = 5,

    [Parameter(Position = 1)]
    [double]$StepDelay = 0.35,

    [Parameter(Position = 2)]
    [string]$Option = "1",

    [string]$TargetWindow = "Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander",
    [double]$SettleDelay = 0.5,

    [switch]$SkipCtrlL,
    [switch]$SkipEnter,
    [switch]$NoAutoFocus,
    [switch]$NoAutoMaximize,
    [switch]$NoCountdown,
    [switch]$DryRun,
    [ValidateSet("auto", "ctypes", "pyautogui")]
    [string]$Engine = "auto",
    [int]$Repeat = 1,
    [string]$Questions = "auto",
    [string]$OptionsList = $null,
    [string]$StateFile = $null
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  [+] STEP 3: KEYBOARD AUTOMATION LAUNCHER (Grill-Me PowerShell)    " -ForegroundColor Yellow
Write-Host "                 AutoSelect-Commander Suite                          " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Locate Python
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$localVenvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$parentVenvPython = Join-Path $scriptDir "..\.venv\Scripts\python.exe"
$grandparentVenvPython = Join-Path $scriptDir "..\..\.venv\Scripts\python.exe"
$mouseVenvPython = Join-Path $scriptDir "..\..\Mouse Automation\.venv\Scripts\python.exe"
$userVenvPython = Join-Path $env:USERPROFILE ".venv\Scripts\python.exe"
$userLocalPython = Join-Path $env:USERPROFILE ".local\bin\python.exe"

$pythonCmd = $null
if (Test-Path $localVenvPython) {
    $pythonCmd = $localVenvPython
    Write-Host "[*] Found local virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $parentVenvPython) {
    $pythonCmd = $parentVenvPython
    Write-Host "[*] Found parent virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $grandparentVenvPython) {
    $pythonCmd = $grandparentVenvPython
    Write-Host "[*] Found project virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $mouseVenvPython) {
    $pythonCmd = $mouseVenvPython
    Write-Host "[*] Found Mouse Automation virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $userVenvPython) {
    $pythonCmd = $userVenvPython
    Write-Host "[*] Found user virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $userLocalPython) {
    $pythonCmd = $userLocalPython
    Write-Host "[*] Found local bin Python: $pythonCmd" -ForegroundColor Green
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = (Get-Command python).Source
    Write-Host "[*] Found system Python: $pythonCmd" -ForegroundColor Green
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "[*] Found Windows py launcher" -ForegroundColor Green
} else {
    Write-Error "[!] Python was not found on PATH or in .venv. Please install Python 3.8+."
    exit 1
}

$pyScript = Join-Path $scriptDir "step3_keyboard_automation.py"
if (-not (Test-Path $pyScript)) {
    $pyScript = Join-Path $scriptDir "grill_me_automation.py"
}

# Build arguments
$argList = @(
    "`"$pyScript`"",
    "-t", "$TargetWindow",
    "-c", "$Countdown",
    "-d", "$StepDelay",
    "-o", "$Option",
    "-e", "$Engine",
    "-r", "$Repeat",
    "--settle-delay", "$SettleDelay"
)

if ($SkipCtrlL) { $argList += "--skip-ctrl-l" }
if ($SkipEnter) { $argList += "--skip-enter" }
if ($NoAutoFocus) { $argList += "--no-auto-focus" }
if ($NoAutoMaximize) { $argList += "--no-auto-maximize" }
if ($NoCountdown) { $argList += "--no-countdown" }
if ($DryRun) { $argList += "--dry-run" }
if ($Questions) { $argList += "-q", "$Questions" }
if ($OptionsList) { $argList += "-ol", "$OptionsList" }
if ($StateFile) { $argList += "--state-file", "$StateFile" }

Write-Host "[*] Launching: $pythonCmd $($argList -join ' ')" -ForegroundColor DarkGray
Write-Host ""

try {
    & $pythonCmd $argList
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "[+] Step 3: Keyboard Automation successfully completed! (Exit Code: 0)" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[!] Step 3: Keyboard Automation finished with exit code: $exitCode" -ForegroundColor Red
    }
    exit $exitCode
} catch {
    Write-Error "[!] Failed to execute automation script: $_"
    exit 1
}
