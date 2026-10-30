# Master Changes Log: AutoSelect-Commander

> **SSOT Audit Trail:** Complete chronological record of all architectural, feature, and configuration changes.

---

### [2026-10-31] - Release 1.0.0
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
