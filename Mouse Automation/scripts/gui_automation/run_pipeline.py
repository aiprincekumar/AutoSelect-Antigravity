#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Pipeline Runner for GUI Mouse Automation
AutoSelect-Commander
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Usage:
  python run_pipeline.py                  # Run all 4 steps sequentially
  python run_pipeline.py --step 1         # Run only Step 1 (Focus chat)
  python run_pipeline.py --step 2         # Run only Step 2 (Select Recommended)
  python run_pipeline.py --step 3         # Run only Step 3 (Click Submit)
  python run_pipeline.py --step 4         # Run only Step 4 (Verify)
  python run_pipeline.py --dry-run        # Preview all movements without clicking
  python run_pipeline.py --delay 2.0      # Set custom pause between steps
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
    run_countdown,
    get_screen_dimensions
)
from step1_open_and_click_chat import run_step1
from step2_select_recommended_option import run_step2
from step3_click_submit_button import run_step3
from step4_verify_execution import run_step4


def run_full_pipeline(step_filter=None, dry_run=False, step_delay=None):
    """Run specified steps or all 4 steps in order with pauses."""
    print("=" * 70)
    print("🤖 MASTER GUI MOUSE AUTOMATION PIPELINE")
    print("   (मास्टर जीयूआई माउस ऑटोमेशन पाइपलाइन)")
    print("=" * 70)

    pyautogui = initialize_pyautogui()
    config = get_config()
    screen_w, screen_h = get_screen_dimensions()
    print(f"Display Mode: {screen_w}x{screen_h}")

    pipeline_cfg = config.get("pipeline", {})
    inter_step_delay = step_delay if step_delay is not None else pipeline_cfg.get("delay_between_steps_seconds", 1.2)
    countdown_secs = pipeline_cfg.get("start_countdown_seconds", 3)

    if dry_run:
        print("⚠️  DRY-RUN MODE: Mouse will smoothly hover targets without sending clicks.")

    # 3-second startup countdown
    run_countdown(countdown_secs, "Focus your target Antigravity/Browser window now! Starting in")

    steps_to_run = [1, 2, 3, 4] if step_filter is None else [step_filter]
    results = {}

    for step_num in steps_to_run:
        print(f"\n>>> EXECUTING PIPELINE STAGE: STEP {step_num} <<<")
        start_time = time.time()
        exit_code = 0

        try:
            if step_num == 1:
                exit_code = run_step1(dry_run=dry_run, skip_countdown=True)
            elif step_num == 2:
                exit_code = run_step2(dry_run=dry_run, skip_countdown=True)
            elif step_num == 3:
                exit_code = run_step3(dry_run=dry_run, skip_countdown=True)
            elif step_num == 4:
                exit_code = run_step4()

            elapsed = time.time() - start_time
            results[step_num] = {"status": "SUCCESS" if exit_code == 0 else "FAILED", "code": exit_code, "time": elapsed}

            if exit_code != 0:
                print(f"\n❌ Pipeline halted at Step {step_num} (Exit Code: {exit_code}).")
                break

            # Pause between steps to allow GUI transition and element render
            if step_num < max(steps_to_run) and exit_code == 0:
                print(f"  [PAUSE] Waiting {inter_step_delay:.2f}s for UI to render and settle before next step...")
                time.sleep(inter_step_delay)

        except pyautogui.FailSafeException:
            print("\n🛑 [FAILSAFE TRIGGERED] Mouse moved to top-left corner (0,0). Pipeline aborted safely.")
            results[step_num] = {"status": "FAILSAFE_ABORTED", "code": 2, "time": 0}
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in Step {step_num}: {e}")
            results[step_num] = {"status": "EXCEPTION", "code": 1, "time": 0}
            break

    # Summary report
    print("\n" + "=" * 70)
    print("📋 PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    all_passed = True
    for s_num, res in results.items():
        symbol = "✅" if res["status"] == "SUCCESS" else "❌"
        print(f"  {symbol} Step {s_num}: {res['status']} (Time: {res.get('time', 0):.2f}s, Exit Code: {res['code']})")
        if res["status"] != "SUCCESS":
            all_passed = False

    if all_passed and len(results) == len(steps_to_run):
        print("\n🎉 ALL REQUESTED STEPS EXECUTED AND VERIFIED SUCCESSFULLY!")
        print("=" * 70 + "\n")
        return 0
    else:
        print("\n⚠️  Pipeline completed with issues. Check individual logs or run with --dry-run.")
        print("=" * 70 + "\n")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Master GUI Automation Pipeline Runner")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4], default=None, help="Run only a specific step")
    parser.add_argument("--dry-run", action="store_true", help="Simulate movements without clicking")
    parser.add_argument("--delay", type=float, default=None, help="Delay in seconds between steps")

    args = parser.parse_args()
    code = run_full_pipeline(
        step_filter=args.step,
        dry_run=args.dry_run,
        step_delay=args.delay
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
