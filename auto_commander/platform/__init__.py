# -*- coding: utf-8 -*-
"""
Platform integration module (Win32 window tracking, process inspection, mouse control).
"""

from auto_commander.platform.win32_window import AntigravityWindowManager
from auto_commander.platform.mouse_ctrl import MouseController

__all__ = ["AntigravityWindowManager", "MouseController"]
