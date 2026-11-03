# ⌨️ AutoSelect-Commander - Unified Antigravity Chat Activation Suite

> **Pipeline Architecture:** **UNIFIED 3-STEP AUTOMATION SUITE**  
> **Subfolder:** `Keyboard Automation` (Consolidated, Fully Autonomous & Self-Contained)  
> **Target Environment:** Windows 10/11, Antigravity Chat UI, IDEs, and Web Terminals  
> **Architecture:** Zero-Dependency Native Windows ctypes (`SendInput` / `keybd_event` / `user32` Windowing) + CDP / DOM WebSocket Bridge + Dynamic Multi-Question Scaling + Win32 Restoration, Maximization & Focus Subsystem.  
> **Primary Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 🏛️ AutoSelect-Commander 3-Step Pipeline Architecture

All three steps of the AutoSelect-Commander chat activation pipeline are unified within this single, self-contained directory:

```
┌──────────────────────────────────────────────────────────────────────────┐
│              AutoSelect-Commander 3-Step Unified Architecture             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Step 1: Scan & Focus] ──────> [Step 2: GUI Chat Select] ─────>         │
│  `step1_find_and_focus.py`       `step2_gui_chat_select.py`              │
│  - Scan brain transcripts        - Chrome DevTools (CDP) WebSocket       │
│  - Extract questions & choices   - Smooth Bezier mouse glide & click     │
│  - Persist target_chat.json      - Focuses chat pane (Ctrl + L)          │
│  - Safe maximize & focus window                                          │
│                                                                          │
│  ──────────────────────────────────────────────────────────────>         │
│  [Step 3: Keyboard Automation]                                           │
│  `step3_keyboard_automation.py`                                          │
│  - Window safety verification & foreground lock bypass                   │
│  - Auto-reads target_chat.json for dynamic question count N             │
│  - Option navigation: Ctrl+L -> Shift+Tab -> Option Key                  │
│  - Dynamic Wizard Progression: Enter confirms selection & advances on Q1..QN-1, submits on QN │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Topology & Runners Directory

### 🏢 Root / Common Infrastructure (Shared by All Steps)
| File / Folder | Role & Description | Type |
| :--- | :--- | :--- |
| **`target_chat.json`** | Shared state file holding extracted question metadata, option choices, and active conversation ID. | **COMMON STATE** |
| **`run_all_steps.bat`** | **Single 1-Click Full Pipeline Master Runner:** Auto-initializes `.venv` and executes Step 1 -> Step 2 -> Step 3 end-to-end. | **MASTER RUNNER** |
| **`setup_env.bat`** | **Dedicated Self-Healing Environment Setup:** Automatically creates `Keyboard Automation\.venv` and installs dependencies. | **SETUP RUNNER** |
| **`requirements.txt`** | Dedicated Python dependencies (`pyautogui`, `psutil`) for Keyboard Automation. | **DEPENDENCIES** |
| **`activating_grill_me.py`** | Master transcript parser & GUI activator engine. | **ORCHESTRATOR** |
| **`config.json`** | Configuration file for coordinate fallbacks and automation timing. | **CONFIG** |
| **`keyboard_automation/`** | Modular internal engine (Win32 API, Input Injector, Window Manager, Automator, CLI). | **SHARED ENGINE** |
| **`prompts/`** | Architectural prompts and specifications. | **DOCUMENTATION** |

---

### 🛡️ Step 0: AntiGravity Detector (`step_0_antigravity_detector/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`antigravity_detector_core.py`** | Modular detector engine: process inspection, window enumeration, browser filter & Step 1 launcher. | **CORE ENGINE** |
| **`step0_antigravity_detector_prod.py`** | Production runner: 5-minute polling interval, fully headless background daemon with auto-trigger. | **PROD SCRIPT** |
| **`step0_antigravity_detector_test.py`** | Testing runner: 10-second polling interval with live console telemetry and `--once` single-shot support. | **TEST SCRIPT** |
| **`run_step0_prod.bat`** | 1-click standalone production launcher for Step 0 (5-min polling). | **STEP RUNNER** |
| **`run_step0_test.bat`** | 1-click standalone testing launcher for Step 0 with rich telemetry. | **STEP RUNNER** |
| **`test_step0_detector.py`** | Automated unit test suite verifying data structures, intervals, and detection logic. | **UNIT TEST** |

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
| **`step3_keyboard_automation.py`** | Keystroke automation, dynamic multi-question scaling & Enter submission. | **PRIMARY SCRIPT** |
| **`run_step3.bat`** | Dedicated 1-click standalone runner for Step 3. | **STEP RUNNER** |
| **`grill_me_automation.py`** | Backward-compatibility alias delegating to `step3_keyboard_automation.py`. | **LEGACY ALIAS** |

---

## 🚀 Quick Start Guide

### Prerequisites
- Windows 10 or 11
- Python 3.8+ (Automatically configures dedicated self-healing virtual environment in `Keyboard Automation\.venv` via `setup_env.bat`)

### Execution Options

#### 🛡️ 0. Run Step 0 Standalone (AntiGravity Detector)
- **Production Runner (5-Minute Interval, Silent Background):**
  ```cmd
  step_0_antigravity_detector\run_step0_prod.bat
  ```
- **Testing Runner (10-Second Interval with Live Console Telemetry):**
  ```cmd
  step_0_antigravity_detector\run_step0_test.bat
  ```
- **Single-Shot Verification Check (No Polling):**
  ```cmd
  .\.venv\Scripts\python.exe step_0_antigravity_detector\step0_antigravity_detector_test.py --once --no-launch
  ```

#### 🌟 1. Run Complete 3-Step Pipeline (Step 1 -> Step 2 -> Step 3)
Double-click [`run_all_steps.bat`](./run_all_steps.bat) or run:
```cmd
run_all_steps.bat
```

#### 🔍 2. Run Step 1 Standalone (Chat Identifier)
```cmd
step_1_chat_identifier\run_step1.bat
```

#### 🖱️ 3. Run Step 2 Standalone (Chat and Focus)
```cmd
step_2_chat_and_focus\run_step2.bat
```

#### ⌨️ 4. Run Step 3 Standalone (Select the Recommendation)
```cmd
step_3_select_the_recommendation\run_step3.bat
```
*(Or specify options: `python step_3_select_the_recommendation\step3_keyboard_automation.py -c 3 -o 1`)*

---

## 🌟 Step-by-Step Technical Details

### Step 1: Scan Transcripts & Focus Window (`step_1_chat_identifier/step1_find_and_focus.py`)
- Scans local Antigravity brain transcripts for pending `ask_question` tool calls.
- Extracts `conversation_id`, question text, choices, recommended options, and timestamp.
- Saves state into root `target_chat.json` adhering to Department 06 API JSON envelopes.
- Safely un-minimizes (`SW_RESTORE`) and maximizes (`SW_MAXIMIZE`) the Antigravity window without restoring down.

### Step 2: GUI Chat Selection (`step_2_chat_and_focus/step2_gui_chat_select.py`)
- Reads `conversation_id` from root `target_chat.json`.
- Connects to Antigravity internal DevTools port via Chrome DevTools Protocol (CDP WebSocket).
- Locates sidebar chat item element via real-time DOM querying.
- Glides mouse with smooth Bezier curve and clicks to select the conversation.
- Dispatches `Ctrl + L` to bring focus directly into the chat input pane.

### Step 3: Keyboard Automation (`step_3_select_the_recommendation/step3_keyboard_automation.py`)
- Automatically probes and detects questions from root `target_chat.json`.
- Injects native Windows `SendInput` / `keybd_event` sequence:
  - Step 1: `Ctrl + L` (Chat box focus)
  - Step 2: `Shift + Tab` (Navigate back to option list)
  - Step 3: Key `1`, `2`, `3`... (Select Option)
  - Step 4: `Enter` Gate: **Suppressed** on intermediate questions (Q1..QN-1), **Fired ONLY** on final question (QN).

---

## 🛡️ Verification & Test Suite Passing
- Zero external package requirements for core pipeline.
- Win32 API ctypes foreground lock bypass with browser disqualification gatekeeper.
- Unit and simulation tests 100% passing (`test_dynamic_questions.py`).
