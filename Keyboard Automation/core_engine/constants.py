#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constants and Configuration for Step 3: Keyboard Automation Suite
=================================================================
Pipeline Step: STEP 3 (Option Selection & Confirmation)
Suite: AutoSelect-Commander
Defines Virtual-Key codes, Win32 window positioning and sizing flags,
disqualified browser processes, shell blacklists, and default settings.
"""

import os
import sys
from typing import Optional

# Step Identification & Pipeline Metadata
STEP_ID = "step3"
STEP_NUMBER = 3
STEP_NAME = "Step 3: Keyboard Automation"
STEP_DESCRIPTION = "Step 3: Keyboard Automation - Interactive Option Selection & Submission"

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# Virtual-Key codes (Win32)
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_L = 0x4C
VK_0 = 0x30
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33
VK_4 = 0x34
VK_5 = 0x35
VK_6 = 0x36
VK_7 = 0x37
VK_8 = 0x38
VK_9 = 0x39
VK_MENU = 0x12  # Alt key (used for OS foreground lock release)
VK_ESCAPE = 0x1B  # Escape key (used to dismiss menu bar/dialogs)

# ShowWindow commands (Win32)
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9
SW_SHOWDEFAULT = 10

# Window Pos flags (Win32)
HWND_TOP = 0
HWND_BOTTOM = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

# ASFW_ANY constant for AllowSetForegroundWindow
ASFW_ANY = -1

# SendInput constants (Win32)
INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

# Disqualified Web Browsers - Must NEVER be targeted or focused by default
DISQUALIFIED_BROWSER_PROCS = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
    "iexplore.exe",
    "safari.exe",
    "chromium.exe",
    "waterfox.exe",
    "tor.exe",
}

# Browser Process Substring Markers
DISQUALIFIED_BROWSER_PROC_SUBSTRINGS = (
    "chrome",
    "msedge",
    "firefox",
    "brave",
    "opera",
    "vivaldi",
    "safari",
    "iexplore",
    "chromium",
    "waterfox",
)

# Browser Window Title Markers - Substrings that explicitly identify web browsers
BROWSER_TITLE_MARKERS = (
    "microsoft edge",
    "google chrome",
    "mozilla firefox",
    "brave browser",
    "opera gx",
    "tor browser",
    "waterfox",
    "chromium",
    " - edge",
    " - chrome",
    " - firefox",
    " - brave",
    " - vivaldi",
    " - opera",
    " - chromium",
)

# Browser Window Title Endings
BROWSER_TITLE_SUFFIXES = (
    " edge",
    " chrome",
    " firefox",
    " brave",
    " vivaldi",
    " opera",
    " chromium",
)


def is_browser_window(pname: str = "", pexe: str = "", title: str = "") -> bool:
    """
    Determines whether a window is a web browser by checking both process metadata
    and window title against known browser signatures.
    Returns True if either process or title indicates a browser, even if pname is empty.
    """
    p_lower = pname.lower().strip() if pname else ""
    pexe_base = os.path.basename(pexe).lower().strip() if pexe else ""
    t_lower = title.lower().strip() if title else ""

    # 1. Process name / executable check
    if p_lower in DISQUALIFIED_BROWSER_PROCS or pexe_base in DISQUALIFIED_BROWSER_PROCS:
        return True
    if any(b in p_lower for b in DISQUALIFIED_BROWSER_PROC_SUBSTRINGS):
        return True
    if any(b in pexe_base for b in DISQUALIFIED_BROWSER_PROC_SUBSTRINGS):
        return True

    # 2. Standalone exact title match
    if t_lower in ("edge", "chrome", "firefox", "brave", "opera", "vivaldi", "chromium", "microsoft edge", "google chrome"):
        return True

    # 3. Window title markers check
    if any(bm in t_lower for bm in BROWSER_TITLE_MARKERS):
        return True
    if any(t_lower.endswith(suffix) for suffix in BROWSER_TITLE_SUFFIXES):
        return True

    return False


def is_explicit_browser_requested(target_keyword: Optional[str]) -> bool:
    """Checks whether the user explicitly requested a web browser by name in target keywords."""
    if not target_keyword:
        return False
    raw = target_keyword.replace("|", ",").split(",")
    browser_names = ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore", "safari", "chromium")
    for kw in raw:
        kw_clean = kw.strip().lower()
        if any(b in kw_clean for b in browser_names):
            return True
    return False

# Blacklisted Shells & Script Interpreters - Must NEVER be targeted
BLACK_LISTED_SHELL_PROCS = {
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
    "conhost.exe",
    "wt.exe",
    "windowsterminal.exe",
    "python.exe",
    "pythonw.exe",
    "explorer.exe",
}

# Default target keyword set for Antigravity 2.0 Harness
DEFAULT_TARGET_WINDOW = "Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander"
