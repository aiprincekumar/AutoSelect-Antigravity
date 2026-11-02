# Activating Grill Me Chat in Antigravity (Method 1)

> **Two-Script Modular Architecture & 1-Click GUI Automation Suite**  
> **Workspace:** `AutoSelect-Commander` \ `Activating Grill Me Chat in anti-gravity`  
> **Target:** Antigravity AI Coding Agent Sessions  
> **Author & Identity:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 📌 Overview & Architectural Evolution

When Antigravity AI agents enter a **Grill Me** interview or trigger an interactive prompt via `ask_question`, the agent goes idle and waits for user confirmation / option selection.

### ❓ The Challenge
Previously, monolithic scripts successfully brought the Antigravity window to the foreground and found the question in the terminal, but the conversation was **not actually selected inside the Antigravity user interface**. The mouse clicked generic screen coordinates rather than the exact conversation item on the sidebar.

### 💡 Two-Script Modular Architecture Solution
Per the user's architectural request, the workflow is split into **two cleanly isolated scripts** orchestrated seamlessly by a **single 1-click batch runner**:

```
                       [ run_activating_grill_me.bat ]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    [ Script 1: step1_find_and_focus.py ]   [ Script 2: step2_gui_chat_select.py ]
    ├─ Scans Antigravity Brain Transcripts   ├─ Reads target_chat.json
    ├─ Detects Unanswered ask_question      ├─ Queries Antigravity DevTools (CDP)
    ├─ Extracts Topics & Recommended Opts   ├─ Locates exact sidebar <a> element
    ├─ Saves target_chat.json (Dept 06)     ├─ Smooth Bezier Mouse Glide to item
    └─ Restores & Focuses Window            ├─ Dispatches DOM + OS Hardware Click
                                            ├─ Fallback: SPA router pushState
                                            └─ Sends [Ctrl + L] to focus chat pane
```

---

## 📂 File Manifest & Department 06 Responsibilities

| File | Type | Primary Role & Responsibilities |
| :--- | :--- | :--- |
| [`run_activating_grill_me.bat`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/run_activating_grill_me.bat) | Batch Runner | **1-Click Master Runner:** Detects Python, runs Script 1, verifies exit code, runs Script 2, and displays complete success status. |
| [`step1_find_and_focus.py`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/step1_find_and_focus.py) | Python (Script 1) | **Search, State Store & Window Focus:** Scans `~/.gemini/antigravity/brain/`, finds active Grill-Me questions, stores metadata in `target_chat.json`, and bypasses Windows foreground lock to bring the window into focus. |
| [`step2_gui_chat_select.py`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/step2_gui_chat_select.py) | Python (Script 2) | **Chat Search & GUI Selection:** Connects to Antigravity internal DevTools port (`DevToolsActivePort`), finds `a[href*="/c/<cid>"]`, performs smooth mouse glide to exact sidebar item, clicks, verifies page state, and sends `Ctrl + L`. |
| [`target_chat.json`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/target_chat.json) | JSON State | **Department 06 State File:** Stores `conversation_id`, questions, options, recommended flags, window HWND, and selection timestamps. |
| [`last_selection_state.json`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/last_selection_state.json) | JSON State | Legacy compatibility state mirror automatically synchronized with `target_chat.json`. |
| [`activating_grill_me.py`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Activating%20Grill%20Me%20Chat%20in%20anti-gravity/activating_grill_me.py) | Unified Engine | Backward-compatible unified script delegating to the new two-script engine. |

---

## 🛠️ Usage & Execution

### 1. Default 1-Click Master Batch Runner (Recommended)

Simply double-click `run_activating_grill_me.bat` from Windows Explorer or run from terminal:

```cmd
run_activating_grill_me.bat
```

**1-Click Execution Sequence:**
1. Step 1 starts: scans transcripts, prints question summary, brings Antigravity window to front, and writes `target_chat.json`.
2. Step 1 exits with code `0`.
3. Runner gives 0.8s settle delay.
4. Step 2 starts: reads `target_chat.json`, finds the conversation element in Antigravity GUI via CDP, glides mouse to sidebar row, clicks, verifies page URL, and sends `Ctrl + L`.
5. Chat is active and ready for prompt typing or option selection!

### 2. Isolated Step-by-Step Execution

You can run each script independently whenever debugging or inspecting intermediate states:

#### Step 1: Scan Transcripts & Focus Window Only
```bash
python step1_find_and_focus.py
```
*(Options: `--cid <CONVO_ID>`, `--dry-run`, `--no-focus`)*

#### Step 2: GUI Chat Selection Only
```bash
python step2_gui_chat_select.py
```
*(Options: `--cid <CONVO_ID>`, `--select-option 1`, `--auto-submit`, `--dry-run`)*

---

## 🔬 Multi-Tier GUI Selection Architecture

Antigravity is an Electron application. Every conversation has a URL route `https://127.0.0.1:<PORT>/c/<CONVERSATION_ID>`. The selection engine utilizes a multi-tiered approach:

1. **Tier 1 (CDP DOM Precision + Smooth Cursor Motion):**
   - Reads `DevToolsActivePort` from `%APPDATA%\Antigravity\DevToolsActivePort`.
   - Queries `a[href*="/c/<target_cid>"]` in the DOM via lightweight RFC 6455 WebSocket client (zero external dependencies).
   - Maps DOM viewport `(x, y)` to Windows screen coordinates via `GetWindowRect`.
   - Performs smooth Bezier mouse movement (`easeOutQuad`) to the exact conversation row.
   - Dispatches full DOM event sequence (`pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click`) AND physical mouse click.
2. **Tier 2 (SPA Route Navigation Fallback):**
   - If the conversation link is scrolled out of view, dispatches `window.history.pushState(null, '', '/c/' + cid)` and triggers client router transition without reloading the page.
3. **Tier 3 (Calibrated Sidebar Coordinate Click):**
   - If CDP is unavailable, calculates sidebar coordinates relative to the Antigravity window frame and clicks.
4. **Tier 4 (Keyboard Focus):**
   - Sends `Ctrl + L` to place keyboard focus directly into the chat prompt input area.

---

## 📋 Standardized JSON State Envelope (Department 06)

Both scripts read and write to `target_chat.json` adhering to the Department 06 API Standard:

```json
{
  "success": true,
  "data": {
    "conversation_id": "0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da",
    "topic_summary": "मुझे डेमो के लिए ग्रिड मी ऑप्शन ऑन करके दो। मुझे स्क्रिप्ट टेस्ट करना है।",
    "last_user_prompt": "Continue",
    "status": "SUCCESS_SELECTED",
    "questions_count": 2,
    "questions": [
      {
        "question_index": 1,
        "question": "आप किस प्रकार की स्क्रिप्ट का डेमो और टेस्टिंग रन करना चाहते हैं?",
        "options": [
          "(Recommended) PowerShell / Windows Terminal स्क्रिप्ट टेस्ट",
          "Node.js / npm स्क्रिप्ट टेस्ट (उदा. rules:check, build, test)"
        ],
        "recommended_option_index": 1,
        "recommended_option_text": "(Recommended) PowerShell / Windows Terminal स्क्रिप्ट टेस्ट"
      }
    ],
    "window_hwnd": 3474542,
    "window_title": "Grid Mode Demo Setup - Outside of Project - Antigravity",
    "window_focused": true,
    "gui_chat_selected": true,
    "gui_selection_method": "cdp_dom_click"
  },
  "meta": {
    "timestamp": "2026-11-02T00:45:18.236108+00:00",
    "generator": "step2_gui_chat_select.py (Dept 06 Architecture)"
  }
}
```

---

## 🛡️ Governance & Developer Profile

- **Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Precedence Hierarchy:** Tier 1 Governance (Rule 15 Local Micro-Commit Cadence & Remote Push Gatekeeper).
