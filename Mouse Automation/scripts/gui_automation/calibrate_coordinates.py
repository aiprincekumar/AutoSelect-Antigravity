#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Coordinate Calibration Tool
AutoSelect-Commander - GUI Automation Pipeline
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Usage:
  python calibrate_coordinates.py          # Interactive wizard to record coordinates
  python calibrate_coordinates.py --live   # Continuous live cursor position tracker
  python calibrate_coordinates.py --show   # View currently saved coordinates
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
    save_config,
    get_screen_dimensions
)


def show_current_config():
    """Print currently configured coordinates."""
    config = get_config()
    screen_w, screen_h = get_screen_dimensions()
    print("\n" + "=" * 65)
    print(f"📊 CURRENT GUI AUTOMATION CONFIGURATION (Display: {screen_w}x{screen_h})")
    print("=" * 65)
    steps = config.get("steps", {})
    for key, step in steps.items():
        name = step.get("name", key)
        x = step.get("x", "N/A")
        y = step.get("y", "N/A")
        hover = step.get("hover_delay", "N/A")
        duration = step.get("move_duration", "N/A")
        print(f"  • {name}")
        print(f"    Position: (X={x}, Y={y}) | Hover: {hover}s | Move Duration: {duration}s")
    print("=" * 65 + "\n")


def live_coordinate_tracker():
    """Continuously track mouse position in real-time."""
    pyautogui = initialize_pyautogui()
    screen_w, screen_h = get_screen_dimensions()
    print("\n" + "=" * 65)
    print(f"📍 LIVE MOUSE POSITION TRACKER (Display: {screen_w}x{screen_h})")
    print("   Move your mouse anywhere on screen. Press Ctrl+C to exit.")
    print("=" * 65)
    try:
        while True:
            x, y = pyautogui.position()
            pos_str = f"X: {str(x).rjust(5)} | Y: {str(y).rjust(5)}  [Press Ctrl+C to stop]"
            print(f"\r{pos_str}", end="", flush=True)
            time.sleep(0.08)
    except KeyboardInterrupt:
        print("\n\n[OK] Live tracker stopped.\n")


def interactive_calibration():
    """Step-by-step wizard to calibrate and save exact target coordinates."""
    pyautogui = initialize_pyautogui()
    config = get_config()
    screen_w, screen_h = get_screen_dimensions()

    print("\n" + "=" * 70)
    print("🎯 GUI AUTOMATION INTERACTIVE COORDINATE CALIBRATION WIZARD")
    print("   (माउस कोर्डिनेट कैलिब्रेशन विज़ार्ड - हिंदी व इंग्लिश गाइड)")
    print("=" * 70)
    print(f"Detected Display Resolution: {screen_w} x {screen_h}")
    print("\nHow this works:")
    print("1. For each step, move your mouse pointer over the target button/option.")
    print("2. Switch back to this terminal and press [ENTER] to lock in the position.")
    print("3. Coordinates will be automatically written into config.json!\n")

    input("Press [ENTER] to start calibration...")

    targets = [
        ("step1_chat", "Step 1: Chat Area / Input Box (चैट एरिया या इनपुट बॉक्स)"),
        ("step2_recommended", "Step 2: '(Recommended)' Option / Radio Button (रिकमेंडेड ऑप्शन)"),
        ("step3_submit", "Step 3: 'Submit' / 'Proceed' Button (सबमिट या कन्फर्म बटन)")
    ]

    for key, description in targets:
        print("\n" + "-" * 70)
        print(f"👉 Target: {description}")
        print("   -> Move your mouse over this element on your screen.")
        print("   -> (You have 3 seconds to place your cursor, or press ENTER when ready)")
        for c in range(3, 0, -1):
            x, y = pyautogui.position()
            print(f"      Locking in {c}s... Current cursor at: ({x}, {y})", flush=True)
            time.sleep(1)

        final_x, final_y = pyautogui.position()
        print(f"   🔒 LOCKED IN: ({final_x}, final_y={final_y}) for {key}")

        if key in config["steps"]:
            config["steps"][key]["x"] = final_x
            config["steps"][key]["y"] = final_y

    # Update screen dimension note
    config["screen"]["expected_width"] = screen_w
    config["screen"]["expected_height"] = screen_h

    # Save to config.json
    save_config(config)

    print("\n" + "=" * 70)
    print("🎉 [CALIBRATION COMPLETE] All coordinates saved successfully into config.json!")
    print("   You can now run individual steps or master pipeline:")
    print("     python step1_open_and_click_chat.py")
    print("     python step2_select_recommended_option.py")
    print("     python step3_click_submit_button.py")
    print("     python run_pipeline.py")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Calibrate GUI automation coordinates")
    parser.add_argument("--live", action="store_true", help="Launch live coordinate tracker")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    args = parser.parse_args()

    if args.live:
        live_coordinate_tracker()
    elif args.show:
        show_current_config()
    else:
        interactive_calibration()


if __name__ == "__main__":
    main()
