# Keyboard Automation Suite - AutoSelect-Commander
===================================================

Autonomous keyboard automation, window management, and chat selection pipeline for Google Anti-Gravity and AutoSelect-Commander.

---

## 🚀 100% Hands-Free One-Liner Quick Start

Launch the complete AutoSelect Antigravity environment and visual dashboard immediately with zero manual configuration. Everything from Python verification to background service registration is 100% automated.

### ⚡ Instant Execution via NPX (Zero Install)
No local cloning or manual setup required. Run directly in any Windows terminal:
```bash
npx github:aiprincekumar/AutoSelect-Antigravity
```

### 📦 Global CLI Installation via NPM
Install once globally for permanent CLI command access across any terminal:
```bash
npm install -g github:aiprincekumar/AutoSelect-Antigravity
autoselect-antigravity
```

### ⚙️ What Happens Under the Hood (5-Step Automated Process)
When executed, the autonomous Node.js CLI harness performs the following sequence with zero human intervention:
1. **Python 3 Detection & Verification:** Scans the host system for a valid Python 3 installation (>= 3.8) via `python`, `py -3`, or `python3`.
2. **Virtual Environment Setup:** Automatically creates and validates an isolated `.venv` directory with scripts and path resolution.
3. **Dependency Installation:** Automatically bootstraps `pip` and installs required packages (`pyautogui`, `psutil`) from `requirements.txt`.
4. **Silent Windows Auto-Start Registration:** Registers a silent startup hook into `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` so the daemon runs on user login.
5. **Headless Background Server & Browser Launch:** Launches the dashboard server in the background on `http://127.0.0.1:8501/` using a windowless daemon and automatically opens your default web browser.

---

## 🔄 Windows Background Auto-Start

The AutoSelect Antigravity Dashboard Server can run silently in the background whenever Windows starts, ensuring telemetry and automation controls are instantly accessible without keeping terminal windows open.

### 🛡️ Zero-Console Silent Daemon Architecture
Unlike standard batch files that display a flashing or permanent black CMD console window, the auto-start system leverages **`wscript.exe`** paired with **`pythonw.exe`**:
- **Zero Console Window:** `wscript.exe` executes `launchers/autostart_dashboard_silent.vbs` hidden in the background (Window Style `0`).
- **Headless Execution:** Invokes Python via `pythonw.exe` with the `--no-browser` flag, keeping CPU usage minimal (< 0.1%) and preventing unwanted browser popups upon Windows login.
- **Port Resilience:** Automatically monitors port `8501` and avoids duplicate process spawning.

### 🖱️ 1-Click Batch Management (in `launchers/`)
| Script | Role & Behavior |
| :--- | :--- |
| **`launchers\enable_autostart.bat`** | Registers a silent background shortcut into `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` pointing to `autostart_dashboard_silent.vbs`. |
| **`launchers\disable_autostart.bat`** | Instantly unregisters and removes the shortcut from the Windows Startup folder. |
| **`launchers\check_autostart.bat`** | Inspects and displays the current registration status (`[ENABLED]` or `[DISABLED]`). |

### 💻 Portable 1-Line Commands (Any PC without opening folders)
Enable or disable auto-start directly from CMD or PowerShell:

#### Enable Auto-Start (1-Line):
- **Command Prompt (CMD):**
  ```cmd
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk\"); $sc.TargetPath = 'wscript.exe'; $sc.Arguments = '\"%cd%\launchers\autostart_dashboard_silent.vbs\" --no-browser'; $sc.WorkingDirectory = '%cd%'; $sc.Description = 'Keyboard Automation Dashboard Server - Background Auto-Start'; $sc.WindowStyle = 7; $sc.Save();"
  ```
- **PowerShell:**
  ```powershell
  $ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk"); $sc.TargetPath = 'wscript.exe'; $sc.Arguments = "`"$PWD\launchers\autostart_dashboard_silent.vbs`" --no-browser"; $sc.WorkingDirectory = "$PWD"; $sc.Description = 'Keyboard Automation Dashboard Server - Background Auto-Start'; $sc.WindowStyle = 7; $sc.Save()
  ```

#### Disable Auto-Start (1-Line):
- **Command Prompt (CMD):**
  ```cmd
  del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk"
  ```
- **PowerShell:**
  ```powershell
  Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Keyboard_Automation_Dashboard.lnk" -ErrorAction SilentlyContinue
  ```

---

## 🏛️ Architecture Overview

The system is organized into a modular Clean Architecture pipeline adhering to **Department 02 (Solution Architecture)** and **Department 06 (Backend & API Engineering)** standards:

```
┌──────────────────────────────────────────────────────────────────────────┐
│              STEP 9: COMPLETE AUTOMATION (MASTER HUB)                    │
│      `step_9_complete_automation/run_complete_automation_prod.bat`       │
│      `step_9_complete_automation/run_complete_automation_test.bat`       │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│        STEP 0         │ │        STEP 1         │ │        STEP 2         │
│ AntiGravity Detector  │ │    Chat Identifier    │ │     Chat & Focus      │
│ `step0_antigravity_   │ │ `step1_find_and_      │ │ `step2_gui_chat_      │
│     detector.py`      │ │      focus.py`        │ │      select.py`       │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌───────────────────────────────────────┐ ┌─────────────────────────────────┐
│                STEP 3                 │ │             STEP 4              │
│       Select the Recommendation       │ │       Reporting & Telemetry     │
│    `step3_keyboard_automation.py`     │ │      `step4_reporting.py`       │
│     (Powered by `core_engine/`)       │ │    (10s User Activity Watch)    │
└───────────────────────────────────────┘ └─────────────────────────────────┘
```

---

## 📁 File Topology & Directory Map

### 🏢 Root Infrastructure & CLI Manifest
| File / Folder | Role & Description | Type |
| :--- | :--- | :--- |
| **`package.json`** | Universal NPM/NPX package manifest registering the `autoselect-antigravity` CLI command. | **PACKAGE MANIFEST** |
| **`bin/cli.js`** | 100% hands-free autonomous Node.js CLI launcher: Python detection, `.venv` bootstrap, auto-start, server launch, and browser trigger. | **CLI ENTRYPOINT** |
| **`launchers/`** | **Dedicated Launchers Hub:** All 1-click batch (`.bat`) and VBScript (`.vbs`) execution runners, auto-start scripts, and dashboard shortcuts. | **LAUNCHERS HUB** |
| **`logs/`** | **Dedicated Logs Hub:** Centralized storage for all execution and server debug logs (`complete_automation.log`, `server_debug.log`, `scratch_err.log`). | **LOG ARCHITECTURE** |
| **`state/`** | **Dedicated Runtime State Hub:** Shared state files (`target_chat.json`, `last_selection_state.json`) with two-tier resolution. | **STATE HUB** |
| **`step_9_complete_automation/`** | **Master User Interaction Hub:** Unified configuration (`config.json`), master controller (`complete_automation.py`), and pipeline execution. | **MASTER HUB (STEP 9)** |
| **`core_engine/`** | **Core Automation Engine:** Win32 API bindings, SendInput injector, window discovery & scoring, automator sequence, and CDP client. | **CORE ENGINE** |
| **`requirements.txt`** | Dedicated Python dependencies (`pyautogui`, `psutil`) for Keyboard Automation. | **DEPENDENCIES** |
| **`project_feature_memory.md`** | Complete feature tracking, architectural changelog, and 7-column diagnostic matrix. | **LIVING MEMORY** |
| **`archive/legacy_monolith/`** | Dedicated archive holding legacy monolithic scripts (`activating_grill_me.py`, `keyboard_automation.py`) and legacy configs. | **ARCHIVE** |
| **`prompts/`** | Architectural specifications and prompt directives. | **DOCUMENTATION** |

---

### 🚀 Launchers Hub (`launchers/`)
| Script | Role & Description | Execution Mode |
| :--- | :--- | :--- |
| **`enable_autostart.bat`** | 1-click installer registering the silent dashboard daemon into Windows Startup. | Interactive Batch |
| **`disable_autostart.bat`** | 1-click uninstaller cleanly removing the dashboard daemon from Windows Startup. | Interactive Batch |
| **`check_autostart.bat`** | 1-click inspection checking if the dashboard daemon is currently registered. | Status Check |
| **`autostart_dashboard_silent.vbs`** | Zero-console VBScript daemon launcher invoking `start_dashboard_background.vbs --no-browser`. | Windowless VBS |
| **`start_dashboard_background.vbs`** | Windowless background runner invoking `dashboard_server.py` via `pythonw.exe`. | Windowless VBS |
| **`run_automation_prod.bat`** | 1-click launcher for Step 9 complete pipeline in Production mode (5-minute polling). | Batch Runner |
| **`run_automation_test.bat`** | 1-click launcher for Step 9 complete pipeline in Testing mode (10-second polling). | Batch Runner |
| **`run_all_steps.bat`** | Sequential execution runner testing Steps 0 through 4 end-to-end. | Batch Runner |
| **`run_dashboard.bat`** | 1-click launcher starting the local dashboard server and opening the browser. | Batch Runner |
| **`open_modern_dashboard.bat`** | 1-click launcher opening the modern interactive telemetry dashboard. | Browser Launcher |
| **`open_classic_dashboard.bat`** | 1-click launcher opening the classic telemetry dashboard. | Browser Launcher |
| **`setup_env.bat`** | 1-click environment setup script initializing `.venv` and installing `requirements.txt`. | Setup Utility |

---

### 🛡️ Step 0: AntiGravity Detector (`step_0_antigravity_detector/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`antigravity_detector_core.py`** | Modular detector engine: process inspection, window enumeration, browser disqualification & brain scan. | **CORE ENGINE** |
| **`step0_antigravity_detector.py`** | **Canonical Unified Status Monitor:** Configurable polling interval (default 10s), 100% Screen Purity clean dashboard box, and `--once` single-shot verification. | **CANONICAL SCRIPT** |
| **`run_step0.bat`** | **1-Click Canonical Launcher:** Launches Step 0 with auto-detected `.venv` and clean terminal output. | **STEP RUNNER** |
| **`step0_antigravity_detector_test.py`** | Backward-compatibility alias delegating directly to `step0_antigravity_detector.py`. | **ALIAS SCRIPT** |
| **`run_step0_test.bat`** | Backward-compatibility batch alias calling `run_step0.bat`. | **ALIAS RUNNER** |
| **`test_step0_detector.py`** | Automated unit test suite verifying data structures, intervals, detection logic, and alias parity (24/24 passed). | **UNIT TEST** |

---

### 🔍 Step 1: Chat Identifier (`step_1_chat_identifier/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`step1_find_and_focus.py`** | Scans transcripts, parses questions, maximizes window & writes root `target_chat.json`. | **PRIMARY SCRIPT** |
| **`run_step1.bat`** | Dedicated 1-click standalone runner for Step 1. | **STEP RUNNER** |

---

### 🖱️ Step 2: Chat and Focus (`step_2_chat_and_focus/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`step2_gui_chat_select.py`** | CDP/DOM chat selection, smooth glide & chat pane focus (`Ctrl + L`). | **PRIMARY SCRIPT** |
| **`run_step2.bat`** | Dedicated 1-click standalone runner for Step 2. | **STEP RUNNER** |

---

### ⌨️ Step 3: Select the Recommendation (`step_3_select_the_recommendation/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`step3_keyboard_automation.py`** | Keystroke automation, dynamic multi-question scaling & Enter submission (powered by `core_engine/`). | **PRIMARY SCRIPT** |
| **`run_step3.bat`** | Dedicated 1-click standalone runner for Step 3. | **STEP RUNNER** |
| **`grill_me_automation.py`** | Backward-compatibility alias delegating to `step3_keyboard_automation.py`. | **LEGACY ALIAS** |

---

### 📊 Step 4: Reporting & Visual Dashboard (`step_4_reporting/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`step4_reporting.py`** | Core reporting engine, persistent execution logging, and Win32 10s idle input watcher. | **PRIMARY SCRIPT** |
| **`dashboard_server.py`** | Local HTTP dashboard server with REST API (`/api/automation/status`) and auto-start manager. | **SERVER DAEMON** |
| **`autostart.py`** | Windows Startup shortcut configuration manager (`--enable`, `--disable`, `--status`). | **AUTOSTART UTILITY** |
| **`run_step4.bat`** | Dedicated 1-click standalone runner to view the visual HTML dashboard. | **STEP RUNNER** |
| **`test_step4_reporting.py`** | Automated unit test suite verifying reporting logic and two-way modes (35/35 passed). | **UNIT TEST** |
| **`test_dashboard_server.py`** | Automated unit test suite verifying REST API and HTTP endpoints (16/16 passed). | **UNIT TEST** |
| **`test_autostart.py`** | Automated unit test suite verifying Windows Startup shortcut creation and removal (9/9 passed). | **UNIT TEST** |
| **`test_modern_dashboard.py`** | Automated unit test suite verifying modern dashboard structure and theme rendering (4/4 passed). | **UNIT TEST** |

---

## 🚀 Manual & Standalone Pipeline Quick Start Guide

### Prerequisites
- Windows 10 or 11
- Python 3.8+ (Automatically bootstrapped via `launchers\setup_env.bat` or `npx github:aiprincekumar/AutoSelect-Antigravity`)

### Execution Options

#### 🌟 1. Master Pipeline (Step 9: Complete Automation)
Run the entire pipeline end-to-end with unified configuration and error handling:
- **Production Mode (5-min polling cadence):**
  ```cmd
  "launchers\run_automation_prod.bat"
  ```
  *(or via master folder: `"step_9_complete_automation\run_complete_automation_prod.bat"`)*
- **Testing Mode (10-sec polling cadence):**
  ```cmd
  "launchers\run_automation_test.bat"
  ```
  *(or via master folder: `"step_9_complete_automation\run_complete_automation_test.bat"`)*
- **Open HTML Report Dashboard:**
  ```cmd
  "launchers\run_dashboard.bat"
  ```

#### 🛡️ 2. Run Step 0 Standalone (AntiGravity Detector)
- **Unified Canonical Launcher (10-second polling cadence with Clean Dashboard):**
  ```cmd
  step_0_antigravity_detector\run_step0.bat
  ```
- **Single-Shot Verification Check (No Polling):**
  ```cmd
  .\.venv\Scripts\python.exe step_0_antigravity_detector\step0_antigravity_detector.py --once --no-pause
  ```

#### 🔍 3. Run Individual Steps Standalone
- **Step 1 (Chat Identifier):** `step_1_chat_identifier\run_step1.bat`
- **Step 2 (Chat and Focus):** `step_2_chat_and_focus\run_step2.bat`
- **Step 3 (Select Recommendation):** `step_3_select_the_recommendation\run_step3.bat`
- **Step 4 (Reporting Dashboard):** `step_4_reporting\run_step4.bat`

---

## 🛡️ Verification & Test Suite Passing
- **151/151 unit tests passed (100% pass rate)**:
  - `core_engine/test_automator_boundary.py` (20/20 passed)
  - `core_engine/test_config_manager.py` (14/14 passed)
  - `step_0_antigravity_detector/test_step0_detector.py` (24/24 passed)
  - `step_4_reporting/test_autostart.py` (9/9 passed)
  - `step_4_reporting/test_dashboard_server.py` (16/16 passed)
  - `step_4_reporting/test_modern_dashboard.py` (4/4 passed)
  - `step_4_reporting/test_step4_reporting.py` (35/35 passed)
  - `step_5_automation/test_sentinel.py` (8/8 passed)
  - `step_9_complete_automation/test_complete_automation.py` (21/21 passed)

- Run all tests with one command:
  ```cmd
  .\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"
  ```
