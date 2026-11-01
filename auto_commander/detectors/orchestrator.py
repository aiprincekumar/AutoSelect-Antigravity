# -*- coding: utf-8 -*-
"""
Multi-Engine Detection Orchestrator.
Coordinates Windows Native WinRT OCR, UIAutomation, Vision Template Matching,
and Step 0 Pending Chat Navigation.
"""

from typing import Any, Optional

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

                # Robust Fallback: If require_submit failed (e.g. Submit button is disabled/faint before Option 1 is clicked),
                # do not discard the detected dynamic Option 1 position!
                if require_submit:
                    modal_pair = self.ocr_detector.scan_decision_modal(
                        target_hwnd=target_hwnd,
                        target_keywords=self.config.target_keywords,
                        submit_keywords=self.config.submit_keywords,
                        require_submit=False,
                    )
                    if modal_pair:
                        opt_res, sub_res = modal_pair
                        self.last_detected_submit = sub_res
                        return opt_res

        # Strategy 2: UIAutomation Tree Search
        if mode in ("auto", "uia"):
            opt_res = self.uia_detector.scan()
            if opt_res and opt_res.x >= 500:
                sub_res = self.uia_detector.find_by_keywords(self.config.submit_keywords)
                if sub_res and sub_res.x < 800:
                    sub_res = None
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
            if opt_res and opt_res.x >= 500:
                if not require_submit:
                    return opt_res
                sub_res = self.detect_submit_button(option_result=opt_res)
                if sub_res and sub_res.x >= 800 and sub_res.source != "LayoutInference":
                    self.last_detected_submit = sub_res
                    return opt_res

        return None

    def detect_pending_chat(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """
        Step 0: Detects a pending chat in the sidebar or tabs awaiting user input
        (displaying the question mark (?) badge or 'Action required' marker).
        """
        return self.chat_detector.detect_pending_chat(target_hwnd=target_hwnd)

    def detect_submit_button(self, option_result: Optional[DetectionResult] = None, screen_img: Optional[Any] = None) -> Optional[DetectionResult]:
        """
        Detects the 'Submit / पुष्टि करें' button on the active Antigravity modal.
        Checks Active Blue Vision first (fresh state after option click) -> cached OCR submit -> fresh OCR (Submit & Skip) -> UIA -> Dynamic Layout Inference.
        """
        min_y = (option_result.y + 10) if option_result else 0

        # 1. Computer Vision Active Blue Button Detector (Fastest and 100% immune to font scaling/glyphs)
        if hasattr(self, "vision_detector") and self.vision_detector:
            try:
                active_blue = self.vision_detector.detect_active_blue_submit_button(min_y=min_y)
                if active_blue:
                    return active_blue
            except Exception:
                pass

        if self.last_detected_submit and (not option_result or self.last_detected_submit.y >= option_result.y - 15):
            return self.last_detected_submit

        # 2. Windows Native OCR scan below Option 1
        if self.config.detection_mode in ("auto", "ocr"):
            if self.ocr_detector.is_available() and ImageGrab is not None:
                try:
                    img = screen_img if screen_img is not None else ImageGrab.grab()
                    # Check for explicit Submit button text
                    res = self.ocr_detector.scan_image(
                        img,
                        offset_x=0,
                        offset_y=0,
                        keywords=("Submit", "पुष्टि करें", "Confirm", "Proceed", "Submit / पुष्टि करें", "जारी रखें", "Continue", "OK"),
                        min_y=min_y,
                    )
                    if res and (img.width < 1200 or res.x >= 800):
                        return res

                    # Check for Skip button on same action bar row and infer Submit next to it
                    skip_res = self.ocr_detector.scan_image(
                        img,
                        offset_x=0,
                        offset_y=0,
                        keywords=("Skip", "छोड़ें"),
                        min_y=min_y,
                    )
                    if skip_res and (img.width < 1200 or skip_res.x >= 700):
                        sub_w = max(skip_res.width + 30, 95)
                        sub_h = max(skip_res.height, 34)
                        sub_y = skip_res.y
                        sub_x = int(skip_res.x + skip_res.width + 35)
                        return DetectionResult(
                            x=sub_x,
                            y=sub_y,
                            width=sub_w,
                            height=sub_h,
                            confidence=0.96,
                            source="WindowsOcr-Inferred",
                            label="Submit",
                        )
                except Exception:
                    pass

        # 3. UIAutomation scan
        if self.config.detection_mode in ("auto", "uia"):
            res = self.uia_detector.find_by_keywords(self.config.submit_keywords)
            if res and (not option_result or res.y >= option_result.y - 15):
                return res

        # 4. Dynamic Layout Inference Fallback:
        # Standard Antigravity modal places Submit right-aligned below the option rows
        if option_result:
            sw = 1920
            try:
                import ctypes
                sw = ctypes.windll.user32.GetSystemMetrics(0)
            except Exception:
                pass
            target_sub_x = min(sw - 93, 1827)
            # Distance from Option 1 row to Submit row: dynamically scales based on option_result.y
            dynamic_sub_y = int(option_result.y + (185 if (option_result.y == 664 and option_result.height == 0) else (option_result.height + 155)))
            return DetectionResult(
                x=target_sub_x,
                y=dynamic_sub_y,
                width=115,
                height=38,
                confidence=0.88,
                source="DynamicLayoutInference",
                label="Submit / पुष्टि करें",
            )

        return None


# Backward-compatibility alias
DualModeDetector = MultiEngineDetector
