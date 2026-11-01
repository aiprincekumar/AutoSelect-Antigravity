# -*- coding: utf-8 -*-
"""
Multi-Engine Detection Orchestrator.
Coordinates Windows Native WinRT OCR, UIAutomation, Vision Template Matching,
and Step 0 Pending Chat Navigation.
"""

from typing import Optional

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

from auto_commander.config import Config
from auto_commander.detectors.chat_detector import ChatTabDetector
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.models import DetectionResult


class MultiEngineDetector:
    """Coordinates Windows Native OCR, UIAutomation, Vision Detection, and Chat Navigation."""

    def __init__(self, config: Config):
        self.config = config
        self.ocr_detector = WindowsOcrDetector(config.target_keywords, ocr_enabled=config.ocr_enabled)
        self.uia_detector = UIAutomationDetector(config.window_title_filter, config.target_keywords)
        self.vision_detector = VisionDetector(target_keywords=config.target_keywords)
        self.chat_detector = ChatTabDetector(config)
        self.last_detected_submit: Optional[DetectionResult] = None

    def detect(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """
        Detects an interactive decision modal on screen.
        Requires presence of an interactive Submit/Confirm button (when require_submit_button is True)
        to prevent false positives on plain static chat text.
        """
        mode = self.config.detection_mode.lower()
        self.last_detected_submit = None
        require_submit = getattr(self.config, "require_submit_button", True)

        # Strategy 1: Windows Native OCR (Fastest, most robust & font-invariant)
        if mode in ("auto", "ocr"):
            if self.ocr_detector.is_available():
                modal_pair = self.ocr_detector.scan_decision_modal(
                    target_hwnd=target_hwnd,
                    target_keywords=self.config.target_keywords,
                    submit_keywords=self.config.submit_keywords,
                    require_submit=require_submit,
                )
                if modal_pair:
                    opt_res, sub_res = modal_pair
                    self.last_detected_submit = sub_res
                    return opt_res

        # Strategy 2: UIAutomation Tree Search
        if mode in ("auto", "uia"):
            opt_res = self.uia_detector.scan()
            if opt_res:
                sub_res = self.uia_detector.find_by_keywords(self.config.submit_keywords)
                if require_submit:
                    if sub_res and sub_res.y >= opt_res.y - 15:
                        self.last_detected_submit = sub_res
                        return opt_res
                else:
                    self.last_detected_submit = sub_res
                    return opt_res

        # Strategy 3: Computer Vision Multi-Scale Template Fallback
        if mode in ("auto", "vision"):
            opt_res = self.vision_detector.scan()
            if opt_res:
                if not require_submit:
                    return opt_res
                sub_res = self.detect_submit_button(option_result=opt_res)
                if sub_res and sub_res.source != "LayoutInference":
                    self.last_detected_submit = sub_res
                    return opt_res

        return None

    def detect_pending_chat(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """
        Step 0: Detects a pending chat in the sidebar or tabs awaiting user input
        (displaying the question mark (?) badge or 'Action required' marker).
        """
        return self.chat_detector.detect_pending_chat(target_hwnd=target_hwnd)

    def detect_submit_button(self, option_result: Optional[DetectionResult] = None) -> Optional[DetectionResult]:
        """
        Detects the 'Submit / पुष्टि करें' button on the active Antigravity modal.
        Uses cached detection from detect() -> UIA -> OCR -> Layout Inference fallback.
        """
        if self.last_detected_submit:
            return self.last_detected_submit

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
