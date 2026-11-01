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

        self.assertEqual(steps["step2_recommended"]["x"], 600)
        self.assertEqual(steps["step2_recommended"]["y"], 664)

        self.assertEqual(steps["step3_submit"]["x"], 1827)
        self.assertEqual(steps["step3_submit"]["y"], 849)


if __name__ == "__main__":
    unittest.main()
