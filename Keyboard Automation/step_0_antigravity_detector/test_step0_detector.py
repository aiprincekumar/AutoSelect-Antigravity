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
import subprocess
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
    PipelineStep,
    discover_pipeline_steps,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
    DEFAULT_STEP_SETTLE_DELAY,
    EXIT_CODE_NO_PENDING_CHATS,
    DISQUALIFIED_BROWSER_PROCS,
    ANTIGRAVITY_PROCESS_NAMES,
    get_antigravity_chat_stats,
    resolve_brain_dir,
)
from step0_antigravity_detector_test import (
    format_dashboard_box,
    clear_screen,
)


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


class TestAntiGravityDetector(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(
            poll_interval=DEFAULT_TEST_POLL_INTERVAL,
            headless=True,
            verbose=False,
            require_grill_me=True,
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
        # In this environment, Antigravity is running
        self.assertIsInstance(result, DetectionResult)
        self.assertTrue(result.is_detected)
        self.assertTrue(result.process_count > 0)
        self.assertTrue(len(result.pids) > 0)
        self.assertIn(result.detection_method, ["process_only", "process_and_window"])
        self.assertIsInstance(result.chat_stats, dict)
        self.assertIn("total_chats", result.chat_stats)
        self.assertIsInstance(result.pending_grill_me_chats, int)
        self.assertIsInstance(result.has_pending_grill_me, bool)
        self.assertEqual(result.trigger_matched, (result.is_detected and result.has_pending_grill_me))

    def test_is_antigravity_open(self):
        is_open = self.detector.is_antigravity_open()
        self.assertIsInstance(is_open, bool)
        self.assertTrue(is_open)

    def test_two_factor_trigger_condition_logic(self):
        # 1. Antigravity running, but 0 pending Grill-Me chats: trigger MUST be False!
        detector_strict = AntiGravityDetector(require_grill_me=True, headless=True)
        # Mocking or simulating stats:
        res = detector_strict.detect()
        if res.pending_grill_me_chats == 0:
            self.assertFalse(res.trigger_matched, "Trigger should be False when 0 grill-me chats are pending")
        else:
            self.assertTrue(res.trigger_matched)

        # 2. Antigravity running, require_grill_me=False: trigger MUST be True on open
        detector_open_only = AntiGravityDetector(require_grill_me=False, headless=True)
        res_open = detector_open_only.detect()
        self.assertTrue(res_open.trigger_matched, "Trigger should be True when require_grill_me is False and Antigravity is open")

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

    def test_run_loop_with_require_grill_me_false(self):
        checks_recorded = []

        def cb(num, res):
            checks_recorded.append((num, res.is_detected))

        # With require_grill_me=False, it triggers on Antigravity open
        detector = AntiGravityDetector(
            poll_interval=0.01,
            headless=True,
            require_grill_me=False
        )
        res = detector.run_loop(
            poll_interval=0.01,
            max_checks=1,
            auto_launch=False,
            on_check_callback=cb
        )
        self.assertIsNotNone(res)
        self.assertEqual(len(checks_recorded), 1)
        self.assertEqual(checks_recorded[0][0], 1)
        self.assertTrue(res.trigger_matched)

    def test_run_loop_with_require_grill_me_true_when_zero_pending(self):
        checks_recorded = []

        def cb(num, res):
            checks_recorded.append((num, res.is_detected, res.trigger_matched))

        # With require_grill_me=True, if 0 chats pending, max_checks exits with None
        detector = AntiGravityDetector(
            poll_interval=0.01,
            headless=True,
            require_grill_me=True
        )
        current_res = detector.detect()
        if current_res.pending_grill_me_chats == 0:
            res = detector.run_loop(
                poll_interval=0.01,
                max_checks=1,
                auto_launch=False,
                on_check_callback=cb
            )
            self.assertIsNone(res)
            self.assertEqual(len(checks_recorded), 1)
            self.assertFalse(checks_recorded[0][2])


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
        self.assertIn("AntiGravity Status", proc.stdout)
        self.assertIn("Total Chats", proc.stdout)
        self.assertIn("Active Chats", proc.stdout)
        self.assertIn("Inactive Chats", proc.stdout)
        self.assertIn("Pending Question", proc.stdout)
        # Ensure extraneous prints are 100% absent (Zero Clutter)
        self.assertNotIn("[*]", proc.stdout)
        self.assertNotIn("STEP 0: ANTIGRAVITY DETECTOR", proc.stdout)
        self.assertNotIn("Checking processes...", proc.stdout)

    def test_screen_purity_strictly_dashboard_box(self):
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
        clean_text = proc.stdout.replace("\x0c", "").strip()
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
        self.assertTrue(lines[0].startswith("┌─"), f"First line must be dashboard top border: {lines[0]}")
        self.assertTrue(lines[-1].startswith("└─"), f"Last line must be dashboard bottom border: {lines[-1]}")
        for line in lines:
            self.assertTrue(line.startswith("│") or line.startswith("┌") or line.startswith("├") or line.startswith("└"),
                            f"Extraneous line detected outside dashboard box: '{line}'")
        first_len = len(lines[0])
        for idx, line in enumerate(lines):
            self.assertEqual(len(line), first_len, f"Line {idx} length {len(line)} does not match top border {first_len}: '{line}'")

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
        stats = get_antigravity_chat_stats()
        self.assertIsInstance(stats, dict)
        self.assertGreaterEqual(stats["total_chats"], 1)
        self.assertGreaterEqual(stats["active_chats"], 0)
        self.assertEqual(stats["total_chats"], stats["active_chats"] + stats["inactive_chats"])
        self.assertIn("pending_grill_me_chats", stats)
        self.assertIsInstance(stats["has_pending_grill_me"], bool)

    def test_format_dashboard_box(self):
        box_open = format_dashboard_box(True, {
            "total_chats": 90,
            "active_chats": 12,
            "inactive_chats": 78,
            "pending_grill_me_chats": 1
        })
        self.assertIn("ANTIGRAVITY STATUS & CHAT DASHBOARD", box_open)
        self.assertIn("AntiGravity Status", box_open)
        self.assertIn("OPEN (Running)", box_open)
        self.assertIn("Total Chats", box_open)
        self.assertIn("90", box_open)
        self.assertIn("Active Chats", box_open)
        self.assertIn("12", box_open)
        self.assertIn("Inactive Chats", box_open)
        self.assertIn("78", box_open)
        self.assertIn("Pending Question", box_open)
        self.assertIn("YES (1 Chats - Waiting Response)", box_open)

        # Verify all lines of box_open have identical character length
        open_lines = [l for l in box_open.splitlines() if l.strip()]
        open_len = len(open_lines[0])
        for idx, line in enumerate(open_lines):
            self.assertEqual(len(line), open_len, f"box_open line {idx} length mismatch: '{line}'")

        box_closed = format_dashboard_box(False, {
            "total_chats": 90,
            "active_chats": 0,
            "inactive_chats": 90,
            "pending_grill_me_chats": 0
        })
        self.assertIn("CLOSED (Not Running)", box_closed)
        self.assertIn("NO (0 Chats)", box_closed)

        # Verify all lines of box_closed have identical character length (standard 58 chars)
        closed_lines = [l for l in box_closed.splitlines() if l.strip()]
        closed_len = len(closed_lines[0])
        self.assertEqual(closed_len, 58, f"Standard box width should be 58 chars, got {closed_len}")
        for idx, line in enumerate(closed_lines):
            self.assertEqual(len(line), closed_len, f"box_closed line {idx} length mismatch: '{line}'")

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
        self.assertIn("ANTIGRAVITY STATUS & CHAT DASHBOARD", proc.stdout)
        self.assertNotIn("STEP 0: ANTIGRAVITY DETECTOR", proc.stdout)
        self.assertNotIn("[SUCCESS]", proc.stdout)


class TestPipelineStep(unittest.TestCase):
    def test_pipeline_step_model(self):
        dummy_path = _this_dir / "step0_antigravity_detector_prod.py"
        step = PipelineStep(
            step_index=1,
            name="Step 1 Test",
            script_path=dummy_path,
            is_optional=False,
            description="Test step description"
        )
        self.assertEqual(step.step_index, 1)
        self.assertEqual(step.name, "Step 1 Test")
        self.assertTrue(step.exists())
        self.assertFalse(step.is_optional)

        d = step.to_dict()
        self.assertEqual(d["step_index"], 1)
        self.assertEqual(d["name"], "Step 1 Test")
        self.assertTrue(d["exists"])
        self.assertFalse(d["is_optional"])

    def test_pipeline_step_absent(self):
        non_existent = _this_dir / "non_existent_step_script.py"
        step = PipelineStep(
            step_index=4,
            name="Step 4 Reporting",
            script_path=non_existent,
            is_optional=True
        )
        self.assertFalse(step.exists())
        self.assertTrue(step.is_optional)


class TestDynamicPipelineDiscovery(unittest.TestCase):
    def test_discover_pipeline_steps_defaults(self):
        steps = discover_pipeline_steps(root_dir=_root_dir, include_future=True)
        indices = [s.step_index for s in steps]
        self.assertIn(1, indices)
        self.assertIn(2, indices)
        self.assertIn(3, indices)
        self.assertIn(4, indices)

        # Steps 1, 2, 3 should physically exist on disk
        step1 = next(s for s in steps if s.step_index == 1)
        step2 = next(s for s in steps if s.step_index == 2)
        step3 = next(s for s in steps if s.step_index == 3)
        self.assertTrue(step1.exists())
        self.assertTrue(step2.exists())
        self.assertTrue(step3.exists())
        self.assertFalse(step1.is_optional)
        self.assertFalse(step2.is_optional)
        self.assertFalse(step3.is_optional)

        # Step 4 (Reporting) is marked optional
        step4 = next(s for s in steps if s.step_index == 4)
        self.assertTrue(step4.is_optional)

    def test_discover_pipeline_steps_active_only(self):
        steps_active = discover_pipeline_steps(root_dir=_root_dir, include_future=False)
        indices = [s.step_index for s in steps_active]
        self.assertIn(1, indices)
        self.assertIn(2, indices)
        self.assertIn(3, indices)
        for s in steps_active:
            self.assertTrue(s.exists())

    def test_custom_script_override(self):
        dummy = _this_dir / "step0_antigravity_detector_prod.py"
        steps = discover_pipeline_steps(root_dir=_root_dir, custom_scripts={2: dummy})
        step2 = next(s for s in steps if s.step_index == 2)
        self.assertEqual(step2.script_path, dummy)


class TestPipelineExecution(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(headless=True, verbose=False)

    @patch("subprocess.run")
    def test_execute_pipeline_success_steps_1_to_3(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        present_steps = [s for s in self.detector.discover_steps(include_future=True) if s.exists()]
        ok, code, msg, reports = self.detector.execute_pipeline(capture_output=True, settle_delay=0.0)
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        self.assertIn("Pipeline completed successfully", msg)
        self.assertEqual(len(reports), len(present_steps))
        self.assertEqual([r["step_index"] for r in reports], [s.step_index for s in present_steps])

    @patch("subprocess.run")
    def test_execute_pipeline_step1_exit_code_10_cancels_remaining(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = EXIT_CODE_NO_PENDING_CHATS
        mock_run.return_value = mock_proc

        ok, code, msg, reports = self.detector.execute_pipeline(capture_output=True, settle_delay=0.0)
        self.assertTrue(ok)
        self.assertEqual(code, EXIT_CODE_NO_PENDING_CHATS)
        self.assertIn("cancelled cleanly", msg)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["step_index"], 1)

    @patch("subprocess.run")
    def test_execute_pipeline_step2_failure_halts_pipeline(self, mock_run):
        res1 = MagicMock(returncode=0)
        res2 = MagicMock(returncode=1)
        mock_run.side_effect = [res1, res2]

        ok, code, msg, reports = self.detector.execute_pipeline(capture_output=True, settle_delay=0.0)
        self.assertFalse(ok)
        self.assertEqual(code, 1)
        self.assertIn("Step 2", msg)
        self.assertEqual(len(reports), 2)

    @patch("subprocess.run")
    def test_execute_pipeline_with_present_step4(self, mock_run):
        mock_proc = MagicMock(returncode=0)
        mock_run.return_value = mock_proc

        dummy_script = _this_dir / "step0_antigravity_detector_prod.py"
        custom_steps = [
            PipelineStep(step_index=1, name="Step 1", script_path=dummy_script),
            PipelineStep(step_index=2, name="Step 2", script_path=dummy_script),
            PipelineStep(step_index=3, name="Step 3", script_path=dummy_script),
            PipelineStep(step_index=4, name="Step 4 Reporting", script_path=dummy_script, is_optional=True),
        ]
        ok, code, msg, reports = self.detector.execute_pipeline(
            capture_output=True,
            settle_delay=0.0,
            steps=custom_steps
        )
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        self.assertEqual(len(reports), 4)
        self.assertEqual([r["step_index"] for r in reports], [1, 2, 3, 4])


class TestPipelineLaunchAndHygiene(unittest.TestCase):
    def setUp(self):
        self.detector = AntiGravityDetector(headless=True, verbose=False)

    @patch.object(AntiGravityDetector, "execute_pipeline")
    def test_launch_pipeline_wait_true(self, mock_exec):
        mock_exec.return_value = (True, 0, "Pipeline completed", [])
        ok, code, msg = self.detector.launch_pipeline(wait=True)
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        mock_exec.assert_called_once()

    @patch("subprocess.Popen")
    def test_launch_pipeline_wait_false_detached(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.pid = 43210
        mock_popen.return_value = mock_proc

        ok, code, msg = self.detector.launch_pipeline(wait=False)
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        self.assertIn("PID: 43210", msg)
        self.assertIn("asynchronously in background", msg)
        mock_popen.assert_called_once()

    @patch.object(AntiGravityDetector, "launch_pipeline")
    def test_launch_step1_backward_compatibility_alias(self, mock_launch):
        mock_launch.return_value = (True, 0, "Pipeline executed via launch_step1")
        ok, code, msg = self.detector.launch_step1(wait=True, extra_args=["--test-flag"])
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        mock_launch.assert_called_once_with(wait=True, extra_args=["--test-flag"], capture_output=True)


if __name__ == "__main__":
    unittest.main()
