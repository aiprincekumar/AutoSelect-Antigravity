#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 0 - AntiGravity Detector (Testing Runner Alias)
===================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Two-Factor Status Monitor)
Part of: AutoSelect-Commander Automation Suite
Workspace: Keyboard Automation (Step 0: Detector & Status Monitor)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Backward Compatibility Notice:
This file maintains full backward compatibility for legacy invocations and test runners.
It delegates all execution and exports to the canonical unified implementation:
`step_0_antigravity_detector/step0_antigravity_detector.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure this directory is in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith("step_") else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

# Import everything from the canonical module
import step0_antigravity_detector as _canonical
from step0_antigravity_detector import (
    clear_screen,
    format_dashboard_box,
    display_dashboard,
    parse_args,
    should_pause,
    wait_for_user,
    main,
)

__all__ = [
    "clear_screen",
    "format_dashboard_box",
    "display_dashboard",
    "parse_args",
    "should_pause",
    "wait_for_user",
    "main",
]

if __name__ == "__main__":
    sys.exit(_canonical.main())
