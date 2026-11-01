#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Select (Recommended) Option
AutoSelect-Commander - GUI Automation Pipeline
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Usage:
  python step2_select_recommended_option.py
  python step2_select_recommended_option.py --x 541 --y 664
  python step2_select_recommended_option.py --no-countdown
  python step2_select_recommended_option.py --dry-run
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_utils import (
    initialize_pyautogui,
    get_config,
    hover_and_click,
    smooth_drag,
    run_countdown,
    capture_debug_screenshot,
    get_screen_dimensions
)


def run_step2(x=None, y=None, hover_delay=None, move_duration=None, drag_mode=False, dry_run=False, skip_countdown=False):
    """Execute Step 2: Smoothly navigate to (Recommended) option, hover, and click to select."""
    print("=" * 65)
    print("🎯 [STEP 2 / 4] SELECT (RECOMMENDED) OPTION")
    print("   (स्टेप 2: रिकमेंडेड ऑप्शन / रेडियो बटन पर स्मूथ मूवमेंट, होवर व चयन)")
    print("=" * 65)

    pyautogui = initialize_pyautogui()
    config = get_config()
    step_cfg = config.get("steps", {}).get("step2_recommended", {})
    settings = config.get("settings", {})

    target_x = x if x is not None else step_cfg.get("x", 541)
    target_y = y if y is not None else step_cfg.get("y", 664)
    hover = hover_delay if hover_delay is not None else step_cfg.get("hover_delay", 0.7)
    duration = move_duration if move_duration is not None else step_cfg.get("move_duration", 0.8)
    easing = settings.get("easing_function", "easeOutQuad")
    clicks = step_cfg.get("clicks", 1)
    button = step_cfg.get("button", "left")

    screen_w, screen_h = get_screen_dimensions()
    if target_x > screen_w or target_y > screen_h:
        print(f"[WARNING] Target ({target_x}, {target_y}) is outside screen bounds ({screen_w}x{screen_h})!")
        print("          Run: python calibrate_coordinates.py to set your exact layout.")

    if not skip_countdown:
        countdown_secs = config.get("pipeline", {}).get("start_countdown_seconds", 3)
        run_countdown(countdown_secs, "Focus the target window! Step 2 starts in")

    try:
        if drag_mode:
            print(f"  [DRAG-MODE] Dragging mouse to ({target_x}, {target_y})")
            smooth_drag(target_x, target_y, duration=duration, button=button)
        else:
            hover_and_click(
                x=target_x,
                y=target_y,
                hover_delay=hover,
                move_duration=duration,
                clicks=clicks,
                button=button,
                label="(Recommended) Option / Radio Button",
                easing=easing,
                dry_run=dry_run
            )

        if settings.get("save_debug_screenshots", True):
            capture_debug_screenshot("step2_recommended_selected")

        print("\n" + "-" * 65)
        print("✅ [STEP 2 SUCCESS] '(Recommended)' option selected successfully!")
        print("👉 Next: Run 'python step3_click_submit_button.py' to submit.")
        print("-" * 65)
        return 0

    except pyautogui.FailSafeException:
        print("\n🛑 [FAILSAFE TRIGGERED] Mouse moved to screen corner (0,0). Automation aborted.")
        return 2
    except Exception as e:
        print(f"\n❌ [ERROR] Step 2 failed with exception: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Step 2: Select (Recommended) option")
    parser.add_argument("--x", type=int, default=None, help="Target X coordinate")
    parser.add_argument("--y", type=int, default=None, help="Target Y coordinate")
    parser.add_argument("--hover", type=float, default=None, help="Hover delay seconds before clicking")
    parser.add_argument("--duration", type=float, default=None, help="Smooth move duration seconds")
    parser.add_argument("--drag", action="store_true", help="Use mouse drag instead of smooth hover move")
    parser.add_argument("--dry-run", action="store_true", help="Simulate mouse move without clicking")
    parser.add_argument("--no-countdown", action="store_true", help="Skip the initial 3-second countdown")

    args = parser.parse_args()
    exit_code = run_step2(
        x=args.x,
        y=args.y,
        hover_delay=args.hover,
        move_duration=args.duration,
        drag_mode=args.drag,
        dry_run=args.dry_run,
        skip_countdown=args.no_countdown
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
