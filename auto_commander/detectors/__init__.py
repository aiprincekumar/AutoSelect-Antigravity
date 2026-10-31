# -*- coding: utf-8 -*-
"""
Detectors module package for modal and decision element discovery.
"""

from auto_commander.detectors.base import BaseDetector
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.detectors.orchestrator import MultiEngineDetector, DualModeDetector

__all__ = [
    "BaseDetector",
    "WindowsOcrDetector",
    "WINSDK_OCR_AVAILABLE",
    "UIAutomationDetector",
    "VisionDetector",
    "MultiEngineDetector",
    "DualModeDetector",
]
