# Activating Grill Me Chat in Antigravity (Method 1)

> **Method 1: File System & Brain Transcript Parsing Engine**  
> **Workspace:** `AutoSelect-Commander`  
> **Target:** Antigravity AI Coding Agent Sessions  
> **Author & Identity:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 📌 Overview

When Antigravity AI agents enter a **Grill Me** interview or trigger an interactive prompt via `ask_question`, the agent goes idle and waits for user confirmation / option selection.

This suite implements **Method 1 (File System & Transcript Parsing)** to:
1. **Automatically detect** which Antigravity chat/conversation currently has an unanswered `ask_question` prompt waiting for response.
2. **Execute a 2-Step Flow**:
   - **Step 1: Identification** — Scans `%USERPROFILE%\.gemini\antigravity\brain`, parses `transcript.jsonl` files, detects unfulfilled `ask_question` tool calls, and extracts the conversation ID, timestamp, topic, questions, and option choices.
   - **Step 2: Selection** — Selects the target conversation, inspects available options, determines the recommended choice (or configured option index), formats the state into a structured JSON payload, and optionally activates/focuses the Antigravity window.

---

## 🚀 Two-Step Execution Architecture

```
[ Antigravity Brain Storage ] (~/.gemini/antigravity/brain/)
               │
               ▼
   [ Step 1: Identification ]
      ├─ Scan conversation subfolders
      ├─ Read .system_generated/logs/transcript.jsonl
      ├─ Filter for tool_calls: "ask_question"
      ├─ Verify unfulfilled state (no subsequent GENERIC/USER_INPUT)
      └─ Extract: CID, Step Index, Questions, Options, Recommended Flag
               │
               ▼
   [ Step 2: Selection ]
      ├─ Target CID or Auto-Select Newest Active Chat
      ├─ Map Question -> Chosen Option (e.g. Option 1 / Recommended)
      ├─ Save Prepared Selection State to JSON
      └─ [Optional] Win32 SetForegroundWindow / Maximize Focus
```

---

## 🛠️ Usage & CLI Commands

### 1. Windows Batch Runner (Interactive or Headless)

Double-click `run_activating_grill_me.bat` from Windows Explorer, or run in cmd/PowerShell:

```cmd
run_activating_grill_me.bat
```

Displays an interactive 7-option menu:
```
  [1] Scan & Identify Pending Grill Me Chats (Step 1)
  [2] Auto-Select Latest Pending Chat & Prepare Selection (Step 1 + 2)
  [3] Dry-Run Simulation (Inspect without modifying state)
  [4] Output Selection State in Structured JSON
  [5] Auto-Select & Focus Antigravity Window
  [6] Run Comprehensive Unit Test Suite
  [7] Exit
```

### 2. Direct Python CLI Commands

```bash
# Step 1: Scan and list all pending Grill Me chats
python activating_grill_me.py --scan

# Step 1 + Step 2: Auto-select latest pending chat and prepare selection
python activating_grill_me.py --auto-select

# Select a specific option number (e.g. Option 2) across questions
python activating_grill_me.py --auto-select --option 2

# Select by specific Conversation ID
python activating_grill_me.py --select 0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da

# Output in standardized JSON envelope (Dept 06 compliant)
python activating_grill_me.py --auto-select --json

# Dry-run test mode (pure simulation)
python activating_grill_me.py --dry-run

# Auto-select and bring Antigravity IDE/Chat window to foreground
python activating_grill_me.py --auto-select --focus
```

---

## 📦 Output Format (Standard JSON Envelope)

When invoked with `--json`, the script returns a predictable envelope compliant with Department 06 RESTful / API standards:

```json
{
  "success": true,
  "data": {
    "chat": {
      "conversation_id": "0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da",
      "step_index": 11,
      "created_at": "2026-11-01T21:42:48Z",
      "topic_summary": "मुझे डेमो के लिए ग्रिड मी ऑप्शन ऑन करके दो...",
      "last_user_prompt": "Continue",
      "questions": [
        {
          "question_index": 1,
          "question": "आप इनमें से किस स्क्रिप्ट का डेमो / टेस्ट रन करना चाहते हैं?",
          "options": [
            "(Recommended) Rule In Hindi ट्रांसलेशन स्क्रिप्ट (run_rule_in_hindi.bat / ps1)",
            "Antigravity Backup स्क्रिप्ट (backup_daily.ps1 / backup_manual.ps1)"
          ],
          "is_multi_select": false,
          "recommended_option_index": 1,
          "recommended_option_text": "(Recommended) Rule In Hindi ट्रांसलेशन स्क्रिप्ट..."
        }
      ],
      "is_last_step": true,
      "total_steps": 11
    },
    "selection": {
      "conversation_id": "0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da",
      "selected_at": "2026-11-01T21:59:47.263947+00:00",
      "status": "READY_FOR_CONFIRMATION",
      "questions_count": 2,
      "selections": [
        {
          "question_index": 1,
          "question": "...",
          "selected_option_index": 1,
          "selected_option_text": "(Recommended)...",
          "is_recommended": true
        }
      ],
      "window_focused": false,
      "dry_run": false
    }
  },
  "meta": {
    "timestamp": "2026-11-01T21:59:47.263947+00:00",
    "action": "selection"
  }
}
```

---

## 🔒 Verification & Test Suite

Run the dedicated test suite:
```powershell
python -m unittest tests/test_activating_grill_me.py
```
Validates transcript parsing, state transitions, option extraction, recommendation heuristics, JSON export, and Win32 focus safety.
