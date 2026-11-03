#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 0 - AntiGravity Detector (Testing Runner - 10s Timer & Simple Clean Dashboard)
================================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Dynamic Pipeline Auto-Trigger)
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 0: Detector & Dynamic Pipeline Runner)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

100% Screen Purity & Two-Factor Timer Specifications:
  1. Ultra-clean, numbers-focused console dashboard:
     - AntiGravity Open/Closed status
     - Total chats count in brain storage
     - Active chats count (current active session / recent activity)
     - Inactive chats count (total - active)
     - Pending Grill-Me (ask_question) count requiring user interaction
  2. Zero technical clutter (100% Screen Purity):
     - Clears the terminal screen (`os.system("cls")`) on each refresh.
     - Strictly prints ONLY and EXCLUSIVELY the Unicode dashboard box.
     - No raw PIDs, HWNDs, window classes, header, footer, or extraneous status lines.
  3. Two-Factor Trigger Timer:
     - Factor 1: Is Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat (ask_question) waiting?
     - If Anti-Gravity is open but no Grill-Me is pending:
       - Refreshes clean dashboard showing NO (0 Chats)
       - Sleeps for 10 seconds (configurable via --interval)
       - Tests again!
     - As soon as a Grill-Me chat is pending:
       - Condition matches!
       - Launches full automation pipeline (Steps 1 -> 2 -> 3) with suppressed stdout
       - Exits cleanly (Universal Rule 26).
  4. Dept 06 JSON Envelope Compatibility:
     - Pass --json to retain complete structured JSON response envelope with chat_stats.
"""

from __future__ import annotations

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

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
    DEFAULT_ACTIVE_HOURS,
    resolve_brain_dir,
    get_antigravity_chat_stats,
)


def clear_screen():
    """Wipe the terminal screen completely clean on Windows or POSIX."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")


def format_dashboard_box(
    is_detected: bool,
    chat_stats: Dict[str, Any]
) -> str:
    """
    Render the ultra-clean, elegant, numbers-focused dashboard box in pure English.
    """
    status_str = "OPEN (Running)" if is_detected else "CLOSED (Not Running)"
    total_str = str(chat_stats.get("total_chats", 0))
    active_str = str(chat_stats.get("active_chats", 0))
    inactive_str = str(chat_stats.get("inactive_chats", 0))

    pending = chat_stats.get("pending_grill_me_chats", 0)
    if pending > 0:
        grill_me_str = f"YES ({pending} Chats - Waiting Response)"
    else:
        grill_me_str = "NO (0 Chats)"

    # Monospace layout calculation
    # Labels prefix: "  • " (4) + label padded to 22 chars = 26 chars total
    # Example: "  • AntiGravity Status  : " (length 26)
    # Standard inside width is 56 characters (base_val_width = 30)
    base_val_width = 30
    val_width = max(base_val_width, len(status_str), len(grill_me_str))
    inner_width = 26 + val_width

    top = "┌" + ("─" * inner_width) + "┐"
    div = "├" + ("─" * inner_width) + "┤"
    bot = "└" + ("─" * inner_width) + "┘"

    title = "🚀 ANTIGRAVITY STATUS & CHAT DASHBOARD"
    needed_spaces = inner_width - len(title)
    left_sp = max(0, needed_spaces // 2)
    right_sp = max(0, needed_spaces - left_sp)
    header = "│" + (" " * left_sp) + title + (" " * right_sp) + "│"

    r1 = f"│  • AntiGravity Status  : {status_str:<{val_width}}│"
    r2 = f"│  • Total Chats         : {total_str:<{val_width}}│"
    r3 = f"│  • Active Chats        : {active_str:<{val_width}}│"
    r4 = f"│  • Inactive Chats      : {inactive_str:<{val_width}}│"
    r5 = f"│  • Pending Question    : {grill_me_str:<{val_width}}│"

    return "\n".join(["", top, header, div, r1, r2, r3, r4, r5, bot, ""])


def display_dashboard(
    result: DetectionResult,
    chat_stats: Optional[Dict[str, Any]] = None,
    wipe_screen: bool = True,
    step1_result: Optional[Tuple[bool, int, str]] = None,
    action_note: Optional[str] = None
):
    """Render strictly the clean dashboard box with zero extra noise."""
    if wipe_screen:
        clear_screen()
    if chat_stats is None:
        chat_stats = result.chat_stats if result.chat_stats else get_antigravity_chat_stats(is_antigravity_running=result.is_detected)

    box = format_dashboard_box(result.is_detected, chat_stats)
    print(box)


def display_telemetry_banner(
    result: DetectionResult,
    step1_result: Optional[Tuple[bool, int, str]] = None,
    action_note: Optional[str] = None,
    chat_stats: Optional[Dict[str, Any]] = None
):
    """Backwards-compatible wrapper routing strictly to the clean dashboard."""
    display_dashboard(result, chat_stats=chat_stats, wipe_screen=True, step1_result=step1_result, action_note=action_note)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 0 - AntiGravity Detector (Dashboard Test Runner)"
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
        help="Dry run: detect without triggering automation pipeline"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        default=True,
        help="Wait for pipeline completion (default: True in test runner)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_false",
        dest="wait",
        help="Do not wait for pipeline completion (spawn detached and exit)"
    )
    parser.add_argument(
        "--max-checks",
        type=int,
        default=None,
        help="Stop after N checks if condition is not met (default: infinite)"
    )
    parser.add_argument(
        "--active-hours",
        type=float,
        default=DEFAULT_ACTIVE_HOURS,
        help="Hours threshold to classify a conversation as active session (default: 12.0 hours)"
    )
    parser.add_argument(
        "--brain-dir",
        type=str,
        default=None,
        help="Custom path to Antigravity brain directory (default: auto-detected)"
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
    parser.add_argument(
        "--any-antigravity",
        action="store_true",
        help="Trigger Step 1 immediately whenever Antigravity is open, without requiring pending Grill-Me chats"
    )
    return parser.parse_args()


def should_pause(args: argparse.Namespace) -> bool:
    """
    Determine whether to keep the console window open on completion.
    Rules:
      1. If --no-pause is passed -> False
      2. If --pause is explicitly passed -> True
      3. If running inside run_step0_test.bat (BATCH_PAUSE_HANDLED=1) -> False
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
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    args = parse_args()
    pause_enabled = should_pause(args)
    require_grill_me = not args.any_antigravity

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=True,
        verbose=False,
        brain_dir=args.brain_dir,
        active_hours=args.active_hours,
        require_grill_me=require_grill_me,
    )

    if args.once:
        result = detector.detect()

        pipeline_info = None
        if result.trigger_matched and not args.no_launch:
            ok, code, msg = detector.launch_pipeline(wait=args.wait, capture_output=True)
            pipeline_info = (ok, code, msg)
            result.details["pipeline_result"] = {
                "success": ok,
                "exit_code": code,
                "message": msg
            }
            result.details["step1_result"] = result.details["pipeline_result"]

        if args.json:
            envelope = result.to_json_envelope()
            print(json.dumps(envelope, indent=2))
        else:
            display_dashboard(
                result,
                chat_stats=result.chat_stats,
                wipe_screen=True
            )

        exit_code = 0
        if not result.is_detected:
            exit_code = 1
        elif pipeline_info and not pipeline_info[0]:
            exit_code = pipeline_info[1]

        if pause_enabled:
            wait_for_user()

        sys.exit(exit_code)

    # Continuous 10-second polling timer loop (Two-Factor Trigger Engine)
    check_count = 0
    try:
        while True:
            check_count += 1
            result = detector.detect()

            if not args.json:
                display_dashboard(
                    result,
                    chat_stats=result.chat_stats,
                    wipe_screen=True
                )

            # Two-Factor Trigger: Antigravity open AND pending Grill-Me chat detected!
            if result.trigger_matched:
                pipeline_info = None
                if not args.no_launch:
                    ok, code, msg = detector.launch_pipeline(wait=args.wait, capture_output=True)
                    pipeline_info = (ok, code, msg)
                    result.details["pipeline_result"] = {
                        "success": ok,
                        "exit_code": code,
                        "message": msg
                    }
                    result.details["step1_result"] = result.details["pipeline_result"]

                if args.json:
                    envelope = result.to_json_envelope()
                    print(json.dumps(envelope, indent=2))

                exit_code = 0
                if pipeline_info and not pipeline_info[0]:
                    exit_code = pipeline_info[1]

                if pause_enabled:
                    wait_for_user()

                sys.exit(exit_code)

            # Not matched yet: check max_checks
            if args.max_checks and check_count >= args.max_checks:
                if args.json:
                    envelope = result.to_json_envelope()
                    print(json.dumps(envelope, indent=2))
                if pause_enabled:
                    wait_for_user()
                sys.exit(0)

            # 10-second timer sleep in 0.5s increments to be reactive to Ctrl+C
            sleep_remaining = args.interval
            while sleep_remaining > 0:
                step = min(0.5, sleep_remaining)
                time.sleep(step)
                sleep_remaining -= step

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
