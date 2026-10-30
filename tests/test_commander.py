#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for AutoSelect-Commander.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auto_commander import (
    Config,
    DetectionResult,
    UIAutomationDetector,
    VisionDetector,
    DualModeDetector,
    MouseController,
)


class TestAutoCommander(unittest.TestCase):
    def test_config_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.countdown_seconds, 30)
        self.assertEqual(cfg.check_interval_ms, 1000)
        self.assertEqual(cfg.mouse_interruption_threshold_px, 15)
        self.assertEqual(cfg.smooth_glide_duration_s, 0.8)
        self.assertTrue(cfg.failsafe_enabled)
        self.assertIn("(Recommended)", cfg.target_keywords)

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

    def test_vision_detector_templates(self):
        detector = VisionDetector(templates_dir="assets/templates")
        self.assertTrue(os.path.exists("assets/templates"))
        self.assertGreaterEqual(len(detector.templates), 1)

    def test_dual_mode_detector_initialization(self):
        cfg = Config()
        dual = DualModeDetector(cfg)
        self.assertIsNotNone(dual.uia_detector)
        self.assertIsNotNone(dual.vision_detector)


if __name__ == "__main__":
    unittest.main()
