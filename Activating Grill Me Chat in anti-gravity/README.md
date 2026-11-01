# Activating Grill Me Chat in Antigravity (Method 1)

> **Method 1: File System & Brain Transcript Parsing Engine + 1-Click GUI Automation**  
> **Workspace:** `AutoSelect-Commander`  
> **Target:** Antigravity AI Coding Agent Sessions  
> **Author & Identity:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 📌 Overview

When Antigravity AI agents enter a **Grill Me** interview or trigger an interactive prompt via `ask_question`, the agent goes idle and waits for user confirmation / option selection.

This suite implements **Method 1 (File System & Transcript Parsing + 1-Click GUI Selection)** to:
1. **Automatically detect** which Antigravity chat/conversation currently has an unanswered `ask_question` prompt waiting for response.
2. **Execute a Streamlined 4-Step 1-Click Automation Flow**:
   - **Step A: Identification** — Scans `%USERPROFILE%\.gemini\antigravity\brain`, parses `transcript.jsonl` files, detects unfulfilled `ask_question` tool calls, and extracts Conversation ID, timestamp, topic, questions, and options.
   - **Step B: Presentation & State Preparation** — Formats pending questions and recommended choices into a clean terminal card, maps options, and exports a standardized Department 06 JSON payload.
   - **Step C: Bulletproof Window Foregrounding** — Un-minimizes and brings the Antigravity window to front focus using Windows 10/11 foreground lock bypass (`ShowWindow SW_RESTORE`, virtual Alt key tap, `AttachThreadInput`, Z-order bump, and process/class matching).
   - **Step D: GUI Chat Selection** — Autonomously selects the chat in the Antigravity GUI with smooth mouse navigation/click to the conversation row and `Ctrl + L` chat panel focus.

---

## 🚀 1-Click Execution Architecture

```
[ Antigravity Brain Storage ] (~/.gemini/antigravity/brain/)
               │
               ▼
   [ Step A: Identification Engine ]
      ├─ Scan conversation subfolders
      ├─ Read .system_generated/logs/transcript.jsonl
      ├─ Filter for tool_calls: "ask_question"
      ├─ Verify unfulfilled state (no subsequent GENERIC/USER_INPUT)
      └─ Extract: CID, Step Index, Questions, Options, Recommended Flag
               │
               ▼
   [ Step B: Presentation & State Packaging ]
      ├─ Print Clean Terminal Summary Card
      ├─ Highlight Auto-Detected (Recommended) Options
      └─ Export last_selection_state.json (Dept 06 Envelope)
               │
               ▼
   [ Step C: Bulletproof Foreground Activation ]
      ├─ Process & Class Match: Antigravity.exe / Chrome_WidgetWin_1
      ├─ Restore Minimized State: ShowWindow(SW_RESTORE) + OpenIcon
      ├─ Break OS Foreground Lock: Virtual Alt Key Pulse (VK_MENU)
      ├─ Thread Desktop Sync: OpenInputDesktop + SetThreadDesktop
      └─ Thread Attachment & Z-Order Bump: AttachThreadInput + SetWindowPos
               │
               ▼
   [ Step D: GUI Chat Selection ]
      ├─ Smooth Mouse Glide & Tactile Click on Chat Row (X=580, Y=815)
      ├─ Shortcut Pulse: [Ctrl + L] to Focus Chat Input Field
      └─ Optional: [Shift + Tab] + Option Number + [Enter] Submission
```

---

## 🛠️ Usage & 1-Click Commands

### 1. Default 1-Click Windows Batch Runner (No "Taam-Jhaam")

Simply double-click `run_activating_grill_me.bat` from Windows Explorer or run in terminal:

```cmd
run_activating_grill_me.bat
```

**What it does automatically:**
- Auto-detects virtualenv and Python.
- Scans transcripts for pending Grill Me chat.
- Prints clean question/answer summary in terminal.
- Brings Antigravity window to front on screen.
- Smoothly moves mouse and clicks chat row in Antigravity GUI.
- Dispatches `Ctrl + L` to activate chat input panel.
- Exports `last_selection_state.json`.

### 2. Direct Python CLI Commands

```bash
# 1-Click execution end-to-end (Default)
python activating_grill_me.py

# Dry-run test mode (inspects without moving mouse or sending clicks)
python activating_grill_me.py --dry-run

# Scan and list pending chats only (no focus or GUI click)
python activating_grill_me.py --scan

# Select specific conversation ID
python activating_grill_me.py --select 0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da

# Select a specific option number across questions (e.g. Option 2)
python activating_grill_me.py --option 2

# Also trigger keyboard option selection (Shift+Tab -> Option -> Enter)
python activating_grill_me.py --select-option --auto-submit

# Output in standardized Department 06 JSON response envelope
python activating_grill_me.py --json
```

---

## 📦 Department 06 Standard Response Envelope

When invoked with `--json`, the script returns a predictable envelope compliant with Department 06 RESTful / API standards:

```json
{
  "success": true,
  "data": {
    "chat": {
      "conversation_id": "0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da",
      "step_index": 11,
      "created_at": "2026-11-01T21:42:48Z",
      "topic_summary": "मुझे डेमो के लिए ग्रिड मी ऑप्शन ऑन करके दो।...",
      "last_user_prompt": "Continue",
      "questions": [
        {
          "question_index": 1,
          "question": "आप इनमें से किस स्क्रिप्ट का डेमो / टेस्ट रन करना चाहते हैं?",
          "options": [
            "(Recommended) Rule In Hindi ट्रांसलेशन स्क्रिप्ट (run_rule_in_hindi.bat / ps1)",
            "Antigravity Backup स्क्रिप्ट (backup_daily.ps1 / backup_manual.ps1)",
            "Rules Health Check & Sentinel स्क्रिप्ट (npm run rules:check / task rules:check)",
            "AutoSelect-Commander GUI ऑटोमेशन स्क्रिप्ट",
            "कोई अन्य कस्टम स्क्रिप्ट (पाथ/नाम चैट में बताएं)"
          ],
          "is_multi_select": false,
          "recommended_option_index": 1,
          "recommended_option_text": "(Recommended) Rule In Hindi ट्रांसलेशन स्क्रिप्ट (run_rule_in_hindi.bat / ps1)"
        }
      ]
    },
    "selection": {
      "conversation_id": "0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da",
      "selected_at": "2026-11-01T22:49:18.759881+00:00",
      "status": "READY_FOR_CONFIRMATION",
      "questions_count": 2,
      "selections": [
        {
          "question_index": 1,
          "question": "आप इनमें से किस स्क्रिप्ट का डेमो / टेस्ट रन करना चाहते हैं?",
          "selected_option_index": 1,
          "selected_option_text": "(Recommended) Rule In Hindi ट्रांसलेशन स्क्रिप्ट (run_rule_in_hindi.bat / ps1)",
          "is_multi_select": false,
          "total_options": 5,
          "is_recommended": true
        }
      ],
      "window_focused": true,
      "gui_chat_selected": true,
      "dry_run": false
    }
  },
  "meta": {
    "timestamp": "2026-11-01T22:49:18.761000+00:00",
    "saved_state_file": "c:\\Users\\Atul Verma\\Desktop\\AutoSelect-Commander\\Activating Grill Me Chat in anti-gravity\\last_selection_state.json",
    "action": "1-click-activation"
  }
}
```

---

## 🧪 Unit Testing

Run the test suite via standard Python or virtualenv:

```bash
python -m unittest tests/test_activating_grill_me.py
```

All 11 unit tests verify transcript detection, recommended option auto-parsing, JSON envelope compatibility, window finding, and GUI selection.
