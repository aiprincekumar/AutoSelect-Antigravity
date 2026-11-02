# Quiz Keyboard Automation Subsystem

> **Module:** `Quiz Automation/`  
> **Target:** Antigravity 2.0 Interactive Prompt / Multi-Question Quiz Mode  
> **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Standard:** UTF-8 Encoding  

---

## 🎯 1. Overview & Purpose (अवलोकन और उद्देश्य)

In Google Antigravity 2.0 (e.g. `ask_question` tool / Grill-Me mode), multi-question interactive cards present several interdependent questions (Q1, Q2, ..., QN) inside a single modal or chat prompt.

If an automation tool presses `Enter` on Question 1, the modal may submit prematurely with incomplete answers or fail validation. 

### ⚡ The Golden Enter Gate Rule (स्वर्ण नियम: अंतिम प्रश्न पर ही एंटर)
- **Questions $1 \dots N-1$ (Intermediate Questions):**
  - Focus input (`Ctrl + L`)
  - Reverse tab to options (`Shift + Tab`)
  - Select option key (e.g. `1`)
  - **STRICTLY SUPPRESS ENTER!** UI settles and loop advances immediately to the next question.
- **Question $N$ (Final Question):**
  - Focus input (`Ctrl + L`)
  - Reverse tab to options (`Shift + Tab`)
  - Select option key (e.g. `1`)
  - **PRESS ENTER** to submit all choices simultaneously!

---

## 🔁 2. Keystroke Loop Architecture

```mermaid
flowchart TD
    Start([Start Quiz Automation Loop]) --> LoadCount[Load N from question_count.json or CLI]
    LoadCount --> PrepareWin[Target Window: Restore + Maximize + Alt-Pulse Focus]
    PrepareWin --> LoopInit[Set q = 1]
    LoopInit --> StepA["[Step 1] Press Ctrl + L (Focus input box)"]
    StepA --> StepB["[Step 2] Press Shift + Tab (Reverse tab to options)"]
    StepB --> StepC["[Step 3] Press Option Key (e.g. '1')"]
    StepC --> CheckLast{Is q == N (Final Question)?}
    CheckLast -- "No (q < N)" --> Suppress["[Step 4] SUPPRESS ENTER! Settle delay..."]
    Suppress --> NextQ[q = q + 1] --> StepA
    CheckLast -- "Yes (q == N)" --> PressEnter["[Step 4] Press Enter (Submit Batch Response)"]
    PressEnter --> Success([Automation Complete])
```

---

## 🛡️ 3. Antigravity 2.0 Focus & Safety Shield

1. **Window State Restoration:**
   - Detects if Antigravity is minimized (`IsIconic`) and restores it via `ShowWindow(SW_RESTORE)`.
   - Optionally maximizes window to full screen (`SW_MAXIMIZE`) to guarantee visible UI controls.
2. **Win32 Alt-Pulse Focus Bypass:**
   - Attaches thread input to current foreground thread (`AttachThreadInput`).
   - Pulses Alt key (`VK_MENU`) to bypass Windows foreground lock restrictions.
   - Calls `SetForegroundWindow` + `BringWindowToTop` + `AllowSetForegroundWindow(ASFW_ANY)`.
3. **External Browser Disqualification Safety:**
   - Probes executable of active foreground window.
   - If user is browsing in Chrome, Edge, Firefox, or Brave, the automation safely halts to prevent sending accidental keystrokes to browser tabs.

---

## 🚀 4. Usage & Launchers

### 1-Click Launchers (Windows Batch)

1. **Standalone Quiz Automation (`run_quiz.bat`):**
   - Reads question count automatically from `question_count.json` or allows manual input.
   - Offers Dry-Run simulation mode.
   ```cmd
   run_quiz.bat
   ```

2. **Chained Detection & Execution (`run_detection_and_quiz.bat`):**
   - Automatically executes `Question Detection` (Stage 1), writes `question_count.json`, and immediately feeds the count into `Quiz Automation` (Stage 2).
   ```cmd
   run_detection_and_quiz.bat
   ```

### Command Line Interface (Python)

```bash
# Auto-run from question_count.json
python quiz_automation.py --questions auto

# Run explicitly with 2 questions
python quiz_automation.py --questions 2

# Select different options per question (e.g., Option 1 for Q1, Option 2 for Q2)
python quiz_automation.py --questions 2 --options 1,2

# Safe Dry-Run (simulate without sending physical keystrokes)
python quiz_automation.py --questions 3 --dry-run

# Custom delays
python quiz_automation.py --questions 2 --step-delay 0.4 --settle-delay 0.6
```

---

## 📊 5. CLI Arguments Reference

| Flag | Default | Description |
| :--- | :--- | :--- |
| `-q`, `--questions` | `auto` | Question count (`auto` to read `question_count.json`, or integer $N$) |
| `-o`, `--options` | `1` | Comma-separated option keys (e.g. `1` or `1,2,1`) |
| `-i`, `--input-file` | `None` | Custom path to `question_count.json` |
| `--dry-run` | `False` | Simulate all actions without sending physical keystrokes |
| `--skip-enter` | `False` | Suppress Enter even on final question |
| `-t`, `--target` | `Antigravity...` | Comma-separated window title/process tokens |
| `--no-maximize` | `False` | Disable automatic window maximization |
| `--no-focus` | `False` | Disable automatic window foregrounding |
| `--step-delay` | `0.35` | Delay in seconds between keystrokes |
| `--hold-delay` | `0.05` | Duration key is held down in seconds |
| `--settle-delay` | `0.50` | Settle delay between questions in seconds |
| `-c`, `--countdown` | `0` | Countdown seconds before starting sequence |
