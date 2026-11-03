# Pipeline Master Memory & Architectural Ledger

> **Document Type:** Active Working Memory & Master Architecture Dossier (What Exists & How Steps Coordinate)  
> **Location:** `Keyboard Automation/prompts/pipeline_master_memory.md`  
> **Suite:** AutoSelect-Commander / Keyboard Automation  
> **Primary Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com` / [GitHub Profile](https://github.com/aiprincekumar))  
> **Operating Environment:** Windows 10/11 x64, Google Antigravity 2.0 IDE, Electron / Chrome DevTools Protocol (CDP RFC 6455)  
> **Standard:** Department 01 (Product Requirements), Department 02 (Solution Architecture), Department 06 (Backend & API Engineering), Department 07 (Technical Documentation) & Universal Rules  
> **Status:** ACTIVE PRODUCTION MASTER MEMORY (44/44 Unit Tests Certified)  

---

## 🏛️ 1. Executive System Manifest & Orchestration Topology

The **AutoSelect-Commander Keyboard Automation Suite** is an autonomous, clean-architecture automation pipeline engineered to detect, navigate to, and interactively answer pending `ask_question` (Grill-Me) questionnaires in Google Antigravity 2.0 sessions completely autonomously.

The suite is structured with a single master interaction hub (**Step 9**), an underlying low-level Win32 engine (**`core_engine/`**), and 5 specialized sequential steps (**Steps 0 through 4**):

```mermaid
flowchart TD
    subgraph MasterHub [Step 9: Complete Automation Hub (Master Orchestrator)]
        Hub[step_9_complete_automation/complete_automation.py]
        Config[step_9_complete_automation/config.json]
        LaunchProd[run_complete_automation_prod.bat]
        LaunchTest[run_complete_automation_test.bat]
        Config --> Hub
        LaunchProd --> Hub
        LaunchTest --> Hub
    end

    subgraph ConditionDetection [Step 0: AntiGravity Detector]
        Hub -->|Poll 300s / 10s| Step0[step_0_antigravity_detector/step0_antigravity_detector.py]
        Step0Core[antigravity_detector_core.py]
        Step0 -->|Two-Factor Trigger| Step0Core
        Step0Core -->|Condition: Antigravity Open + Pending Question| Hub
    end

    subgraph SequentialPipeline [Sequential Execution Pipeline]
        Hub -->|Trigger Matched| Step1[Step 1: Chat Identifier & Window Focus]
        Step1 -->|Exit Code 10: No Pending Chats| CancelFlow[Cancel Remaining Steps Cleanly]
        CancelFlow --> Hub

        Step1 -->|Exit Code 0: target_chat.json| Settle1[Settle 0.8s]
        Settle1 --> Step2[Step 2: GUI Chat Select & Pane Focus]
        Step2 -->|Exit Code 0: Window Focused| Settle2[Settle 0.8s]
        Settle2 --> Step3[Step 3: Select Recommendation]
        
        subgraph EngineLayer [Core Automation Engine]
            Step3 -->|Imports| CoreEngine[core_engine/ - Win32 SendInput & Window Manager]
        end

        Step3 -->|Exit Code 0: Golden Enter Gate Submitted| Settle3[Settle 0.8s]
        Settle3 --> Step4[Step 4: Reporting & Visual Dashboard]
        Step4 -->|Silent Persistence| JSONHistory[reports/automation_history.json]
        Step4 -->|Win32 10s Activity Watcher| HTMLDashboard[reports/dashboard.html]
    end
```

---

## 📋 2. Complete Step Inventory & Technical Footprint

### 🛡️ Step 0: AntiGravity Detector & Two-Factor Status Monitor
- **Directory:** `step_0_antigravity_detector/`
- **Purpose:** Continuous background status monitoring and condition detection.
- **Single Responsibility (Decoupled):** Step 0 detects Antigravity state and pending questions; it does **NOT** chain or execute Step 1. Chaining is strictly owned by Step 9.
- **Two-Factor Trigger Condition:**
  1. **Factor 1:** Antigravity IDE running and top-level window (`Chrome_WidgetWin_1`) present. Web browsers (`chrome.exe`, `msedge.exe`, `firefox.exe`, `brave.exe`) are strictly disqualified.
  2. **Factor 2:** Local transcript logs (`~/.gemini/antigravity/brain/`) contain an unanswered `ask_question` tool call.
- **100% Screen Purity Clean Dashboard Box:** Renders an ANSI-refreshed, border-aligned Unicode box in pure English without technical stdout noise.
- **Canonical Entrypoint:** `step0_antigravity_detector.py` and `run_step0.bat`. Supports configurable `--interval` (default 10s), `--once`, `--no-pause`, and `--json`.
- **Test Suite:** `test_step0_detector.py` (19/19 unit tests passing).

---

### 🔍 Step 1: Chat Identifier & Window Focus
- **Directory:** `step_1_chat_identifier/`
- **Purpose:** Brain transcript reverse-scanning, question/option extraction, and Win32 foreground lock bypass.
- **Zero-Truncation Priority:** Prioritizes `transcript_full.jsonl` over `transcript.jsonl` to ensure large questionnaires ($N \ge 4$) are never truncated.
- **Win32 Focus Bypass:** Combines `AllowSetForegroundWindow`, `AttachThreadInput`, Alt key pulse, and `SetForegroundWindow` to reliably bring Antigravity to the foreground, setting `SW_MAXIMIZE` safely.
- **Exit Code 10 Protocol:** If no unanswered `ask_question` exists, writes `status: "NO_PENDING_CHATS"` and `cancelled_remaining_steps: true` to `target_chat.json` and immediately exits with process code `10`.
- **Runner:** `run_step1.bat` / `step1_find_and_focus.py`.

---

### 🖱️ Step 2: GUI Chat Select & Input Pane Focus
- **Directory:** `step_2_chat_and_focus/`
- **Purpose:** Visual sidebar navigation, smooth cursor glide, precision click, and chat pane focus.
- **Cancellation Passthrough:** If `target_chat.json` contains `NO_PENDING_CHATS`, exits cleanly with code `0`.
- **3-Tier Discovery Engine:**
  - **Tier 1:** Chrome DevTools Protocol (CDP RFC 6455 WebSocket on port 9222) queries DOM element for `conversation_id`, computes physical screen coordinates, and glides cursor via 25-30 step Bezier curve.
  - **Tier 2:** SPA client router navigation via CDP runtime evaluation if item is virtualized off-screen.
  - **Tier 3:** Calibrated sidebar coordinate fallback from `config.json`.
- **Focus Keystroke:** Injects `Ctrl + L` to place OS keyboard focus into the chat input pane.
- **Runner:** `run_step2.bat` / `step2_gui_chat_select.py`.

---

### ⌨️ Step 3: Select Recommendation & Golden Enter Gate
- **Directory:** `step_3_select_the_recommendation/`
- **Purpose:** Pure native Win32 `SendInput` hardware keystroke injection and dynamic multi-question scaling.
- **Underlying Core:** Powered directly by `core_engine/` (`win32_api.py`, `window_manager.py`, `keystroke_injector.py`, `automator.py`).
- **Dynamic Multi-Question Progression Loop:**
  - For each question $q \in [1, N]$:
    - Step A: `Ctrl + L` (focus input pane) $\to$ settle 0.22s
    - Step B: `Shift + Tab` (reverse-tab to option button group) $\to$ settle 0.22s
    - Step C: Option Key (e.g. `'1'`, `'2'`) $\to$ settle 0.22s
    - **The Golden Enter Gate:**
      - If $q < N$ (intermediate question): **STRICTLY DO NOT PRESS ENTER!** (Pause 0.4s and proceed to next question).
      - If $q == N$ (final question): **PRESS ENTER!** (Commit and submit the entire batch questionnaire).
- **Safety Blacklist:** Blocks injection if active window is a console (`cmd.exe`, `powershell.exe`, `WindowsTerminal.exe`) or web browser.
- **Runner:** `run_step3.bat` / `step3_keyboard_automation.py`.

---

### 📊 Step 4: Reporting & Visual Dashboard Subsystem
- **Directory:** `step_4_reporting/`
- **Purpose:** Telemetry persistence, historical audit trail, and user-friendly visual reporting.
- **Two-Way Operating Model:**
  1. **Automated Pipeline Mode:**
     - Silently writes execution summary and chat records to `reports/automation_history.json` (Department 06 envelope).
     - Renders updated `reports/dashboard.html` (Department 04 tokens).
     - **Win32 User Activity Watcher (`GetLastInputInfo`):** Remains 100% silent while the user is idle/away. When user activity is detected, waits 10 seconds post-movement before popping open the dashboard in the default browser.
  2. **Manual Mode (`run_step4.bat` / `--show`):** Immediately opens `reports/dashboard.html` in the default browser.
- **7 Core KPIs:** Total Runs, Questions Answered, Runtime, Unique Chats, Chat-wise counts, Detailed Question Cards with Emerald Badge `[RECOMMENDED]`, and offline self-contained HTML dashboard.
- **Test Suite:** `test_step4_reporting.py` (13/13 unit tests passing).

---

### 🌟 Step 9: Complete Automation Hub (Master Orchestrator)
- **Directory:** `step_9_complete_automation/`
- **Purpose:** Single Point of User Interaction, master scheduler, pipeline controller, and configuration center.
- **Alphabetical Anchoring:** Named `step_9_complete_automation` so it consistently stays at the bottom of directory listings, eliminating navigation clutter.
- **Master Configuration (`config.json`):** User-editable JSON controlling timing intervals (prod 300s, test 10s, settle delay 0.8s, step 4 user activity delay 10s) and step toggles (`enabled_steps`).
- **Scheduling Logic:**
  - Step 0 condition check (Antigravity Open + Pending Grill-Me)
  - Step 1 $\longrightarrow$ Settle (0.8s) $\longrightarrow$ Step 2 $\longrightarrow$ Settle (0.8s) $\longrightarrow$ Step 3 $\longrightarrow$ Settle (0.8s) $\longrightarrow$ Step 4
  - Intercepts Step 1 Exit Code 10 and cleanly cancels subsequent steps without failure.
- **Launchers:** `run_complete_automation_prod.bat`, `run_complete_automation_test.bat`, `open_dashboard.bat`.
- **Test Suite:** `test_complete_automation.py` (12/12 unit tests passing).

---

## ⚙️ 3. Core Engine Architecture (`core_engine/`)

The low-level automation engine was standardized from legacy `keyboard_automation/` to industry-standard `core_engine/`:

| Module | Role & Responsibility | Implementation Details |
| :--- | :--- | :--- |
| **`core_engine/win32_api.py`** | Win32 ctypes API bindings | `SendInput`, `INPUT`, `KEYBDINPUT`, `MOUSEINPUT`, `HARDWAREINPUT`. Hardware scan code translation (`MapVirtualKeyW`), virtual key codes (`VK_CONTROL`, `VK_SHIFT`, `VK_TAB`, `VK_RETURN`), and event flags (`KEYEVENTF_KEYUP`, `KEYEVENTF_SCANCODE`). |
| **`core_engine/window_manager.py`** | Window Discovery & Safety Scoring | Enumerates top-level HWNDs via `EnumWindows`. Scores Antigravity windows (`Chrome_WidgetWin_1`). Enforces blacklist disqualification (`cmd.exe`, `powershell.exe`, `WindowsTerminal.exe`, `chrome.exe`, `msedge.exe`). Executes focus locks (`AllowSetForegroundWindow`, `AttachThreadInput`). |
| **`core_engine/keystroke_injector.py`** | Atomic Keystroke Injection | Clean abstractions for `key_down`, `key_up`, `press_key`, `hotkey("ctrl", "l")`, and text typing. Enforces configurable `hold_delay` (0.05s) and `step_delay` (0.22s). |
| **`core_engine/automator.py`** | High-Level Sequence Orchestrator | Coordinates multi-question navigation loops, option selection, and the Golden Enter Gate. |
| **`core_engine/cdp_client.py`** | Chrome DevTools Protocol Client | RFC 6455 WebSocket client connecting to Antigravity's Electron CDP debugging port (9222). DOM node queries and bounding box calculations. |
| **`keyboard_automation.py`** | Root Backward-Compatibility Proxy | Transparent root module delegating all calls and submodules to `core_engine/`. Ensures legacy scripts and tests never break. |

---

## 🔄 4. Inter-Process Communication (IPC) Data Contracts

### Contract A: Runtime State (`target_chat.json` & `last_selection_state.json`)
Adheres strictly to the **Department 06 JSON Envelope Standard**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "6b52232f-0326-437c-9a22-cecab6452125",
    "topic_summary": "Prompts Overhaul & Complete Automation Renaming",
    "last_user_prompt": "Update all step prompts and create master memory...",
    "selected_at": "2026-11-04T05:25:00.000Z",
    "status": "READY_FOR_GUI_SELECTION",
    "cancelled_remaining_steps": false,
    "questions_count": 2,
    "total_questions_count": 2,
    "is_multi_question": true,
    "questions": [
      {
        "question_index": 1,
        "question": "Which architecture pattern should be applied for reporting?",
        "options": [
          "(Recommended) Department 06 JSON Envelope + Win32 GetLastInputInfo",
          "Monolithic file append without schema"
        ],
        "is_multi_select": false,
        "recommended_option_index": 1,
        "recommended_option_text": "(Recommended) Department 06 JSON Envelope + Win32 GetLastInputInfo"
      }
    ],
    "window_hwnd": 268912,
    "window_title": "Keyboard Automation - Antigravity",
    "window_focused": true,
    "gui_chat_selected": true,
    "gui_selection_method": "cdp_dom_click"
  },
  "meta": {
    "timestamp": "2026-11-04T05:25:00.000Z",
    "generator": "step1_find_and_focus.py"
  }
}
```

### Contract B: Historical Telemetry Ledger (`reports/automation_history.json`)
Maintains cumulative execution metrics across all pipeline runs:
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_runs": 14,
      "total_questions_answered": 28,
      "unique_chats_count": 6,
      "average_runtime_seconds": 1.42,
      "last_updated": "2026-11-04T05:25:00.000Z"
    },
    "runs": [ ... ],
    "chats": { ... }
  },
  "meta": {
    "generator": "step4_reporting.py",
    "version": "1.0.0",
    "timestamp": "2026-11-04T05:25:00.000Z"
  }
}
```

### Contract C: Master Orchestration Configuration (`step_9_complete_automation/config.json`)
```json
{
  "_comment": "Step 9: Complete Automation Configuration - AutoSelect-Commander Master Configuration",
  "mode": "production",
  "timing": {
    "step0_poll_interval_prod_seconds": 300.0,
    "step0_poll_interval_test_seconds": 10.0,
    "settle_delay_between_steps_seconds": 0.8,
    "step4_user_activity_delay_seconds": 10.0
  },
  "enabled_steps": {
    "step1_find_and_focus": true,
    "step2_gui_chat_select": true,
    "step3_keyboard_automation": true,
    "step4_reporting": true
  },
  "antigravity": {
    "require_grill_me": true,
    "active_hours": 12.0
  },
  "logging": {
    "log_file": "complete_automation.log",
    "verbose": true
  }
}
```

---

## 🚦 5. Exit Code Signal Protocols & Cancellation Governance

| Exit Code | Emitting Step | Meaning & Signal Flow | Master Orchestrator (Step 9) Action |
| :---: | :--- | :--- | :--- |
| **`0`** | Steps 0, 1, 2, 3, 4, 9 | **SUCCESS:** Step completed its operation cleanly and successfully. | Applies configured settle delay (0.8s) and advances to next step. |
| **`1`** | Steps 0, 1, 2, 3, 4, 9 | **FATAL ERROR:** Process crashed, dependency missing, or window focus failed. | Halts pipeline immediately, logs error with traceback, and alerts user. |
| **`10`** | **Step 1 Only** | **NO_PENDING_CHATS:** Zero active unanswered `ask_question` sessions exist in brain transcripts. State written with `status: "NO_PENDING_CHATS"` and `cancelled_remaining_steps: true`. | **Clean Pipeline Cancel:** Step 9 intercepts code 10, logs `Step 1 reported no pending chats. Remaining steps cancelled cleanly`, skips Steps 2..4, and completes cycle with code 0. |

---

## 🗂️ 6. Directory Topology & Runner Matrix

| Step / Module | Directory | Standalone Batch Runner | Master Production / Test Runner |
| :--- | :--- | :--- | :--- |
| **Step 9 (Master Hub)** | `step_9_complete_automation/` | `run_complete_automation_prod.bat` / `run_complete_automation_test.bat` / `open_dashboard.bat` | **Master Entrypoint** |
| **Step 0 (Detector)** | `step_0_antigravity_detector/` | `run_step0.bat` (alias: `run_step0_test.bat`) | Orchestrated by Step 9 |
| **Step 1 (Identifier)** | `step_1_chat_identifier/` | `run_step1.bat` | Orchestrated by Step 9 |
| **Step 2 (Chat & Focus)**| `step_2_chat_and_focus/` | `run_step2.bat` | Orchestrated by Step 9 |
| **Step 3 (Keystroke)** | `step_3_select_the_recommendation/` | `run_step3.bat` | Orchestrated by Step 9 |
| **Step 4 (Reporting)** | `step_4_reporting/` | `run_step4.bat` | Orchestrated by Step 9 |
| **Core Engine** | `core_engine/` | N/A (Python Library) | Imported by Step 3 & root proxy |
| **Documentation & Prompts** | `prompts/` | N/A (Markdown Specifications) | Architectural Reference |

---

## 🧪 7. Test Gate Certification (44/44 Unit Tests Passed)

The entire suite is verified via automated unit test harnesses:
- **`step_0_antigravity_detector/test_step0_detector.py`**: 19 tests verifying detector core, two-factor trigger, clean dashboard, interval timings, and alias parity.
- **`step_4_reporting/test_step4_reporting.py`**: 13 tests verifying telemetry data structures, JSON envelope persistence, HTML generation, and the two-way operating model.
- **`step_9_complete_automation/test_complete_automation.py`**: 12 tests verifying master configuration loading, step discovery, sequential execution, settle delays, step disabling, and Exit Code 10 cancellation.

**Single-Command Workspace Verification:**
```cmd
.\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"
```
**Result:** `Ran 44 tests in 1.857s -> OK` (100% Green Pass Rate).
