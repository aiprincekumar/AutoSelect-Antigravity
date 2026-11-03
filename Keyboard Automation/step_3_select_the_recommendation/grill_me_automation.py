#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 3: KEYBOARD AUTOMATION (AutoSelect-Commander) - Backward Compatibility Wrapper
==================================================================================
Subfolder: Keyboard Automation
Pipeline Step: Step 3 of 3 (Option Selection & Confirmation)
Suite: AutoSelect-Commander
Target: Antigravity 2.0 Harness / IDE / Browser / Terminal Chat Window
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

NOTE ON STEP IDENTIFICATION:
This script (`grill_me_automation.py`) is the legacy/backward-compatible entrypoint
for STEP 3: KEYBOARD AUTOMATION. It delegates directly to:
    `step3_keyboard_automation.py`
All imports, flags, batch scripts, and tests continue to work with 100% fidelity.
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

# Ensure the package and root directories are resolvable whether invoked from root or step subfolder
_pkg_dir = Path(__file__).resolve().parent
_root_dir = _pkg_dir.parent if _pkg_dir.name.startswith(("step_", "step-")) else _pkg_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

# Import everything from the primary step3 module
import step3_keyboard_automation as _step3
from step3_keyboard_automation import (
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

logger = logging.getLogger("Step3KeyboardAutomation.GrillMeCompat")


class _GrillMeCompatModule(sys.modules[__name__].__class__):
    """
    Transparent proxy module enabling backward-compatible dynamic monkey-patching
    across legacy script attributes, step3 module, and underlying sub-packages.
    """
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        setattr(_step3, name, value)


sys.modules[__name__].__class__ = _GrillMeCompatModule

if __name__ == "__main__":
    sys.exit(main())
