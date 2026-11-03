#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 3: KEYBOARD AUTOMATION (AutoSelect-Commander)
==================================================
Subfolder: Keyboard Automation
Pipeline Step: Step 3 of 3 (Option Selection & Confirmation)
Suite: AutoSelect-Commander
Target: Antigravity 2.0 Harness / IDE / Browser / Terminal Chat Window
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Pipeline Architecture:
  - Step 1: `step1_find_and_focus.py` (Identify Chat & Focus Window)
  - Step 2: `step2_gui_chat_select.py` (DOM/CDP Chat Selection & Input Focus)
  - Step 3: `step3_keyboard_automation.py` (Option Selection & Enter Confirmation)

This script serves as the primary CLI entrypoint for Step 3: Keyboard Automation,
providing robust native ctypes keystroke injection (SendInput / keybd_event)
with dynamic multi-question scaling, window maximization, and safety aborts.
"""

import os
import sys
import logging
from pathlib import Path

# Safe stdout encoding configuration for Windows consoles
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger("Step3KeyboardAutomation")

# Ensure the package and root directories are resolvable whether invoked from root or step subfolder
_pkg_dir = Path(__file__).resolve().parent
_root_dir = _pkg_dir.parent if _pkg_dir.name.startswith(("step_", "step-")) else _pkg_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

import core_engine
import core_engine.constants as _c
import core_engine.win32_api as _wapi
import core_engine.input_injector as _inj
import core_engine.window_manager as _wm
import core_engine.automator as _aut
import core_engine.cli as _cli

# Re-export all modular components
from core_engine import (
    STEP_ID,
    STEP_NUMBER,
    STEP_NAME,
    STEP_DESCRIPTION,
    DISQUALIFIED_BROWSER_PROCS,
    BLACK_LISTED_SHELL_PROCS,
    DEFAULT_TARGET_WINDOW,
    IS_WINDOWS,
    VK_SHIFT,
    VK_CONTROL,
    VK_RETURN,
    VK_TAB,
    VK_L,
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
    VK_MENU,
    SW_HIDE,
    SW_SHOWNORMAL,
    SW_SHOWMINIMIZED,
    SW_MAXIMIZE,
    SW_SHOWNOACTIVATE,
    SW_SHOW,
    SW_MINIMIZE,
    SW_SHOWMINNOACTIVE,
    SW_SHOWNA,
    SW_RESTORE,
    SW_SHOWDEFAULT,
    HWND_TOP,
    HWND_BOTTOM,
    HWND_TOPMOST,
    HWND_NOTOPMOST,
    SWP_NOSIZE,
    SWP_NOMOVE,
    SWP_NOZORDER,
    SWP_NOACTIVATE,
    SWP_SHOWWINDOW,
    ASFW_ANY,
    INPUT_KEYBOARD,
    KEYEVENTF_KEYDOWN,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    KEYEVENTF_EXTENDEDKEY,
    ensure_input_desktop,
    get_process_info_for_hwnd,
    get_active_window_title,
    get_option_vk,
    send_key_combo,
    send_single_key,
    PYAUTOGUI_AVAILABLE,
    get_window_info,
    find_all_candidate_windows,
    find_windows_by_title,
    select_target_window,
    ensure_window_on_screen,
    GrillMeAutomator,
    Step3KeyboardAutomator,
    execute_multi_question,
    parse_arguments,
    print_banner,
    main,
)


class _Step3CompatModule(sys.modules[__name__].__class__):
    """
    Transparent proxy module enabling backward-compatible dynamic monkey-patching
    across both legacy script attributes and underlying modular sub-packages.
    """
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        for mod in (core_engine, _c, _wapi, _inj, _wm, _aut, _cli):
            if hasattr(mod, name):
                setattr(mod, name, value)


sys.modules[__name__].__class__ = _Step3CompatModule

if __name__ == "__main__":
    sys.exit(main())
