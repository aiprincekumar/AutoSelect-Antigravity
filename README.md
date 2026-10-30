# AutoSelect-Commander 🎯

> **Autonomous Visual Mouse Automation & Auto-Selector for Antigravity Coding Agents**  
> **एंटीग्रेविटी कोडिंग एजेंट्स के लिए विज़ुअल माउस ऑटोमेशन एवं ऑटो-सिलेक्टर**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-blue.svg)](https://www.microsoft.com/)
[![Fail-Safe: Active](https://img.shields.io/badge/Fail--Safe-Instant%20Mouse%20Override-red.svg)](#fail-safe--safety-features)

---

## 🌟 English Overview / परिचय (Hindi & English)

### What is AutoSelect-Commander?
When running long autonomous coding sessions with **Antigravity** (e.g. overnight testing, multi-file refactoring, git push gates), the agent often prompts the developer with an interactive modal card via `ask_question`, where the first option is marked **`(Recommended)`**.

If you step away from your desk, this halts the entire pair programming flow indefinitely. **AutoSelect-Commander** solves this:
1. It continuously monitors the screen using **Dual-Mode Detection** (Windows UIAutomation + OpenCV Computer Vision).
2. When a modal containing `(Recommended)` appears, it triggers a **30-second visual countdown** in your terminal.
3. **Instant Human Override:** If you touch or nudge the mouse (> 15 pixels), the countdown aborts immediately, giving you 100% control!
4. If left untouched for 30s, it smoothly glides the mouse cursor to `(Recommended)` using cubic ease-in-out (`easeInOutQuad`) and clicks it safely, allowing the agent to continue uninterrupted.

### ऑटो-सेलेक्ट कमांडर क्या है?
जब आप एंटीग्रेविटी (Antigravity) में ऑटोमेशन या लंबे टास्क चलाते हैं, तो यह `ask_question` टूल द्वारा स्क्रीन पर एक पॉपअप दिखाता है, जिसमें पहला विकल्प **`(Recommended)`** होता है। यदि आप डेस्क पर नहीं हैं, तो पूरी कोडिंग प्रोसेस रुक जाती है।  
**AutoSelect-Commander** स्क्रीन को स्कैन करता है, 30 सेकंड का लाइव टाइमर दिखाता है। यदि आप माउस हिलाते हैं तो यह तुरंत रुक जाता है; अन्यथा 30 सेकंड बाद यह खुद स्मूथली कर्सर ले जाकर **`(Recommended)`** पर क्लिक कर देता है ताकि आपका काम रुके नहीं!

---

## 🚀 1-Click Quick Start / शुरू कैसे करें

### Method 1: 1-Click Launcher (एक-क्लिक रनर)
Simply double-click:
```cmd
run.bat
```
- It automatically detects Python 3.10+ (or `uv`).
- Automatically provisions `.venv` and installs all dependencies (`requirements.txt`).
- Launches `auto_commander.py` in your terminal with live ANSI status.

### Method 2: Manual CLI Launch (कमांड लाइन से)
```powershell
# 1. Activate virtual environment
.venv\Scripts\activate

# 2. Run AutoSelect-Commander
python auto_commander.py
```

---

## 🧪 Instant Testing & Simulation / टेस्ट और सिमुलेशन

You don't have to wait for Antigravity to prompt you to test this tool! It has a built-in interactive simulator:

```powershell
run.bat --test
# या
python auto_commander.py --test
```

### What happens in `--test` mode:
1. A mock Antigravity decision card pops up on your screen.
2. The terminal detects the window and initiates a 5-second countdown.
3. **Test 1 (Auto-Click):** Do not touch the mouse. Watch the cursor glide smoothly to `(Recommended)` and click it!
4. **Test 2 (Fail-Safe):** Run again, and gently move your mouse during the countdown. The countdown will abort instantly (`[FAIL-SAFE TRIGGERED]`), proving you always have priority.

---

## 🛡️ Fail-Safe & Safety Features / सुरक्षा फीचर्स

| Safety Feature | Description / विवरण |
| :--- | :--- |
| **Instant Mouse Abort** | If the physical mouse moves more than 15 pixels, the timer halts immediately and enters cooldown. (माउस 15px हिलते ही ऑटोमेशन तुरंत बंद). |
| **PyAutoGUI Corner Fail-Safe** | Slamming the mouse into any screen corner (`0, 0`) triggers an immediate hard emergency halt (`pyautogui.FAILSAFE = True`). |
| **Hotkey Abort** | Press **`ESC`** or **`Q`** at any moment to cancel the active countdown or exit. |
| **High-DPI Awareness** | Uses Windows Per-Monitor DPI awareness (`SetProcessDpiAwareness(2)`) to eliminate coordinate drift on 125%/150% scaled displays. |
| **Non-Destructive Cooldown** | After any user override, the daemon enters a cooldown state to prevent fighting the user. |

---

## ⚙️ Configuration (`config.json`)

All operational parameters can be customized without touching code:

```json
{
  "countdown_seconds": 30,
  "check_interval_ms": 1000,
  "mouse_interruption_threshold_px": 15,
  "smooth_glide_duration_s": 0.8,
  "cooldown_after_dismissal_s": 5,
  "failsafe_enabled": true,
  "sound_notification": true,
  "window_title_filter": "Antigravity",
  "target_keywords": [
    "(Recommended)",
    "Recommended",
    "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
    "(Recommended) GitHub",
    "Proceed"
  ],
  "detection_mode": "auto"
}
```

- **`countdown_seconds`**: Timeout duration before auto-clicking (default: `30` seconds).
- **`mouse_interruption_threshold_px`**: Distance in pixels to trigger instant abort (default: `15` px).
- **`smooth_glide_duration_s`**: Mouse transition time in seconds (default: `0.8`s).
- **`detection_mode`**: `"auto"` (UIAutomation first, Computer Vision fallback), `"uia"`, or `"vision"`.

---

## 🏛️ Architecture & Project Structure

```
C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
├── auto_commander.py        # Core Python daemon & state machine
├── config.json              # User-configurable parameters
├── requirements.txt         # Lightweight Python dependencies
├── run.bat                  # 1-Click Windows batch launcher
├── README.md                # Bilingual documentation
├── PRD.md                   # Product Requirements Document
├── assets/
│   └── templates/           # Multi-scale OpenCV visual templates
│       ├── recommended_dark.png
│       ├── recommended_light.png
│       └── recommended_badge.png
└── tests/
    └── test_commander.py    # Automated test suite
```

---

## 👤 Author & Identity

- **Developer:** Atul Verma (`aiprincekumar`)
- **Email:** `aiprincekumar010100@gmail.com`
- **GitHub:** [https://github.com/aiprincekumar](https://github.com/aiprincekumar)
- **License:** MIT License
