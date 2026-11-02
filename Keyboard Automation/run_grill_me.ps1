<#
.SYNOPSIS
    PowerShell runner for the Grill Me Keyboard Automation suite.

.DESCRIPTION
    Runs grill_me_automation.py with configurable parameters, automatically locating
    the local project virtual environment or system Python. Features automatic window
    detection, un-minimizing, full-screen maximizing, and foreground focus.

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
    [int]$Repeat = 1
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "            GRILL ME KEYBOARD AUTOMATION LAUNCHER (PowerShell)        " -ForegroundColor Yellow
Write-Host "                 AutoSelect-Commander Suite                          " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Locate Python
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$mouseVenvPython = Join-Path (Split-Path -Parent $scriptDir) "Mouse Automation\.venv\Scripts\python.exe"
$venvPython = Join-Path (Split-Path -Parent $scriptDir) ".venv\Scripts\python.exe"

$pythonCmd = $null
if (Test-Path $mouseVenvPython) {
    $pythonCmd = $mouseVenvPython
    Write-Host "[*] Found project virtualenv: $pythonCmd" -ForegroundColor Green
} elseif (Test-Path $venvPython) {
    $pythonCmd = $venvPython
    Write-Host "[*] Found project virtualenv: $pythonCmd" -ForegroundColor Green
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

$pyScript = Join-Path $scriptDir "grill_me_automation.py"

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

Write-Host "[*] Launching: $pythonCmd $($argList -join ' ')" -ForegroundColor DarkGray
Write-Host ""

try {
    & $pythonCmd $argList
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "[+] Automation successfully completed! (Exit Code: 0)" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[!] Automation finished with exit code: $exitCode" -ForegroundColor Red
    }
    exit $exitCode
} catch {
    Write-Error "[!] Failed to execute automation script: $_"
    exit 1
}
