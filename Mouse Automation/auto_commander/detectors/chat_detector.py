# -*- coding: utf-8 -*-
"""
Chat Tab & Sidebar Navigation Detector (Step 0).
Scans for conversation items displaying the question mark badge (?) or
'Action required' indicator indicating an unanswered prompt awaiting user decision.
"""

import os
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = ImageGrab = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

from auto_commander.config import Config
from auto_commander.detectors.base import BaseDetector
from auto_commander.detectors.ocr_detector import WindowsOcrDetector
from auto_commander.detectors.uia_detector import UIAutomationDetector
from auto_commander.models import DetectionResult
from auto_commander.platform.win32_window import AntigravityWindowManager, user32


class ChatTabDetector(BaseDetector):
    """
    Detects pending conversations awaiting decision in the Antigravity sidebar or tabs.
    Recognizes the distinct circular question mark (?) badge, 'Action required' markers,
    and returns coordinates for autonomous chat switching.
    """

    def __init__(
        self,
        config: Config,
        template_path: str = "assets/badge_question_template.png",
    ):
        if not os.path.exists(template_path):
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fallback = os.path.join(module_dir, template_path)
            if os.path.exists(fallback):
                template_path = fallback
        self.config = config
        self.template_path = template_path
        self.templates: List[Tuple[str, "np.ndarray"]] = []
        self.ocr_detector = WindowsOcrDetector(
            target_keywords=("?", "(?)", "Action required"),
            ocr_enabled=config.ocr_enabled,
        )
        self.uia_detector = UIAutomationDetector(
            title_filter=config.window_title_filter,
            target_keywords=("Action required", "(?)", "?"),
        )
        self._load_templates()

    def _load_templates(self):
        """Loads question mark badge template from disk or assets."""
        if cv2 is None:
            return

        # Load primary template if present
        if os.path.exists(self.template_path):
            tpl = cv2.imread(self.template_path, cv2.IMREAD_GRAYSCALE)
            if tpl is not None:
                self.templates.append(("badge_question_default", tpl))

    def is_available(self) -> bool:
        """Returns True if at least one detection engine is operational."""
        return (cv2 is not None and len(self.templates) > 0) or self.ocr_detector.is_available() or self.uia_detector.is_available()

    def scan(self) -> Optional[DetectionResult]:
        """Scans for pending chat tab or sidebar item (implements BaseDetector)."""
        return self.detect_pending_chat()

    def detect_pending_chat(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """
        Scans the sidebar and tab regions of Antigravity for a pending conversation item
        with the question mark (?) indicator.
        Returns DetectionResult on the clickable conversation row.
        """
        # Strategy 1: Template Matching on Sidebar Crop (Fastest & Pixel-Exact: ~10ms)
        if cv2 is not None and len(self.templates) > 0 and ImageGrab is not None:
            match = self._scan_sidebar_template(target_hwnd)
            if match:
                return match

        # Strategy 2: Windows WinRT OCR Scan on Sidebar
        if self.ocr_detector.is_available() and ImageGrab is not None:
            match = self._scan_sidebar_ocr(target_hwnd)
            if match:
                return match

        # Strategy 3: UIAutomation Tree Search
        if self.uia_detector.is_available():
            match = self._scan_uia()
            if match:
                return match

        return None

    def _get_sidebar_bbox(self, target_hwnd: Optional[int] = None) -> Optional[Tuple[int, int, int, int]]:
        """Calculates screen bounding box for the Antigravity left sidebar and tab header, strictly clamped to monitor bounds."""
        sw = 1920
        sh = 1080
        if user32:
            try:
                sw = user32.GetSystemMetrics(0)
                sh = user32.GetSystemMetrics(1)
            except Exception:
                pass

        if target_hwnd:
            rect = AntigravityWindowManager.get_window_rect(target_hwnd)
            if rect and rect.width > 100 and rect.height > 80:
                # Sidebar and conversation drawer/tabs span leftmost ~750px of the window
                x1 = max(0, min(rect.left, sw - 1))
                y1 = max(0, min(rect.top, sh - 1))
                x2 = max(x1 + 10, min(rect.left + 750, rect.right, sw))
                y2 = max(y1 + 10, min(rect.bottom, sh))
                if x2 > x1 and y2 > y1:
                    return (x1, y1, x2, y2)

        # Fallback to general left screen strip (0 to min(750, sw))
        return (0, 0, min(750, sw), sh)

    def _scan_sidebar_template(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """Runs multi-scale normalized cross-correlation for the (?) badge in the sidebar region."""
        try:
            bbox = self._get_sidebar_bbox(target_hwnd)
            if not bbox:
                return None

            screenshot = ImageGrab.grab(bbox=bbox)
            crop_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

            highest_score = 0.82  # Robust threshold for the distinct circular ? badge
            best_match: Optional[DetectionResult] = None
            scales = [0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5]

            for tpl_name, tpl_gray in self.templates:
                th, tw = tpl_gray.shape[:2]
                for scale in scales:
                    nw = int(tw * scale)
                    nh = int(th * scale)
                    if nw >= crop_gray.shape[1] or nh >= crop_gray.shape[0]:
                        continue

                    resized_tpl = cv2.resize(tpl_gray, (nw, nh), interpolation=cv2.INTER_AREA)
                    res = cv2.matchTemplate(crop_gray, resized_tpl, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    if max_val > highest_score:
                        highest_score = max_val
                        abs_x = bbox[0] + max_loc[0]
                        abs_y = bbox[1] + max_loc[1]
                        badge_cx = abs_x + nw // 2
                        badge_cy = abs_y + nh // 2

                        # Clickable target is the conversation row containing this badge.
                        # In the sidebar, conversation row spans leftwards from the badge.
                        row_w = 160
                        row_h = max(nh, 28)
                        row_x = max(bbox[0] + 30, badge_cx - 100)
                        row_y = badge_cy - row_h // 2

                        best_match = DetectionResult(
                            x=row_x,
                            y=row_y,
                            width=row_w,
                            height=row_h,
                            confidence=float(max_val),
                            source=f"VisionChatBadge ({tpl_name})",
                            label="Pending Chat (?) Action Required",
                        )

            return best_match
        except Exception:
            return None

    def _scan_sidebar_ocr(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """Scans the sidebar region using OCR for question mark or 'Action required' markers."""
        try:
            bbox = self._get_sidebar_bbox(target_hwnd)
            if not bbox:
                return None

            sidebar_img = ImageGrab.grab(bbox=bbox)

            # Look for lines with question mark
            match = self.ocr_detector.scan_image(
                sidebar_img,
                offset_x=bbox[0],
                offset_y=bbox[1],
                keywords=("?", "(?)", "Action required"),
                mask_console=False,
            )
            if match:
                # Target the entire conversation row dynamically centered on the matched badge / text
                row_w = 160
                row_h = max(match.height, 28)
                row_x = max(bbox[0] + 30, match.center[0] - 100)
                row_y = match.center[1] - row_h // 2
                return DetectionResult(
                    x=row_x,
                    y=row_y,
                    width=row_w,
                    height=row_h,
                    confidence=match.confidence,
                    source="OcrChatBadge",
                    label="Pending Chat (?) Action Required",
                )
        except Exception:
            pass
        return None

    def _scan_uia(self) -> Optional[DetectionResult]:
        """Searches UIA accessibility tree for conversation items indicating action required."""
        try:
            return self.uia_detector.find_by_keywords(("Action required", "(?)"))
        except Exception:
            return None
