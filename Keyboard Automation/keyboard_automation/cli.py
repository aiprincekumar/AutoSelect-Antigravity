#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-Line Interface (CLI) Subsystem
======================================
Parses command-line arguments, displays execution banner, orchestrates
repeat sequences and countdowns, and returns process exit status.
"""

import sys
import time
import argparse
import logging

from .constants import IS_WINDOWS, DEFAULT_TARGET_WINDOW
from .automator import GrillMeAutomator

logger = logging.getLogger("GrillMeAutomation.CLI")


def parse_arguments():
    """Defines and parses command-line arguments for the Grill Me automation suite."""
    parser = argparse.ArgumentParser(
        description="Grill Me Keyboard Automation Suite for Antigravity 2.0 Harness & Chat Interfaces.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-t", "--target-window",
        type=str,
        default=DEFAULT_TARGET_WINDOW,
        help="Keyword(s) to identify target window (e.g. 'Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander'). Supports comma-separated keywords and process image matching."
    )
    parser.add_argument(
        "--auto-focus",
        dest="auto_focus",
        action="store_true",
        default=True,
        help="Automatically bring target window to foreground before injection (default: True)."
    )
    parser.add_argument(
        "--no-auto-focus",
        dest="auto_focus",
        action="store_false",
        help="Disable automatic foreground window focusing."
    )
    parser.add_argument(
        "--auto-maximize",
        dest="auto_maximize",
        action="store_true",
        default=True,
        help="Automatically restore and maximize target window to full screen (default: True)."
    )
    parser.add_argument(
        "--no-auto-maximize",
        dest="auto_maximize",
        action="store_false",
        help="Disable automatic window maximization."
    )
    parser.add_argument(
        "--settle-delay",
        type=float,
        default=0.5,
        help="Delay in seconds after window focus/maximize to allow UI rendering to settle."
    )
    parser.add_argument(
        "-c", "--countdown",
        type=int,
        default=5,
        help="Seconds of countdown to focus the target chat window before keystrokes are sent."
    )
    parser.add_argument(
        "-d", "--step-delay",
        type=float,
        default=0.35,
        help="Delay in seconds between keystroke steps (e.g. 0.35 = 350ms)."
    )
    parser.add_argument(
        "--hold-delay",
        type=float,
        default=0.05,
        help="Duration in seconds keys are held down before releasing."
    )
    parser.add_argument(
        "-o", "--option",
        type=str,
        default="1",
        help="The option number or character to choose (default: 1)."
    )
    parser.add_argument(
        "--skip-ctrl-l",
        action="store_true",
        help="Skip sending Ctrl + L (if chat input is already focused)."
    )
    parser.add_argument(
        "--skip-enter",
        action="store_true",
        help="Skip sending Enter (leaves selection active without auto-submitting)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without sending actual keyboard events."
    )
    parser.add_argument(
        "-e", "--engine",
        choices=["auto", "ctypes", "pyautogui"],
        default="auto",
        help="Input simulation engine to use."
    )
    parser.add_argument(
        "-r", "--repeat",
        type=int,
        default=1,
        help="Number of times to run the sequence."
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=2.0,
        help="Interval between repeats in seconds."
    )
    parser.add_argument(
        "--no-countdown",
        action="store_true",
        help="Execute immediately without countdown."
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="Non-interactive execution flag (skip prompt at end)."
    )
    args, _ = parser.parse_known_args()
    return args


def print_banner(args):
    """Outputs structured execution banner to terminal."""
    print("\n" + "=" * 65)
    print("      [*] AutoSelect-Commander: Grill Me Keyboard Automation")
    print("=" * 65)
    print(f" Target Window: '{args.target_window}' (Focus: {args.auto_focus}, Maximize: {args.auto_maximize})")
    print(f" Engine      : {args.engine.upper()} (Zero-dependency ctypes: {IS_WINDOWS})")
    print(f" Sequence    : {'Ctrl+L -> ' if not args.skip_ctrl_l else ''}Shift+Tab -> Option '{args.option}' -> {'Enter' if not args.skip_enter else '[No Enter]'}")
    print(f" Step Delay  : {int(args.step_delay * 1000)}ms | Settle Delay: {int(args.settle_delay * 1000)}ms")
    print(f" Mode        : {'DRY RUN (Simulated)' if args.dry_run else 'ACTIVE INJECTION'}")
    print("=" * 65 + "\n")


def main():
    """Main CLI execution entrypoint."""
    args = parse_arguments()
    print_banner(args)

    automator = GrillMeAutomator(
        engine=args.engine,
        step_delay=args.step_delay,
        hold_delay=args.hold_delay,
        option=args.option,
        skip_ctrl_l=args.skip_ctrl_l,
        skip_enter=args.skip_enter,
        dry_run=args.dry_run,
        target_window=args.target_window,
        auto_focus=args.auto_focus,
        auto_maximize=args.auto_maximize,
        settle_delay=args.settle_delay,
    )

    if not args.no_countdown and args.countdown > 0:
        automator.run_countdown(seconds=args.countdown)

    total_runs = max(1, args.repeat)
    success_count = 0

    for iteration in range(1, total_runs + 1):
        if total_runs > 1:
            print(f"\n--- Iteration {iteration} of {total_runs} ---")
        
        ok = automator.execute()
        if ok:
            success_count += 1

        if iteration < total_runs and args.interval > 0:
            logger.info(f"Waiting {args.interval}s before next iteration...")
            time.sleep(args.interval)

    print("\n" + "=" * 65)
    print(f"  [+] Execution Finished: {success_count}/{total_runs} runs successful.")
    print("=" * 65 + "\n")

    return 0 if success_count == total_runs else 1


if __name__ == "__main__":
    sys.exit(main())
