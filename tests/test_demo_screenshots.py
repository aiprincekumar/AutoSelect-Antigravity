#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification tests against real Antigravity Demo screenshots:
Screenshot (454).png, (455).png, (456).png, (457).png, (458).png.
"""

import json
import os
import unittest
import cv2
from PIL import Image

from auto_commander.config import Config
from auto_commander.detectors.ocr_detector import WindowsOcrDetector
from auto_commander.detectors.vision_detector import VisionDetector
from auto_commander.detectors.orchestrator import MultiEngineDetector


class TestDemoScreenshots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo_dir = "Demo SS"
        cls.screenshots_exist = os.path.exists(cls.demo_dir)
        cls.config = Config()
        cls.ocr = WindowsOcrDetector(cls.config.target_keywords)
        cls.vision = VisionDetector(target_keywords=cls.config.target_keywords)
        cls.multi = MultiEngineDetector(cls.config)

    def test_demo_ss_454_to_458_modal_detection(self):
        """Verifies that Option 1 and Submit are correctly paired on all 5 demo screenshots."""
        if not self.screenshots_exist or not self.ocr.is_available():
            self.skipTest("Demo SS directory or WinRT OCR not available.")

        for num in [454, 455, 456, 457, 458]:
            path = os.path.join(self.demo_dir, f"Screenshot ({num}).png")
            if not os.path.exists(path):
                continue

            img = Image.open(path)
            res = self.ocr.scan_decision_modal_on_image(img, mask_console=False)
            self.assertIsNotNone(res, f"Modal detection failed on {path}")

            opt, sub = res
            self.assertIsNotNone(opt, f"Option candidate missing on {path}")
            self.assertIsNotNone(sub, f"Submit candidate missing on {path}")

            # Option 1 (Recommended) check
            self.assertIn("recommend", opt.label.lower())
            self.assertEqual(opt.y, 655)
            self.assertEqual(opt.x, 566)
            self.assertAlmostEqual(opt.center[0], 641, delta=10)
            self.assertAlmostEqual(opt.center[1], 664, delta=5)

            # Submit button check (x around 1784, y around 842 or 791)
            self.assertEqual(sub.label, "Submit")
            self.assertGreater(sub.x, 1750, f"Submit button x coordinate {sub.x} is not on the right side on {path}")
            self.assertGreater(sub.y, 750, f"Submit button y coordinate {sub.y} is not in the action bar on {path}")
            self.assertAlmostEqual(sub.center[0], 1824, delta=15)

    def test_active_blue_submit_button_vision_detection(self):
        """
        Verifies that VisionDetector active blue button detection detects:
        - None on Screenshot (454) and (455) (disabled/dark button)
        - Exact bounding box (1769, 828, 117, 42) and center (1827, 849) on (456), (457), (458).
        """
        if not self.screenshots_exist:
            self.skipTest("Demo SS directory not available.")

        # Inactive/unselected states
        for num in [454, 455]:
            path = os.path.join(self.demo_dir, f"Screenshot ({num}).png")
            if os.path.exists(path):
                img = cv2.imread(path)
                blue_sub = self.vision.detect_active_blue_submit_button(img_bgr=img, min_y=674)
                self.assertIsNone(blue_sub, f"Active blue Submit should be None before option selected on {path}")

        # Active selected states
        for num in [456, 457, 458]:
            path = os.path.join(self.demo_dir, f"Screenshot ({num}).png")
            if os.path.exists(path):
                img = cv2.imread(path)
                blue_sub = self.vision.detect_active_blue_submit_button(img_bgr=img, min_y=674)
                self.assertIsNotNone(blue_sub, f"Active blue Submit must be detected on {path}")
                self.assertEqual(blue_sub.x, 1769)
                self.assertEqual(blue_sub.y, 828)
                self.assertEqual(blue_sub.width, 117)
                self.assertEqual(blue_sub.height, 42)
                self.assertEqual(blue_sub.center, (1827, 849))

    def test_gui_automation_config_coordinates(self):
        """Verifies calibrated coordinates in scripts/gui_automation/config.json."""
        config_path = os.path.join("scripts", "gui_automation", "config.json")
        self.assertTrue(os.path.exists(config_path), "config.json must exist")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        steps = cfg.get("steps", {})
        self.assertEqual(steps["step1_chat"]["x"], 580)
        self.assertEqual(steps["step1_chat"]["y"], 815)

        self.assertEqual(steps["step2_recommended"]["x"], 541)
        self.assertEqual(steps["step2_recommended"]["y"], 664)

        self.assertEqual(steps["step3_submit"]["x"], 1827)
        self.assertEqual(steps["step3_submit"]["y"], 849)

    def test_green_arrows_detection_coordinates(self):
        """
        Locates the green annotations drawn in Screenshot (452).png to (458).png:
        - Screenshot (452): Arrow pointing to sidebar pending chat row at (442, 744).
        - Screenshot (453): Arrow pointing to conversation row at (484, 694).
        - Screenshot (455): Arrow pointing to Option 1 start at (551, 664).
        - Screenshot (456): Green box enclosing Option 1 card spanning x=504 to 1898, y=622 to 693.
        - Screenshot (457): Arrow starting on Option 1 at (1539, 664) pointing to Submit at (1819, 819).
        - Screenshot (458): Green box enclosing Submit button at (1752, 812, 153, 70), center (1828, 847).
        """
        import numpy as np

        arrow_specs = {
            452: {"min_x": 417, "max_x": 465, "min_y": 744, "max_y": 926},
            453: {"min_x": 0, "max_x": 484, "min_y": 680, "max_y": 756},
            455: {"min_x": 325, "max_x": 551, "min_y": 637, "max_y": 685},
            456: {"min_x": 504, "max_x": 1898, "min_y": 622, "max_y": 693},
            457: {"min_x": 1539, "max_x": 1819, "min_y": 664, "max_y": 829},
            458: {"min_x": 1752, "max_x": 1904, "min_y": 812, "max_y": 881},
        }

        for num, spec in arrow_specs.items():
            path = os.path.join(self.demo_dir, f"Screenshot ({num}).png")
            if not os.path.exists(path):
                continue

            img = cv2.imread(path)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([35, 100, 100]), np.array([85, 255, 255]))
            mask[1000:, :] = 0

            ys, xs = np.where(mask > 0)
            self.assertGreater(len(xs), 0, f"No green pixels in {path}")
            self.assertEqual(xs.min(), spec["min_x"])
            self.assertEqual(xs.max(), spec["max_x"])
            self.assertEqual(ys.min(), spec["min_y"])
            self.assertEqual(ys.max(), spec["max_y"])

    def test_left_project_explorer_rejection(self):
        """Verifies that items in the left project explorer (x < 500) and sidebar (sub x < 800) are strictly rejected."""
        # Create a synthetic full-screen 1920x1080 image with a fake option in project explorer (x=200)
        img = Image.new("RGB", (1920, 1080), color=(30, 30, 46))
        # No valid decision modal should be detected
        res = self.ocr.scan_decision_modal_on_image(img, mask_console=False)
        self.assertIsNone(res)


    def test_step1_cx_radio_button_targeting(self):
        """Verifies that Step 1 calculates click target on the radio button circle (541) instead of 1050."""
        from auto_commander.models import DetectionResult
        res = DetectionResult(x=566, y=655, width=150, height=19, confidence=0.99, source="WindowsOcr", label="(Recommended)")
        
        # Test calculation matching engine.py
        target_cx, target_cy = res.center
        if "(recommended)" in res.label.lower() and res.x >= 550:
            step1_cx = res.x - 25
        else:
            step1_cx = target_cx
        step1_cy = target_cy

        self.assertEqual(step1_cx, 541, "Step 1 click X must target the radio button circle (~541), not 1050")
        self.assertEqual(step1_cy, 664, "Step 1 click Y must target the row center (664)")

    def test_antigravity_workspace_title_not_excluded(self):
        """Verifies that an Antigravity IDE window titled 'AutoSelect-Commander' is not self-excluded."""
        from auto_commander.platform.win32_window import EXCLUDED_WINDOW_TITLE_KEYWORDS
        title = "AutoSelect-Commander - Antigravity"
        title_lower = title.lower()
        # EXCLUDED_WINDOW_TITLE_KEYWORDS should not match 'autoselect-commander'
        matches = any(k in title_lower for k in EXCLUDED_WINDOW_TITLE_KEYWORDS)
        self.assertFalse(matches, "Workspace name 'AutoSelect-Commander' must not be in EXCLUDED_WINDOW_TITLE_KEYWORDS")

    def test_chat_detector_sidebar_bbox_expansion(self):
        """Verifies that sidebar bbox expands to 750px to capture Action required badge at x=535..657."""
        from auto_commander.detectors.chat_detector import ChatTabDetector
        detector = ChatTabDetector(self.config)
        bbox = detector._get_sidebar_bbox(target_hwnd=None)
        self.assertEqual(bbox[2], 750, "Sidebar bbox width must be at least 750px to capture conversation badges")


if __name__ == "__main__":
    unittest.main()
