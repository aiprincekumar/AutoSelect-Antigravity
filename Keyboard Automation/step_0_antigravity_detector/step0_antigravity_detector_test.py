#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (टेस्टिंग रनर - 10 सेकंड टेलीमेट्री)
Step 0 - AntiGravity Detector (Testing Runner - 10-Second Telemetry)
==================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Step 1 Auto-Trigger)
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 0 of 3)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

Testing Specifications:
  1. Manual Inspection Runner:
     - Polling interval: 10 seconds.
     - Rich console telemetry displaying check iteration, UTC timestamp,
       PIDs, process count, window title, HWND, and next check countdown.
  2. Immediate Verification:
     - When Antigravity is open, displays comprehensive detection details and
       launches Step 1 (or performs dry-run verification if --no-launch is passed).
  3. Single-Shot Mode:
     - Pass --once for an instant single check and immediate result display.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import datetime, timezone
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
    DetectionResult,
    DEFAULT_TEST_POLL_INTERVAL,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (टेस्टिंग - 10 सेकंड) / Step 0 - AntiGravity Detector (Testing - 10 Sec)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_TEST_POLL_INTERVAL,
        help="Polling interval in seconds between detection checks (default: 10.0s)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform a single instantaneous detection check and exit immediately"
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Dry run: detect Antigravity without triggering Step 1"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        default=True,
        help="Wait for Step 1 completion and display exit status in console (default: True in test runner)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_false",
        dest="wait",
        help="Do not wait for Step 1 completion (spawn detached and exit)"
    )
    parser.add_argument(
        "--max-checks",
        type=int,
        default=None,
        help="Stop after N checks if Antigravity is not detected (default: infinite)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the detection result as a Dept 06 JSON response envelope"
    )
    return parser.parse_args()


def display_telemetry_banner(result: DetectionResult):
    """Render a clean, structured visual telemetry report for manual inspection."""
    print("\n" + "=" * 78)
    print("  🎯 [DETECTION REPORT] Google Antigravity State Identified!")
    print("=" * 78)
    print(f"  • Detection Status  : {'ACTIVE & RUNNING' if result.is_detected else 'NOT RUNNING'}")
    print(f"  • Detection Method  : {result.detection_method.upper()}")
    print(f"  • Total Processes   : {result.process_count} instances")
    print(f"  • Main Process PID  : {result.main_pid if result.main_pid else 'N/A'}")
    print(f"  • All PIDs          : {', '.join(str(p) for p in result.pids[:8])}{' ...' if len(result.pids) > 8 else ''}")
    print(f"  • Binary Path       : {result.exe_path or 'N/A'}")
    print(f"  • Window Found      : {'YES' if result.has_window else 'NO'}")
    if result.has_window:
        print(f"  • Window Handle     : HWND {result.window_hwnd}")
        print(f"  • Window Title      : '{result.window_title}'")
        print(f"  • Window Class      : {result.window_class}")
    print(f"  • Timestamp (UTC)   : {result.timestamp}")
    print("=" * 78 + "\n")


def on_check_telemetry(check_num: int, result: DetectionResult):
    """Callback providing real-time telemetry updates during polling."""
    now = datetime.now().strftime("%H:%M:%S")
    if not result.is_detected:
        print(f"  [{now}] Check #{check_num:03d} | Status: [SCANNING] | Antigravity: Closed/Not Detected")


def main():
    args = parse_args()

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=False,
        verbose=True,
    )

    if args.once:
        # Single-shot manual inspection
        print(f"[*] Performing single-shot Antigravity detection check...")
        result = detector.detect()

        if args.json:
            print(json.dumps(result.to_json_envelope(), indent=2))
        else:
            display_telemetry_banner(result)

        if result.is_detected and not args.no_launch:
            print("[*] Antigravity is open. Triggering Step 1 now...")
            ok, code, msg = detector.launch_step1(wait=args.wait)
            print(f"[*] Step 1 Result: Success={ok}, ExitCode={code}, Message: {msg}")
            sys.exit(0 if ok else code)
        elif result.is_detected and args.no_launch:
            print("[*] Antigravity detected. (--no-launch passed: skipping Step 1 trigger)")
            sys.exit(0)
        else:
            print("[-] Antigravity is not currently running.")
            sys.exit(1)

    # Continuous 10-second polling runner
    auto_trigger = not args.no_launch
    result = detector.run_loop(
        poll_interval=args.interval,
        max_checks=args.max_checks,
        auto_launch=auto_trigger,
        wait_for_step1=args.wait,
        on_check_callback=on_check_telemetry,
    )

    if result and result.is_detected:
        if args.json:
            print(json.dumps(result.to_json_envelope(), indent=2))
        else:
            display_telemetry_banner(result)
        sys.exit(0)
    else:
        print("\n[INFO] Polling stopped without detection.")
        sys.exit(0)


if __name__ == "__main__":
    main()
