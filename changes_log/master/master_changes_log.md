# Master Changes Log: AutoSelect-Commander

> **SSOT Audit Trail:** Complete chronological record of all architectural, feature, and configuration changes.

---

### [2026-11-02 05:30:00 IST] - Release 1.8.2 (Verified Keyboard Automation Archive Snapshot)
- **Commit:** `chore(backup): archive verified keyboard automation suite inside Keyboard Automation/archive`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Archive Directory Establishment:**
    - Created dedicated immutable archive container `Keyboard Automation/archive/` at the same folder level.
  - **Asset Replication & Exclusions:**
    - Replicated verified suite: `grill_me_automation.py`, `run_grill_me.bat`, `run_grill_me.ps1`, `requirements.txt`.
    - Excluded transient `__pycache__` artifacts and prevented circular recursive nesting.
  - **Archive Documentation & Integrity Proof:**
    - Published `Keyboard Automation/archive/README.md` with version (`v1.0.0-verified`), detailed capability matrix, direct run commands, and restore runbook.
    - Generated SHA-256 integrity hash table verifying 100% bit-for-bit identity against working files.
  - **Execution & Test Gate Certification:**
    - Direct archive dry run verified against Antigravity 2.0 (PID 15024).
    - Unittest test gate certified with 93/93 passing tests and 0 gitleaks findings.

---

### [2026-11-02 04:40:00 IST] - Release 1.8.1 (Browser Disqualification & Strict Antigravity 2.0 Process Targeting)
- **Commit:** `fix(automation): strictly exclude chrome/browsers and enforce exact Antigravity process targeting`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Browser Disqualification:**
    - Diagnosed that `chrome.exe` shares class `Chrome_WidgetWin_1` with Antigravity and was receiving positive scores, leading to `Ctrl + L` focusing the Chrome address bar and performing web searches.
    - Added `DISQUALIFIED_BROWSER_PROCS` across `grill_me_automation.py`, `activating_grill_me.py`, and `win32_window.py`.
    - Browsers are strictly disqualified (-9999 / filtered out) unless explicitly targeted via CLI.
  - **Antigravity 2.0 Priority Targeting:**
    - Enforced process matching against `Antigravity.exe` or process path containing `antigravity`, awarding highest priority (+1000).
    - Restricted `Chrome_WidgetWin_1` class scoring strictly to verified Antigravity/Electron processes.
  - **Win32 Image Resolution Fallback:**
    - Added native `OpenProcess` + `QueryFullProcessImageNameW` in `get_process_info_for_hwnd`.
  - **Pre-Execution Foreground Gatekeeper:**
    - Checks foreground window immediately before key simulation; aborts execution if foreground is a browser to protect user tabs.
  - **Verification:**
    - Expanded unit tests in `tests/test_grill_me.py` to 17 tests; full suite 93/93 tests passing; gitleaks 0 leaks.

---

### [2026-11-02 04:05:00 IST] - Release 1.8.0 (Antigravity 2.0 Harness Window Restore, Maximize & Force-Focus)
- **Commit:** `fix(automation): enhance antigravity 2.0 harness window detection, restore, maximize, and force-focus pipeline`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - Resolved window title mismatch for Antigravity 2.0 Harness.
  - Added multi-layered matching: process name (`Antigravity.exe`), window class (`Chrome_WidgetWin_1`), and multi-keyword comma-separated list.
  - Thread desktop attachment via `OpenInputDesktop` + `SetThreadDesktop`.
  - Window restoration (`SW_RESTORE` + `OpenIcon`), full-screen maximization (`SW_MAXIMIZE`), and Windows 10/11 focus lock bypass.

---

### [2026-11-02 03:25:00 IST] - Release 1.7.0 (Antigravity Window Auto-Target, Restore, Maximize & Focus Subsystem)
- **Commit:** `feat(automation): add antigravity auto-detect, restore, maximize, and focus subsystem`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Intelligent Window Detection & Targeting (`Keyboard Automation/`):**
    - Win32 `EnumWindows` and `GetWindowTextW` integration to locate target window by keyword (default: `"Antigravity"`).
    - Window title scoring algorithm and console runner exclusion via `kernel32.GetConsoleWindow`.
  - **Auto-Restore & Maximize Subsystem:**
    - Checks `user32.IsIconic(hwnd)`: if minimized, automatically restores window state (`SW_RESTORE`).
    - Checks `user32.IsZoomed(hwnd)`: if not maximized, automatically expands window to full screen (`SW_MAXIMIZE`).
  - **Robust Foreground Activation:**
    - Thread input attachment (`AttachThreadInput`) and synthetic `Alt` key event (`VK_MENU = 0x12`) to bypass Windows OS foreground lock restrictions.
    - Activates foreground focus using `BringWindowToTop`, `SetForegroundWindow`, and `SetFocus`.
  - **Geometry Bounds Verification & Settling Delay:**
    - Checks window geometry bounds using `user32.GetWindowRect`.
    - 500ms default settle delay (`--settle-delay`) to ensure UI rendering is complete before key injection.
  - **Runner Enhancements:**
    - Updated `run_grill_me.bat` and `run_grill_me.ps1` with auto-targeting and maximize support.
    - Updated `Keyboard Automation/README.md` with complete architecture workflow and CLI reference.
    - Expanded unit tests (`tests/test_grill_me.py`) to 11/11 passing tests.

---

### [2026-11-02 02:50:00 IST] - Release 1.6.0 (Grill Me Keyboard Automation Suite)
- **Commit:** `feat(automation): add grill me keyboard automation scripts suite`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Grill Me Keyboard Automation Suite (`Keyboard Automation/`):**
    - High-reliability hybrid focus + automated keyboard sequence for interactive `/grill-me` options in Antigravity and IDEs.
    - Zero-dependency native Windows `ctypes` engine using `SendInput` and `keybd_event` (runs out-of-the-box on standard Python with no pip packages required).
    - Optional interop and auto-fallback with `pyautogui` when installed.
    - Real-time countdown timer with continuous Win32 foreground window title detection.
    - 4-step sequence: `Ctrl + L` -> `Shift + Tab` -> Option `1` -> `Enter` with configurable delays and dry-run simulation mode.
    - Windows double-click batch launcher (`run_grill_me.bat`) and PowerShell launcher (`run_grill_me.ps1`).
    - Dedicated unit test suite in `tests/test_grill_me.py` (5/5 passed).
- **Verification & Testing:**
  - Syntax compilation verified clean with `python -m py_compile`.
  - Dry-run verification passed across Python, PowerShell, and Batch runners with exit code 0.
  - Full unit test matrix (`tests/test_commander.py` and `tests/test_grill_me.py`) confirmed 62/62 tests passing.

---

### [2026-11-01 11:45:00 IST] - Release 1.5.0 (Modular Step-by-Step GUI Automation Pipeline & Calibrator)
- **Commit:** `feat(automation): integrate modular step-by-step GUI automation pipeline and calibrator into scripts/gui_automation/`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Modular Step-by-Step Architecture (`scripts/gui_automation/`):**
    - Eliminates single-loop automation freeze by dividing actions into 4 isolated, independently runnable Python scripts:
      - `step1_open_and_click_chat.py`: Chat area target navigation and focus click.
      - `step2_select_recommended_option.py`: Option 1 / `(Recommended)` radio button selection.
      - `step3_click_submit_button.py`: Confirmation click on Submit button.
      - `step4_verify_execution.py`: State verification and evidence screenshot capture.
    - Master Runner (`run_pipeline.py`): Orchestrates all steps sequentially with customizable inter-step render delays (`--delay`) and `--dry-run` inspection mode.
    - Interactive Screen Calibrator (`calibrate_coordinates.py`): Real-time interactive tool for recording screen coordinates for different display geometries and resolutions.
    - Unified Engine & Config: `common_utils.py` with smooth Bezier mouse travel (`easeOutQuad`) and `config.json` matrix.
  - **Verification & Testing:**
    - Full dry-run across all 4 stages executed successfully with zero errors (exit code 0).
    - Unit test suite (`unittest discover tests`) confirmed 43/43 tests passing.

---

### [2026-11-01 06:30:00 IST] - Release 1.4.0 (Step 0 Chat Navigation via (?) Badge & Demo Code Separation)
- **Commit:** `feat(navigation): add Step 0 (?) chat badge navigation, purge demo code into standalone files, streamline production run.bat`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Step 0 Chat Navigation via (?) Badge (`ChatTabDetector`):**
    - Identifies conversation tabs/sidebar items awaiting confirmation using multi-scale template matching (`assets/badge_question_template.png`), WinRT OCR (`?`, `(?)`, `Action required`), and UIAutomation tree search.
    - Resolves multi-chat deadlock: automatically switches from inactive/background chats to the pending conversation, waits 0.4s for rendering, then seamlessly triggers Step 1 (Option 1) and Step 2 (Submit).
  - **Purge & Complete Architectural Separation of Demo Simulator:**
    - Fully decoupled test simulator from production codebase into `standalone_demo.py` and dedicated `run_demo.bat`.
    - Deleted `auto_commander/gui/simulator.py` and removed all demo overrides (`is_demo`, `DEMO_WINDOW_TITLE_KEYWORDS`) from production modules.
  - **Fast Production Launcher (`run.bat`):**
    - Streamlined `run.bat` to launch the production daemon directly without delay or prompt menus.
  - **Testing & Verification:**
    - Expanded test suite to 31 tests with 100% green pass rate in 0.78s.

---

### [2026-11-01 03:05:00 IST] - Release 1.3.0 (Modular Package Deconstruction & Window Tracking Fixes)
- **Commit:** `refactor(architecture): decompose into modular auto_commander package, fix Antigravity window tracking and click safety`
- **Author:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)
- **Key Enhancements:**
  - **Modular Package Deconstruction (`auto_commander/`):**
    - `models.py`: Clean geometric and detection primitives (`Point`, `Rect`, `DetectionResult`).
    - `config.py`: Dataclass configuration manager with default fallbacks and validation.
    - `platform/win32_window.py`: Win32 window management, process inspection, self-exclusion filtering, and safe activation.
    - `platform/mouse_ctrl.py`: Human-like cubic easing cursor motion, firm click, and boundary validation.
    - `detectors/`: Decoupled engines (`base.py`, `ocr_detector.py`, `uia_detector.py`, `vision_detector.py`, `orchestrator.py`).
    - `gui/`: Interactive UI components (`hud.py`, `dashboard.py`, `simulator.py`).
    - `core/`: Orchestration state machine (`engine.py`) and diagnostics probe (`diagnostics.py`).
    - `cli.py` & `__main__.py`: Modular CLI entrypoint and package execution (`python -m auto_commander`).
  - **Backward-Compatible Root Facade (`auto_commander.py`):**
    - Retained root `auto_commander.py` as a facade exposing all public classes and functions, ensuring `run.bat` and legacy imports work without modification.
  - **Antigravity Tracking & Foregrounding Bug Fixes:**
    - Strict Self-Exclusion: Excluded own PID, parent shell PIDs (`cmd.exe`, `powershell.exe`, `wt.exe`, `conhost.exe`, `python.exe`), and File Explorer (`explorer.exe`).
    - Title Keyword Disambiguation: Eliminated false matching where repository directory title (`AutoSelect-Commander`) matched as Antigravity.
    - Desktop Session Attachment: Implemented thread attachment to interactive user desktop (`OpenInputDesktop` + `EnumDesktopWindows`) ensuring robust discovery across execution contexts.
    - Zero Unwanted Minimization: Only calls `ShowWindow(SW_RESTORE)` if target window is iconic (`IsIconic`); never minimizes background windows.
    - Click Target Boundary Safety: Validates target coordinates against console window rect and target window boundaries before moving or clicking.
  - **Testing & Verification:**
    - Expanded unit test suite to 17 automated tests (100% green in 0.20s).
    - Verified screen diagnostics, simulator mode, and CLI argument parsing.

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
