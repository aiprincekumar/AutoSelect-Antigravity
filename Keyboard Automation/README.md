# 🎯 Grill Me Keyboard Automation Suite

> **Module:** `Keyboard Automation`  
> **Parent Workspace:** [`AutoSelect-Commander`](..)  
> **Target Environment:** Windows 10/11, Antigravity Chat UI, IDEs, and Web Terminals  
> **Architecture:** Zero-Dependency Native Windows ctypes (`SendInput` / `keybd_event` / `user32` Windowing) + Intelligent Auto-Targeting, Restoration, Full-Screen Maximization & Focus Subsystem.

---

## 📖 Overview

The **Grill Me Keyboard Automation** suite provides an automated keystroke injection and window-management mechanism designed to respond to interactive multi-choice prompts (such as `/grill-me` or interactive task questions) in Antigravity or any chat-based interface.

### 🌟 Intelligent Auto-Targeting & Maximization Subsystem (Default: Enabled)
By default, regardless of current desktop state, the suite automatically inspects and prepares the target application window:
1. **Window Detection & Enumeration:** Scans all top-level windows via Win32 `EnumWindows` and matches the target keyword (default: `"Antigravity"`). Excludes the script's own console window.
2. **Auto-Restore (Un-minimize):** If Antigravity is minimized (`IsIconic == True`), the subsystem automatically un-minimizes and restores it.
3. **Auto-Maximize (Full Screen):** If Antigravity is not maximized (`IsZoomed == False`), it automatically maximizes it (`SW_MAXIMIZE`) so the interface expands edge-to-edge.
4. **Foreground Lock Bypass & Focus:** Uses `AttachThreadInput` and synthetic `Alt` unlock signals to reliably bring Antigravity to the absolute foreground (`BringWindowToTop` / `SetForegroundWindow` / `SetFocus`).
5. **Geometry Verification & Settling Delay:** Verifies window bounds (`GetWindowRect`) and waits for rendering to stabilize (`--settle-delay 0.5s`) before injecting keystrokes.
6. **Graceful Fallback:** If the target window is not open, the system logs a clear warning and seamlessly continues using the active foreground window.

---

## ⌨️ Keystroke Sequence Workflow

```
[Target Detection: "Antigravity"]
          │
          ├─ Minimized?    ──> Restore Window (SW_RESTORE)
          ├─ Not Maxed?    ──> Maximize to Full Screen (SW_MAXIMIZE)
          ├─ Out of Focus? ──> BringToTop + SetForegroundWindow
          └─ Verified Geometry & Settle (500ms delay)
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
- Auto-locates project `.venv` or system Python.
- Auto-detects, un-minimizes, maximizes, and focuses Antigravity.
- Executes the selection sequence and keeps the window open to inspect results.

### Option B: PowerShell Runner
```powershell
# Standard run (auto-maximizes Antigravity, 5s countdown, selects Option 1)
.\run_grill_me.ps1

# Dry-run simulation (safe testing without sending actual keystrokes)
.\run_grill_me.ps1 -DryRun

# Target custom window keyword (e.g. VS Code) with 3s countdown
.\run_grill_me.ps1 -TargetWindow "Visual Studio Code" -Countdown 3

# Disable auto-maximize if you prefer a floating window
.\run_grill_me.ps1 -NoAutoMaximize -Option "2"
```

### Option C: Direct Python Execution
```bash
# Basic run with default auto-focus and auto-maximize
python grill_me_automation.py

# Dry run to test detection, geometry, and timing
python grill_me_automation.py --dry-run

# Custom window target with 3-second countdown and 400ms step delay
python grill_me_automation.py --target-window "Antigravity" --countdown 3 --option 1 --step-delay 0.4

# Repeat twice
python grill_me_automation.py --repeat 2 --interval 3.0
```

---

## ⚙️ CLI Arguments Reference

| Argument | Short | Type | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `--target-window` | `-t` | `str` | `"Antigravity"` | Window title keyword to locate, maximize, and focus. |
| `--auto-focus` | - | `bool` | `True` | Automatically bring target window to foreground before injection. |
| `--no-auto-focus` | - | `flag` | - | Disable automatic window focusing. |
| `--auto-maximize` | - | `bool` | `True` | Automatically un-minimize and maximize target window to full screen. |
| `--no-auto-maximize` | - | `flag` | - | Disable automatic window maximization. |
| `--settle-delay` | - | `float` | `0.5` | Settle delay in seconds after focus/maximize for UI rendering. |
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

- **Default Engine:** Windows `ctypes.windll.user32` + `kernel32` (SendInput, EnumWindows, ShowWindow, AttachThreadInput).
- **Requirements:** 100% standard library Python 3.8+ on Windows. **No `pip install` required!**
- **PyAutoGUI (Optional):** If `pyautogui` is installed and specified via `-e pyautogui`, the script will utilize it seamlessly.

---

## 🔍 Verification & Safety Features

1. **Intelligent Window Geometry Inspection:** Reads window rect, iconic state, and zoom state before and after repositioning to guarantee full screen readiness.
2. **Active Window Inspection:** Continuously reads the foreground window handle during countdown so you know exactly which application will receive keystrokes.
3. **Dry Run Mode:** Passing `--dry-run` logs the full timeline without dispatching actual OS keystroke events.
4. **Graceful Error Recovery:** Uses try/except blocks and falls back to Win32 `keybd_event` if `SendInput` returns unexpected error codes.
