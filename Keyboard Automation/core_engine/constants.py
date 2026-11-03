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

import sys

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
    "vivaldi.exe",
    "iexplore.exe",
    "safari.exe",
}

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
