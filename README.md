# AutoSelect Antigravity 🎯⚡
===================================

> **Autonomous Multi-Modal Automation Suite for Antigravity AI Coding Agents**  
> **Author & Lead Architect:** Atul Verma ([@aiprincekumar](https://github.com/aiprincekumar) / [aiprincekumar010100@gmail.com](mailto:aiprincekumar010100@gmail.com))  
> **Target Environment:** Google AntiGravity IDE & Windows 11 / 10 Enterprise

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Node: >=16.0.0](https://img.shields.io/badge/Node.js-%3E%3D16.0.0-green.svg)](https://nodejs.org/)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-blue.svg)](https://www.microsoft.com/)
[![Subsystems: Keyboard + Mouse](https://img.shields.io/badge/Subsystems-Keyboard%20%2B%20Mouse-purple.svg)](#-system-architecture)
[![Dashboard: Port 8501](https://img.shields.io/badge/Dashboard-Port%208501%20Active-emerald.svg)](#-real-time-telemetry--control-dashboard)
[![Fail-Safe: 60s Sentinel](https://img.shields.io/badge/Fail--Safe-60s%20Auto--Pause%20Sentinel-amber.svg)](#2-3-state-real-time-process-control)
[![NPX: 1-Click Run](https://img.shields.io/badge/NPX-1--Click%20Hands--Free-gradient.svg)](#-100-hands-free-quick-start-1-click-run-on-any-pc)

---

## 🚀 100% Hands-Free Quick Start (1-Click Run on Any PC)

AutoSelect Antigravity provides an autonomous, zero-configuration bootstrap harness. Run on any Windows machine with Node.js and Python installed without manual environment configuration, pip dependency hunting, or background service tinkering.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      100% HANDS-FREE AUTONOMOUS BOOTSTRAP                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [1/5] Python 3 Detection  ──►  [2/5] Isolated .venv Setup                      │
│  [3/5] Pip Dependencies    ──►  [4/5] Windows Startup Registration              │
│  [5/5] Port 8501 Daemon    ──►  🟢 Default Web Browser Auto-Launch             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### ⚡ Option 1: Instant Zero-Install Run via NPX (Recommended)
Run directly from GitHub without cloning or manual package installation:
```bash
npx github:aiprincekumar/AutoSelect-Antigravity
```
*Automatically executes the 5-step setup pipeline, starts the headless background control daemon on port 8501, and launches the visual dashboard in your default browser.*

---

### 📦 Option 2: Global NPM CLI Installation
Install globally as a system-wide CLI utility to control AutoSelect from any terminal:
```bash
npm install -g github:aiprincekumar/AutoSelect-Antigravity
autoselect-antigravity
```

#### CLI Options & Flags:
| Command / Flag | Purpose |
| :--- | :--- |
| `autoselect-antigravity` | Full autonomous bootstrap + background server + browser launch |
| `autoselect-antigravity --no-browser` | Launch headless background daemon without popping up a browser window |
| `autoselect-antigravity --status` | Check system Python, `.venv`, Port 8501 server health, and Auto-Start status |
| `autoselect-antigravity --port 8501` | Specify custom HTTP control daemon port (default: `8501`) |
| `autoselect-antigravity --help` | Display interactive CLI usage documentation and flags |

---

### 🔄 Option 3: 1-Line Windows Auto-Start Registration (Login Persistence)
To guarantee the automation daemon and visual telemetry server are always alive whenever your PC boots or restarts, execute the 1-line Windows Startup registration command:

#### Pure Windows CMD (Command Prompt):
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk\");$s.TargetPath=\"wscript.exe\";$s.Arguments=\"`\"$((Get-Item .).FullName)\Keyboard Automation\launchers\autostart_dashboard_silent.vbs`\" --no-browser\";$s.WorkingDirectory=\"$((Get-Item .).FullName)\Keyboard Automation\";$s.Description=\"Keyboard Automation Dashboard Server Auto-Start\";$s.WindowStyle=7;$s.Save();Write-Host \"[SUCCESS] Auto-Start registered in Windows Startup folder!\""
```

#### Pure PowerShell:
```powershell
$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk");$s.TargetPath='wscript.exe';$s.Arguments="`"$((Get-Item .).FullName)\Keyboard Automation\launchers\autostart_dashboard_silent.vbs`\" --no-browser";$s.WorkingDirectory="$((Get-Item .).FullName)\Keyboard Automation";$s.Description='Keyboard Automation Dashboard Server Auto-Start';$s.WindowStyle=7;$s.Save();Write-Host "[SUCCESS] Auto-Start registered in Windows Startup folder!"
```

> [!NOTE]
> The auto-start registration places a silent Windows shortcut into `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk`. Upon Windows user login, `wscript.exe` runs `autostart_dashboard_silent.vbs` completely hidden (Window Style 7/0) with `--no-browser`, keeping port 8501 listening invisibly in the background.

---

### ⚙️ Under the Hood: The 5-Step Autonomous Pipeline

Whenever `npx` or `autoselect-antigravity` is invoked, the self-healing Node.js runner (`Keyboard Automation/bin/cli.js`) coordinates 5 deterministic phases:

1. **[1/5] Python 3 Detection & Verification:**
   - Scans system PATH for available Python runtimes (`python`, `py -3`, `python3`).
   - Validates semantic version requirement ($\ge 3.8$, recommended $3.10+$).
   - If missing, provides immediate download guidance and gracefully halts.
2. **[2/5] Virtual Environment (`.venv`) Bootstrap:**
   - Checks for existing `.venv` inside `Keyboard Automation/`.
   - If absent, provisions a dedicated virtual environment (`python -m venv .venv`).
   - Runs `ensurepip` to verify standard package installer integrity.
3. **[3/5] Self-Healing Dependency Installation:**
   - Audits required packages against `requirements.txt` (`pyautogui`, `psutil`).
   - Performs fast import verification (`import pyautogui, psutil`). If already satisfied, bypasses installation in $<100\text{ms}$.
   - Otherwise, executes silent batch installation (`pip install -r requirements.txt -q`).
4. **[4/5] Hands-Free Windows Auto-Start Registration:**
   - On Windows systems, executes `step_4_reporting/autostart.py --enable` to register the startup shortcut.
   - Idempotent and non-destructive: updates target paths if the workspace folder was relocated.
5. **[5/5] Headless Background Server & Browser Launch:**
   - Performs an active HTTP socket probe on `http://127.0.0.1:8501/api/automation/status`.
   - If an instance is already listening, reuses the live daemon instantly.
   - If offline, spawns `start_dashboard_background.vbs` (or detached `pythonw.exe`) with Window Style `0` (100% windowless background execution).
   - Polls socket readiness until HTTP 200 is confirmed, then automatically opens the default web browser to `http://127.0.0.1:8501/`.

---

## 🌟 Executive Summary

When running long autonomous coding workflows with **Google AntiGravity** (such as overnight refactoring, continuous test suite execution, or Git push verification gates), the AI assistant presents interactive decision prompts via `ask_question` (e.g. `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना`). If the developer steps away, the session blocks indefinitely.

**AutoSelect Antigravity** eliminates this bottleneck with two decoupled, production-grade automation subsystems:

1. **Keyboard Automation (`Keyboard Automation/`):**
   - High-throughput transcript parsing and Win32 `SendInput` keystroke automation.
   - Clean 4-step modular pipeline orchestrated by Step 9 Complete Automation.
   - **Local Control Daemon & Visual Dashboard (Port 8501)** with live Server Health Bridge, 3-state real-time process monitoring (`🟢 Active` / `⏸️ Paused` / `⚪ Inactive`), and automatic 60-second user activity auto-pause sentinel (`LastActivitySentinel`).
   - Headless background launcher (`start_dashboard_background.vbs` / `launchers/`) for persistent operation independent of console windows.
   - Dedicated runtime state architecture (`state/target_chat.json`, `state/last_selection_state.json`) isolating state from project root.

2. **Mouse Automation (`Mouse Automation/`):**
   - Autonomous computer vision & Windows Native WinRT OCR (`Windows.Media.Ocr`, <50ms text recognition).
   - Natural human-like Bezier cursor trajectory with 80ms firm mouse click.
   - Always-on-top floating HUD countdown overlay (`⏱️ AutoSelect-Commander: 8.2s remaining`).
   - Hardware-level physical mouse interrupt fail-safe (>15px displacement aborts instantly).

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AUTOCONNECT / GRILL-ME SUITE                          │
│                   AutoSelect Antigravity (Atul Verma)                           │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
     ┌─────────────────────────────────┴─────────────────────────────────┐
     ▼                                                                   ▼
┌──────────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐
│             KEYBOARD AUTOMATION              │ │              MOUSE AUTOMATION               │
│      (Transcript & Keystroke Pipeline)       │ │     (Computer Vision & WinRT OCR Engine)    │
├──────────────────────────────────────────────┤ ├─────────────────────────────────────────────┤
│ • Step 0: AntiGravity Detector & Process Mon │ │ • WinRT OCR Engine (<50ms Latin/Devanagari) │
│ • Step 1: Chat Identifier & Window Maximizer │ │ • Bezier Glide & 80ms Firm Click Pipeline   │
│ • Step 2: GUI Chat Select & Focus (CDP/DOM)  │ │ • Top-Most Floating HUD Overlay             │
│ • Step 3: SendInput Keystroke Recommendation │ │ • Hardware Mouse-Move Instant Fail-Safe     │
│ • Step 4: Visual Dashboard & REST Daemon     │ │ • 1-Click Interactive Menu (run.bat 1/2/3)  │
│ • Step 9: Complete Automation Master Hub     │ │ • Standalone Demo & Synthetic Test Harness  │
│ • CLI Harness: NPX / Global NPM Wrapper      │ │                                             │
└──────────────────────┬───────────────────────┘ └─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│        LOCAL CONTROL SERVER BRIDGE & VISUAL TELEMETRY DASHBOARD (PORT 8501)     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • RESTful Control: GET/POST /api/automation/status, /api/automation/start/stop  │
│ • Server Health Pill: 🟢 Server Online | 🔴 Server Offline                      │
│ • 3-State Execution:  🟢 Active | ⏸️ Paused (User Active <60s) | ⚪ Inactive     │
│ • Silent Runner:     start_dashboard_background.vbs (Headless Window Style 0)   │
│ • Startup Shortcut:  %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Real-Time Telemetry & Control Dashboard

The visual dashboard (`step_4_reporting/reports/dashboard.html`) connects directly to the local Python control daemon (`dashboard_server.py`) running on `http://127.0.0.1:8501/`.

### 1. Live Server Health Bridge Indicator
- **🟢 Server Online:** Displays when the backend control daemon is alive and responding. Enables direct 1-click Start/Stop from the browser.
- **🔴 Server Offline:** Displays if the server is stopped or closed. The dashboard maintains an automatic background reconnect poller (every 3 seconds). The instant the server starts, the UI automatically transitions to Online and triggers:
  > `🟢 Server Reconnected! Control daemon is active on port 8501.`

### 2. 3-State Real-Time Process Control
| Status Badge | Trigger Condition | System Behavior |
| :--- | :--- | :--- |
| `🟢 Active` | Daemon started, user idle ≥ 60s | Scans transcripts, auto-focuses chat, selects Option 1 `(Recommended)`. |
| `⏸️ Paused (User Active)` | Physical mouse or keyboard input < 60s | Automation yields 100% control to developer. Automatically resumes when idle reaches 60s. |
| `⚪ Inactive` | Process stopped or test run finished | Daemon idle, awaiting 1-click trigger or scheduled cron. |

### 3. Persistent Headless Runner (`start_dashboard_background.vbs`)
To prevent the control server from terminating when a command prompt window is closed, a lightweight Windows VBScript runner is provided:
- Launches `dashboard_server.py` headlessly with window style `0` (completely hidden).
- If port 8501 is already running, reuses it immediately and opens the default web browser.
- Persists across terminal sessions as a background daemon.

---

## 📁 Repository Directory Structure

```
AutoSelect Antigravity/
├── README.md                              # Master System Documentation (This file)
├── start_dashboard_background.vbs         # Root 1-Click Silent Background Dashboard Launcher
├── .gitignore                             # Universal Git Exclusions
│
├── Keyboard Automation/                   # Subsystem A: Transcript & Keystroke Pipeline
│   ├── package.json                       # Node.js Package Manifest (autoselect-antigravity CLI)
│   ├── requirements.txt                   # Python Dependencies (pyautogui, psutil, pywin32)
│   ├── project_feature_memory.md          # 7-Column Diagnostic Matrix & Architecture Memory
│   ├── run_dashboard.bat                  # Root Launcher for Dashboard Server
│   ├── setup_env.bat                      # Self-Healing .venv Environment Initializer
│   ├── start_dashboard_background.vbs     # Local Silent Background Server Launcher
│   │
│   ├── bin/                               # CLI Executable Distribution
│   │   └── cli.js                         # 100% Hands-Free NPM/NPX 5-Step Autonomous Runner
│   │
│   ├── launchers/                         # Centralized Windows Execution Launchers
│   │   ├── autostart_dashboard_silent.vbs # Windows Startup Folder Headless Daemon Wrapper
│   │   ├── enable_autostart.bat           # 1-Click Windows Auto-Start Enabler
│   │   ├── disable_autostart.bat          # 1-Click Windows Auto-Start Disabler
│   │   ├── check_autostart.bat            # Auto-Start Verification & Diagnostic Utility
│   │   ├── open_modern_dashboard.bat      # Launches Modern Port 8501 Web Interface
│   │   ├── open_classic_dashboard.bat     # Launches Legacy Fallback UI
│   │   ├── run_automation_prod.bat        # Production Pipeline Execution
│   │   ├── run_automation_test.bat        # Single-Shot Test Pipeline Execution
│   │   ├── run_dashboard.bat              # Centralized Dashboard Launcher
│   │   ├── setup_env.bat                  # Launcher Environment Initializer
│   │   └── start_dashboard_background.vbs # Windowless VBScript Background Daemon
│   │
│   ├── state/                             # Dedicated Ephemeral Runtime State Directory
│   │   ├── .gitkeep                       # Directory Persistence Anchor
│   │   ├── target_chat.json               # Detected Chat Window Bounds & PID State
│   │   └── last_selection_state.json      # Last Executed Option & Timestamp Cache
│   │
│   ├── core_engine/                       # Win32 API, Window Scoring, SendInput Engine
│   │   ├── win32_api.py                   # Win32 User32 Native API Bindings
│   │   ├── scoring.py                     # Window Heuristic Scoring Matrix (+1000 Process Score)
│   │   └── runtime_state.py               # Resilient Dual-Tier State File Path Resolver
│   │
│   ├── step_0_antigravity_detector/       # AntiGravity Process Inspection & 10s Sentinel
│   ├── step_1_chat_identifier/            # Transcript Parser, Maximizer & State Writer
│   ├── step_2_chat_and_focus/             # GUI Chat Select & CDP/DOM Focus
│   ├── step_3_select_the_recommendation/  # Keystroke Option Selection & Submission
│   │
│   ├── step_4_reporting/                  # Visual Dashboard, REST Server & Watcher
│   │   ├── dashboard_server.py            # Local HTTP/REST Server on Port 8501
│   │   ├── step4_reporting.py             # Dashboard Generator & Win32 Idle Watcher
│   │   ├── autostart.py                   # Windows Startup Shortcut Creator & Inspector
│   │   ├── run_dashboard.bat              # Local Launcher for Dashboard Server
│   │   └── reports/
│   │       └── dashboard.html             # Rich Interactive Visual Telemetry Interface
│   │
│   └── step_9_complete_automation/        # Master Orchestrator Hub
│       ├── complete_automation.py         # 4-Step Pipeline Orchestration Engine
│       ├── config.json                    # Unified System Runtime Configuration
│       ├── open_dashboard.bat             # 1-Click Dashboard & Server Launcher
│       ├── run_complete_automation_prod.bat # Continuous Production Background Sentinel
│       └── run_complete_automation_test.bat # Single-Shot Smoke Test
│
└── Mouse Automation/                      # Subsystem B: Visual OCR & Mouse Auto-Selector
    ├── run.bat                            # 1-Click Interactive Menu (Demo / Sentinel / Diag)
    ├── run_demo.bat                       # Standalone Visual Demo Launcher
    ├── auto_commander.py                  # Background Sentinel Entry Point
    ├── standalone_demo.py                 # Synthetic Decision Card & HUD Showcase
    ├── config.json                        # Detection Thresholds & Coordinate Offsets
    └── auto_commander/                    # Modular Engine (WinRT OCR, HUD, Input, Flow)
```

---

## 🛠️ Step-by-Step Manual Operations

If you prefer operating directly via the command line or batch scripts rather than NPX:

### 1. Initialize Python Virtual Environment
Navigate to `Keyboard Automation` and run the self-healing setup script:
```cmd
cd "Keyboard Automation"
setup_env.bat
```

### 2. Launch Visual Dashboard & Control Server
Choose between persistent background execution or foreground console mode:

- **1-Click Persistent Background (Recommended):**
  Double-click `start_dashboard_background.vbs` or run:
  ```cmd
  wscript start_dashboard_background.vbs
  ```
  *The dashboard opens at `http://127.0.0.1:8501/` and remains active even if all terminals are closed.*

- **1-Click Centralized Launcher:**
  ```cmd
  launchers\run_dashboard.bat
  ```
  *Automatically detects if port 8501 is already active; reuses existing instance or starts a persistent background server.*

- **Foreground Debug Mode:**
  ```cmd
  run_dashboard.bat --fg
  ```

### 3. Run Keyboard Automation Pipeline Directly
- **Production Autonomous Monitoring:**
  ```cmd
  cd step_9_complete_automation
  run_complete_automation_prod.bat
  ```
- **Single-Shot Verification Test:**
  ```cmd
  run_complete_automation_test.bat
  ```

### 4. Run Mouse Automation Sentinel
Navigate to `Mouse Automation` and execute:
```cmd
cd "..\Mouse Automation"
run.bat 1    # Live Visual Demo Mode with Top-Most HUD
run.bat 2    # Autonomous Background Sentinel
run.bat 3    # Screen & OCR Diagnostics
```

---

## 🧪 Automated Test Suite & Quality Gates

The system includes comprehensive automated unit tests covering all modular steps, server endpoints, CORS headers, process lifecycle, runtime state resolution, and configuration syncing:

```cmd
cd "Keyboard Automation"
.venv\Scripts\python.exe -m unittest discover
```
or via pytest:
```cmd
pytest
```
**Test Gate Certification:** 131/131 Tests Passing (100% Green / Grade A+ Certified).

---

## 🛡️ Enterprise Compliance

- **Department 02 (Solution Architecture):** Clean Architecture pipeline with complete decoupling between transcript analysis, input injection, dedicated ephemeral runtime state (`state/`), and visual telemetry.
- **Department 05 (Frontend Engineering):** Reactive client-side dashboard with live server bridge health polling, instant auto-reconnect, and zero DOM memory leaks.
- **Department 06 (Backend & API Engineering):** Multi-threaded Python control daemon with standardized JSON envelopes (`{"success": true, "data": ...}`), universal CORS support (`*`), and graceful PID tree termination.
- **Department 07 (Technical Documentation):** Zero-drift comprehensive documentation, copy-paste ready 1-line commands, architectural diagrams, and verified test gates.
- **Universal Rule 26 (Zero-Hang Standard):** Clean process tree teardown (`taskkill /F /T /PID`) preventing zombie background threads or orphaned locks.

---

## 📄 License & Attribution

Created and maintained by **Atul Verma** ([@aiprincekumar](https://github.com/aiprincekumar) / [aiprincekumar010100@gmail.com](mailto:aiprincekumar010100@gmail.com)).  
Licensed under the [MIT License](LICENSE).
