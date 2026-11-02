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

| File | Identity & Role | Step | Type |
| :--- | :--- | :--- | :--- |
| **`run_all_steps.bat`** | **1-Click Full Pipeline Runner:** Executes Step 1 -> Step 2 -> Step 3 end-to-end. | **1 + 2 + 3** | **MASTER RUNNER** |
| **`run_activating_grill_me_with_automation.bat`** | Canonical complete 3-step batch launcher. | **1 + 2 + 3** | **MASTER RUNNER** |
| **`step1_find_and_focus.py`** | **Step 1:** Scans transcripts, parses questions, maximizes window & writes `target_chat.json`. | **Step 1** | **PRIMARY SCRIPT** |
| **`run_step1.bat`** | Quick 1-click shortcut runner for Step 1. | **Step 1** | **SHORTCUT** |
| **`run_step1_find_and_focus.bat`** | Full standalone batch launcher for Step 1. | **Step 1** | **STEP RUNNER** |
| **`step2_gui_chat_select.py`** | **Step 2:** CDP/DOM chat selection, smooth glide & chat pane focus (`Ctrl + L`). | **Step 2** | **PRIMARY SCRIPT** |
| **`run_step2.bat`** | Quick 1-click shortcut runner for Step 2. | **Step 2** | **SHORTCUT** |
| **`run_step2_gui_chat_select.bat`** | Full standalone batch launcher for Step 2. | **Step 2** | **STEP RUNNER** |
| **`run_activating_grill_me.bat`** | Two-step runner executing Step 1 + Step 2. | **Step 1 + 2** | **MODULAR RUNNER** |
| **`step3_keyboard_automation.py`** | **Step 3:** Keystroke automation, dynamic multi-question scaling & Enter submission. | **Step 3** | **PRIMARY SCRIPT** |
| **`run_step3.bat`** | Quick 1-click shortcut runner for Step 3. | **Step 3** | **SHORTCUT** |
| **`run_step3_keyboard_automation.bat`** | Full standalone batch launcher for Step 3. | **Step 3** | **STEP RUNNER** |
| **`run_step3_keyboard_automation.ps1`**| PowerShell runner for Step 3 with parameter binding. | **Step 3** | **PS1 RUNNER** |
| **`activating_grill_me.py`** | Master transcript parser & GUI activator engine. | **Master** | **UTILITY ENGINE** |
| **`grill_me_automation.py`** | Backward-compatibility alias delegating to `step3_keyboard_automation.py`. | **Step 3** | **LEGACY ALIAS** |
| **`run_grill_me.bat`** | Legacy alias launcher for Step 3. | **Step 3** | **LEGACY ALIAS** |
| **`run_grill_me.ps1`** | Legacy PowerShell launcher for Step 3. | **Step 3** | **LEGACY ALIAS** |
| **`target_chat.json`** | State file holding extracted question metadata, option choices, and conversation ID. | **State** | **PERSISTENCE** |
| **`config.json`** | Configuration file for coordinate fallbacks and automation timing. | **Config** | **CONFIG** |
| **`test_dynamic_questions.py`** | Automated unit & simulation test suite verifying multi-question scaling. | **Tests** | **TEST SUITE** |
| **`keyboard_automation/`** | Modular internal engine (Win32 API, Input Injector, Window Manager, Automator, CLI). | **Engine** | **PACKAGE** |
| **`archive/`** | Frozen certified reference archive. | **Archive** | **SNAPSHOT** |

---

## 🚀 Quick Start Guide

### Prerequisites
- Windows 10 or 11
- Python 3.8+ (Zero external dependencies strictly required; standard library ctypes / json / urllib used natively)

### Execution Options

#### 🌟 1. Run Complete 3-Step Pipeline (Step 1 -> Step 2 -> Step 3)
Double-click [`run_all_steps.bat`](./run_all_steps.bat) or run:
```cmd
run_all_steps.bat
```
*(Or use `run_activating_grill_me_with_automation.bat`)*

#### 🔍 2. Run Step 1 Standalone (Scan Transcripts & Focus Window)
```cmd
run_step1.bat
```

#### 🖱️ 3. Run Step 2 Standalone (CDP / DOM GUI Chat Select)
```cmd
run_step2.bat
```

#### ⌨️ 4. Run Step 3 Standalone (Keyboard Keystroke Automation)
```cmd
run_step3.bat
```
*(Or specify options: `python step3_keyboard_automation.py -c 3 -o 1`)*

#### 🧪 5. Run Verification Test Suite
```cmd
python test_dynamic_questions.py
```

---

## 🌟 Step-by-Step Technical Details

### Step 1: Scan Transcripts & Focus Window (`step1_find_and_focus.py`)
- Scans local Antigravity brain transcripts for pending `ask_question` tool calls.
- Extracts `conversation_id`, question text, choices, recommended options, and timestamp.
- Saves state into local `target_chat.json` adhering to Department 06 API JSON envelopes.
- Safely un-minimizes (`SW_RESTORE`) and maximizes (`SW_MAXIMIZE`) the Antigravity window without restoring down.

### Step 2: GUI Chat Selection (`step2_gui_chat_select.py`)
- Reads `conversation_id` from local `target_chat.json`.
- Connects to Antigravity internal DevTools port via Chrome DevTools Protocol (CDP WebSocket).
- Locates sidebar chat item element via real-time DOM querying.
- Glides mouse with smooth Bezier curve and clicks to select the conversation.
- Dispatches `Ctrl + L` to bring focus directly into the chat input pane.

### Step 3: Keyboard Automation (`step3_keyboard_automation.py`)
- Automatically probes and detects questions from `target_chat.json`.
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
