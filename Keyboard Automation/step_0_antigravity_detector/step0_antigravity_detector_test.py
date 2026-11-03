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
    parser.add_argument(
        "--pause",
        action="store_true",
        default=None,
        help="Keep console window open and wait for user keypress on completion"
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        default=False,
        help="Do not pause on completion (for automated scripts and unit tests)"
    )
    return parser.parse_args()


def should_pause(args: argparse.Namespace) -> bool:
    """
    Determine whether to keep the console window open on completion.
    Rules:
      1. If --no-pause is passed -> False
      2. If --pause is explicitly passed -> True
      3. If running inside run_step0_test.bat (BATCH_PAUSE_HANDLED=1) -> False
         (the batch runner will display the final banner and handle pause)
      4. If running in an interactive terminal session (TTY) -> True
      5. Otherwise (headless, non-interactive, pipe) -> False
    """
    if args.no_pause:
        return False
    if args.pause is True:
        return True
    if os.environ.get("BATCH_PAUSE_HANDLED") == "1":
        return False
    if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        return True
    return False


def wait_for_user(msg: Optional[str] = None):
    """Wait for user confirmation before exiting, keeping the terminal open."""
    if not (sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
        return
    print("\n" + "=" * 78)
    if msg:
        print(f"  {msg}")
    print("  [विंडो खुली रखी गई है / Window is kept open for inspection]")
    print("  बाहर निकलने के लिए Enter दबाएं (Press Enter to exit)...")
    print("=" * 78)
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def display_telemetry_banner(
    result: DetectionResult,
    step1_result: Optional[Tuple[bool, int, str]] = None,
    action_note: Optional[str] = None
):
    """Render a clean, structured, bilingual visual telemetry report for manual inspection."""
    status_str = "चालू और सक्रिय / ACTIVE & RUNNING ✅" if result.is_detected else "बंद / NOT RUNNING ❌"
    window_str = "हाँ / YES (विंडो मौजूद है)" if result.has_window else "नहीं / NO (बैकग्राउंड प्रोसेस केवल)"

    method_map = {
        "process_and_window": "प्रोसेस और जीयूआई विंडो दोनों (Process & GUI Window)",
        "process_only": "बैकग्राउंड प्रोसेस केवल (Process Table Only)",
        "window_only": "जीयूआई विंडो केवल (Window Hierarchy Only)",
        "none": "कोई नहीं (None)",
    }
    method_str = method_map.get(result.detection_method, result.detection_method.upper())

    print("\n" + "=" * 78)
    print("  🎯 [निरीक्षण रिपोर्ट / DETECTION REPORT] Google Antigravity State Identified!")
    print("=" * 78)
    print(f"  • स्थिति / Status       : {status_str}")
    print(f"  • पहचान विधि / Method   : {method_str}")
    print(f"  • कुल प्रोसेस / Count    : {result.process_count} instances")
    print(f"  • मुख्य PID / Main PID  : {result.main_pid if result.main_pid else 'N/A'}")
    if result.pids:
        pid_list_str = ', '.join(str(p) for p in result.pids[:8])
        if len(result.pids) > 8:
            pid_list_str += f" ... (+{len(result.pids) - 8} more)"
        print(f"  • सभी PIDs / All PIDs   : {pid_list_str}")
    if result.exe_path:
        print(f"  • फ़ाइल पाथ / Binary    : {result.exe_path}")
    print(f"  • विंडो स्थिति / Window  : {window_str}")
    if result.has_window:
        print(f"  • विंडो हैंडल / HWND   : {result.window_hwnd}")
        print(f"  • विंडो शीर्षक / Title  : '{result.window_title}'")
        if result.window_class:
            print(f"  • विंडो क्लास / Class   : {result.window_class}")
    print(f"  • समय / Timestamp (UTC) : {result.timestamp}")

    # Step 1 Execution Details
    if step1_result is not None:
        ok, code, msg = step1_result
        print("-" * 78)
        print("  🚀 [स्टेप 1 ट्रिगर परिणाम / STEP 1 TRIGGER RESULT]")
        print(f"  • निष्पादन स्थिति / Status : {'सफल / SUCCESS ✅' if ok else 'असफल / FAILED ❌'}")
        print(f"  • एग्जिट कोड / Exit Code   : {code}")
        print(f"  • विवरण / Details          : {msg}")
    elif action_note:
        print("-" * 78)
        print(f"  ℹ️ [कार्रवाई / ACTION] : {action_note}")

    print("=" * 78 + "\n")


def on_check_telemetry(check_num: int, result: DetectionResult):
    """Callback providing real-time telemetry updates during polling."""
    now = datetime.now().strftime("%H:%M:%S")
    if not result.is_detected:
        print(f"  [{now}] Check #{check_num:03d} | Status: [SCANNING] | Antigravity: Closed/Not Detected (जांच जारी...)")


def main():
    args = parse_args()
    pause_enabled = should_pause(args)

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=args.json,
        verbose=not args.json,
    )

    if args.once:
        # Single-shot manual inspection
        if not args.json:
            print("[*] Performing single-shot Antigravity detection check...")
            print("    (सिंगल-शॉट एंटी-ग्रेविटी डिटेक्शन जांच की जा रही है...)")
        result = detector.detect()

        step1_info = None
        action_note = None

        if result.is_detected and not args.no_launch:
            if not args.json:
                print("[*] Antigravity चालू है। Step 1 (find_and_focus) ट्रिगर किया जा रहा है...")
            ok, code, msg = detector.launch_step1(wait=args.wait)
            step1_info = (ok, code, msg)
            result.details["step1_result"] = {
                "success": ok,
                "exit_code": code,
                "message": msg
            }
        elif result.is_detected and args.no_launch:
            action_note = "Antigravity detected. (--no-launch passed: Step 1 trigger skipped / स्टेप 1 ट्रिगर छोड़ दिया गया)"
        else:
            action_note = "Antigravity is not currently running (एंटी-ग्रेविटी अभी नहीं चल रहा है)"

        if args.json:
            print(json.dumps(result.to_json_envelope(), indent=2))
        else:
            display_telemetry_banner(result, step1_result=step1_info, action_note=action_note)

        exit_code = 0
        if not result.is_detected:
            exit_code = 1
        elif step1_info and not step1_info[0]:
            exit_code = step1_info[1]

        if pause_enabled:
            wait_for_user()

        sys.exit(exit_code)

    # Continuous 10-second polling runner
    auto_trigger = not args.no_launch
    result = detector.run_loop(
        poll_interval=args.interval,
        max_checks=args.max_checks,
        auto_launch=auto_trigger,
        wait_for_step1=args.wait,
        on_check_callback=on_check_telemetry,
    )

    step1_info = None
    action_note = None

    if result and result.is_detected:
        if result.details and "step1_result" in result.details:
            s1 = result.details["step1_result"]
            step1_info = (s1.get("success", False), s1.get("exit_code", 0), s1.get("message", ""))
        elif args.no_launch:
            action_note = "Antigravity detected. (--no-launch passed: Step 1 trigger skipped / स्टेप 1 छोड़ दिया गया)"

        if args.json:
            print(json.dumps(result.to_json_envelope(), indent=2))
        else:
            display_telemetry_banner(result, step1_result=step1_info, action_note=action_note)

        exit_code = 0
        if step1_info and not step1_info[0]:
            exit_code = step1_info[1]

        if pause_enabled:
            wait_for_user()

        sys.exit(exit_code)
    else:
        if args.json:
            dummy_res = DetectionResult(is_detected=False)
            print(json.dumps(dummy_res.to_json_envelope(), indent=2))
        else:
            print("\n" + "=" * 78)
            print("  ℹ️ [सूचना / INFO] पोलिंग बिना डिटेक्शन के समाप्त हुई।")
            print("  Polling stopped without detecting Google Antigravity.")
            print("=" * 78 + "\n")

        if pause_enabled:
            wait_for_user()

        sys.exit(0)


if __name__ == "__main__":
    main()
