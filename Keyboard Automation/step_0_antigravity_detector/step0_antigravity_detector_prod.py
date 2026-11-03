#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (प्रोडक्शन रनर - 5 मिनट इंटरवल एवं टू-फैक्टर ट्रिगर)
Step 0 - AntiGravity Detector (Production Runner - 5-Minute Two-Factor Polling)
==============================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Dynamic Pipeline Auto-Trigger)
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 0: Detector & Dynamic Pipeline Runner)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

Production Specifications:
  1. Fully automatic & headless background execution:
     - No questions, no popups/GUI windows, silent background operation.
  2. Polling Interval:
     - Default 300 seconds (5 minutes).
  3. Two-Factor Trigger:
     - Factor 1: Is Google Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat requiring user input?
     - Only when BOTH conditions match, automatically launches the full automation
       pipeline (Steps 1 -> 2 -> 3, and Step 4 when available) as a detached background process.
  4. Execution Hygiene (Universal Rule 26):
     - Immediately and cleanly exits with code 0 after the pipeline is triggered.
     - Zero lingering background processes or zombies.
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
        "--step1-path",
        default=None,
        help="Custom path to Step 1 script (step1_find_and_focus.py)"
    )
    parser.add_argument(
        "--step2-path",
        default=None,
        help="Custom path to Step 2 script (step2_gui_chat_select.py)"
    )
    parser.add_argument(
        "--step3-path",
        default=None,
        help="Custom path to Step 3 script (step3_keyboard_automation.py)"
    )
    parser.add_argument(
        "--step4-path",
        default=None,
        help="Custom path to Step 4 script (step4_reporting.py)"
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Custom path to target_chat.json state file"
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
        "--wait",
        action="store_true",
        help="Wait for pipeline completion instead of detached spawn-and-exit"
    )
    parser.add_argument(
        "--any-antigravity",
        action="store_true",
        help="Legacy mode: trigger pipeline immediately on Antigravity open, without requiring pending Grill-Me chats"
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
        step1_script_path=args.step1_path,
        step2_script_path=args.step2_path,
        step3_script_path=args.step3_path,
        step4_script_path=args.step4_path,
        state_file_path=args.state_file,
        log_file_path=args.log_file,
        require_grill_me=require_grill_me,
    )

    result = detector.run_loop(
        poll_interval=args.interval,
        auto_launch=True,
        wait_for_pipeline=args.wait,
    )

    if result and result.trigger_matched:
        # Detected and pipeline launched! Clean exit with code 0.
        sys.exit(0)
    else:
        # Loop interrupted or stopped cleanly
        sys.exit(0)


if __name__ == "__main__":
    main()
