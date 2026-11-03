#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (टेस्टिंग रनर - सिंपल क्लीन डैशबोर्ड)
Step 0 - AntiGravity Detector (Testing Runner - Simple Clean Dashboard)
==================================================================
Pipeline Step: STEP 0 (AntiGravity Detector & Step 1 Auto-Trigger)
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 0 of 3)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

Clean Dashboard Specifications:
  1. Ultra-clean, human-readable numbers-focused console dashboard:
     - AntiGravity Open/Closed status
     - Total chats count in brain storage
     - Active chats count (current active session / recent activity)
     - Inactive chats count (total - active)
     - Pending Grill-Me (ask_question) count requiring user interaction
  2. Zero technical clutter:
     - No raw PIDs, HWNDs, window classes, or internal method traces
     - No progress text, no extra status strings, strictly only the dashboard box
  3. Single-Shot Mode:
     - Pass --once for immediate detection, metrics computation, and clean dashboard
  4. Dept 06 JSON Envelope Compatibility:
     - Pass --json to retain complete structured JSON response envelope with chat_stats
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
)

# Optional import of GrillMeDetector from step_1_chat_identifier
try:
    from step_1_chat_identifier.step1_find_and_focus import GrillMeDetector
except ImportError:
    GrillMeDetector = None

DEFAULT_ACTIVE_HOURS = 12.0


def resolve_brain_dir(explicit_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the Antigravity brain storage directory."""
    if explicit_path:
        p = Path(explicit_path).resolve()
        if p.is_dir():
            return p

    env_brain = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
    if env_brain and Path(env_brain).is_dir():
        return Path(env_brain).resolve()

    candidates = [
        Path(r"C:\Users\Atul Verma\.gemini\antigravity\brain"),
        Path(os.path.expanduser(r"~\.gemini\antigravity\brain")),
    ]
    for c in candidates:
        if c.is_dir():
            return c.resolve()

    return candidates[0]


def _fallback_scan_grill_me(convo_dirs: List[Path]) -> List[str]:
    """Fallback scanner for pending ask_question tool calls if GrillMeDetector is unavailable."""
    pending: List[str] = []
    for d in convo_dirs:
        cid = d.name
        logs_dir = d / ".system_generated" / "logs"
        full_transcript = logs_dir / "transcript_full.jsonl"
        compact_transcript = logs_dir / "transcript.jsonl"
        transcript = full_transcript if full_transcript.is_file() else compact_transcript
        if not transcript.is_file():
            continue

        lines: List[Dict[str, Any]] = []
        try:
            with open(transcript, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            lines.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            continue

        if not lines:
            continue

        total_steps = len(lines)
        for i in range(total_steps - 1, -1, -1):
            step = lines[i]
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name") or tc.get("tool_name") or ""
                if name == "ask_question":
                    # Check if answered
                    answered = False
                    for j in range(i + 1, total_steps):
                        sub = lines[j]
                        stype = sub.get("type", "")
                        if stype in ("USER_INPUT", "GENERIC"):
                            answered = True
                            break
                        if stype == "PLANNER_RESPONSE" and sub.get("status") == "DONE":
                            if not any((c.get("name") == "ask_question" or c.get("tool_name") == "ask_question") for c in sub.get("tool_calls", [])):
                                answered = True
                                break
                    if not answered:
                        pending.append(cid)
                    break
            if pending and pending[-1] == cid:
                break
    return pending


def get_antigravity_chat_stats(
    brain_dir: Optional[Union[str, Path]] = None,
    active_hours: float = DEFAULT_ACTIVE_HOURS,
    is_antigravity_running: bool = True
) -> Dict[str, Any]:
    """
    Calculate exact chat telemetry metrics from Antigravity brain storage:
      - total_chats: Total valid conversation directories
      - active_chats: Conversations with recent activity (within active_hours)
      - inactive_chats: total_chats - active_chats
      - pending_grill_me_chats: Conversations where ask_question is waiting for user
      - has_pending_grill_me: Boolean (True if pending_grill_me_chats > 0)
    """
    p = resolve_brain_dir(brain_dir)
    if not p.is_dir():
        return {
            "total_chats": 0,
            "active_chats": 0,
            "inactive_chats": 0,
            "pending_grill_me_chats": 0,
            "has_pending_grill_me": False,
            "brain_path": str(p),
            "pending_chat_ids": [],
        }

    now = time.time()
    valid_convos: List[Path] = []
    active_count = 0

    try:
        entries = [e for e in p.iterdir() if e.is_dir() and not e.name.startswith(".") and e.name != "tempmediaStorage"]
    except Exception:
        entries = []

    for d in entries:
        t1 = d / ".system_generated" / "logs" / "transcript.jsonl"
        t2 = d / ".system_generated" / "logs" / "transcript_full.jsonl"
        if t1.is_file() or t2.is_file() or (d / ".system_generated").is_dir():
            valid_convos.append(d)
            mtimes = [f.stat().st_mtime for f in [t1, t2, d] if f.exists()]
            if mtimes and (now - max(mtimes)) <= (active_hours * 3600.0):
                active_count += 1

    total_count = len(valid_convos)
    inactive_count = max(0, total_count - active_count)

    pending_ids: List[str] = []
    try:
        if GrillMeDetector is not None:
            detector = GrillMeDetector(str(p))
            pending_chats = detector.scan_transcripts()
            pending_ids = [c.conversation_id for c in pending_chats]
        else:
            pending_ids = _fallback_scan_grill_me(valid_convos)
    except Exception:
        pending_ids = []

    pending_count = len(pending_ids)

    return {
        "total_chats": total_count,
        "active_chats": active_count,
        "inactive_chats": inactive_count,
        "pending_grill_me_chats": pending_count,
        "has_pending_grill_me": (pending_count > 0),
        "brain_path": str(p.resolve()),
        "pending_chat_ids": pending_ids,
    }


def format_dashboard_box(
    is_detected: bool,
    chat_stats: Dict[str, Any]
) -> str:
    """
    Render the ultra-clean, elegant, numbers-focused dashboard box.
    """
    status_str = "खुला है / OPEN (चालू)" if is_detected else "बंद है / CLOSED (0 active processes)"
    total_str = str(chat_stats.get("total_chats", 0))
    active_str = str(chat_stats.get("active_chats", 0))
    inactive_str = str(chat_stats.get("inactive_chats", 0))

    pending = chat_stats.get("pending_grill_me_chats", 0)
    if pending > 0:
        grill_me_str = f"हाँ / YES ({pending} चैट)"
    else:
        grill_me_str = "नहीं / NO (0 चैट)"

    base_val_len = 23
    val_len = max(len(status_str) + 2, len(grill_me_str) + 2, base_val_len)
    extra = val_len - base_val_len
    dash_count = 56 + extra

    top = "┌" + ("─" * dash_count) + "┐"
    div = "├" + ("─" * dash_count) + "┤"
    bot = "└" + ("─" * dash_count) + "┘"

    title = "🚀 ANTIGRAVITY STATUS & CHAT DASHBOARD"
    needed_spaces = dash_count - len(title) - 1
    left_sp = max(0, needed_spaces // 2)
    right_sp = max(0, needed_spaces - left_sp)
    header = "│" + (" " * left_sp) + title + (" " * right_sp) + "│"

    r1 = f"│  • एंटी-ग्रेविटी स्थिति (Status)       : {status_str:<{val_len}}│"
    r2 = f"│  • कुल चैट्स (Total Chats)             : {total_str:<{val_len}}│"
    r3 = f"│  • एक्टिव चैट्स (Active Chats)         : {active_str:<{val_len}}│"
    r4 = f"│  • इनएक्टिव चैट्स (Inactive Chats)     : {inactive_str:<{val_len}}│"
    r5 = f"│  • ग्रिल-मी पेंडिंग (Pending Question) : {grill_me_str:<{val_len}}│"

    return "\n".join(["", top, header, div, r1, r2, r3, r4, r5, bot, ""])


def display_dashboard(
    result: DetectionResult,
    chat_stats: Optional[Dict[str, Any]] = None,
    step1_result: Optional[Tuple[bool, int, str]] = None,
    action_note: Optional[str] = None
):
    """Render strictly the clean dashboard box with zero extra noise."""
    if chat_stats is None:
        chat_stats = get_antigravity_chat_stats(is_antigravity_running=result.is_detected)

    box = format_dashboard_box(result.is_detected, chat_stats)
    print(box)


def display_telemetry_banner(
    result: DetectionResult,
    step1_result: Optional[Tuple[bool, int, str]] = None,
    action_note: Optional[str] = None,
    chat_stats: Optional[Dict[str, Any]] = None
):
    """Backwards-compatible wrapper routing strictly to the clean dashboard."""
    display_dashboard(result, chat_stats=chat_stats, step1_result=step1_result, action_note=action_note)


def parse_args():
    parser = argparse.ArgumentParser(
        description="स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर (डैशबोर्ड टेस्ट रनर) / Step 0 - AntiGravity Detector (Dashboard Test Runner)"
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
        help="Wait for Step 1 completion (default: True in test runner)"
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


def on_check_telemetry(check_num: int, result: DetectionResult):
    """Callback for polling iterations (silent in clean dashboard mode)."""
    pass


def main():
    args = parse_args()
    pause_enabled = should_pause(args)

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        headless=True,
        verbose=False,
    )

    if args.once:
        result = detector.detect()
        chat_stats = get_antigravity_chat_stats(
            brain_dir=args.brain_dir,
            active_hours=args.active_hours,
            is_antigravity_running=result.is_detected
        )

        step1_info = None

        if result.is_detected and not args.no_launch:
            ok, code, msg = detector.launch_step1(wait=args.wait)
            step1_info = (ok, code, msg)
            result.details["step1_result"] = {
                "success": ok,
                "exit_code": code,
                "message": msg
            }

        if args.json:
            envelope = result.to_json_envelope()
            envelope["data"]["chat_stats"] = chat_stats
            envelope["data"]["details"]["chat_stats"] = chat_stats
            print(json.dumps(envelope, indent=2))
        else:
            display_dashboard(
                result,
                chat_stats=chat_stats,
            )

        exit_code = 0
        if not result.is_detected:
            exit_code = 1
        elif step1_info and not step1_info[0]:
            exit_code = step1_info[1]

        if pause_enabled:
            wait_for_user()

        sys.exit(exit_code)

    # Continuous polling runner
    auto_trigger = not args.no_launch
    result = detector.run_loop(
        poll_interval=args.interval,
        max_checks=args.max_checks,
        auto_launch=auto_trigger,
        wait_for_step1=args.wait,
        on_check_callback=on_check_telemetry,
    )

    is_running = bool(result and result.is_detected)
    chat_stats = get_antigravity_chat_stats(
        brain_dir=args.brain_dir,
        active_hours=args.active_hours,
        is_antigravity_running=is_running
    )

    step1_info = None

    if result and result.is_detected:
        if result.details and "step1_result" in result.details:
            s1 = result.details["step1_result"]
            step1_info = (s1.get("success", False), s1.get("exit_code", 0), s1.get("message", ""))

        if args.json:
            envelope = result.to_json_envelope()
            envelope["data"]["chat_stats"] = chat_stats
            envelope["data"]["details"]["chat_stats"] = chat_stats
            print(json.dumps(envelope, indent=2))
        else:
            display_dashboard(
                result,
                chat_stats=chat_stats,
            )

        exit_code = 0
        if step1_info and not step1_info[0]:
            exit_code = step1_info[1]

        if pause_enabled:
            wait_for_user()

        sys.exit(exit_code)
    else:
        dummy_res = DetectionResult(is_detected=False)
        if args.json:
            envelope = dummy_res.to_json_envelope()
            envelope["data"]["chat_stats"] = chat_stats
            envelope["data"]["details"]["chat_stats"] = chat_stats
            print(json.dumps(envelope, indent=2))
        else:
            display_dashboard(
                dummy_res,
                chat_stats=chat_stats,
            )

        if pause_enabled:
            wait_for_user()

        sys.exit(0)


if __name__ == "__main__":
    main()
