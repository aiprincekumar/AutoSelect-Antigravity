#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
AutoSelect-Commander: Visual Mouse Automation & Auto-Selector for Antigravity
===============================================================================
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Repository: C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
Version: 1.4.0

Backward-Compatible Root Facade:
All internal logic is modularized inside the `auto_commander` package:
  auto_commander/
  ├── config.py              # Configuration dataclass, load/save, defaults
  ├── models.py              # Point, Rect, DetectionResult
  ├── platform/
  │   ├── win32_window.py    # Win32 window APIs, Antigravity detection & activation
  │   └── mouse_ctrl.py      # Mouse movement, cubic bezier easing, firm_click
  ├── detectors/
  │   ├── base.py            # Base detector
  │   ├── ocr_detector.py    # Windows WinRT native OCR
  │   ├── uia_detector.py    # UIAutomation detector
  │   ├── vision_detector.py # OpenCV template matching
  │   ├── chat_detector.py   # Chat tab & (?) action badge navigation detector
  │   └── orchestrator.py    # MultiEngineDetector
  ├── gui/
  │   ├── hud.py             # Always-on-top FloatingHUD
  │   └── dashboard.py       # Terminal ANSI dashboard
  ├── core/
  │   ├── engine.py          # AutoCommanderEngine state machine
  │   └── diagnostics.py     # System & OCR diagnostics probe
  └── cli.py                 # CLI argument parsing and entrypoint
===============================================================================
"""

from auto_commander import (
    Config,
    Point,
    Rect,
    DetectionResult,
    AntigravityWindowManager,
    MouseController,
    BaseDetector,
    WindowsOcrDetector,
    WINSDK_OCR_AVAILABLE,
    UIAutomationDetector,
    VisionDetector,
    MultiEngineDetector,
    DualModeDetector,
    FloatingHUD,
    TerminalDashboard,
    AutoCommanderEngine,
    run_diagnostics,
    main,
    __version__,
    __author__,
)

if __name__ == "__main__":
    main()
