# Step 3: Select Recommendation & Golden Enter Gate - Autonomous Agent Implementation Prompt

> **Document Type:** Autonomous Agent Engineering Specification & Execution Blueprint  
> **Target Module:** `Keyboard Automation/step_3_select_the_recommendation/`  
> **Pipeline Step:** Step 3 of 9 (Hardware Keystroke Injection, Multi-Question Scaling & Enter Gate)  
> **Suite:** AutoSelect-Commander  
> **Primary Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** Department 01 (Product Requirements) & Department 06 (Backend & API Engineering)  
> **Status:** APPROVED FOR AUTONOMOUS AGENT EXECUTION  

---

## 🎯 1. Mission & System Directive

You are tasked with implementing, verifying, or executing **Step 3: Keyboard Automation (Option Selection & Confirmation)** of the AutoSelect-Commander automation pipeline.

### Core Directive
The agent running this step must:
1. Ingest question count $N$, target window handle, and selected option choices from `target_chat.json`.
2. Check if Step 1 signalled `NO_PENDING_CHATS` or `cancelled_remaining_steps: true`. If so, exit cleanly with code `0`.
3. Disqualify shell consoles (`cmd.exe`, `powershell.exe`, `WindowsTerminal.exe`, `conhost.exe`) and web browsers (`chrome.exe`, `msedge.exe`) to prevent accidental keystroke theft.
4. Utilize `core_engine/` (Core Win32 Automation & Input Injection Engine) for robust `SendInput` hardware scan code injection and active window management.
5. Execute pure native Win32 `SendInput` hardware keystroke sequences:
   - For intermediate questions $Q_1, Q_2, \dots, Q_{N-1}$:
     - `Ctrl + L` (focus input box)
     - `Shift + Tab` (navigate backward to option button group)
     - `Option Key` (select option number, e.g. `'1'`)
     - **CRITICAL:** **DO NOT PRESS ENTER!**
   - For final question $Q_N$:
     - `Ctrl + L`
     - `Shift + Tab`
     - `Option Key`
     - **THE GOLDEN ENTER GATE:** **PRESS ENTER** to commit and submit the batch questionnaire response.

---

## 🔍 2. Architectural Blueprint & Operational Flow

```mermaid
flowchart TD
    Start([Execute Step 3]) --> IngestState[Read target_chat.json]
    IngestState --> CheckCancel{status == NO_PENDING_CHATS or cancelled == true?}
    
    CheckCancel -- Yes --> CleanExit([Log Step 3 Cancelled Notice & Exit Code 0])
    CheckCancel -- No --> IngestQ[Extract Total Questions N and Options List O1..ON]
    
    IngestQ --> DetectWindow[Scan & Verify Antigravity Target Window]
    DetectWindow --> BlacklistCheck{Active Process in Console or Browser Blacklist?}
    
    BlacklistCheck -- Yes (Blacklisted) --> FocusTarget[Force Focus Back to Antigravity HWND]
    BlacklistCheck -- No --> WindowReady[Window Verified & Stable]
    FocusTarget --> WindowReady
    
    WindowReady --> LoopInit[Initialize Dynamic Progression Loop: q = 1]
    
    subgraph MultiQuestionLoop [Deterministic Multi-Question Progression Loop]
        LoopInit --> LoopCheck{q <= N?}
        LoopCheck -- Yes --> StepA[Step A: SendInput Ctrl + L - Focus Input Pane]
        StepA --> PauseA[Settle Pause: step_delay = 0.22s]
        
        PauseA --> StepB[Step B: SendInput Shift + Tab - Reverse to Option Group]
        StepB --> PauseB[Settle Pause: step_delay = 0.22s]
        
        PauseB --> StepC[Step C: SendInput Option Key e.g. '1']
        StepC --> PauseC[Settle Pause: step_delay = 0.22s]
        
        PauseC --> IsLastQuestion{Is q == N (Final Question)?}
        
        IsLastQuestion -- No (Intermediate Q) --> SkipEnter[DO NOT PRESS ENTER! Settle Pause 0.4s]
        SkipEnter --> IncrementQ[q = q + 1]
        IncrementQ --> LoopCheck
        
        IsLastQuestion -- Yes (Golden Enter Gate) --> PressEnter[THE GOLDEN ENTER GATE: SendInput ENTER]
        PressEnter --> SettleSubmit[Submission Settle Pause 0.5s]
        SettleSubmit --> LoopDone[Loop Finished]
    end
    
    LoopCheck -- No --> LoopDone
    LoopDone --> FinalLog[Log Pipeline Success & Audit Trail]
    FinalLog --> SuccessExit([Exit with Code 0 - SUCCESS])
```

---

## 🛠️ 3. Exhaustive Technical Specifications

### 3.1 State File Ingestion & Cancellation Passthrough
Step 3 reads `target_chat.json` to configure its loop parameters dynamically:

```python
# 1. State Ingestion
state_data = {}
with open(state_file, "r", encoding="utf-8") as f:
    envelope = json.load(f)
    state_data = envelope.get("data", {})

# 2. Check Cancellation Status
if state_data.get("status") == "NO_PENDING_CHATS" or state_data.get("cancelled_remaining_steps") is True:
    logger.info("State file indicates NO_PENDING_CHATS. Step 3 cancelled cleanly.")
    return 0

# 3. Dynamic Question Count Resolution
total_questions = 1
options_list = []

if "questions" in state_data and isinstance(state_data["questions"], list):
    total_questions = len(state_data["questions"])
    for q in state_data["questions"]:
        opt_idx = q.get("recommended_option_index") or 1
        options_list.append(str(opt_idx))
elif "total_questions_count" in state_data:
    total_questions = int(state_data["total_questions_count"])
    options_list = [state_data.get("default_option", "1")] * total_questions
```

### 3.2 Target Window Safety & Console Blacklist Verification
Before injecting keystrokes into the OS message queue, Step 3 verifies that the currently focused window is **not** an executing console or unauthorized web browser.

#### Disqualified Process Sets
```python
DISQUALIFIED_BROWSER_PROCS = {
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", 
    "opera.exe", "vivaldi.exe", "arc.exe"
}

BLACK_LISTED_SHELL_PROCS = {
    "cmd.exe", "powershell.exe", "windowsterminal.exe", 
    "conhost.exe", "bash.exe", "wsl.exe", "wt.exe"
}
```

#### Window Verification Subsystem
1. Query foreground window handle: `fore_hwnd = user32.GetForegroundWindow()`.
2. Retrieve PID and process image name via `kernel32.OpenProcess` and `psapi.GetModuleBaseNameW`.
3. If the active window matches `BLACK_LISTED_SHELL_PROCS` or `DISQUALIFIED_BROWSER_PROCS`:
   - Immediately abort keystroke dispatch or force restore focus to Antigravity's target HWND using the Win32 focus lock release protocol.

---

## ⚡ 4. Pure Native Win32 `SendInput` Hardware Keystroke Subsystem

Step 3 uses the Windows native `SendInput` API via Python `ctypes`. Unlike legacy `keybd_event` or software hooks, `SendInput` injects physical hardware scan codes directly into the Windows input stream, bypassing UI virtualization barriers and Chromium focus traps.

### Ctypes Structural Definitions
```python
import ctypes
from ctypes import wintypes

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class InputUnion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", InputUnion)]

INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
```

### Scan Code Resolution & Key Combos
To ensure zero key drop across physical keyboards:
```python
def send_key_combo(vk_codes: List[int], hold_delay: float = 0.05):
    """Presses a sequence of keys down, then releases them in reverse order."""
    # 1. Key Down (Forward order)
    for vk in vk_codes:
        scan = user32.MapVirtualKeyW(vk, 0)
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.union.ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=KEYEVENTF_KEYDOWN, time=0, dwExtraInfo=None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    
    time.sleep(hold_delay)
    
    # 2. Key Up (Reverse order)
    for vk in reversed(vk_codes):
        scan = user32.MapVirtualKeyW(vk, 0)
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.union.ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
```

### Virtual Key Code Reference
| Virtual Key | Hex Code | Decimal | Target Action |
| :--- | :---: | :---: | :--- |
| `VK_CONTROL` | `0x11` | 17 | Modifier for chat focus |
| `VK_L` | `0x4C` | 76 | Primary key for chat focus (`Ctrl + L`) |
| `VK_SHIFT` | `0x10` | 16 | Modifier for reverse tab |
| `VK_TAB` | `0x09` | 9 | Reverse navigation (`Shift + Tab`) |
| `VK_RETURN` | `0x0D` | 13 | Final batch questionnaire submit (**Enter**) |
| `VK_1` .. `VK_9` | `0x31` .. `0x39` | 49 .. 57 | Numbered option selections (Option 1 to 9) |

---

## 🔁 5. Dynamic Multi-Question Progression Loop (The Golden Enter Gate)

When $N$ questions are detected ($N \ge 1$), the loop executes deterministically:

```python
def execute_multi_question(total_questions: int, options: List[str], step_delay: float = 0.22, hold_delay: float = 0.05) -> bool:
    logger.info(f"Initiating multi-question automation loop: {total_questions} questions")
    
    for q_idx in range(1, total_questions + 1):
        opt = options[q_idx - 1] if q_idx - 1 < len(options) else "1"
        opt_vk = get_option_vk(opt) # maps '1' -> VK_1 (0x31)
        is_last = (q_idx == total_questions)
        
        logger.info(f"--- Processing Question {q_idx}/{total_questions} [Select Option: '{opt}'] ---")
        
        # Step A: Focus chat box
        send_key_combo([VK_CONTROL, VK_L], hold_delay=hold_delay)
        time.sleep(step_delay)
        
        # Step B: Reverse tab into option button group
        send_key_combo([VK_SHIFT, VK_TAB], hold_delay=hold_delay)
        time.sleep(step_delay)
        
        # Step C: Select option key
        send_single_key(opt_vk, hold_delay=hold_delay)
        time.sleep(step_delay)
        
        # Step D: THE GOLDEN ENTER GATE
        if not is_last:
            # Intermediate question (Q1 .. QN-1)
            logger.info(f"[GATE PASS] Question {q_idx}/{total_questions}: Choice registered. DO NOT PRESS ENTER.")
            time.sleep(0.4) # UI transition settle pause
        else:
            # Final question (QN)
            logger.info(f"[GOLDEN ENTER GATE] Final Question {q_idx}/{total_questions}: PRESSING ENTER TO SUBMIT!")
            send_single_key(VK_RETURN, hold_delay=hold_delay)
            time.sleep(0.5)
            logger.info("[SUBMITTED] Full questionnaire batch committed.")
            
    return True
```

---

## ⏱️ 6. Timing & Latency Calibrations

| Parameter | Calibrated Value | Purpose |
| :--- | :---: | :--- |
| `hold_delay` | `0.05s` (50ms) | Minimum key hold duration ensuring Electron/DOM event listeners register keydown. |
| `step_delay` | `0.22s` (220ms) | Inter-step settle time allowing DOM focus tree transitions to complete. |
| `settle_delay` | `0.30s` (300ms) | Window foreground focus stabilization delay. |
| `inter_question_delay` | `0.40s` (400ms) | Pause between consecutive questions during multi-question card execution. |
| `countdown` | `0s` (default with `--no-countdown`) | Eliminates blocking countdowns during autonomous agent execution. |

---

## 💻 7. CLI Parameters & Standalone Runner

### Runner Location: `step_3_select_the_recommendation\run_step3.bat`
```cmd
cd "c:\Users\Atul Verma\Desktop\AutoSelect-Commander\Keyboard Automation\step_3_select_the_recommendation"
run_step3.bat
```

### CLI Flag Reference
| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--state-file` | `str` | `"target_chat.json"` | Path to read questions, options, and status. |
| `--questions` | `int` or `"auto"` | `"auto"` | Explicit question count override (auto-detects from state). |
| `--options-list` | `str` | `None` | Comma-separated options (e.g. `"1,2,1,1"`). |
| `--engine` | `str` | `"auto"` | Injection engine: `"ctypes"` (native SendInput), `"pyautogui"`, or `"auto"`. |
| `--step-delay` | `float` | `0.22` | Delay between sequence keystrokes in seconds. |
| `--hold-delay` | `float` | `0.05` | Keystroke depression duration in seconds. |
| `--no-countdown` | `flag` | `False` | Skips visual countdown for autonomous pipelines. |
| `--dry-run` | `flag` | `False` | Logs intended keystrokes without dispatching hardware input. |

---

## 🧪 8. Acceptance Criteria (Given-When-Then)

### Scenario 3-A: Clean Cancellation when No Pending Chat
- **Given:** `target_chat.json` contains `status: "NO_PENDING_CHATS"`.
- **When:** `step3_keyboard_automation.py` is executed.
- **Then:** It detects cancellation status, resolves question count to 0, logs cancellation notice, and cleanly exits with code `0`.

### Scenario 3-B: Single-Question Selection & Submission ($N = 1$)
- **Given:** `target_chat.json` specifies 1 question with recommended option 1.
- **When:** `step3_keyboard_automation.py` runs.
- **Then:** It dispatches `Ctrl + L` $\to$ `Shift + Tab` $\to$ `1` $\to$ `Enter`, submitting the response, and exits with code `0`.

### Scenario 3-C: Multi-Question Batch Survey ($N = 4$) with The Golden Enter Gate
- **Given:** `target_chat.json` specifies 4 questions with selected options `[1, 1, 1, 1]`.
- **When:** `step3_keyboard_automation.py` runs.
- **Then:** 
  - For $Q_1, Q_2, Q_3$: It executes `Ctrl + L` $\to$ `Shift + Tab` $\to$ `1`, and strictly skips Enter.
  - For $Q_4$: It executes `Ctrl + L` $\to$ `Shift + Tab` $\to$ `1` $\to$ `Enter`.
  - The batch submission is complete and the script terminates with exit code `0`.

---

## 🔗 9. Integration Contract with Step 9 (Master Orchestrator)

Step 3 is orchestrated sequentially by **Step 9: Complete Automation Hub** (`step_9_complete_automation/complete_automation.py`):
1. **Config Toggle:** Step 9 inspects `config.json` (`enabled_steps.step3_keyboard_automation`). If disabled, Step 9 skips Step 3 cleanly.
2. **Pre-Step Settle:** Step 9 pauses for 0.8s after Step 2 finishes before invoking Step 3.
3. **Execution & Failure Isolation:** Step 9 invokes Step 3 and evaluates the return code. If Step 3 succeeds (code 0), Step 9 settles for 0.8s before executing Step 4. If Step 3 fails, Step 9 halts and logs the failure to prevent corrupted reporting.
4. **Underlying Engine:** Step 3 imports directly from `core_engine` (Core Win32 Automation & Input Injection Engine), ensuring zero dependencies on legacy external tools.
