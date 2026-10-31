# AutoSelect-Commander 🎯

> **Autonomous Visual Mouse Automation & Auto-Selector for Antigravity Coding Agents**  
> **एंटीग्रेविटी कोडिंग एजेंट्स के लिए विज़ुअल माउस ऑटोमेशन एवं ऑटो-सिलेक्टर**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-blue.svg)](https://www.microsoft.com/)
[![Timer: 10s Default](https://img.shields.io/badge/Timer-10s%20Default-brightgreen.svg)](#modes-of-operation--cli-flags)
[![Fail-Safe: Active](https://img.shields.io/badge/Fail--Safe-Instant%20Mouse%20Override-red.svg)](#fail-safe--safety-features)
[![Overlay: Floating HUD](https://img.shields.io/badge/Overlay-Floating%20HUD%20(Top--Most)-brightgreen.svg)](#floating-on-screen-hud-overlay)
[![Engine: WinRT OCR](https://img.shields.io/badge/Engine-Windows%20Native%20OCR%20(50ms)-blue.svg)](#triple-engine-detection-architecture)

---

## 🌟 English Overview / परिचय (Hindi & English)

### What is AutoSelect-Commander?
When running long autonomous coding sessions with **Antigravity** (e.g. overnight testing, multi-file refactoring, git push gates), the agent prompts the developer with interactive modal cards via `ask_question`, where the recommended option is marked **`(Recommended)`**.

If you step away from your workstation, this halts the entire pair programming flow indefinitely. **AutoSelect-Commander v1.2.0** solves this completely:
1. **Interactive 1-Click Launcher Menu (`run.bat`):** Launch directly with `run.bat 1` (Live Demo), `run.bat 2` (Background Sentinel), or `run.bat 3` (Diagnostics), or let the 5-second automatic countdown default to Demo mode!
2. **10-Second Countdown Default:** High-efficiency 10-second default countdown timer across config, CLI, HUD, and demo.
3. **Reliable Firm Click:** Uses an explicit `mouseDown()` + 80ms dwell + `mouseUp()` sequence, eliminating dropped synthetic clicks on Electron, Chromium, and native Windows controls.
4. **Complete 2-Step Decision Flow:**
   - **Step 1:** Smoothly glides cursor to Option 1 `(Recommended)` and clicks firmly to select/highlight it.
   - **Step 2:** Smoothly glides cursor to the `Submit / पुष्टि करें` button and clicks firmly to confirm and submit.
5. **Antigravity Tracking & Auto-Foregrounding:** Detects if Antigravity is open/running. If closed, it notifies clearly: `एंटी-ग्रैविटी अभी ओपन नहीं है (Antigravity is currently not open)`. If minimized or running in the background, it restores (`SW_RESTORE`) and foregrounds it automatically without moving the mouse before starting countdown.
6. **Always-On-Top Floating HUD Overlay:** When a decision modal appears, a sleek floating HUD pops up at the very top of your display (`⏱️ AutoSelect-Commander: [████████░░░░] 8.2s remaining | Move mouse to cancel`), ensuring full visibility even if your terminal is minimized.
7. **Triple-Engine Detection (WinRT OCR + UIA + Vision):** Uses native Windows 10/11 WinRT OCR (`Windows.Media.Ocr`) to locate text regardless of font, theme, or window title in under 50ms, with zero API token spend.
8. **Instant Human Fail-Safe:** If you move the physical mouse (> 15 pixels), the countdown aborts immediately, yielding 100% control back to you.

### ऑटो-सेलेक्ट कमांडर क्या है?
जब आप एंटीग्रेविटी (Antigravity) में ऑटोमेशन या लंबे कोडिंग टास्क चलाते हैं, तो यह स्क्रीन पर `ask_question` कार्ड दिखाता है (जैसे `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना`)। यदि आप डेस्क पर नहीं हैं, तो पूरा काम रुक जाता है।  
**AutoSelect-Commander v1.2.0** इस समस्या का संपूर्ण समाधान है:
- **10 सेकंड का डिफ़ॉल्ट टाइमर:** तेज़ी से काम पूरा करने के लिए 10 सेकंड का टाइमर।
- **2-स्टेप कन्फर्मेशन फ्लो:** पहले Option 1 पर फर्म क्लिक करके चुनता है, फिर नीचे `Submit / पुष्टि करें` बटन पर क्लिक करके फॉर्म सबमिट करता है।
- **फर्म क्लिक (Firm Click):** माउस को 80ms तक दबाकर विश्वसनीय क्लिक करता है, ताकि इलेक्ट्रॉन/वेब यूआई कोई क्लिक मिस न करे।
- **ऑटो-विंडो फोरग्राउंडिंग:** यदि एंटीग्रेविटी मिनिमाइज़ या बैकग्राउंड में है, तो बिना माउस हिलाए उसे खुद फोरग्राउंड में लाता है। यदि ओपन नहीं है, तो स्पष्ट मैसेज देता है: `एंटी-ग्रैविटी अभी ओपन नहीं है (Antigravity is currently not open)`।
- **फ्लोटिंग स्क्रीन टाइमर (Floating HUD):** स्क्रीन के सबसे ऊपर एक सुंदर तैरता हुआ टाइमर बार दिखाता है।
- **इंस्टेंट माउस कंट्रोल:** माउस जरा सा (15px) हिलाते ही टाइमर तुरंत कैंसिल हो जाता है और पूरा नियंत्रण आपके हाथ में आ जाता है।

---

## 🚀 1-Click Interactive Launcher / शुरू कैसे करें

### 1-Click Launcher Menu (`run.bat`)
Simply double-click `run.bat` on your Desktop, or pass direct arguments:
```cmd
run.bat 1    # Directly launch Live Visual Demo Mode
run.bat 2    # Directly launch Active Background Sentinel
run.bat 3    # Directly launch Screen & Window Diagnostics
```

Or run `run.bat` interactively:
```cmd
=============================================================================
                            SELECT EXECUTION MODE
=============================================================================

  [1] Live Visual Demo / Test Mode (Recommended)
      -> Spawns mock question card, floating countdown HUD & glides mouse!

  [2] Active Background Sentinel
      -> Monitors live screen for Antigravity decision modals.

  [3] Screen & Window Diagnostics
      -> Scans screen, tests OCR, lists detected windows and text.

  [4] Exit

-----------------------------------------------------------------------------
Auto-launching [1] Demo Mode in 5 seconds (Press 1, 2, 3, or 4 to choose now)...
-----------------------------------------------------------------------------
```

---

## 🖥️ Floating On-Screen HUD Overlay

Whenever an Antigravity question card is detected (or during Demo mode), the built-in **Floating HUD** appears at the top center of your primary monitor:

```
┌────────────────────────────────────────────────────────────────────────┐
│  ⏱️ AutoSelect-Commander | Auto-Selecting: (Recommended) Option       │
│  [████████████████░░░░░░]  8.4s remaining | Move mouse to cancel       │
└────────────────────────────────────────────────────────────────────────┘
```

- **Top-Most & Semi-Transparent:** Stays visible above Visual Studio Code, Antigravity, Chrome, and full-screen windows.
- **Dynamic Color Gradient:** Progress bar shifts smoothly from Green (> 6s) ➔ Warm Yellow (> 3s) ➔ Soft Red (≤ 3s).
- **2-Step Progress Badges:** Dynamically updates: `Step 1/2: Selecting Option 1...` ➔ `Step 2/2: Confirming Submission...`.

---

## 🔍 Triple-Engine Detection Architecture

| Engine | Technology | Performance | Strengths |
| :--- | :--- | :--- | :--- |
| **Engine 1 (Primary)** | **Windows WinRT OCR (`Windows.Media.Ocr`)** | ~30-50ms | 100% immune to font, theme, antialiasing, and window title variations. |
| **Engine 2 (Secondary)** | **Windows UIAutomation (`uiautomation`)** | ~20ms | Inspects native control trees and accessibility labels without screen grabbing. |
| **Engine 3 (Fallback)** | **Computer Vision (`opencv-python`)** | ~60ms | Multi-scale, multi-theme normalized cross-correlation template matching. |

---

## 🧪 Modes of Operation & CLI Flags

### 1. Live Visual Demo (`--demo` / `--simulate` / `--test`)
```powershell
python auto_commander.py --demo
```
Spawns a mock Antigravity question card, shows the floating HUD at the top, and demonstrates the complete 2-step flow:
1. Glides cursor to `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना` and firmly clicks.
2. Glides cursor to `Submit / पुष्टि करें` button and firmly clicks to submit with sound alert!

### 2. Active Sentinel Mode (Daemon)
```powershell
python auto_commander.py
```
Monitors your desktop in the background. When an Antigravity prompt appears, it activates the HUD, counts down 10s, and completes the 2-step submission.

### 3. Screen Diagnostics (`--diagnostics`)
```powershell
python auto_commander.py --diagnostics
```
Scans display resolution, checks OCR engine status, enumerates visible windows, and probes text elements.

---

## 🛡️ Fail-Safe & Safety Features / सुरक्षा फीचर्स

| Safety Feature | Description / विवरण |
| :--- | :--- |
| **Instant Mouse Abort** | Moving the physical mouse > 15px aborts the countdown immediately and returns control to developer. (माउस 15px हिलते ही ऑटो-क्लिक रद्द). |
| **HUD Cancellation Alert** | Floating HUD immediately flashes red (`⚠️ INTERRUPTED — Developer Control Restored`) upon human intervention. |
| **Screen Corner Emergency Stop** | Moving the mouse cursor into any corner of the screen (`0, 0`) triggers PyAutoGUI failsafe. |
| **Hotkey Abort** | Press **`ESC`** or **`Q`** at any moment to cancel the active countdown or stop the daemon. |
| **High-DPI Awareness** | Certified Windows Per-Monitor DPI awareness (`SetProcessDpiAwareness(2)`) eliminates coordinate drift on 125%/150% scaled displays. |

---

## ⚙️ Configuration (`config.json`)

```json
{
  "countdown_seconds": 10,
  "check_interval_ms": 1000,
  "mouse_interruption_threshold_px": 15,
  "smooth_glide_duration_s": 0.8,
  "cooldown_after_dismissal_s": 5,
  "failsafe_enabled": true,
  "sound_notification": true,
  "window_title_filter": "",
  "floating_hud_enabled": true,
  "floating_hud_alpha": 0.92,
  "ocr_enabled": true,
  "target_keywords": [
    "(Recommended)",
    "Recommended",
    "(अनुशंसित)",
    "अनुशंसित",
    "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
    "(Recommended) GitHub",
    "Proceed"
  ],
  "submit_keywords": [
    "Submit",
    "पुष्टि करें",
    "Confirm",
    "Proceed",
    "Submit / पुष्टि करें",
    "जारी रखें"
  ],
  "detection_mode": "auto"
}
```

---

## 🏛️ Project Structure

```
C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
├── auto_commander.py        # Core Python daemon & triple-engine state machine
├── config.json              # Configurable countdown (10s), HUD, and OCR parameters
├── requirements.txt         # Lightweight Python dependencies (including winsdk)
├── run.bat                  # 1-Click Interactive Menu launcher (supports run.bat 1, 2, 3)
├── README.md                # Comprehensive bilingual documentation
├── PRD.md                   # Product Requirements Document
├── changes_log/             # Comprehensive 5-tier audit changes trail
├── assets/
│   └── templates/           # Multi-theme visual templates for OpenCV fallback
└── tests/
    └── test_commander.py    # Automated test suite (13/13 tests passing)
```

---

## 👤 Author & Identity

- **Developer:** Atul Verma (`aiprincekumar`)
- **Email:** `aiprincekumar010100@gmail.com`
- **GitHub:** [https://github.com/aiprincekumar](https://github.com/aiprincekumar)
- **License:** MIT License
