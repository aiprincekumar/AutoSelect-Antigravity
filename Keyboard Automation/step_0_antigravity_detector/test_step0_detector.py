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
import json
import subprocess
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

    def test_is_antigravity_open(self):
        is_open = self.detector.is_antigravity_open()
        self.assertIsInstance(is_open, bool)
        self.assertTrue(is_open)

    def test_stop_signal(self):
        self.assertFalse(self.detector._stop_requested)
        self.detector.stop()
        self.assertTrue(self.detector._stop_requested)

    def test_launch_step1_missing_script(self):
        # Point to a nonexistent script
        orig_script = self.detector.step1_script
        try:
            self.detector.step1_script = Path("nonexistent_step1.py")
            ok, code, msg = self.detector.launch_step1()
            self.assertFalse(ok)
            self.assertEqual(code, 1)
            self.assertIn("not found", msg)
        finally:
            self.detector.step1_script = orig_script

    def test_run_loop_max_checks_no_auto_launch(self):
        checks_recorded = []

        def cb(num, res):
            checks_recorded.append((num, res.is_detected))

        res = self.detector.run_loop(
            poll_interval=0.01,
            max_checks=1,
            auto_launch=False,
            on_check_callback=cb
        )
        self.assertIsNotNone(res)
        self.assertEqual(len(checks_recorded), 1)
        self.assertEqual(checks_recorded[0][0], 1)


class TestStep0TestRunnerCLI(unittest.TestCase):
    def test_cli_once_no_launch_no_pause(self):
        py_exe = _root_dir / ".venv" / "Scripts" / "python.exe"
        if not py_exe.is_file():
            py_exe = Path(sys.executable)
        script = _this_dir / "step0_antigravity_detector_test.py"

        proc = subprocess.run(
            [str(py_exe), str(script), "--once", "--no-launch", "--no-pause"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ANTIGRAVITY STATUS & CHAT DASHBOARD", proc.stdout)
        self.assertIn("कुल चैट्स (Total Chats)", proc.stdout)
        self.assertIn("एंटी-ग्रेविटी स्थिति (Status)", proc.stdout)
        self.assertIn("एक्टिव चैट्स (Active Chats)", proc.stdout)
        self.assertIn("ग्रिल-मी पेंडिंग (Pending Question)", proc.stdout)

    def test_cli_json_envelope(self):
        py_exe = _root_dir / ".venv" / "Scripts" / "python.exe"
        if not py_exe.is_file():
            py_exe = Path(sys.executable)
        script = _this_dir / "step0_antigravity_detector_test.py"

        proc = subprocess.run(
            [str(py_exe), str(script), "--once", "--no-launch", "--no-pause", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("meta", {}).get("step"), "step_0_antigravity_detector")
        self.assertIn("chat_stats", data.get("data", {}))
        stats = data["data"]["chat_stats"]
        self.assertIn("total_chats", stats)
        self.assertIn("active_chats", stats)
        self.assertIn("inactive_chats", stats)
        self.assertIn("pending_grill_me_chats", stats)
        self.assertIn("has_pending_grill_me", stats)

    def test_get_antigravity_chat_stats(self):
        from step0_antigravity_detector_test import get_antigravity_chat_stats
        stats = get_antigravity_chat_stats()
        self.assertIsInstance(stats, dict)
        self.assertGreaterEqual(stats["total_chats"], 1)
        self.assertGreaterEqual(stats["active_chats"], 0)
        self.assertEqual(stats["total_chats"], stats["active_chats"] + stats["inactive_chats"])
        self.assertIn("pending_grill_me_chats", stats)
        self.assertIsInstance(stats["has_pending_grill_me"], bool)

    def test_format_dashboard_box(self):
        from step0_antigravity_detector_test import format_dashboard_box
        box_open = format_dashboard_box(True, {
            "total_chats": 90,
            "active_chats": 12,
            "inactive_chats": 78,
            "pending_grill_me_chats": 1
        })
        self.assertIn("ANTIGRAVITY STATUS & CHAT DASHBOARD", box_open)
        self.assertIn("खुला है / OPEN", box_open)
        self.assertIn("90", box_open)
        self.assertIn("हाँ / YES (1 चैट)", box_open)

        box_closed = format_dashboard_box(False, {
            "total_chats": 90,
            "active_chats": 0,
            "inactive_chats": 90,
            "pending_grill_me_chats": 0
        })
        self.assertIn("बंद है / CLOSED", box_closed)
        self.assertIn("नहीं / NO (0 चैट)", box_closed)

    def test_batch_file_no_pause_execution(self):
        bat_file = _this_dir / "run_step0_test.bat"
        proc = subprocess.run(
            ["cmd.exe", "/c", str(bat_file), "--no-pause", "--once", "--no-launch"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[SUCCESS]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
