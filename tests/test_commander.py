#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for AutoSelect-Commander.
"""

import math
import os
import sys
import unittest
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auto_commander import (
    Config,
    DetectionResult,
    WindowsOcrDetector,
    UIAutomationDetector,
    VisionDetector,
    MultiEngineDetector,
    DualModeDetector,
    FloatingHUD,
    MouseController,
    WINSDK_OCR_AVAILABLE,
)


class TestAutoCommander(unittest.TestCase):
    def test_config_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.countdown_seconds, 30)
        self.assertEqual(cfg.check_interval_ms, 1000)
        self.assertEqual(cfg.mouse_interruption_threshold_px, 15)
        self.assertEqual(cfg.smooth_glide_duration_s, 0.8)
        self.assertTrue(cfg.failsafe_enabled)
        self.assertTrue(cfg.floating_hud_enabled)
        self.assertTrue(cfg.ocr_enabled)
        self.assertEqual(cfg.window_title_filter, "")
        self.assertIn("(Recommended)", cfg.target_keywords)

    def test_config_load_from_json(self):
        cfg = Config.load("config.json")
        self.assertTrue(cfg.floating_hud_enabled)
        self.assertTrue(cfg.ocr_enabled)
        self.assertIn("Recommended", cfg.target_keywords)

    def test_detection_result_center(self):
        result = DetectionResult(
            x=100,
            y=200,
            width=80,
            height=40,
            confidence=0.95,
            source="Test",
            label="(Recommended)",
        )
        self.assertEqual(result.center, (140, 220))

    def test_failsafe_euclidean_distance(self):
        start_x, start_y = 500, 500
        threshold = 15

        # Minor drift (within threshold) -> No fail-safe trigger
        drift_x, drift_y = 508, 506
        dist = math.hypot(drift_x - start_x, drift_y - start_y)
        self.assertLess(dist, threshold)

        # Human intentional movement -> Triggers fail-safe (> 15px)
        human_x, human_y = 515, 515
        dist_human = math.hypot(human_x - start_x, human_y - start_y)
        self.assertGreater(dist_human, threshold)

    def test_ocr_detector_initialization(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        self.assertEqual(detector.is_available(), WINSDK_OCR_AVAILABLE)

    def test_ocr_detector_scan_image(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        test_img = Image.new("RGB", (500, 100), color=(30, 30, 46))
        draw = ImageDraw.Draw(test_img)
        draw.text((40, 30), "Option 1: (Recommended) GitHub Commit Push", fill=(166, 227, 161))

        match = detector.scan_image(test_img, offset_x=100, offset_y=200)
        self.assertIsNotNone(match)
        self.assertIn("WindowsOcr", match.source)
        self.assertGreater(match.x, 100)
        self.assertGreater(match.y, 200)

    def test_vision_detector_templates(self):
        detector = VisionDetector(templates_dir="assets/templates")
        self.assertTrue(os.path.exists("assets/templates"))
        self.assertGreaterEqual(len(detector.templates), 1)

    def test_multi_engine_detector_initialization(self):
        cfg = Config()
        multi = MultiEngineDetector(cfg)
        self.assertIsNotNone(multi.ocr_detector)
        self.assertIsNotNone(multi.uia_detector)
        self.assertIsNotNone(multi.vision_detector)

    def test_dual_mode_detector_alias(self):
        self.assertIs(DualModeDetector, MultiEngineDetector)

    def test_floating_hud_initialization_and_lifecycle(self):
        hud = FloatingHUD(alpha=0.92)
        self.assertFalse(hud.is_visible)
        self.assertIsNone(hud.root)
        self.assertEqual(hud.alpha, 0.92)
        # Verify safe close when uninitialized
        hud.close()
        self.assertFalse(hud.is_visible)


if __name__ == "__main__":
    unittest.main()
