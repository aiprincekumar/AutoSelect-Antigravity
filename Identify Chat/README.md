# 🔍 Identify Chat - Standalone Antigravity Chat Activation Suite

> **Architecture:** Two-Script Modular Architecture & 1-Click GUI Automation Suite  
> **Subfolder:** `Identify Chat` (100% Autonomous, Standalone & Decoupled)  
> **Target:** Antigravity AI Coding Agent Sessions & Interactive Multi-Choice Dialogs  
> **Author & Identity:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 📌 Overview & Independence

The **Identify Chat** suite is a completely autonomous, standalone tool. It has **zero dependencies on any other subfolder or external modules** and can be moved, copied, or deployed anywhere on Windows independently.

When Antigravity AI agents enter a `/grill-me` interview or present an interactive prompt via `ask_question`, the agent goes idle and waits for user choice confirmation.

This suite performs two decoupled operations:
1. **Step 1 (Scan & Focus):** Scans the local Antigravity brain transcripts, locates pending Grill-Me questions, extracts questions & options, maximizes and focuses the Antigravity window without restoring down, and writes the state to `target_chat.json`.
2. **Step 2 (GUI Select & Activate):** Connects to the Antigravity internal DevTools port via Chrome DevTools Protocol (CDP WebSocket), locates the active conversation element in the sidebar, glides the mouse pointer smoothly, clicks to select the conversation, and injects `Ctrl + L` to focus the chat pane.

---

## 🚀 Quick Start (100% Standalone)

### Prerequisites
- Windows 10 or 11
- Python 3.10+ (Standard library only; zero external packages strictly required)

### Setup (Optional Virtualenv)
```bash
# 1. Open terminal inside this folder:
cd "Identify Chat"

# 2. (Optional) Create local virtual environment:
python -m venv .venv

# 3. (Optional) Install optional enhancements:
pip install -r requirements.txt
```

### Running the Suite

#### Option A: 1-Click 3-Step Full Pipeline Runner (Step 1 + Step 2 + Step 3)
Double-click `run_activating_grill_me_with_automation.bat` or run from terminal:
```cmd
run_activating_grill_me_with_automation.bat
```
This runs Step 1 (find & focus window), settles for 0.8s, runs Step 2 (GUI chat select & focus), settles for 0.8s, and runs Step 3 (hybrid keyboard automation to choose option and submit).

#### Option B: 2-Step Modular Runner (Step 1 + Step 2)
Double-click `run_activating_grill_me.bat` or run from terminal:
```cmd
run_activating_grill_me.bat
```
This runs Step 1, settles for 0.8s, and runs Step 2 seamlessly.

#### Option C: Step 1 Standalone (Scan transcripts & focus window)
```cmd
run_step1_find_and_focus.bat
```
Or directly with Python:
```bash
python step1_find_and_focus.py
```
*(Flags: `--cid <CONVO_ID>`, `--dry-run`, `--no-focus`)*

#### Option D: Step 2 Standalone (GUI Chat Select & Focus)
```cmd
run_step2_gui_chat_select.bat
```
Or directly with Python:
```bash
python step2_gui_chat_select.py
```
*(Flags: `--cid <CONVO_ID>`, `--select-option 1`, `--auto-submit`, `--dry-run`)*

---

## 📂 File Manifest

| File | Purpose |
| :--- | :--- |
| `run_activating_grill_me_with_automation.bat` | 3-step master pipeline runner (Step 1 + Step 2 + Step 3 Keyboard Automation) |
| `run_activating_grill_me.bat` | 2-step batch runner orchestrating Step 1 and Step 2 |
| `run_step1_find_and_focus.bat` | Standalone runner for Step 1 (scan & focus) |
| `run_step2_gui_chat_select.bat` | Standalone runner for Step 2 (GUI chat selection & focus) |
| `step1_find_and_focus.py` | Scans brain transcripts, extracts questions, focuses window, saves `target_chat.json` |
| `step2_gui_chat_select.py` | Connects via CDP WebSocket, finds sidebar chat item, glides mouse, clicks, sends `Ctrl + L` |
| `activating_grill_me.py` | Unified runner delegating to Step 1 and Step 2 with local coordinate fallbacks |
| `config.json` | Local calibrated coordinates and step configuration for full HD displays |
| `target_chat.json` | Runtime state cache produced by Step 1 containing question metadata and HWND |
| `requirements.txt` | Dependency declaration (100% standard library compatible) |
| `.gitignore` | Local ignore rules for `.venv/`, `__pycache__/`, and runtime state files |

---

## ⚙️ Configuration (`config.json`)

All coordinates are local to this folder inside `config.json`:
- `chat_click_x`: Default fallback X coordinate for conversation item (580)
- `chat_click_y`: Default fallback Y coordinate for conversation item (815)
- `option_radio_x`: Option radio circle coordinate (541)
- `option_radio_y`: Option radio circle coordinate (664)
- `submit_button_x`: Submit button coordinate (1827)
- `submit_button_y`: Submit button coordinate (849)

If running on a non-standard resolution, edit `config.json` directly.
