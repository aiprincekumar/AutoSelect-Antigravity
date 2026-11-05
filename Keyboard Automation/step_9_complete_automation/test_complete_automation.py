#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Step 9: Complete Automation Master Controller & Step Orchestrator
========================================================================
Test Suite: step_9_complete_automation/test_complete_automation.py
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) / Dept 06 (Backend & API Engineering)
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure paths are configured
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from complete_automation import (
    CompleteAutomationController,
    AutomationConfig,
    TimingConfig,
    EnabledStepsConfig,
    PipelineStep,
    discover_pipeline_steps,
    EXIT_CODE_SUCCESS,
    EXIT_CODE_NO_PENDING_CHATS,
    EXIT_CODE_GENERAL_ERROR,
)
from step_0_antigravity_detector.antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
)


class TestAutomationConfig(unittest.TestCase):
    def test_config_defaults(self):
        cfg = AutomationConfig()
        self.assertEqual(cfg.mode, "production")
        self.assertEqual(cfg.timing.step0_poll_interval_prod_seconds, 300.0)
        self.assertEqual(cfg.timing.step0_poll_interval_test_seconds, 10.0)
        self.assertEqual(cfg.timing.settle_delay_between_steps_seconds, 0.8)
        self.assertEqual(cfg.timing.user_activity_pause_threshold_seconds, 60.0)
        self.assertEqual(cfg.timing.step4_user_activity_delay_seconds, 10.0)
        self.assertTrue(cfg.enabled_steps.step1_find_and_focus)
        self.assertTrue(cfg.enabled_steps.step2_gui_chat_select)
        self.assertTrue(cfg.enabled_steps.step3_keyboard_automation)
        self.assertTrue(cfg.enabled_steps.step4_reporting)

    def test_config_load_from_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps({
                "mode": "test",
                "timing": {
                    "step0_poll_interval_prod_seconds": 120.0,
                    "step0_poll_interval_test_seconds": 5.0,
                    "settle_delay_between_steps_seconds": 0.5,
                    "user_activity_pause_threshold_seconds": 45.0,
                    "step4_user_activity_delay_seconds": 8.0,
                },
                "enabled_steps": {
                    "step1_find_and_focus": True,
                    "step2_gui_chat_select": False,
                    "step3_keyboard_automation": True,
                    "step4_reporting": False,
                }
            }))
            temp_path = f.name

        try:
            cfg = AutomationConfig.load_from_file(temp_path)
            self.assertEqual(cfg.mode, "test")
            self.assertEqual(cfg.timing.step0_poll_interval_test_seconds, 5.0)
            self.assertEqual(cfg.timing.settle_delay_between_steps_seconds, 0.5)
            self.assertEqual(cfg.timing.user_activity_pause_threshold_seconds, 45.0)
            self.assertFalse(cfg.enabled_steps.step2_gui_chat_select)
            self.assertFalse(cfg.enabled_steps.step4_reporting)
            self.assertTrue(cfg.enabled_steps.step1_find_and_focus)
        finally:
            os.remove(temp_path)

    def test_config_to_dict(self):
        cfg = AutomationConfig(mode="test")
        d = cfg.to_dict()
        self.assertEqual(d["mode"], "test")
        self.assertIn("timing", d)
        self.assertIn("enabled_steps", d)
        self.assertIn("antigravity", d)


class TestPipelineStepDiscovery(unittest.TestCase):
    def test_discover_pipeline_steps(self):
        steps = discover_pipeline_steps(root_dir=_root_dir, include_future=True)
        indices = [s.step_index for s in steps]
        self.assertIn(1, indices)
        self.assertIn(2, indices)
        self.assertIn(3, indices)
        self.assertIn(4, indices)

        s1 = next(s for s in steps if s.step_index == 1)
        s2 = next(s for s in steps if s.step_index == 2)
        s3 = next(s for s in steps if s.step_index == 3)
        s4 = next(s for s in steps if s.step_index == 4)

        self.assertTrue(s1.exists())
        self.assertTrue(s2.exists())
        self.assertTrue(s3.exists())
        self.assertTrue(s4.exists())
        self.assertFalse(s1.is_optional)
        self.assertTrue(s4.is_optional)

    def test_custom_script_override(self):
        dummy = _this_dir / "complete_automation.py"
        steps = discover_pipeline_steps(root_dir=_root_dir, custom_scripts={2: dummy})
        s2 = next(s for s in steps if s.step_index == 2)
        self.assertEqual(s2.script_path, dummy)


class TestCompleteAutomationExecution(unittest.TestCase):
    def setUp(self):
        self.cfg = AutomationConfig(
            mode="test",
            timing=TimingConfig(settle_delay_between_steps_seconds=0.0)
        )
        self.controller = CompleteAutomationController(config=self.cfg, headless=True)

    @patch("subprocess.run")
    def test_execute_pipeline_success_all_steps(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        ok, code, msg, reports = self.controller.execute_pipeline(capture_output=True)
        self.assertTrue(ok)
        self.assertEqual(code, 0)
        self.assertIn("completed successfully", msg)
        self.assertEqual(len(reports), len(self.controller.pipeline_steps))

    @patch("subprocess.run")
    def test_execute_pipeline_step1_exit_10_cancels_remaining(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = EXIT_CODE_NO_PENDING_CHATS
        mock_run.return_value = mock_proc

        ok, code, msg, reports = self.controller.execute_pipeline(capture_output=True)
        self.assertTrue(ok)
        self.assertEqual(code, EXIT_CODE_NO_PENDING_CHATS)
        self.assertIn("cancelled cleanly", msg)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["step_index"], 1)

    @patch("subprocess.run")
    def test_execute_pipeline_step2_failure_aborts(self, mock_run):
        res1 = MagicMock(returncode=0)
        res2 = MagicMock(returncode=1)
        mock_run.side_effect = [res1, res2]

        ok, code, msg, reports = self.controller.execute_pipeline(capture_output=True)
        self.assertFalse(ok)
        self.assertEqual(code, 1)
        self.assertIn("Step 2", msg)
        self.assertEqual(len(reports), 2)

    @patch("subprocess.run")
    def test_step_disabling_honored(self, mock_run):
        mock_proc = MagicMock(returncode=0)
        mock_run.return_value = mock_proc

        self.controller.config.enabled_steps.step2_gui_chat_select = False
        ok, code, msg, reports = self.controller.execute_pipeline(capture_output=True)
        self.assertTrue(ok)
        executed_indices = [r["step_index"] for r in reports]
        self.assertNotIn(2, executed_indices)
        self.assertIn(1, executed_indices)
        self.assertIn(3, executed_indices)

    @patch("subprocess.run")
    def test_headless_controls_subprocess_creationflags(self, mock_run):
        import subprocess
        mock_proc = MagicMock(returncode=0)
        mock_run.return_value = mock_proc

        # Case 1: headless=True -> passes creationflags
        self.controller.headless = True
        self.controller.execute_pipeline(capture_output=True)
        if sys.platform == "win32":
            call_kwargs = mock_run.call_args[1]
            self.assertEqual(call_kwargs.get("creationflags"), subprocess.CREATE_NO_WINDOW)
            self.assertIsNotNone(call_kwargs.get("startupinfo"))

        # Case 2: headless=False -> visible mode, no creationflags or SW_HIDE
        mock_run.reset_mock()
        self.controller.headless = False
        self.controller.execute_pipeline(capture_output=False)
        call_kwargs = mock_run.call_args[1]
        self.assertNotIn("creationflags", call_kwargs)
        self.assertNotIn("startupinfo", call_kwargs)

    @patch("subprocess.run")
    def test_step4_subsequent_executions_pass_no_watch(self, mock_run):
        """Verify that after step 4 completes once, subsequent step 4 calls append --no-watch."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        self.assertFalse(self.controller._dashboard_opened)

        # Run pipeline first time
        self.controller.execute_pipeline(capture_output=True)
        self.assertTrue(self.controller._dashboard_opened)

        # Inspect commands from first run
        step4_calls = [call for call in mock_run.call_args_list if any("step4" in str(arg).lower() for arg in call[0][0])]
        self.assertTrue(len(step4_calls) > 0)
        first_step4_cmd = step4_calls[0][0][0]
        self.assertNotIn("--no-watch", first_step4_cmd)

        # Run pipeline second time
        mock_run.reset_mock()
        self.controller.execute_pipeline(capture_output=True)
        step4_calls_2 = [call for call in mock_run.call_args_list if any("step4" in str(arg).lower() for arg in call[0][0])]
        self.assertTrue(len(step4_calls_2) > 0)
        second_step4_cmd = step4_calls_2[0][0][0]
        self.assertIn("--no-watch", second_step4_cmd)


class TestCompleteAutomationControllerLifecycle(unittest.TestCase):
    def setUp(self):
        self.cfg = AutomationConfig(
            mode="test",
            timing=TimingConfig(step0_poll_interval_test_seconds=0.01)
        )
        self.controller = CompleteAutomationController(config=self.cfg, headless=True)

    @patch.object(AntiGravityDetector, "detect")
    def test_run_once_no_detection(self, mock_detect):
        mock_detect.return_value = DetectionResult(is_detected=False, trigger_matched=False)
        code = self.controller.run(once=True)
        self.assertEqual(code, 1)

    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_once_trigger_matched(self, mock_pipeline, mock_detect):
        mock_detect.return_value = DetectionResult(
            is_detected=True,
            trigger_matched=True,
            pending_grill_me_chats=1
        )
        mock_pipeline.return_value = (True, 0, "All steps executed", [])

        code = self.controller.run(once=True)
        self.assertEqual(code, 0)
        mock_pipeline.assert_called_once()

    @patch("time.sleep")
    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_test_mode_once_exits_after_single_trigger_and_pipeline(self, mock_pipeline, mock_detect, mock_sleep):
        """Verify Test Mode with once=True stops and returns code after 1 trigger + pipeline run."""
        mock_detect.return_value = DetectionResult(
            is_detected=True,
            trigger_matched=True,
            pending_grill_me_chats=1
        )
        mock_pipeline.return_value = (True, 0, "Pipeline completed", [])

        with self.assertLogs(self.controller.logger, level="INFO") as log_cm:
            code = self.controller.run(once=True)

        self.assertEqual(code, 0)
        mock_pipeline.assert_called_once()
        self.assertTrue(any(
            "Single-run execution completed (Exit Code: 0). Stopping." in msg
            for msg in log_cm.output
        ))

    @patch("time.sleep")
    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_test_mode_continuous_continues_loop_after_pipeline(self, mock_pipeline, mock_detect, mock_sleep):
        """Verify continuous Test Mode (once=False) continues monitoring after pipeline run until stopped."""
        call_count = 0
        def detect_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return DetectionResult(is_detected=True, trigger_matched=True, pending_grill_me_chats=1)
            elif call_count == 2:
                self.controller.stop()
                return DetectionResult(is_detected=True, trigger_matched=False)
            return DetectionResult(is_detected=False, trigger_matched=False)

        mock_detect.side_effect = detect_side_effect
        mock_pipeline.return_value = (True, 0, "Pipeline completed", [])

        with self.assertLogs(self.controller.logger, level="INFO") as log_cm:
            code = self.controller.run(once=False)

        self.assertEqual(code, 0)
        self.assertEqual(call_count, 2)
        mock_pipeline.assert_called_once()
        self.assertTrue(any(
            "Test Mode: Pipeline cycle completed" in msg
            for msg in log_cm.output
        ))

    @patch("time.sleep")
    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_test_mode_continues_on_step1_exit_code_10(self, mock_pipeline, mock_detect, mock_sleep):
        """Verify continuous Test Mode (once=False) does not halt when Step 1 returns exit code 10."""
        call_count = 0
        def detect_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return DetectionResult(is_detected=True, trigger_matched=True, pending_grill_me_chats=1)
            elif call_count == 2:
                self.controller.stop()
                return DetectionResult(is_detected=True, trigger_matched=False)
            return DetectionResult(is_detected=False, trigger_matched=False)

        mock_detect.side_effect = detect_side_effect
        mock_pipeline.return_value = (True, EXIT_CODE_NO_PENDING_CHATS, "Step 1 reported no pending chats", [])

        with self.assertLogs(self.controller.logger, level="INFO") as log_cm:
            code = self.controller.run(once=False)

        self.assertEqual(code, 0)
        self.assertEqual(call_count, 2)
        mock_pipeline.assert_called_once()
        self.assertTrue(any(
            "Step 1 reported no pending chats (Exit Code 10)" in msg
            for msg in log_cm.output
        ))

    @patch("time.sleep")
    @patch("complete_automation.get_idle_duration_seconds", return_value=120.0)
    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_production_mode_continues_loop_after_pipeline(self, mock_pipeline, mock_detect, mock_idle, mock_sleep):
        """Verify Production Mode does NOT exit after pipeline execution, continuing until manually stopped."""
        prod_cfg = AutomationConfig(
            mode="production",
            timing=TimingConfig(step0_poll_interval_prod_seconds=300.0)
        )
        prod_controller = CompleteAutomationController(config=prod_cfg, headless=True)

        call_count = 0
        def detect_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First check: trigger matched -> executes pipeline
                return DetectionResult(is_detected=True, trigger_matched=True, pending_grill_me_chats=1)
            elif call_count == 2:
                # Second check: proves the loop continued after pipeline run! Stop controller.
                prod_controller.stop()
                return DetectionResult(is_detected=True, trigger_matched=False)
            return DetectionResult(is_detected=False, trigger_matched=False)

        mock_detect.side_effect = detect_side_effect
        mock_pipeline.return_value = (True, 0, "Pipeline completed", [])

        with self.assertLogs(prod_controller.logger, level="INFO") as log_cm:
            code = prod_controller.run(once=False)

        self.assertEqual(code, 0)
        self.assertEqual(call_count, 2)
        mock_pipeline.assert_called_once()
        self.assertTrue(any(
            "Production Mode: Pipeline cycle completed successfully. Continuing continuous autonomous background monitoring until manually stopped by user." in msg
            for msg in log_cm.output
        ))

    def test_stop(self):
        self.controller.stop()
        self.assertTrue(self.controller._stop_requested)

    @patch("time.sleep")
    @patch("complete_automation.get_idle_duration_seconds")
    def test_wait_for_user_idle_pauses_and_resumes(self, mock_idle, mock_sleep):
        """Verify _wait_for_user_idle pauses while idle < 60s and resumes when idle >= 60s."""
        # Returns 10.0 (active), 25.0 (active), 65.0 (idle)
        mock_idle.side_effect = [10.0, 25.0, 65.0]

        with self.assertLogs(self.controller.logger, level="INFO") as log_cm:
            paused = self.controller._wait_for_user_idle(pause_threshold=60.0)

        self.assertTrue(paused)
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertTrue(any("Production automation is PAUSED" in msg for msg in log_cm.output))
        self.assertTrue(any("Production automation is ACTIVE. Resuming normal monitoring" in msg for msg in log_cm.output))

    @patch("time.sleep")
    @patch("complete_automation.get_idle_duration_seconds")
    @patch.object(AntiGravityDetector, "detect")
    @patch.object(CompleteAutomationController, "execute_pipeline")
    def test_run_production_mode_auto_pauses_on_user_activity(self, mock_pipeline, mock_detect, mock_idle, mock_sleep):
        """Verify run() in production mode halts execution while user is active, and proceeds once idle."""
        prod_cfg = AutomationConfig(
            mode="production",
            timing=TimingConfig(user_activity_pause_threshold_seconds=60.0)
        )
        prod_controller = CompleteAutomationController(config=prod_cfg, headless=True)

        idle_sequence = [5.0, 5.0, 75.0]
        mock_idle.side_effect = lambda: idle_sequence.pop(0) if idle_sequence else 80.0
        mock_detect.return_value = DetectionResult(is_detected=True, trigger_matched=True, pending_grill_me_chats=1)
        mock_pipeline.return_value = (True, 0, "Pipeline completed", [])

        with self.assertLogs(prod_controller.logger, level="INFO") as log_cm:
            code = prod_controller.run(once=True)

        self.assertEqual(code, 0)
        mock_pipeline.assert_called_once()
        self.assertTrue(any("Production automation is PAUSED" in msg for msg in log_cm.output))
        self.assertTrue(any("Production automation is ACTIVE" in msg for msg in log_cm.output))


if __name__ == "__main__":
    unittest.main()
