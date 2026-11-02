#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input Injector Subsystem
========================
Dispatches low-level keyboard events using Win32 ctypes SendInput (with keybd_event fallback)
or optional PyAutoGUI interoperability.
"""

import sys
import time
import logging
from typing import List

from .constants import (
    IS_WINDOWS,
    INPUT_KEYBOARD,
    KEYEVENTF_KEYDOWN,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    VK_0,
    VK_1,
    VK_2,
    VK_3,
    VK_4,
    VK_5,
    VK_6,
    VK_7,
    VK_8,
    VK_9,
)

logger = logging.getLogger("GrillMeAutomation.InputInjector")

# Optional PyAutoGUI Engine
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None


def get_option_vk(option_char: str) -> int:
    """Map string option ('1', '2', etc.) to Virtual Key code."""
    opt = str(option_char).strip().lower()
    if opt == "1":
        return VK_1
    elif opt == "2":
        return VK_2
    elif opt == "3":
        return VK_3
    elif opt == "4":
        return VK_4
    elif opt == "5":
        return VK_5
    elif opt == "6":
        return VK_6
    elif opt == "7":
        return VK_7
    elif opt == "8":
        return VK_8
    elif opt == "9":
        return VK_9
    elif opt == "0":
        return VK_0
    elif len(opt) == 1 and opt.isalpha():
        return ord(opt.upper())
    return VK_1


if IS_WINDOWS:
    import ctypes
    from .win32_api import user32, INPUT

    def _send_key_event(vk_code: int, key_up: bool = False, use_scancode: bool = True) -> bool:
        """Send a single key press or release event via SendInput."""
        try:
            scan = user32.MapVirtualKeyW(vk_code, 0)
            flags = KEYEVENTF_KEYUP if key_up else KEYEVENTF_KEYDOWN
            if use_scancode and scan:
                flags |= KEYEVENTF_SCANCODE

            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = 0 if (use_scancode and scan) else vk_code
            inp.union.ki.wScan = scan if use_scancode else 0
            inp.union.ki.dwFlags = flags
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None

            res = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            if res != 1:
                # Fallback to keybd_event if SendInput failed
                flags_legacy = KEYEVENTF_KEYUP if key_up else 0
                user32.keybd_event(vk_code, scan, flags_legacy, 0)
            return True
        except Exception as ex:
            logger.warning(f"Fallback keybd_event on error: {ex}")
            try:
                flags_legacy = KEYEVENTF_KEYUP if key_up else 0
                user32.keybd_event(vk_code, 0, flags_legacy, 0)
                return True
            except Exception as ex2:
                logger.error(f"Failed to send key event vk={vk_code}: {ex2}")
                return False

    def send_key_combo(keys: List[int], hold_delay: float = 0.05) -> bool:
        """Press down a sequence of keys, hold briefly, then release in reverse order."""
        for key in keys:
            _send_key_event(key, key_up=False)
            time.sleep(0.01)
        time.sleep(hold_delay)
        for key in reversed(keys):
            _send_key_event(key, key_up=True)
            time.sleep(0.01)
        return True

    def send_single_key(key: int, hold_delay: float = 0.05) -> bool:
        """Press and release a single key."""
        return send_key_combo([key], hold_delay=hold_delay)

else:
    def _send_key_event(vk_code: int, key_up: bool = False, use_scancode: bool = True) -> bool:
        logger.error("Native ctypes SendInput is only supported on Windows.")
        return False

    def send_key_combo(keys: List[int], hold_delay: float = 0.05) -> bool:
        logger.error("Native ctypes SendInput is only supported on Windows.")
        return False

    def send_single_key(key: int, hold_delay: float = 0.05) -> bool:
        logger.error("Native ctypes SendInput is only supported on Windows.")
        return False
