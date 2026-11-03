# 🧭 AutoSelect-Commander - Master Autonomous Prompt Manifest

> **Suite:** AutoSelect-Commander / Keyboard Automation  
> **Target Environment:** Windows 10/11 x64, Google Antigravity 2.0 IDE, Electron / CDP RFC 6455  
> **Document Role:** Master Index, Architectural Blueprint & Autonomous Execution Manifest  
> **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com` / [GitHub Profile](https://github.com/aiprincekumar))  
> **Standard:** Department 01 (Product Requirements), Department 02 (Solution Architecture), Department 06 (Backend & API Engineering) & Department 07 (Technical Documentation)  
> **Active Memory Dossier:** [`pipeline_master_memory.md`](./pipeline_master_memory.md)  
> **Operating Boundary:** Self-contained within `prompts/` directory. Zero manual user intervention required.

---

## 🏛️ 1. Executive Pipeline Architecture

The **AutoSelect-Commander Keyboard Automation Suite** is engineered to detect, navigate to, and interactively answer pending `ask_question` (Grill-Me) questionnaires in Google Antigravity 2.0 sessions completely autonomously.

The system is coordinated by **Step 9: Complete Automation Hub** (`step_9_complete_automation/`), which acts as the **Single Point of User Interaction** and master scheduler orchestrating Steps 0 through 4:

```mermaid
flowchart TD
    subgraph MasterOrchestrator [Step 9: Complete Automation Hub (Master Controller)]
        Hub[complete_automation.py]
        Config[config.json - User Delays & Toggles]
        LaunchProd[run_complete_automation_prod.bat - 5m Background]
        LaunchTest[run_complete_automation_test.bat - 10s Live Box]
        Config --> Hub
        LaunchProd --> Hub
        LaunchTest --> Hub
    end

    subgraph ConditionMonitor [Step 0: AntiGravity Detector]
        Hub -->|Poll 300s Prod / 10s Test| Step0[step0_antigravity_detector.py]
        Step0Core[antigravity_detector_core.py]
        Step0 -->|Two-Factor Condition| Step0Core
        Step0Core -->|Condition Matched: Antigravity Open + Pending Question| Hub
    end

    subgraph SequentialExecution [Sequential Pipeline Execution]
        Hub -->|Launch Step 1| S1[Step 1: Chat Identifier & Window Focus]
        
        subgraph Step1Details [step_1_chat_identifier_prompt.md]
            S1 --> S1_Scan[Scan ~/.gemini/antigravity/brain transcripts]
            S1_Scan --> S1_Priority[Prioritize transcript_full.jsonl over transcript.jsonl]
            S1_Priority --> S1_Detect{Pending ask_question found?}
            S1_Detect -- No --> S1_Exit10[Write status: NO_PENDING_CHATS & Exit Code 10]
            S1_Detect -- Yes --> S1_Parse[Extract Questions & Detect Recommended Options]
            S1_Parse --> S1_Focus[Win32 Focus Bypass: Alt Pulse + AllowSetForegroundWindow]
            S1_Focus --> S1_State[Save target_chat.json Dept 06 Envelope]
        end

        S1_Exit10 --> PipeCancel[Step 9 cancels remaining steps cleanly with Code 0]

        S1_State -->|Settle Delay: 0.8s| S2[Step 2: GUI Chat Select & Input Pane Focus]

        subgraph Step2Details [step_2_chat_and_focus_prompt.md]
            S2 --> S2_CDP[Connect to Chrome DevTools Protocol port 9222]
            S2_CDP --> S2_DOM[Query DOM for conversation_id element rect]
            S2_DOM --> S2_Glide[Humanized Smooth Bezier Cursor Glide: 25-30 steps]
            S2_Glide --> S2_Click[Dispatch Precision Click: DOM + OS mouse_event]
            S2_Click --> S2_CtrlL[Dispatch Ctrl + L to focus Chat Input Pane]
            S2_CtrlL --> S2_Update[Update target_chat.json: gui_chat_selected = true]
        end

        S2_Update -->|Settle Delay: 0.8s| S3[Step 3: Keyboard Automation & Golden Enter Gate]

        subgraph Step3Details [step_3_select_the_recommendation_prompt.md]
            S3 --> S3_Ingest[Read Question Count N & Option Indices from State]
            S3_Ingest --> S3_Loop[Deterministic Multi-Question Loop: Q1..QN]
            S3_Loop --> S3_Intermediate[Q1 to QN-1: Ctrl+L -> Shift+Tab -> Option -> NO ENTER]
            S3_Intermediate --> S3_Final[QN: Ctrl+L -> Shift+Tab -> Option -> PRESS ENTER]
            S3_Final --> S3_Confirm[Submit Batch Questionnaire Response]
        end

        S3_Confirm -->|Settle Delay: 0.8s| S4[Step 4: Reporting & Visual Dashboard]

        subgraph Step4Details [step_4_reporting_prompt.md]
            S4 --> S4_JSON[Append to reports/automation_history.json Dept 06 Envelope]
            S4 --> S4_HTML[Generate reports/dashboard.html Dept 04 Glassmorphism UI]
            S4 --> S4_Idle{User Active or Away?}
            S4_Idle -- User Away --> S4_Silent[Remain 100% Silent - Zero Interruption]
            S4_Idle -- User Returns --> S4_Wait10s[Wait 10s Post-Movement Settle Delay]
            S4_Wait10s --> S4_Popup[Pop open dashboard.html in default browser]
        end

        S4_Popup --> S_Done([Pipeline Cycle Certified Complete])
        S4_Silent --> S_Done
    end
```

---

## 📁 2. Step Prompts Master Directory & Manifest

To allow AI agents, subagents, and test harnesses to build, maintain, or debug each step independently without coupling, exhaustive standalone prompt specifications are maintained:

| Specification Document | Step | Purpose & Core Subsystems | Primary Standalone Runner |
| :--- | :--- | :--- | :--- |
| [`pipeline_master_memory.md`](./pipeline_master_memory.md) | **MASTER MEMORY** | Comprehensive ecosystem memory: all steps, Win32 `core_engine/`, IPC schemas, exit code signals, and directory topology. | Reference Dossier |
| [`step_9_complete_automation_prompt.md`](./step_9_complete_automation_prompt.md) | **Step 9** | **Master Hub & Pipeline Controller:** Single Point of User Interaction, `config.json` timing/toggles, sequential step scheduling, settle pauses, and Exit Code 10 handling. | `step_9_complete_automation\run_complete_automation_prod.bat` / `test.bat` |
| [`step_0_antigravity_detector_prompt.md`](./step_0_antigravity_detector_prompt.md) | **Step 0** | Decoupled Status & Condition Monitor: Two-factor trigger (Antigravity Open + Pending Question), browser disqualification, 100% Screen Purity clean Unicode box. | `step_0_antigravity_detector\run_step0.bat` |
| [`step_1_chat_identifier_prompt.md`](./step_1_chat_identifier_prompt.md) | **Step 1** | Transcript reverse scanning, zero-truncation safeguard (`transcript_full.jsonl`), Win32 foreground lock bypass, maximization, and **Exit Code 10 Protocol**. | `step_1_chat_identifier\run_step1.bat` |
| [`step_2_chat_and_focus_prompt.md`](./step_2_chat_and_focus_prompt.md) | **Step 2** | Antigravity GUI navigation, Chrome DevTools Protocol (CDP RFC 6455) WebSocket, Bezier mouse glide, precision click, and `Ctrl + L` chat pane focus. | `step_2_chat_and_focus\run_step2.bat` |
| [`step_3_select_the_recommendation_prompt.md`](./step_3_select_the_recommendation_prompt.md) | **Step 3** | Pure native Win32 `SendInput` hardware keystrokes (powered by `core_engine/`), console blacklist check, multi-question loop, and **The Golden Enter Gate**. | `step_3_select_the_recommendation\run_step3.bat` |
| [`step_4_reporting_prompt.md`](./step_4_reporting_prompt.md) | **Step 4** | Two-way reporting model: silent JSON telemetry (`automation_history.json`), Win32 `GetLastInputInfo` 10s idle activity watcher, and glassmorphism HTML visual dashboard (`dashboard.html`). | `step_4_reporting\run_step4.bat` |
| [`multi_question_automation_prompt.md`](./multi_question_automation_prompt.md) | **Reference** | Foundational architectural specification and algorithmic proof for multi-question quiz mode and radio button detection. | N/A (Reference) |

---

## 🔄 3. Inter-Process State File Protocol (`target_chat.json`)

All steps communicate via the root-level IPC state file [`target_chat.json`](../target_chat.json), structured strictly under the **Department 06 JSON Envelope Standard**:

### Envelope Schema
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
    "dry_run": false,
    "gui_chat_selected": true,
    "gui_selection_method": "cdp_dom_click",
    "gui_selected_at": "2026-11-04T05:25:02.000Z"
  },
  "meta": {
    "timestamp": "2026-11-04T05:25:02.000Z",
    "generator": "step1_find_and_focus.py (Dept 06 Architecture)"
  }
}
```

---

## 🚦 4. Exit Code Governance & Pipeline Signal Flow

| Exit Code | Emitting Step | Meaning & Signal Flow | Runner / Orchestrator Action |
| :---: | :---: | :--- | :--- |
| **`0`** | Steps 0, 1, 2, 3, 4, 9 | **SUCCESS:** Step completed its operation cleanly and successfully. | Proceed to next step in pipeline after configured settle delay (0.8s). |
| **`1`** | Steps 0, 1, 2, 3, 4, 9 | **FATAL ERROR:** Process crashed, dependency missing, or unhandled exception. | Halt pipeline immediately with failure status and record error in log. |
| **`10`** | **Step 1 Only** | **NO_PENDING_CHATS:** Zero active unanswered `ask_question` sessions exist in brain transcripts. State written with `status: "NO_PENDING_CHATS"` and `cancelled_remaining_steps: true`. | **Clean Pipeline Cancel:** Step 9 intercepts code 10, skips Steps 2..4, and completes cycle with code 0. |

---

## 🤖 5. Autonomous Agent Consumption Guidelines

When an external AI coding agent, subagent, or autonomous test harness is tasked with maintaining or extending any step:
1. **Zero-Scan Constraint:** Do NOT scan arbitrary machine folders or execute recursive directory searches. Rely entirely on [`pipeline_master_memory.md`](./pipeline_master_memory.md) and the dedicated step prompts.
2. **Step Isolation:** Each step is self-contained. Any step can be updated independently without breaking adjacent steps, provided the IPC contracts (`target_chat.json`, `automation_history.json`, `config.json`) are preserved.
3. **Execution Verification:** After modifying any step, verify execution using the dedicated step runner batch script (`run_step0.bat`, `run_step1.bat`, `run_step2.bat`, `run_step3.bat`, `run_step4.bat`) or the end-to-end master runner (`step_9_complete_automation\run_complete_automation_test.bat`).
4. **Automated Test Gate:** Ensure all 44 unit tests pass (`.\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"`).
