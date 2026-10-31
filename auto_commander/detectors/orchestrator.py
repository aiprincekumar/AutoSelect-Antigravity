# -*- coding: utf-8 -*-
"""
Multi-Engine Detection Orchestrator.
Coordinates Windows Native WinRT OCR, UIAutomation, and Vision Template Matching.
"""

from typing import Optional

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

from auto_commander.config import Config
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.models import DetectionResult


class MultiEngineDetector:
    """Coordinates Windows Native OCR, UIAutomation, and Vision Detection."""

    def __init__(self, config: Config):
        self.config = config
        self.ocr_detector = WindowsOcrDetector(config.target_keywords, ocr_enabled=config.ocr_enabled)
        self.uia_detector = UIAutomationDetector(config.window_title_filter, config.target_keywords)
        self.vision_detector = VisionDetector(target_keywords=config.target_keywords)

    def detect(self) -> Optional[DetectionResult]:
        """Detects the (Recommended) option modal on screen."""
        mode = self.config.detection_mode.lower()

        # Strategy 1: Windows Native OCR (Fastest & most robust)
        if mode in ("auto", "ocr"):
            if self.ocr_detector.is_available():
                res = self.ocr_detector.scan()
                if res:
                    return res

        # Strategy 2: UIAutomation Tree Search
        if mode in ("auto", "uia"):
            res = self.uia_detector.scan()
            if res:
                return res

        # Strategy 3: Computer Vision Multi-Scale Template Fallback
        if mode in ("auto", "vision"):
            res = self.vision_detector.scan()
            if res:
                return res

        return None

    def detect_submit_button(self, option_result: Optional[DetectionResult] = None) -> Optional[DetectionResult]:
        """
        Detects the 'Submit / पुष्टि करें' button on the active Antigravity modal.
        Uses UIA -> OCR -> Layout Inference fallback.
        """
        # 1. UIAutomation scan
        if self.config.detection_mode in ("auto", "uia"):
            res = self.uia_detector.find_by_keywords(self.config.submit_keywords)
            if res:
                return res

        # 2. Windows Native OCR scan
        if self.config.detection_mode in ("auto", "ocr"):
            if self.ocr_detector.is_available() and ImageGrab is not None:
                try:
                    screen_img = ImageGrab.grab()
                    min_y = (option_result.y + option_result.height) if option_result else 0
                    res = self.ocr_detector.scan_image(
                        screen_img,
                        offset_x=0,
                        offset_y=0,
                        keywords=self.config.submit_keywords,
                        min_y=min_y,
                    )
                    if res:
                        return res
                except Exception:
                    pass

        # 3. Layout Inference Fallback: Standard Antigravity modal places Submit ~65px below option
        if option_result:
            return DetectionResult(
                x=option_result.x,
                y=option_result.y + option_result.height + 65,
                width=min(option_result.width, 160),
                height=38,
                confidence=0.85,
                source="LayoutInference",
                label="Submit / पुष्टि करें",
            )

        return None


# Backward-compatibility alias
DualModeDetector = MultiEngineDetector
