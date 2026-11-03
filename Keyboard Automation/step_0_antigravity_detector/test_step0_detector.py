#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Step 0 - AntiGravity Detector Core Engine & Clean Timer Dashboard
================================================================================
Test Suite: step_0_antigravity_detector/test_step0_detector.py
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) / Dept 06 (Backend & API Engineering)
"""

import sys
import json
import unittest
from unittest.mock import patch, MagicMock
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
    get_antigravity_chat_stats,
    resolve_brain_dir,
)
from step0_antigravity_detector import (
    format_dashboard_box,
    clear_screen,
    should_pause,
)
import step0_antigravity_detector_test as step0_test_alias


class TestDetectionResult(unittest.TestCase):
    def test_detection_result_defaults(self):
        res = DetectionResult()
        self.assertFalse(res.is_detected)
        self.assertFalse(res.is_process_running)
        self.assertFalse(res.has_window)
        self.assertEqual(res.detection_method, "none")
        self.assertEqual(res.pending_grill_me_chats, 0)
        self.assertFalse(res.has_pending_grill_me)
        self.assertFalse(res.trigger_matched)
        self.assertEqual(res.chat_stats, {})
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
            pending_grill_me_chats=2,
            has_pending_grill_me=True,
            trigger_matched=True,
            chat_stats={"total_chats": 10, "active_chats": 2, "inactive_chats": 8, "pending_grill_me_chats": 2}
        )
        envelope = res.to_json_envelope()
        self.assertTrue(envelope["success"])
        self.assertEqual(envelope["data"]["main_pid"], 100)
        self.assertEqual(envelope["data"]["detection_method"], "process_and_window")
        self.assertEqual(envelope["data"]["pending_grill_me_chats"], 2)
        self.assertTrue(envelope["data"]["has_pending_grill_me"])
        self.assertTrue(envelope["meta"]["trigger_matched"])
        self.assertEqual(envelope["meta"]["step"], "step_0_antigravity_detector")

    def test_detection_methods(self):
        # Process only
        r_proc = DetectionResult(is_detected=True, is_process_running=True, has_window=False)
        self.assertEqual(r_proc.detection_method, "process_only")

        # Window only
        r_win = DetectionResult(is_detected=True, is_process_running=False, has_window=True)
        self.assertEqual(r_win.detection_method, "window_only")

        # Dict serialization
        d = r_win.to_dict()
        self.assertIsInstance(d, dict)
        self.assertTrue(d["is_detected"])
        self.assertTrue(d["has_window"])


class TestProcessDetection(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(headless=True, verbose=False)

    @patch("antigravity_detector_core.AntiGravityDetector._scan_processes")
    def test_is_antigravity_running_process_true(self, mock_scan):
        mock_scan.return_value = ([1234, 5678], 1234, "C:\\test\\antigravity.exe", [])
        self.assertTrue(self.detector.is_antigravity_running())
        self.assertEqual(self.detector.get_antigravity_pids(), [1234, 5678])

    @patch("antigravity_detector_core.AntiGravityDetector._scan_processes")
    @patch("antigravity_detector_core.AntiGravityDetector._scan_windows")
    def test_is_antigravity_running_false(self, mock_win, mock_proc):
        mock_proc.return_value = ([], None, None, [])
        mock_win.return_value = []
        self.assertFalse(self.detector.is_antigravity_running())
        self.assertEqual(self.detector.get_antigravity_pids(), [])

    def test_disqualified_browser_set(self):
        self.assertIn("chrome.exe", DISQUALIFIED_BROWSER_PROCS)
        self.assertIn("msedge.exe", DISQUALIFIED_BROWSER_PROCS)
        self.assertIn("firefox.exe", DISQUALIFIED_BROWSER_PROCS)
        self.assertIn("brave.exe", DISQUALIFIED_BROWSER_PROCS)


class TestWindowDetection(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(headless=True, verbose=False)

    @patch("antigravity_detector_core.AntiGravityDetector._scan_windows")
    def test_get_antigravity_windows(self, mock_win):
        mock_win.return_value = [
            {"hwnd": 123, "title": "Antigravity Workspace", "class": "Chrome_WidgetWin_1", "is_minimized": False}
        ]
        wins = self.detector.get_antigravity_windows()
        self.assertEqual(len(wins), 1)
        self.assertEqual(wins[0]["hwnd"], 123)
        self.assertFalse(wins[0]["is_minimized"])


class TestChatStatisticsAndBrain(unittest.TestCase):
    def test_resolve_brain_dir_explicit(self):
        p = resolve_brain_dir(_this_dir)
        self.assertEqual(p, _this_dir.resolve())

    @patch("pathlib.Path.is_dir")
    def test_get_antigravity_chat_stats_empty(self, mock_isdir):
        mock_isdir.return_value = False
        stats = get_antigravity_chat_stats(brain_dir="C:\\nonexistent_brain_dir_12345")
        self.assertEqual(stats["total_chats"], 0)
        self.assertEqual(stats["active_chats"], 0)
        self.assertEqual(stats["inactive_chats"], 0)
        self.assertEqual(stats["pending_grill_me_chats"], 0)
        self.assertFalse(stats["has_pending_grill_me"])

    @patch("antigravity_detector_core.get_antigravity_chat_stats")
    def test_check_pending_grill_me(self, mock_stats):
        mock_stats.return_value = {
            "total_chats": 5,
            "active_chats": 1,
            "inactive_chats": 4,
            "pending_grill_me_chats": 1,
            "has_pending_grill_me": True,
            "pending_chat_ids": ["chat_abc_123"]
        }
        detector = AntiGravityDetector(headless=True, verbose=False)
        count, ids = detector.check_pending_grill_me()
        self.assertEqual(count, 1)
        self.assertEqual(ids, ["chat_abc_123"])


class TestAntiGravityDetectorCore(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(headless=True, verbose=False)

    @patch("antigravity_detector_core.AntiGravityDetector._scan_processes")
    @patch("antigravity_detector_core.AntiGravityDetector._scan_windows")
    @patch("antigravity_detector_core.AntiGravityDetector.get_chat_statistics")
    def test_detect_trigger_matched_true(self, mock_stats, mock_win, mock_proc):
        mock_proc.return_value = ([999], 999, "C:\\antigravity.exe", [{"pid": 999}])
        mock_win.return_value = [{"hwnd": 888, "title": "Antigravity", "class": "Chrome_WidgetWin_1", "is_minimized": False}]
        mock_stats.return_value = {"total_chats": 3, "active_chats": 1, "inactive_chats": 2, "pending_grill_me_chats": 1}

        res = self.detector.detect()
        self.assertTrue(res.is_detected)
        self.assertTrue(res.is_process_running)
        self.assertTrue(res.has_window)
        self.assertEqual(res.main_pid, 999)
        self.assertEqual(res.pending_grill_me_chats, 1)
        self.assertTrue(res.has_pending_grill_me)
        self.assertTrue(res.trigger_matched)

    @patch("antigravity_detector_core.AntiGravityDetector._scan_processes")
    @patch("antigravity_detector_core.AntiGravityDetector._scan_windows")
    @patch("antigravity_detector_core.AntiGravityDetector.get_chat_statistics")
    def test_detect_trigger_matched_false_when_no_pending_grill_me(self, mock_stats, mock_win, mock_proc):
        mock_proc.return_value = ([999], 999, "C:\\antigravity.exe", [])
        mock_win.return_value = [{"hwnd": 888, "title": "Antigravity", "class": "Chrome_WidgetWin_1", "is_minimized": False}]
        mock_stats.return_value = {"total_chats": 3, "active_chats": 1, "inactive_chats": 2, "pending_grill_me_chats": 0}

        res = self.detector.detect()
        self.assertTrue(res.is_detected)
        self.assertEqual(res.pending_grill_me_chats, 0)
        self.assertFalse(res.has_pending_grill_me)
        self.assertFalse(res.trigger_matched)

    @patch("antigravity_detector_core.AntiGravityDetector.detect")
    def test_run_loop_with_max_checks(self, mock_detect):
        mock_res = DetectionResult(is_detected=False, trigger_matched=False)
        mock_detect.return_value = mock_res

        checks = []
        def _cb(i, r):
            checks.append(i)

        res = self.detector.run_loop(poll_interval=0.01, max_checks=3, on_check_callback=_cb)
        self.assertIsNone(res)
        self.assertEqual(len(checks), 3)

    @patch("antigravity_detector_core.AntiGravityDetector.detect")
    def test_run_loop_returns_on_trigger_matched(self, mock_detect):
        mock_res = DetectionResult(is_detected=True, trigger_matched=True, pending_grill_me_chats=1)
        mock_detect.return_value = mock_res

        triggered_results = []
        def _on_trigger(r):
            triggered_results.append(r)

        res = self.detector.run_loop(poll_interval=0.01, on_trigger_callback=_on_trigger)
        self.assertIsNotNone(res)
        self.assertTrue(res.trigger_matched)
        self.assertEqual(len(triggered_results), 1)

    def test_stop(self):
        self.detector.stop()
        self.assertTrue(self.detector._stop_requested)


class TestDashboardFormatting(unittest.TestCase):
    def test_format_dashboard_box_open_with_grill_me(self):
        res = DetectionResult(
            is_detected=True,
            chat_stats={
                "total_chats": 24,
                "active_chats": 2,
                "inactive_chats": 22,
                "pending_grill_me_chats": 1,
            }
        )
        box = format_dashboard_box(res)
        self.assertIn("OPEN", box)
        self.assertIn("24 Chats", box)
        self.assertIn("2 Chats", box)
        self.assertIn("22 Chats", box)
        self.assertIn("YES (1 Chat)", box)

    def test_format_dashboard_box_closed(self):
        res = DetectionResult(
            is_detected=False,
            chat_stats={
                "total_chats": 0,
                "active_chats": 0,
                "inactive_chats": 0,
                "pending_grill_me_chats": 0,
            }
        )
        box = format_dashboard_box(res)
        self.assertIn("CLOSED", box)
        self.assertIn("NO (0 Chats)", box)

    def test_should_pause(self):
        class DummyArgs:
            no_pause = False
            pause = True
        self.assertTrue(should_pause(DummyArgs()))

        class DummyNoPause:
            no_pause = True
            pause = None
        self.assertFalse(should_pause(DummyNoPause()))

    def test_backward_compat_test_alias(self):
        """Verify that step0_antigravity_detector_test cleanly re-exports all canonical symbols."""
        self.assertTrue(callable(step0_test_alias.format_dashboard_box))
        self.assertTrue(callable(step0_test_alias.clear_screen))
        self.assertTrue(callable(step0_test_alias.should_pause))
        self.assertTrue(callable(step0_test_alias.display_dashboard))
        self.assertTrue(callable(step0_test_alias.main))


if __name__ == "__main__":
    unittest.main()
