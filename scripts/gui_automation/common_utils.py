#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Utilities for Modular GUI Mouse Automation Pipeline
AutoSelect-Commander
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
"""

import os
import sys
import json
import time
import math
from pathlib import Path
from datetime import datetime

# Enforce UTF-8 stdout on Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[WARNING] 'pyautogui' is not installed. Run: pip install pyautogui pillow")

# Base paths
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"


def get_config():
    """Load config.json safely or provide default schema."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config_data):
    """Write updated configuration to config.json with clean formatting."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Configuration updated successfully: {CONFIG_PATH}")


def initialize_pyautogui(enable_failsafe=None):
    """Configure PyAutoGUI settings from config or explicit parameter."""
    if not PYAUTOGUI_AVAILABLE:
        print("[ERROR] pyautogui library missing. Please install via: pip install pyautogui pillow")
        sys.exit(1)

    try:
        cfg = get_config().get("settings", {})
        default_failsafe = cfg.get("failsafe_enabled", False)
        
        if enable_failsafe is not None:
            pyautogui.FAILSAFE = enable_failsafe
        else:
            # If cursor is at (0, 0), strict failsafe would immediately trigger on startup
            pos = pyautogui.position()
            if pos == (0, 0) and default_failsafe:
                print("  [NOTE] Cursor at (0, 0). Failsafe relaxed to avoid false startup abort.")
                pyautogui.FAILSAFE = False
            else:
                pyautogui.FAILSAFE = default_failsafe

        pyautogui.PAUSE = cfg.get("pause_between_pyautogui_actions", 0.1)
    except Exception as e:
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1

    return pyautogui


def get_screen_dimensions():
    """Return tuple (width, height) of current primary display."""
    if not PYAUTOGUI_AVAILABLE:
        return (1920, 1080)
    size = pyautogui.size()
    return (size.width, size.height)


def smooth_move(target_x, target_y, duration=0.8, easing="easeOutQuad"):
    """
    Smoothly glide mouse from current position to (target_x, target_y).
    Uses tweening for natural human-like deceleration.
    """
    if not PYAUTOGUI_AVAILABLE:
        print(f"[SIMULATION] Smooth move to ({target_x}, {target_y}) over {duration}s")
        return

    # Select easing function
    easing_map = {
        "easeOutQuad": pyautogui.easeOutQuad,
        "easeInOutQuad": pyautogui.easeInOutQuad,
        "easeInQuad": pyautogui.easeInQuad,
        "linear": pyautogui.linear,
    }
    tween_func = easing_map.get(easing, pyautogui.easeOutQuad)

    start_x, start_y = pyautogui.position()
    distance = math.hypot(target_x - start_x, target_y - start_y)
    
    print(f"  [MOVING] Smoothly traveling from ({start_x}, {start_y}) -> ({target_x}, {target_y})")
    print(f"           Distance: {distance:.1f}px | Duration: {duration:.2f}s | Easing: {easing}")

    pyautogui.moveTo(target_x, target_y, duration=duration, tween=tween_func)


def smooth_drag(target_x, target_y, duration=0.8, button="left"):
    """
    Smoothly drag with mouse button held down to (target_x, target_y).
    """
    if not PYAUTOGUI_AVAILABLE:
        print(f"[SIMULATION] Smooth drag to ({target_x}, {target_y})")
        return

    start_x, start_y = pyautogui.position()
    print(f"  [DRAGGING] Dragging with '{button}' held from ({start_x}, {start_y}) -> ({target_x}, {target_y})")
    pyautogui.dragTo(target_x, target_y, duration=duration, button=button)


def hover_and_click(
    x,
    y,
    hover_delay=0.6,
    move_duration=0.8,
    clicks=1,
    button="left",
    label="Target",
    easing="easeOutQuad",
    dry_run=False
):
    """
    Complete action pipeline for a single target:
    1. Smooth move to (x, y)
    2. Tactile hover delay so UI registers mouseover state
    3. Click target
    4. Settle delay
    """
    print(f"\n========================================================")
    print(f"🎯 TARGET ACTION: {label}")
    print(f"   Coordinates: (X={x}, Y={y})")
    print(f"   Hover Delay: {hover_delay}s | Click Count: {clicks} | Button: {button}")
    if dry_run:
        print(f"   [DRY-RUN MODE ACTIVE: Mouse will move but will NOT click]")
    print(f"========================================================")

    # 1. Smooth move
    smooth_move(x, y, duration=move_duration, easing=easing)

    # 2. Tactile hover
    if hover_delay > 0:
        print(f"  [HOVER] Hovering over target for {hover_delay:.2f}s to let UI register state...")
        time.sleep(hover_delay)

    # 3. Click
    if not dry_run:
        print(f"  [CLICK] Dispatched {clicks} '{button}'-click(s) at ({x}, {y})")
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        # Short settle delay
        time.sleep(0.3)
    else:
        print(f"  [DRY-RUN] Click simulated at ({x}, {y})")

    current_pos = pyautogui.position()
    print(f"  [OK] Target '{label}' action completed at position: {current_pos}")
    return True


def capture_debug_screenshot(step_name="step"):
    """Save an evidence screenshot to screenshots directory."""
    if not PYAUTOGUI_AVAILABLE:
        return None

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOTS_DIR / f"{step_name}_{timestamp}.png"
    
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"  [SCREENSHOT] Evidence screenshot saved to: {filepath}")
        return filepath
    except Exception as e:
        # Screen grab gracefully skips in non-display / headless environments
        return None


def run_countdown(seconds=3, message="Automation starting in"):
    """User-friendly countdown so user can switch window if needed."""
    print(f"\n⏳ {message}:")
    for i in range(seconds, 0, -1):
        print(f"   {i}...", flush=True)
        time.sleep(1)
    print("   🚀 GO!\n", flush=True)
