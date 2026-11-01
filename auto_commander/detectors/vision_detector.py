# -*- coding: utf-8 -*-
"""
Computer Vision / Multi-Scale Multi-Theme Template Matching Engine.
Uses OpenCV normalized cross-correlation across themes (Dark, Dracula, VS Code, Light).
"""

import os
from typing import Any, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageGrab
except ImportError:
    Image = ImageDraw = ImageFont = ImageGrab = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

from auto_commander.detectors.base import BaseDetector
from auto_commander.models import DetectionResult


class VisionDetector(BaseDetector):
    """Uses OpenCV multi-scale multi-template matching to detect '(Recommended)' on screen."""

    def __init__(self, templates_dir: str = "assets/templates", target_keywords: Tuple[str, ...] = ()):
        self.templates_dir = templates_dir
        self.templates: List[Tuple[str, Any]] = []
        self._ensure_and_load_templates()

    def is_available(self) -> bool:
        """Returns True if OpenCV and PIL ImageGrab are ready and templates are loaded."""
        return cv2 is not None and ImageGrab is not None and len(self.templates) > 0

    def _ensure_and_load_templates(self):
        """Ensures template directory exists with multiple theme templates and loads them."""
        os.makedirs(self.templates_dir, exist_ok=True)

        tpl_variants = [
            ("recommended_dark_16.png", (30, 30, 46), (166, 227, 161), 16),
            ("recommended_dark_14.png", (24, 24, 37), (205, 214, 244), 14),
            ("recommended_vscode_14.png", (37, 37, 38), (255, 255, 255), 14),
            ("recommended_light_16.png", (245, 245, 250), (20, 20, 30), 16),
        ]

        if Image and ImageDraw:
            for fname, bg, fg, sz in tpl_variants:
                path = os.path.join(self.templates_dir, fname)
                if not os.path.exists(path):
                    self._generate_template(path, bg, fg, sz)

        if cv2 is not None:
            for file in os.listdir(self.templates_dir):
                if file.lower().endswith(".png"):
                    path = os.path.join(self.templates_dir, file)
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        self.templates.append((file, img))

    def _generate_template(
        self,
        path: str,
        bg_color: Tuple[int, int, int],
        fg_color: Tuple[int, int, int],
        font_size: int,
    ):
        """Generates a clean synthetic template image."""
        w = int(font_size * 9.5)
        h = int(font_size * 2.2)
        img = Image.new("RGB", (w, h), color=bg_color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        draw.text((6, 4), "(Recommended)", fill=fg_color, font=font)
        img.save(path)

    def scan(self) -> Optional[DetectionResult]:
        if not self.is_available():
            return None

        try:
            screenshot = ImageGrab.grab()
            screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

            best_match = None
            highest_score = 0.72  # Matching threshold

            scales = [0.85, 1.0, 1.15]
            for tpl_name, tpl_gray in self.templates:
                th, tw = tpl_gray.shape[:2]
                for scale in scales:
                    new_w = int(tw * scale)
                    new_h = int(th * scale)
                    if new_w >= screen_gray.shape[1] or new_h >= screen_gray.shape[0]:
                        continue

                    resized_tpl = cv2.resize(tpl_gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    res = cv2.matchTemplate(screen_gray, resized_tpl, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    if max_val > highest_score:
                        # Reject matches in the left project explorer / sidebar
                        if screen_gray.shape[1] >= 1200 and max_loc[0] < 500:
                            continue
                        highest_score = max_val
                        best_match = DetectionResult(
                            x=max_loc[0],
                            y=max_loc[1],
                            width=new_w,
                            height=new_h,
                            confidence=float(max_val),
                            source=f"Vision ({tpl_name})",
                            label="(Recommended)",
                        )

            return best_match
        except Exception:
            return None

    def detect_active_blue_submit_button(self, img_bgr: Optional[Any] = None, min_y: int = 0) -> Optional[DetectionResult]:
        """
        Detects the active bright-blue Submit button in Antigravity.
        Active blue color is ~#0371BB (BGR around [187, 113, 3]).
        """
        if cv2 is None or np is None:
            return None
        try:
            if img_bgr is None:
                if ImageGrab is None:
                    return None
                screenshot = ImageGrab.grab()
                img_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            h, w = img_bgr.shape[:2]
            y_start = max(0, min_y)
            crop = img_bgr[y_start:, :]
            if crop.shape[0] < 20 or crop.shape[1] < 50:
                return None

            lower_blue = np.array([130, 70, 0], dtype=np.uint8)
            upper_blue = np.array([245, 160, 60], dtype=np.uint8)
            mask = cv2.inRange(crop, lower_blue, upper_blue)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            candidates = []
            for c in contours:
                bx, by, bw, bh = cv2.boundingRect(c)
                if 50 <= bw <= 200 and 20 <= bh <= 60:
                    # Action bar filter: Submit button must be in the right-side action bar
                    if w >= 1200 and bx < 800:
                        continue
                    candidates.append((bx, by + y_start, bw, bh))

            if candidates:
                candidates.sort(key=lambda b: (b[0] + b[2]), reverse=True)
                bx, by, bw, bh = candidates[0]
                return DetectionResult(
                    x=bx,
                    y=by,
                    width=bw,
                    height=bh,
                    confidence=0.99,
                    source="Vision-ActiveBlue",
                    label="Submit",
                )
        except Exception:
            return None
        return None
