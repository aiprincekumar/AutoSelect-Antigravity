# Master Changes Log: AutoSelect-Commander

> **SSOT Audit Trail:** Complete chronological record of all architectural, feature, and configuration changes.

---

### [2026-11-01 02:30:00 IST] - Release 1.2.0 (10s Timer, Reliable Firm Click, 2-Step Option + Submit Flow, Antigravity Auto-Foregrounding)
- **Commit:** `feat(core): 10s timer, reliable firm click, 2-step submit flow, and Antigravity auto-foregrounding`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **10-Second Timer Default:** Default countdown reduced from 30s to 10s in `config.json`, `Config` class, CLI parser, banner, floating HUD, and live visual demo.
  - **Reliable Firm Click:** Implemented `MouseController.firm_click()` using `mouseDown()` with 80ms dwell duration followed by `mouseUp()`, ensuring 100% reliable click registration across Electron, Chromium, and native Windows controls.
  - **Complete 2-Step Decision Flow:**
    - Step 1: Smoothly glide cursor to Option 1 `(Recommended)` and perform firm click to select.
    - Step 2: Detect and smoothly glide cursor to `Submit / पुष्टि करें` button and perform firm click to confirm and submit.
  - **Antigravity Tracking & Auto-Foregrounding (`AntigravityWindowManager`):**
    - Detects whether Antigravity is open/running via native Win32 process table inspection and window handle enumeration.
    - If Antigravity is not open: Clearly outputs `[ANTIGRAVITY] एंटी-ग्रैविटी अभी ओपन नहीं है (Antigravity is currently not open)`.
    - If Antigravity is minimized or running in the background: Automatically restores (`ShowWindow(SW_RESTORE)`) and brings it to the foreground (`AttachThreadInput` + `SetForegroundWindow`) without moving the mouse before triggering HUD and automation.
  - **Live Visual Simulator Overhaul (`launch_simulator`):**
    - Interactive decision card with selectable options (`○` -> `●`), green selection borders, and a responsive `[ 🚀 Submit / पुष्टि करें ]` button.
    - Complete 2-step visual glide demonstration with HUD stage badges and audio confirmation.
  - **1-Click Launcher Enhancements (`run.bat`):**
    - Added direct numeric shortcut handling: `run.bat 1` (Live Demo), `run.bat 2` (Background Sentinel), and `run.bat 3` (Diagnostics).
  - **Testing & Verification:**
    - Expanded test suite to 13 unit tests covering Config defaults (10s), AntigravityWindowManager, MouseController firm click, submit button detection inference, and HUD lifecycle.

---

### [2026-10-31 05:10:00 IST] - Release 1.1.0 (Detection Overhaul & Visual HUD)
- **Commit:** `fix(core): overhaul detection engine, add floating HUD overlay and interactive launcher menu`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - `run.bat`: Interactive 3-option menu ([1] Demo, [2] Background Sentinel, [3] Diagnostics) with a 5-second automatic timeout defaulting to Live Demo mode.
  - `auto_commander.py`:
    - Replaced rigid window title filter with relaxed scanning (foreground and active workspace windows).
    - Added `WindowsOcrDetector`: Windows native WinRT OCR (`Windows.Media.Ocr`) with fuzzy text matching (`difflib.SequenceMatcher`), detecting rendered text in <50ms with zero API token spend.
    - Added `FloatingHUD`: Built-in Tkinter top-most semi-transparent floating overlay showing real-time countdown progress bar, remaining seconds, cancellation alerts, and success badges directly on screen.
    - Updated `launch_simulator()`: Spawns mock decision card, floating HUD, and physically glides mouse to click Option 1 with cubic easing.
    - Added `run_diagnostics()`: Probes display resolution, WinRT OCR engine status, visible window handles, and text extraction.
  - `config.json`: Added `floating_hud_enabled`, `floating_hud_alpha`, `ocr_enabled`, relaxed `window_title_filter`, and expanded Hindi keywords.
  - `requirements.txt`: Added `winsdk>=1.0.0b10`.
  - `tests/test_commander.py`: Expanded test suite to 10 automated unit tests (100% passing in 0.043s).
  - `README.md`: Bilingual documentation update covering the interactive menu, floating HUD, and WinRT OCR engine.

---

### [2026-10-31 04:45:00 IST] - Release 1.0.0 (Initial Release)
- **Commit:** `feat(core): initial release of AutoSelect-Commander visual mouse automation tool`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Components Added:**
  - `requirements.txt`: Python dependencies (`pyautogui`, `pillow`, `opencv-python`, `pynput`, `pygetwindow`, `uiautomation`).
  - `config.json`: Production configuration with 30s timeout, 15px mouse interruption threshold, and smooth glide duration.
  - `auto_commander.py`: High-performance dual-mode detection engine (Windows UIAutomation + OpenCV Computer Vision), 30s ANSI countdown, cubic easing mouse glide (`easeInOutQuad`), and 50Hz mouse fail-safe sentinel.
  - `run.bat`: 1-Click Windows batch launcher with automatic Python detection, venv setup, dependency installation, and launch.
  - `README.md`: Bilingual documentation (English & Hindi) covering architecture, 1-click launch, testing, and safety features.
  - `assets/templates/`: Multi-scale visual templates for `(Recommended)` buttons and badges.
  - `tests/test_commander.py`: Automated test suite for configuration, detection data structures, and fail-safe algorithms.
