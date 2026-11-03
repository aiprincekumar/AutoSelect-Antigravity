# Keyboard Automation Suite - AutoSelect-Commander
===================================================

Autonomous keyboard automation, window management, and chat selection pipeline for Google Anti-Gravity and AutoSelect-Commander.

---

## 🏛️ Architecture Overview

The system is organized into a modular Clean Architecture pipeline adhering to **Department 02 (Solution Architecture)** and **Department 06 (Backend & API Engineering)** standards:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE AUTOMATION (MASTER HUB)                     │
│         `Complete Automation/run_complete_automation_prod.bat`          │
│         `Complete Automation/run_complete_automation_test.bat`          │
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

### 🏢 Root Infrastructure (Clean & Minimal)
| File / Folder | Role & Description | Type |
| :--- | :--- | :--- |
| **`Complete Automation/`** | **Master User Interaction Hub:** Unified configuration (`config.json`), master controller (`complete_automation.py`), 1-click batch runners, and dashboard launcher. | **MASTER HUB** |
| **`core_engine/`** | **Core Automation Engine:** Win32 API bindings, SendInput injector, window discovery & scoring, automator sequence, and CDP client (renamed from `keyboard_automation`). | **CORE ENGINE** |
| **`keyboard_automation.py`** | **Backward Compatibility Proxy:** Transparent module delegating all calls and submodules to `core_engine/`. | **COMPATIBILITY PROXY** |
| **`target_chat.json`** | Shared runtime state file holding extracted question metadata, option choices, and active conversation ID. | **COMMON STATE** |
| **`last_selection_state.json`** | Runtime state backup synchronized with `target_chat.json`. | **COMMON STATE** |
| **`setup_env.bat`** | **Self-Healing Environment Setup:** Automatically creates `Keyboard Automation\.venv` and installs dependencies. | **SETUP RUNNER** |
| **`requirements.txt`** | Dedicated Python dependencies (`pyautogui`, `psutil`) for Keyboard Automation. | **DEPENDENCIES** |
| **`archive/legacy_monolith/`** | Dedicated archive holding the original monolithic script (`activating_grill_me.py`) and legacy coordinate configuration (`config.json`). | **ARCHIVE** |
| **`prompts/`** | Architectural specifications and prompt directives. | **DOCUMENTATION** |

---

### 🛡️ Step 0: AntiGravity Detector (`step_0_antigravity_detector/`)
| File | Role & Description | Type |
| :--- | :--- | :--- |
| **`antigravity_detector_core.py`** | Modular detector engine: process inspection, window enumeration, browser disqualification & brain scan. | **CORE ENGINE** |
| **`step0_antigravity_detector.py`** | **Canonical Unified Status Monitor:** Configurable polling interval (default 10s), 100% Screen Purity clean dashboard box, and `--once` single-shot verification. | **CANONICAL SCRIPT** |
| **`run_step0.bat`** | **1-Click Canonical Launcher:** Launches Step 0 with auto-detected `.venv` and clean terminal output. | **STEP RUNNER** |
| **`step0_antigravity_detector_test.py`** | Backward-compatibility alias delegating directly to `step0_antigravity_detector.py`. | **ALIAS SCRIPT** |
| **`run_step0_test.bat`** | Backward-compatibility batch alias calling `run_step0.bat`. | **ALIAS RUNNER** |
| **`test_step0_detector.py`** | Automated unit test suite verifying data structures, intervals, detection logic, and alias parity (19/19 passed). | **UNIT TEST** |

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
| **`run_step4.bat`** | Dedicated 1-click standalone runner to view the visual HTML dashboard. | **STEP RUNNER** |
| **`test_step4_reporting.py`** | Automated unit test suite verifying reporting logic and two-way modes (13/13 passed). | **UNIT TEST** |

---

## 🚀 Quick Start Guide

### Prerequisites
- Windows 10 or 11
- Python 3.8+ (Automatically bootstrapped via `setup_env.bat`)

### Execution Options

#### 🌟 1. Master Pipeline (Complete Automation)
Run the entire pipeline end-to-end with unified configuration and error handling:
- **Production Mode (5-min polling cadence):**
  ```cmd
  "Complete Automation\run_complete_automation_prod.bat"
  ```
- **Testing Mode (10-sec polling cadence):**
  ```cmd
  "Complete Automation\run_complete_automation_test.bat"
  ```
- **Open HTML Report Dashboard:**
  ```cmd
  "Complete Automation\open_dashboard.bat"
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
- All test suites passing 100%:
  - `Complete Automation/test_complete_automation.py` (12/12 passing)
  - `step_0_antigravity_detector/test_step0_detector.py` (19/19 passing)
  - `step_4_reporting/test_step4_reporting.py` (13/13 passing)
- Run all tests with one command:
  ```cmd
  .\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"
  ```
