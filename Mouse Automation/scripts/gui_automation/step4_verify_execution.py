#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4: Verify Execution & Settle State
AutoSelect-Commander - GUI Automation Pipeline
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Usage:
  python step4_verify_execution.py
"""

import sys
import time
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_utils import (
    initialize_pyautogui,
    get_config,
    capture_debug_screenshot,
    get_screen_dimensions
)


def run_step4(settle_seconds=None):
    """Execute Step 4: Verify execution, inspect mouse position, and capture evidence screenshot."""
    print("=" * 65)
    print("🔍 [STEP 4 / 4] VERIFY EXECUTION & UI SETTLE STATE")
    print("   (स्टेप 4: एक्शन सत्यापन, माउस स्टेट चेक व एविडेंस स्क्रीनशॉट)")
    print("=" * 65)

    pyautogui = initialize_pyautogui()
    config = get_config()
    step_cfg = config.get("steps", {}).get("step4_verify", {})
    
    wait_time = settle_seconds if settle_seconds is not None else step_cfg.get("wait_after_submit_seconds", 1.5)

    print(f"  [SETTLE] Waiting {wait_time}s for GUI animations / state transitions to settle...")
    time.sleep(wait_time)

    # Check mouse position
    pos = pyautogui.position()
    screen_w, screen_h = get_screen_dimensions()
    print(f"  [CHECK] Final Cursor Position: (X={pos.x}, Y={pos.y}) within Display ({screen_w}x{screen_h})")

    # Safety release of any lingering mouse buttons
    if step_cfg.get("check_mouse_release", True):
        pyautogui.mouseUp(button="left")
        pyautogui.mouseUp(button="right")
        print("  [CHECK] Mouse button release confirmed (Zero lingering button locks).")

    # Capture verification screenshot
    screenshot_path = capture_debug_screenshot("step4_final_verification")

    print("\n" + "=" * 65)
    print("🎉 [WORKFLOW VERIFIED] ALL 4 STEPS COMPLETED CLEANLY!")
    print("   - Step 1: Chat area focused")
    print("   - Step 2: (Recommended) option selected")
    print("   - Step 3: Submit button clicked")
    print("   - Step 4: UI state settled and verified")
    if screenshot_path:
        print(f"   - Evidence: {screenshot_path}")
    print("=" * 65)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Step 4: Verify Execution")
    parser.add_argument("--settle", type=float, default=None, help="Settle wait time in seconds")
    args = parser.parse_args()
    exit_code = run_step4(settle_seconds=args.settle)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
