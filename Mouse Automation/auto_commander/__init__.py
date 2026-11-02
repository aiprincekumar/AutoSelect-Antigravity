# -*- coding: utf-8 -*-
r"""
AutoSelect-Commander: Visual Mouse Automation & Auto-Selector for Antigravity
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Repository: C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
Version: 1.4.0
"""

from auto_commander.config import Config
from auto_commander.models import Point, Rect, DetectionResult
from auto_commander.platform.win32_window import AntigravityWindowManager
from auto_commander.platform.mouse_ctrl import MouseController
from auto_commander.detectors.base import BaseDetector
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.detectors.orchestrator import MultiEngineDetector, DualModeDetector
from auto_commander.gui.hud import FloatingHUD
from auto_commander.gui.dashboard import TerminalDashboard
from auto_commander.core.engine import AutoCommanderEngine
from auto_commander.core.diagnostics import run_diagnostics
from auto_commander.cli import main

__version__ = "1.4.0"
__author__ = "Atul Verma (aiprincekumar)"

__all__ = [
    "Config",
    "Point",
    "Rect",
    "DetectionResult",
    "AntigravityWindowManager",
    "MouseController",
    "BaseDetector",
    "WindowsOcrDetector",
    "WINSDK_OCR_AVAILABLE",
    "UIAutomationDetector",
    "VisionDetector",
    "MultiEngineDetector",
    "DualModeDetector",
    "FloatingHUD",
    "TerminalDashboard",
    "AutoCommanderEngine",
    "run_diagnostics",
    "main",
]
