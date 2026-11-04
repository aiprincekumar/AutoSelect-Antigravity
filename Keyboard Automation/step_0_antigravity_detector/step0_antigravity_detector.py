#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 0 - AntiGravity Detector (Canonical Unified Status Monitor & 10s Timer Dashboard)
======================================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Two-Factor Status Monitor)
Part of: AutoSelect-Commander Automation Suite
Workspace: Keyboard Automation (Step 0: Detector & Status Monitor)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)

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
  3. Two-Factor Trigger Verification:
     - Factor 1: Is Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat (ask_question) waiting?
  4. Unified Architecture:
     - Single canonical runner for both development testing and production monitoring.
     - Configurable polling cadence via `--interval` (default: 10.0s).
     - Execution of remaining steps is decoupled and handled by Complete Automation.
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
    get_antigravity_chat_stats,
    resolve_brain_dir,
)


def clear_screen():
    """Clear terminal console screen safely for 100% Screen Purity."""
    try:
        if sys.platform == "win32":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
    except Exception:
        pass


def format_dashboard_box(
    result: DetectionResult,
    chat_stats: Optional[Dict[str, Any]] = None,
    poll_interval: Optional[float] = None,
) -> str:
    """
    Format the ultra-clean, numbers-focused 100% Screen Purity Unicode dashboard box.
    Box width: 70 characters.
    """
    stats = chat_stats or result.chat_stats or {}

    total_chats = stats.get("total_chats", 0)
    active_chats = stats.get("active_chats", 0)
    inactive_chats = stats.get("inactive_chats", 0)
    pending_chats = stats.get("pending_grill_me_chats", 0)

    effective_interval = poll_interval if poll_interval is not None else DEFAULT_TEST_POLL_INTERVAL

    # Status formatting
    if result.is_detected:
        ag_status_str = "OPEN"
    else:
        ag_status_str = "CLOSED"

    if pending_chats > 0:
        grill_me_str = f"YES ({pending_chats} Chat{'s' if pending_chats != 1 else ''})"
    else:
        grill_me_str = "NO (0 Chats)"

    total_str = f"{total_chats} Chats"
    active_str = f"{active_chats} Chats"
    inactive_str = f"{inactive_chats} Chats"

    # Box dimensions
    INNER_WIDTH = 68
    LEFT_COL_WIDTH = 28
    RIGHT_COL_WIDTH = INNER_WIDTH - LEFT_COL_WIDTH - 3

    def _row(label: str, val: str) -> str:
        content = f"  {label:<{LEFT_COL_WIDTH}} : {val:<{RIGHT_COL_WIDTH}}"
        pad_len = INNER_WIDTH - len(content)
        if pad_len > 0:
            content += " " * pad_len
        elif pad_len < 0:
            content = content[:INNER_WIDTH]
        return f"│{content}│"

    lines = [
        "┌" + "─" * INNER_WIDTH + "┐",
        _row("AntiGravity Status", ag_status_str),
        _row("Total Chats", total_str),
        _row("Active Chats", active_str),
        _row("Inactive Chats", inactive_str),
        _row("Pending Grill-Me", grill_me_str),
        "└" + "─" * INNER_WIDTH + "┘",
    ]
    return "\n".join(lines)


def display_dashboard(
    result: DetectionResult,
    chat_stats: Optional[Dict[str, Any]] = None,
    wipe_screen: bool = True,
    poll_interval: float = DEFAULT_TEST_POLL_INTERVAL
):
    """Render the dashboard box to stdout with 100% Screen Purity."""
    if wipe_screen:
        clear_screen()
    box = format_dashboard_box(result, chat_stats=chat_stats, poll_interval=poll_interval)
    sys.stdout.write(box + "\n")
    sys.stdout.flush()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 0 - AntiGravity Detector (Canonical Unified Status Monitor & 10s Timer Dashboard)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform a single detection check, print clean dashboard box, and exit immediately"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Polling interval in seconds between detection checks (default: from config.json based on mode)"
    )
    parser.add_argument(
        "--active-hours",
        type=float,
        default=None,
        help="Hours threshold to classify a conversation as active session (default: from config.json)"
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
        help="Trigger immediately whenever Antigravity is open, without requiring pending Grill-Me chats"
    )
    return parser.parse_args()


def should_pause(args: argparse.Namespace) -> bool:
    """Determine whether to keep the console window open on completion."""
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
    require_grill_me = False if args.any_antigravity else None

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=True,
        verbose=False,
        brain_dir=args.brain_dir,
        active_hours=args.active_hours,
        require_grill_me=require_grill_me,
    )
    actual_interval = detector.poll_interval

    if args.once:
        result = detector.detect()

        if args.json:
            envelope = result.to_json_envelope()
            print(json.dumps(envelope, indent=2))
        else:
            display_dashboard(
                result,
                chat_stats=result.chat_stats,
                wipe_screen=True,
                poll_interval=actual_interval,
            )

        exit_code = 0 if result.is_detected else 1
        if pause_enabled:
            wait_for_user()
        sys.exit(exit_code)

    # Continuous polling timer loop (Two-Factor Status Monitor)
    try:
        while True:
            result = detector.detect()

            if not args.json:
                display_dashboard(
                    result,
                    chat_stats=result.chat_stats,
                    wipe_screen=True,
                    poll_interval=actual_interval,
                )

            # Two-Factor Trigger: Antigravity open AND pending Grill-Me chat detected!
            if result.trigger_matched:
                if args.json:
                    envelope = result.to_json_envelope()
                    print(json.dumps(envelope, indent=2))

                if pause_enabled:
                    wait_for_user()
                sys.exit(0)

            # Sleep in small increments for Ctrl+C responsiveness
            sleep_remaining = actual_interval
            while sleep_remaining > 0:
                time.sleep(min(0.5, sleep_remaining))
                sleep_remaining -= 0.5

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)


if __name__ == "__main__":
    main()
