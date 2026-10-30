# AutoSelect-Commander 🎯

> **Autonomous Visual Mouse Automation & Auto-Selector for Antigravity Coding Agents**  
> **एंटीग्रेविटी कोडिंग एजेंट्स के लिए विज़ुअल माउस ऑटोमेशन एवं ऑटो-सिलेक्टर**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-blue.svg)](https://www.microsoft.com/)
[![Fail-Safe: Active](https://img.shields.io/badge/Fail--Safe-Instant%20Mouse%20Override-red.svg)](#fail-safe--safety-features)
[![Overlay: Floating HUD](https://img.shields.io/badge/Overlay-Floating%20HUD%20(Top--Most)-brightgreen.svg)](#floating-on-screen-hud-overlay)
[![Engine: WinRT OCR](https://img.shields.io/badge/Engine-Windows%20Native%20OCR%20(50ms)-blue.svg)](#triple-engine-detection-architecture)

---

## 🌟 English Overview / परिचय (Hindi & English)

### What is AutoSelect-Commander?
When running long autonomous coding sessions with **Antigravity** (e.g. overnight testing, multi-file refactoring, git push gates), the agent prompts the developer with interactive modal cards via `ask_question`, where the recommended option is marked **`(Recommended)`**.

If you step away from your workstation, this halts the entire pair programming flow indefinitely. **AutoSelect-Commander v1.1.0** solves this completely:
1. **Interactive 1-Click Launcher Menu (`run.bat`):** Launch directly with a 5-second automatic countdown defaulting to **[1] Live Visual Demo**, giving you instant proof on screen!
2. **Always-On-Top Floating HUD Overlay:** When a decision modal appears, a sleek floating HUD pops up at the very top of your display (`⏱️ AutoSelect-Commander: [████████░░░░] 25s remaining | Move mouse to cancel`), ensuring you see the timer even if your terminal is minimized or behind your IDE.
3. **Triple-Engine Detection (WinRT OCR + UIA + Vision):** Uses native Windows 10/11 WinRT OCR (`Windows.Media.Ocr`) to locate text regardless of font, theme, or workspace window title in under 50ms, with zero API token spend.
4. **Instant Human Fail-Safe:** If you move the physical mouse (> 15 pixels), the countdown aborts immediately, yielding 100% control back to you.
5. **Smooth Cubic Easing Glide:** If untouched, it smoothly glides the mouse cursor with human-like easing (`easeInOutQuad`) and auto-selects the `(Recommended)` option.

### ऑटो-सेलेक्ट कमांडर क्या है?
जब आप एंटीग्रेविटी (Antigravity) में ऑटोमेशन या लंबे कोडिंग टास्क चलाते हैं, तो यह स्क्रीन पर `ask_question` कार्ड दिखाता है (जैसे `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना`)। यदि आप डेस्क पर नहीं हैं, तो पूरा काम रुक जाता है।  
**AutoSelect-Commander v1.1.0** इस समस्या का संपूर्ण समाधान है:
- **1-क्लिक इंटरएक्टिव मेनू (`run.bat`):** 5 सेकंड में डिफ़ॉल्ट रूप से लाइव डेमो शुरू करता है ताकि आपको तुरंत काम करते हुए दिखाई दे!
- **फ्लोटिंग स्क्रीन टाइमर (Floating HUD):** स्क्रीन के सबसे ऊपर एक सुंदर तैरता हुआ टाइमर बार दिखाता है—टर्मिनल बैकग्राउंड में होने पर भी सब कुछ स्पष्ट दिखता है।
- **विंडोज़ नेटिव ओसीआर (WinRT OCR):** 50 मिलीसेकंड में स्क्रीन पर किसी भी फॉन्ट/थीम में लिखे `(Recommended)` शब्द को पकड़ लेता है।
- **इंस्टेंट माउस कंट्रोल:** माउस जरा सा (15px) हिलाते ही टाइमर तुरंत कैंसिल हो जाता है और पूरा नियंत्रण आपके हाथ में आ जाता है।

---

## 🚀 1-Click Interactive Launcher / शुरू कैसे करें

### 1-Click Launcher Menu (`run.bat`)
Simply double-click `run.bat` on your Desktop:
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

-----------------------------------------------------------------------------
Auto-launching [1] Demo Mode in 5 seconds (Press 1, 2, or 3 to choose now)...
-----------------------------------------------------------------------------
```
- If you don't press any key, it **automatically launches Option [1] Demo Mode in 5 seconds**, showing you a mock question card, the floating HUD, and the smooth mouse glide right before your eyes!
- Press **`2`** to start the continuous Background Sentinel daemon.
- Press **`3`** to run deep Screen & Window Diagnostics.

---

## 🖥️ Floating On-Screen HUD Overlay

Whenever an Antigravity question card is detected (or during Demo mode), the built-in **Floating HUD** appears at the top center of your primary monitor:

```
┌────────────────────────────────────────────────────────────────────────┐
│  ⏱️ AutoSelect-Commander | Auto-Selecting: (Recommended) Option       │
│  [████████████████░░░░░░] 22.4s remaining | Move mouse to cancel       │
└────────────────────────────────────────────────────────────────────────┘
```

- **Top-Most & Semi-Transparent:** Stays visible above Visual Studio Code, Antigravity, Chrome, and full-screen windows.
- **Dynamic Color Gradient:** Progress bar shifts smoothly from Green (> 10s) ➔ Warm Yellow (> 5s) ➔ Soft Red (≤ 5s).
- **Zero Extra Dependencies:** Powered by Python's built-in `tkinter` library.

---

## 🔍 Triple-Engine Detection Architecture

| Engine | Technology | Performance | Strengths |
| :--- | :--- | :--- | :--- |
| **Engine 1 (Primary)** | **Windows WinRT OCR (`Windows.Media.Ocr`)** | ~30-50ms | 100% immune to font, theme, antialiasing, and window title variations. |
| **Engine 2 (Secondary)** | **Windows UIAutomation (`uiautomation`)** | ~20ms | Inspects native control trees and accessibility labels without screen grabbing. |
| **Engine 3 (Fallback)** | **Computer Vision (`opencv-python`)** | ~60ms | Multi-scale, multi-theme normalized cross-correlation template matching. |

---

## 🧪 Modes of Operation & CLI Flags

### 1. Live Visual Demo (`--simulate` / `--test`)
```powershell
python auto_commander.py --simulate
```
Spawns a mock Antigravity question card, shows the floating HUD at the top, and smoothly glides the mouse cursor to click `Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना`.

### 2. Active Sentinel Mode (Daemon)
```powershell
python auto_commander.py
```
Monitors your desktop in the background. When an Antigravity prompt appears, it activates the HUD, counts down 30s, and auto-selects.

### 3. Screen Diagnostics (`--diagnostics`)
```powershell
python auto_commander.py --diagnostics
```
Scans your display resolution, checks OCR engine status, enumerates visible windows, and probes text elements.

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
  "countdown_seconds": 30,
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
  "detection_mode": "auto"
}
```

---

## 🏛️ Project Structure

```
C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
├── auto_commander.py        # Core Python daemon & triple-engine state machine
├── config.json              # Configurable countdown, HUD, and OCR parameters
├── requirements.txt         # Lightweight Python dependencies (including winsdk)
├── run.bat                  # 1-Click Interactive Menu launcher (5s default to Demo)
├── README.md                # Comprehensive bilingual documentation
├── PRD.md                   # Product Requirements Document
├── assets/
│   └── templates/           # Multi-theme visual templates for OpenCV fallback
└── tests/
    └── test_commander.py    # Automated test suite (10/10 tests passing)
```

---

## 👤 Author & Identity

- **Developer:** Atul Verma (`aiprincekumar`)
- **Email:** `aiprincekumar010100@gmail.com`
- **GitHub:** [https://github.com/aiprincekumar](https://github.com/aiprincekumar)
- **License:** MIT License
