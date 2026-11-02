# -*- coding: utf-8 -*-
"""
Detectors package: Windows Native OCR, UIAutomation, Vision Template Matching,
Chat Navigation Detector, and Multi-Engine Orchestrator.
"""

from auto_commander.detectors.base import BaseDetector
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.detectors.chat_detector import ChatTabDetector
from auto_commander.detectors.orchestrator import MultiEngineDetector, DualModeDetector

__all__ = [
    "BaseDetector",
    "WindowsOcrDetector",
    "WINSDK_OCR_AVAILABLE",
    "UIAutomationDetector",
    "VisionDetector",
    "ChatTabDetector",
    "MultiEngineDetector",
    "DualModeDetector",
]
