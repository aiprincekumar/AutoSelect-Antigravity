# 🎯 Grill Me Keyboard Automation Suite

> **Module:** `Keyboard Automation`  
> **Parent Workspace:** [`AutoSelect-Commander`](..)  
> **Target Environment:** Windows 10/11, Antigravity Chat UI, IDEs, and Web Terminals  
> **Architecture:** Hybrid Focus + Zero-Dependency Native Windows ctypes (`SendInput` / `keybd_event`) with optional `pyautogui` interop.

---

## 📖 Overview

The **Grill Me Keyboard Automation** suite provides an automated keystroke injection mechanism designed to respond to interactive multi-choice prompts (such as `/grill-me` or interactive task questions) in Antigravity or any chat-based interface.

### 🔄 The Hybrid Approach
1. **Focus / Window Selection:** The user launches the script, which initiates a configurable countdown (default: 5 seconds). During this countdown, the user simply clicks on or switches to the target Antigravity/IDE chat window.
2. **Foreground Window Detection:** The script detects and logs the active window title via Windows Win32 API (`GetForegroundWindow` / `GetWindowTextW`).
3. **Automated Keyboard Sequence:** Once the countdown reaches zero, the script executes the precision keystroke sequence without requiring manual typing or cursor navigation.

---

## ⌨️ Keystroke Sequence Workflow

```
[Window Focus / User Switch]
         │
         ▼
[Step 1]  Ctrl + L        ───>  Focus the chat input field / prompt box
         │ (350ms delay)
         ▼
[Step 2]  Shift + Tab     ───>  Navigate focus backwards to option choices
         │ (350ms delay)
         ▼
[Step 3]  1 (or custom)   ───>  Select Option 1 (Recommended answer)
         │ (350ms delay)
         ▼
[Step 4]  Enter           ───>  Confirm and submit the selection
```

---

## 🚀 Quick Start

### Option A: Double-Click Batch File (Fastest)
Double-click [`run_grill_me.bat`](./run_grill_me.bat).  
- It auto-locates project `.venv` or system Python.
- Starts a 5-second countdown.
- Gives you time to click on the Antigravity window.
- Executes the sequence and keeps the window open to inspect results.

### Option B: PowerShell Runner
```powershell
# Standard 5s countdown and select Option 1
.\run_grill_me.ps1

# Dry run simulation (safe testing without sending actual keystrokes)
.\run_grill_me.ps1 -DryRun

# Custom 3s countdown with Option 2
.\run_grill_me.ps1 -Countdown 3 -Option "2"
```

### Option C: Direct Python Execution
```bash
# Basic run with default 5-second countdown
python grill_me_automation.py

# Dry run to test detection and timing
python grill_me_automation.py --dry-run

# Select Option 2 with a 3-second countdown and 400ms step delay
python grill_me_automation.py --countdown 3 --option 2 --step-delay 0.4

# Repeat twice
python grill_me_automation.py --repeat 2 --interval 3.0
```

---

## ⚙️ CLI Arguments Reference

| Argument | Short | Type | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `--countdown` | `-c` | `int` | `5` | Countdown in seconds before keystrokes are triggered. |
| `--step-delay` | `-d` | `float` | `0.35` | Delay in seconds between steps (e.g. 0.35 = 350ms). |
| `--hold-delay` | - | `float` | `0.05` | Time in seconds each key is held down before release. |
| `--option` | `-o` | `str` | `"1"` | The option character/number to choose (e.g. `1`, `2`, `y`). |
| `--skip-ctrl-l`| - | `flag`| `False` | Skip pressing `Ctrl + L` if input is already focused. |
| `--skip-enter` | - | `flag`| `False` | Skip pressing `Enter` to allow manual review before submitting. |
| `--dry-run` | - | `flag`| `False` | Simulates and logs all actions without sending physical key events. |
| `--engine` | `-e` | `str` | `"auto"`| Simulation engine: `auto`, `ctypes`, or `pyautogui`. |
| `--repeat` | `-r` | `int` | `1` | Number of times to run the sequence. |
| `--interval` | `-i` | `float` | `2.0` | Delay between repeat runs in seconds. |
| `--no-countdown`| - | `flag`| `False` | Execute immediately with 0s countdown delay. |

---

## 📦 Zero-Dependency Architecture

- **Default Engine:** Windows `ctypes.windll.user32.SendInput` with fallback to `keybd_event`.
- **Requirements:** 100% standard library Python 3.8+ on Windows. **No `pip install` required!**
- **PyAutoGUI (Optional):** If `pyautogui` is installed and specified via `-e pyautogui`, the script will utilize it seamlessly.

---

## 🔍 Verification & Safety Features

1. **Active Window Inspection:** Continuously reads the foreground window handle during countdown so you know exactly which application will receive keystrokes.
2. **Dry Run Mode:** Passing `--dry-run` logs the full timeline without dispatching actual OS keystroke events.
3. **Graceful Error Recovery:** Uses try/except blocks and falls back to Win32 `keybd_event` if `SendInput` returns unexpected error codes.
