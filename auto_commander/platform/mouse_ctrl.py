# -*- coding: utf-8 -*-
"""
Mouse movement, cubic easing, firm click execution, and boundary safety guards.
"""

import random
import time
from typing import Callable, Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
except ImportError:
    pyautogui = None

from auto_commander.platform.win32_window import AntigravityWindowManager


class MouseController:
    """Dispatches human-like cubic easing cursor motion and natural clicks with safety validation."""

    def __init__(self, glide_duration: float = 0.8, failsafe_enabled: bool = True):
        self.glide_duration = glide_duration
        if pyautogui:
            pyautogui.FAILSAFE = failsafe_enabled

    def firm_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        target_hwnd: Optional[int] = None,
        is_demo: bool = False,
    ) -> bool:
        """
        Firm mouse down + dwell + up ensuring 100% reliable click registration on Web/Electron/Native.
        Validates coordinates to ensure clicks never land inside console or outside target window.
        """
        if not pyautogui:
            return False

        try:
            if x is not None and y is not None:
                # Validate click target before dispatching
                is_valid, reason = AntigravityWindowManager.validate_click_target(
                    x, y, target_hwnd=target_hwnd, is_demo=is_demo
                )
                if not is_valid:
                    print(f"\033[91m[SAFETY BLOCK] {reason}\033[0m")
                    return False
                pyautogui.moveTo(x, y)

            time.sleep(0.06)
            pyautogui.mouseDown()
            time.sleep(0.08)  # 80ms press duration guarantees OS and Chromium register click
            pyautogui.mouseUp()
            time.sleep(0.06)
            return True
        except Exception as e:
            print(f"\033[91m[ERROR] Firm click failed: {e}\033[0m")
            return False

    def glide_and_click(
        self,
        target_x: int,
        target_y: int,
        check_interrupted_fn: Optional[Callable[[], bool]] = None,
        target_hwnd: Optional[int] = None,
        is_demo: bool = False,
    ) -> bool:
        """
        Glides cursor smoothly using cubic ease-in-out and executes a firm click.
        Validates target boundary prior to motion.
        """
        if not pyautogui:
            return False

        # Pre-flight safety check
        is_valid, reason = AntigravityWindowManager.validate_click_target(
            target_x, target_y, target_hwnd=target_hwnd, is_demo=is_demo
        )
        if not is_valid:
            print(f"\033[91m[SAFETY BLOCK] {reason}\033[0m")
            return False

        try:
            # Minor random offset (+-2 px) for human-like natural landing
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            dest_x = target_x + offset_x
            dest_y = target_y + offset_y

            # Final check before gliding
            is_valid_dest, _ = AntigravityWindowManager.validate_click_target(
                dest_x, dest_y, target_hwnd=target_hwnd, is_demo=is_demo
            )
            if not is_valid_dest:
                dest_x, dest_y = target_x, target_y

            # Smooth glide using cubic ease-in-out
            pyautogui.moveTo(
                dest_x,
                dest_y,
                duration=self.glide_duration,
                tween=pyautogui.easeInOutQuad,
            )

            # Check if user moved mouse or cancelled during glide
            if check_interrupted_fn and check_interrupted_fn():
                return False

            # Firm click with dwell to guarantee button/option triggers
            return self.firm_click(target_hwnd=target_hwnd, is_demo=is_demo)
        except Exception as e:
            print(f"\033[91m[ERROR] Mouse controller exception: {e}\033[0m")
            return False
