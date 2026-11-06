#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legacy Compatibility Module: keyboard_automation -> core_engine
================================================================
Workspace: Keyboard Automation
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 02 (Clean Architecture) & Department 06 (Backend Engineering)

Architecture Notice:
The internal Win32 automation and input injection package previously named
`keyboard_automation/` has been renamed to `core_engine/` to avoid naming confusion
with the parent repository `Keyboard Automation/` and to match industry-standard
Clean Architecture boundaries.

This file serves as a transparent backward-compatibility proxy so any existing scripts,
tools, or tests importing `keyboard_automation` or its submodules continue to work
seamlessly without modification.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root directory is in sys.path
_this_dir = Path(__file__).resolve().parent
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

import core_engine
from core_engine import *

# Explicitly import submodules for transparent namespace binding
import core_engine.constants as constants
import core_engine.win32_api as win32_api
import core_engine.input_injector as input_injector
import core_engine.window_manager as window_manager
import core_engine.automator as automator
import core_engine.cli as cli
import core_engine.cdp_helper as cdp_helper

# Alias submodules into sys.modules to satisfy submodule import statements
sys.modules["keyboard_automation.constants"] = constants
sys.modules["keyboard_automation.win32_api"] = win32_api
sys.modules["keyboard_automation.input_injector"] = input_injector
sys.modules["keyboard_automation.window_manager"] = window_manager
sys.modules["keyboard_automation.automator"] = automator
sys.modules["keyboard_automation.cli"] = cli
sys.modules["keyboard_automation.cdp_helper"] = cdp_helper
