#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (प्रोडक्शन रनर - 5 मिनट इंटरवल एवं टू-फैक्टर मॉनिटर)
Step 0 - AntiGravity Detector (Production Runner - 5-Minute Status Monitor)
==============================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Two-Factor Status Monitor)
Part of: AutoSelect-Commander Automation Suite
Workspace: Keyboard Automation (Step 0: Detector & Status Monitor)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)

Production Specifications:
  1. Headless Background Status Monitor:
     - Checks process and window status silently in background.
  2. Polling Interval:
     - Default 300 seconds (5 minutes).
  3. Two-Factor Trigger Verification:
     - Factor 1: Is Google Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat requiring user input?
  4. Execution Hygiene (Universal Rule 26):
     - Pure single responsibility: Detector & Status Monitor.
     - Chaining of steps 1, 2, 3, 4 is decoupled and orchestrated by Complete Automation.
"""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path

# Ensure root directory and package are in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith("step_") else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

# Reconfigure stdout/stderr for proper UTF-8 handling on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from antigravity_detector_core import (
    AntiGravityDetector,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (प्रोडक्शन - 5 मिनट) / Step 0 - AntiGravity Detector (Production - 5 Min)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_PRODUCTION_POLL_INTERVAL,
        help="Polling interval in seconds between detection checks (default: 300.0s = 5 minutes)"
    )
    parser.add_argument(
        "--log-file",
        default=str(_this_dir / "step0_production.log"),
        help="Path to production log file (default: step_0_antigravity_detector/step0_production.log)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in visible interactive mode instead of silent headless mode"
    )
    parser.add_argument(
        "--any-antigravity",
        action="store_true",
        help="Legacy mode: match trigger immediately on Antigravity open, without requiring pending Grill-Me chats"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Headless mode is default for production unless --interactive is explicitly passed
    headless = not args.interactive
    require_grill_me = not args.any_antigravity

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=headless,
        verbose=not headless,
        log_file_path=args.log_file,
        require_grill_me=require_grill_me,
    )

    result = detector.run_loop(
        poll_interval=args.interval,
    )

    if result and result.trigger_matched:
        # Detected and trigger condition matched cleanly!
        sys.exit(0)
    else:
        # Loop interrupted or stopped cleanly
        sys.exit(0)


if __name__ == "__main__":
    main()
