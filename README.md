# AutoSelect Antigravity 🎯⚡
===================================

> **Autonomous Multi-Modal Automation Suite for Antigravity AI Coding Agents**  
> **Author & Lead Architect:** Atul Verma ([@aiprincekumar](https://github.com/aiprincekumar) / [aiprincekumar010100@gmail.com](mailto:aiprincekumar010100@gmail.com))  
> **Target Environment:** Google AntiGravity IDE & Windows 11 / 10 Enterprise

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-blue.svg)](https://www.microsoft.com/)
[![Subsystems: Keyboard + Mouse](https://img.shields.io/badge/Subsystems-Keyboard%20%2B%20Mouse-purple.svg)](#-subsystems-overview)
[![Dashboard: Port 8501](https://img.shields.io/badge/Dashboard-Port%208501%20Active-emerald.svg)](#-real-time-telemetry--control-dashboard)
[![Fail-Safe: 60s Sentinel](https://img.shields.io/badge/Fail--Safe-60s%20Auto--Pause%20Sentinel-amber.svg)](#3-state-real-time-process-control)

---

## 🌟 Executive Summary

When running long autonomous coding workflows with **Google AntiGravity** (such as overnight refactoring, continuous test suite execution, or Git push verification gates), the AI assistant presents interactive decision prompts via `ask_question` (e.g. `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना`). If the developer steps away, the session blocks indefinitely.

**AutoSelect Antigravity** eliminates this bottleneck with two decoupled, production-grade automation subsystems:

1. **Keyboard Automation (`Keyboard Automation/`):**
   - High-throughput transcript parsing and Win32 `SendInput` keystroke automation.
   - Clean 4-step modular pipeline orchestrated by Step 9 Complete Automation.
   - **Local Control Daemon & Visual Dashboard (Port 8501)** with live Server Health Bridge, 3-state real-time process monitoring (`🟢 Active` / `⏸️ Paused` / `⚪ Inactive`), and automatic 60-second user activity auto-pause sentinel (`LastActivitySentinel`).
   - Headless background launcher (`start_dashboard_background.vbs`) for persistent operation independent of console windows.

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
└──────────────────────┬───────────────────────┘ └─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│        LOCAL CONTROL SERVER BRIDGE & VISUAL TELEMETRY DASHBOARD (PORT 8501)     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • RESTful Control: GET/POST /api/automation/status, /api/automation/start/stop  │
│ • Server Health Pill: 🟢 Server Bridge Online (8501) | 🔴 Server Bridge Offline  │
│ • 3-State Execution:  🟢 Active | ⏸️ Paused (User Active <60s) | ⚪ Inactive     │
│ • Silent Runner:     start_dashboard_background.vbs (Headless Window Style 0)   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Real-Time Telemetry & Control Dashboard

The visual dashboard (`step_4_reporting/reports/dashboard.html`) connects directly to the local Python control daemon (`dashboard_server.py`) running on `http://127.0.0.1:8501/`.

### 1. Live Server Health Bridge Indicator
- **🟢 Server Bridge Online (Port 8501):** Displays when the backend control daemon is alive and responding. Enables direct 1-click Start/Stop from the browser.
- **🔴 Server Bridge Offline:** Displays if the server is stopped or closed. The dashboard maintains an automatic background reconnect poller (every 3 seconds). The instant the server starts, the UI automatically transitions to Online and triggers:
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
├── start_dashboard_background.vbs         # 1-Click Silent Background Dashboard Launcher
├── .gitignore                             # Universal Git Exclusions
│
├── Keyboard Automation/                   # Subsystem A: Transcript & Keystroke Pipeline
│   ├── run_dashboard.bat                  # 1-Click Dashboard Server Launcher (checks port 8501)
│   ├── start_dashboard_background.vbs     # Local Silent Background Server Launcher
│   ├── setup_env.bat                      # Self-Healing .venv Environment Initializer
│   ├── requirements.txt                   # Subsystem Dependencies (pyautogui, psutil)
│   ├── project_feature_memory.md          # 7-Column Diagnostic Matrix & Architecture Log
│   ├── core_engine/                       # Win32 API, Window Scoring, SendInput Engine
│   ├── step_0_antigravity_detector/       # AntiGravity Process Inspection & 10s Sentinel
│   ├── step_1_chat_identifier/            # Transcript Parser, Maximizer & State Writer
│   ├── step_2_chat_and_focus/             # GUI Chat Select & CDP/DOM Focus
│   ├── step_3_select_the_recommendation/  # Keystroke Option Selection & Submission
│   ├── step_4_reporting/                  # Visual Dashboard, REST Server & Watcher
│   │   ├── dashboard_server.py            # Local HTTP/REST Server on Port 8501
│   │   ├── step4_reporting.py             # Dashboard Generator & Win32 Idle Watcher
│   │   ├── run_dashboard.bat              # Local Launcher for Dashboard Server
│   │   └── reports/dashboard.html         # Rich Interactive Visual Telemetry Interface
│   └── step_9_complete_automation/        # Master Orchestrator Hub
│       ├── complete_automation.py         # 4-Step Pipeline Orchestration Engine
│       ├── config.json                    # Unified System Runtime Configuration
│       └── open_dashboard.bat             # 1-Click Dashboard & Server Launcher
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

## 🚀 Quick Start Guide

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

- **1-Click Batch Launcher:**
  ```cmd
  run_dashboard.bat
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

## 🧪 Automated Test Suite

The system includes comprehensive automated unit tests covering all modular steps, server endpoints, CORS headers, process lifecycle, and configuration syncing:

```cmd
cd "Keyboard Automation"
.venv\Scripts\python.exe -m unittest discover
```
**Test Gate Certification:** 94/94+ Tests Passing (100% Green).

---

## 🛡️ Enterprise Compliance

- **Department 02 (Solution Architecture):** Clean Architecture pipeline with complete decoupling between transcript analysis, input injection, and visual telemetry.
- **Department 05 (Frontend Engineering):** Reactive client-side dashboard with live server bridge health polling, instant auto-reconnect, and zero DOM memory leaks.
- **Department 06 (Backend & API Engineering):** Multi-threaded Python control daemon with standardized JSON envelopes (`{"success": true, "data": ...}`), universal CORS support (`*`), and graceful PID tree termination.
- **Universal Rule 26 (Zero-Hang Standard):** Clean process tree teardown (`taskkill /F /T /PID`) preventing zombie background threads or orphaned locks.

---

## 📄 License & Attribution

Created and maintained by **Atul Verma** ([@aiprincekumar](https://github.com/aiprincekumar) / `aiprincekumar010100@gmail.com`).  
Licensed under the [MIT License](LICENSE).
