# ⌨️ Step 3: Keyboard Automation - Antigravity Chat Activation Suite

> **Pipeline Step:** **STEP 3 OF 3** (`Step 3: Keyboard Automation`)  
> **Subfolder:** `Keyboard Automation` (Decoupled, Standalone & Pipeline Integrated)  
> **Target Environment:** Windows 10/11, Antigravity Chat UI, IDEs, and Web Terminals  
> **Architecture:** Zero-Dependency Native Windows ctypes (`SendInput` / `keybd_event` / `user32` Windowing) + Dynamic Multi-Question Scaling + Intelligent Auto-Targeting, Restoration, Full-Screen Maximization & Focus Subsystem.  
> **Primary Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 06 (Backend & API Engineering) & Universal Rule 15  

---

## 🏛️ AutoSelect-Commander 3-Step Pipeline Context

The `Keyboard Automation` subfolder is specifically designed as **Step 3** of the complete 3-Step AutoSelect-Commander automation architecture:

```
┌──────────────────────────────────────────────────────────────────────────┐
│              AutoSelect-Commander 3-Step Pipeline Architecture            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Step 1: Scan & Focus] ──────> [Step 2: GUI Chat Select] ─────>         │
│  `Identify Chat/`                `Identify Chat/`                        │
│  `step1_find_and_focus.py`       `step2_gui_chat_select.py`              │
│  - Transcript scan & Q parser   - DevTools CDP/DOM chat locator          │
│  - target_chat.json persistence - Smooth cursor glide & click            │
│  - Window un-minimize/maximize  - Focuses chat pane (Ctrl + L)           │
│                                                                          │
│  ──────────────────────────────────────────────────────────────>         │
│  [Step 3: Keyboard Automation]                                           │
│  `Keyboard Automation/`                                                  │
│  `step3_keyboard_automation.py`                                          │
│  - Window safety verification & foreground focus                         │
│  - Dynamic multi-question loop (Q1..QN)                                  │
│  - Option navigation (Ctrl+L -> Shift+Tab -> Option)                     │
│  - The Golden Enter Gate (suppressed on Q1..QN-1, fired ONLY on QN)      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 Overview & Independence

While functioning as **Step 3** in the master pipeline, the **Step 3: Keyboard Automation** suite remains 100% autonomous and standalone. It has **zero required dependencies on external libraries or other subfolders** and can be run independently at any time.

It provides an automated keystroke injection and window-management mechanism designed to respond to interactive multi-choice prompts (such as `/grill-me` or interactive task questions) in Antigravity or any chat-based interface.

### 📁 Step 3 File Topology & Identification

| File | Identity & Role | Status |
| :--- | :--- | :--- |
| **`step3_keyboard_automation.py`** | **Primary Step 3 Entry Point:** Main script executing Step 3 keystroke automation, dynamic multi-question scaling, and window focus. | **PRIMARY** |
| **`run_step3_keyboard_automation.bat`** | **1-Click Step 3 Batch Launcher:** Standardized runner matching Step 1 & 2 batch launchers. | **PRIMARY RUNNER** |
| **`run_step3.bat`** | **Quick Step 3 Shortcut:** Fast 1-click alias to `run_step3_keyboard_automation.bat`. | **SHORTCUT** |
| **`run_step3_keyboard_automation.ps1`**| **Step 3 PowerShell Runner:** Native parameter-bound PowerShell launcher. | **PRIMARY RUNNER** |
| **`grill_me_automation.py`** | **Backward-Compatibility Wrapper:** Delegates directly to `step3_keyboard_automation.py`. Prevents breaking existing scripts. | **LEGACY ALIAS** |
| **`run_grill_me.bat`** | **Backward-Compatibility Batch Runner:** Legacy launcher pointing to `step3_keyboard_automation.py`. | **LEGACY ALIAS** |
| **`run_grill_me.ps1`** | **Backward-Compatibility PS1 Runner:** Legacy PowerShell launcher pointing to `step3_keyboard_automation.py`. | **LEGACY ALIAS** |
| **`keyboard_automation/`** | **Modular Engine Package:** Sub-modules for Win32 API, Input Injector, Window Manager, Automator, CLI, and Constants. | **INTERNAL ENGINE** |
| **`archive/`** | **Frozen Certified Snapshot:** Historical verified v1.0.0 reference. (Read-only, untouched). | **ARCHIVE** |

---

## 🚀 Quick Start (Step 3 Standalone)

### Prerequisites
- Windows 10 or 11
- Python 3.8+ (Standard library only; zero third-party packages required for standard ctypes engine)

### Running Step 3

#### Method 1: 1-Click Windows Batch Runner (Recommended)
Double-click [`run_step3_keyboard_automation.bat`](./run_step3_keyboard_automation.bat) or [`run_step3.bat`](./run_step3.bat):
```cmd
run_step3_keyboard_automation.bat
```

#### Method 2: PowerShell Runner
```powershell
.\run_step3_keyboard_automation.ps1 -Countdown 3 -Option 1
```

#### Method 3: Direct Python CLI
```bash
python step3_keyboard_automation.py -c 3 -o 1
```

#### Method 4: Backward-Compatible Runner (Legacy)
```cmd
run_grill_me.bat
```

---

## 🌟 Intelligent Auto-Targeting & Maximization Subsystem

By default, regardless of current desktop state, Step 3 automatically inspects and prepares the target application window:
1. **Window Detection & Enumeration:** Scans all top-level windows via Win32 `EnumWindows`, strictly prioritizing `Antigravity.exe` (+1000 score) and Antigravity 2.0 process image paths.
2. **Web Browser Disqualification Gatekeeper:** Strictly disqualifies and rejects all web browsers (`chrome.exe`, `msedge.exe`, `firefox.exe`, `brave.exe`, `opera.exe`, etc.) to prevent accidental browser focus or address bar typing.
3. **Auto-Restore (Un-minimize):** If Antigravity is minimized (`IsIconic == True`), the subsystem automatically un-minimizes and restores it.
4. **Auto-Maximize (Full Screen):** If Antigravity is not maximized (`IsZoomed == False`), it automatically maximizes it (`SW_MAXIMIZE`) so the interface expands edge-to-edge.
5. **Foreground Lock Bypass & Focus:** Uses `AttachThreadInput` and synthetic `Alt` unlock signals to reliably bring Antigravity to the absolute foreground (`BringWindowToTop` / `SetForegroundWindow` / `SetFocus`).
6. **Pre-Execution Safety Verification:** Verifies the live foreground window immediately before key simulation; if a browser is detected, key injection aborts immediately.
7. **Geometry Verification & Settling Delay:** Verifies window bounds (`GetWindowRect`) and waits for rendering to stabilize (`--settle-delay 0.5s`) before injecting keystrokes.

---

## ⌨️ Keystroke Sequence & Dynamic Multi-Question Engine

### Single Question Workflow (N = 1)
```
[Target Detection: "Antigravity"]
          │
          ├─ Minimized?    ──> Restore Window (SW_RESTORE)
          ├─ Not Maxed?    ──> Maximize to Full Screen (SW_MAXIMIZE)
          ├─ Out of Focus? ──> BringToTop + SetForegroundWindow
          └─ Verified Geometry & Settle (500ms delay)
          │
          ▼
[Step Q1.1] Ctrl + L        ───>  Focus the chat input field / prompt box
          │ (350ms delay)
          ▼
[Step Q1.2] Shift + Tab     ───>  Navigate focus backwards to option choices
          │ (350ms delay)
          ▼
[Step Q1.3] 1 (or custom)   ───>  Select Option 1 (Recommended answer)
          │ (350ms delay)
          ▼
[Step Q1.4] Enter           ───>  Confirm and submit the selection
```

### Multi-Question Workflow (N >= 2) - Dynamic Quiz Mode
When multiple questions are present (e.g. 2, 3, or more questions in a single card):
- **For Questions 1 through N-1:**
  - `Ctrl + L` (Reset focus to chat input)
  - `Shift + Tab` (Navigate to option choices)
  - Select Option key (e.g. `1`)
  - **ENTER IS STRICTLY SUPPRESSED!** (Does NOT submit prematurely).
- **For Final Question N:**
  - `Ctrl + L`
  - `Shift + Tab`
  - Select Option key
  - **ENTER IS FIRED!** (Submits all chosen options in one atomic submission).

Auto-detection can read question counts and recommended options directly from `target_chat.json` generated by Step 1!

---

## ⚙️ CLI Arguments Reference

| Argument | Short | Type | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `--target-window` | `-t` | `str` | `"Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander"` | Window title / process keyword to locate, maximize, and focus. |
| `--questions` | `-q` | `str` | `"auto"` | Number of questions: `auto` (detect from `target_chat.json`), or integer (`1`, `2`, `3`). |
| `--options-list` | `-ol` | `str` | `None` | Comma-separated list of options per question (e.g. `1,1` or `1,2,1`). |
| `--state-file` | - | `str` | `None` | Path to `target_chat.json` state file for auto-detection. |
| `--auto-focus` | - | `bool` | `True` | Automatically bring target window to foreground before injection. |
| `--no-auto-focus` | - | `flag` | - | Disable automatic window focusing. |
| `--auto-maximize` | - | `bool` | `True` | Automatically un-minimize and maximize target window to full screen. |
| `--no-auto-maximize` | - | `flag` | - | Disable automatic window maximization. |
| `--settle-delay` | - | `float` | `0.5` | Settle delay in seconds after focus/maximize for UI rendering. |
| `--countdown` | `-c` | `int` | `5` | Countdown in seconds before keystrokes are triggered. |
| `--step-delay` | `-d` | `float` | `0.35` | Delay in seconds between steps (e.g. 0.35 = 350ms). |
| `--hold-delay` | - | `float` | `0.05` | Time in seconds each key is held down before release. |
| `--option` | `-o` | `str` | `"1"` | The fallback option character/number to choose. |
| `--skip-ctrl-l`| - | `flag`| `False` | Skip pressing `Ctrl + L` if input is already focused. |
| `--skip-enter` | - | `flag`| `False` | Skip pressing `Enter` to allow manual review before submitting. |
| `--dry-run` | - | `flag`| `False` | Simulates and logs all actions without sending physical key events. |
| `--engine` | `-e` | `str` | `"auto"`| Simulation engine: `auto`, `ctypes`, or `pyautogui`. |
| `--repeat` | `-r` | `int` | `1` | Number of times to run the sequence. |
| `--interval` | `-i` | `float` | `2.0` | Delay between repeat runs in seconds. |
| `--no-countdown`| - | `flag`| `False` | Execute immediately with 0s countdown delay. |

---

## 📦 Modular Architecture & Package Layout

```
Keyboard Automation/
├── step3_keyboard_automation.py       # PRIMARY Step 3 CLI entry point & sequence runner
├── run_step3_keyboard_automation.bat  # PRIMARY 1-Click Windows Batch launcher for Step 3
├── run_step3.bat                      # PRIMARY Quick shortcut batch launcher
├── run_step3_keyboard_automation.ps1  # PRIMARY Native PowerShell runner for Step 3
├── grill_me_automation.py             # Backward-compatible wrapper (<80 lines)
├── run_grill_me.bat                   # Backward-compatible Windows Batch launcher
├── run_grill_me.ps1                   # Backward-compatible PowerShell launcher
├── test_dynamic_questions.py          # Unit & integration regression test suite
├── requirements.txt                   # Dependency manifest (zero required external deps)
├── keyboard_automation/               # Modular Python Package
│   ├── __init__.py                    # Public API exports & Step 3 metadata
│   ├── constants.py                   # VK codes, Win32 flags, process blacklists, Step metadata
│   ├── win32_api.py                   # Native ctypes user32/kernel32 bindings
│   ├── input_injector.py              # SendInput key event / combo dispatcher & PyAutoGUI interop
│   ├── window_manager.py              # Window discovery, Antigravity scoring & focus lock bypass
│   ├── automator.py                   # Step3KeyboardAutomator sequence orchestrator
│   └── cli.py                         # Argument parser & Step 3 execution banner
└── archive/                           # Historical frozen v1.0.0-verified snapshot (untouched)
```

- **Zero External Dependencies:** Built with native Windows `ctypes.windll.user32` and `kernel32`. Runs on pure standard Python on Windows.
- **PyAutoGUI Interop:** Automatically detected as optional fallback if installed.

---

## 🔒 Safety & Gatekeeper Guarantees

1. **Browser Gatekeeper:** Web browsers (`chrome.exe`, `msedge.exe`, etc.) are disqualified and blocked from being focused or typed into.
2. **Pre-Execution Check:** Live foreground window is checked before key injection; aborts immediately if an unsafe window is active.
3. **Dry-Run Validation:** Use `--dry-run` anytime to verify detection, timing, and dynamic multi-question logic without sending real keystrokes.
4. **Untouched Archive:** The `archive/` folder remains frozen as a permanent reference snapshot.
