#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Step 0 - AntiGravity Detector Core Engine
========================================================
Test Suite: step_0_antigravity_detector/test_step0_detector.py
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) / Dept 06 (Backend & API Engineering)
"""

import sys
import unittest
from pathlib import Path

# Ensure package and root directories are resolvable
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
    DISQUALIFIED_BROWSER_PROCS,
    ANTIGRAVITY_PROCESS_NAMES,
)


class TestDetectionResult(unittest.TestCase):
    def test_detection_result_defaults(self):
        res = DetectionResult()
        self.assertFalse(res.is_detected)
        self.assertFalse(res.is_process_running)
        self.assertFalse(res.has_window)
        self.assertEqual(res.detection_method, "none")
        self.assertTrue(bool(res.timestamp))

    def test_json_envelope(self):
        res = DetectionResult(
            is_detected=True,
            is_process_running=True,
            has_window=True,
            process_count=3,
            pids=[100, 101, 102],
            main_pid=100,
            exe_path="C:\\test\\antigravity.exe",
            window_hwnd=9999,
            window_title="Antigravity Test Window",
            window_class="Chrome_WidgetWin_1",
        )
        envelope = res.to_json_envelope()
        self.assertTrue(envelope["success"])
        self.assertEqual(envelope["data"]["main_pid"], 100)
        self.assertEqual(envelope["data"]["detection_method"], "process_and_window")
        self.assertEqual(envelope["meta"]["step"], "step_0_antigravity_detector")


class TestAntiGravityDetector(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(
            poll_interval=DEFAULT_TEST_POLL_INTERVAL,
            headless=True,
            verbose=False,
        )

    def test_intervals(self):
        self.assertEqual(DEFAULT_PRODUCTION_POLL_INTERVAL, 300.0)
        self.assertEqual(DEFAULT_TEST_POLL_INTERVAL, 10.0)

    def test_path_resolution(self):
        self.assertTrue(self.detector.step1_script.is_file(), f"Step 1 script not found: {self.detector.step1_script}")
        self.assertTrue(str(self.detector.state_file).endswith("target_chat.json"))
        self.assertTrue(self.detector.python_exe.is_file(), f"Python exe not found: {self.detector.python_exe}")

    def test_browser_disqualification(self):
        for b in ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"]:
            self.assertIn(b, DISQUALIFIED_BROWSER_PROCS)

    def test_live_detection(self):
        result = self.detector.detect()
        # In this environment, Antigravity is currently running
        self.assertIsInstance(result, DetectionResult)
        self.assertTrue(result.is_detected)
        self.assertTrue(result.process_count > 0)
        self.assertTrue(len(result.pids) > 0)
        self.assertIn(result.detection_method, ["process_only", "process_and_window"])


if __name__ == "__main__":
    unittest.main()
