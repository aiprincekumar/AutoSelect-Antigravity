#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Complete Automation Master Controller & Step Orchestrator
========================================================================
Test Suite: Complete Automation/test_complete_automation.py
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

    def test_stop(self):
        self.controller.stop()
        self.assertTrue(self.controller._stop_requested)


if __name__ == "__main__":
    unittest.main()
