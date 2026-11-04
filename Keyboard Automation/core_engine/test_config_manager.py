#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Single Source of Truth Configuration Subsystem (config_manager.py)
================================================================================
Test Suite: core_engine/test_config_manager.py
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) / Dept 06 (Backend & API Engineering)
"""

import os
import sys
import json
import shutil
import tempfile
import logging
import unittest
from pathlib import Path

# Ensure root directory is in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name == "core_engine" else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from core_engine.config_manager import (
    get_canonical_config_path,
    get_default_runtime_config,
    load_runtime_config,
    save_runtime_config,
    get_effective_poll_interval,
    get_settle_delay,
    get_user_activity_delay,
    get_window_focus_delay,
    get_dom_click_settle_delay,
    get_step4_poll_interval,
    get_keyboard_timing,
    get_step_timing,
    is_step_enabled,
    apply_logging_config,
    DEFAULT_RUNTIME_CONFIG,
)


class TestConfigManager(unittest.TestCase):
    """Unit test suite verifying single source of truth configuration engine."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_cfg_mgr_"))
        self.custom_config_path = self.test_dir / "custom_config.json"

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_01_canonical_config_path_resolution(self):
        """Verify canonical config path resolves correctly and ends in config.json."""
        path = get_canonical_config_path()
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "config.json")
        self.assertTrue("step_9_complete_automation" in str(path) or "Complete Automation" in str(path) or path.is_file())

    def test_02_default_runtime_config_structure(self):
        """Verify default configuration schema meets all Department 06 requirements."""
        cfg = get_default_runtime_config()
        self.assertIn("mode", cfg)
        self.assertIn("timing", cfg)
        self.assertIn("enabled_steps", cfg)
        self.assertIn("antigravity", cfg)
        self.assertIn("logging", cfg)

        self.assertEqual(cfg["mode"], "production")
        self.assertEqual(cfg["timing"]["step0_poll_interval_prod_seconds"], 300.0)
        self.assertEqual(cfg["timing"]["step0_poll_interval_test_seconds"], 10.0)
        self.assertEqual(cfg["timing"]["settle_delay_between_steps_seconds"], 0.8)
        self.assertEqual(cfg["timing"]["step4_user_activity_delay_seconds"], 10.0)
        self.assertEqual(cfg["timing"]["step4_poll_interval_seconds"], 0.1)
        self.assertEqual(cfg["timing"]["step1_window_focus_delay_seconds"], 0.2)
        self.assertEqual(cfg["timing"]["step2_dom_click_settle_delay_seconds"], 0.3)
        self.assertEqual(cfg["timing"]["step3_countdown_seconds"], 3.0)
        self.assertEqual(cfg["timing"]["step3_key_hold_delay_ms"], 50.0)
        self.assertEqual(cfg["timing"]["step3_post_keypress_delay_ms"], 250.0)
        self.assertEqual(cfg["timing"]["step3_inter_question_delay_ms"], 500.0)
        self.assertEqual(cfg["timing"]["step3_round_completion_pause_ms"], 1000.0)

        self.assertTrue(cfg["enabled_steps"]["step1_find_and_focus"])
        self.assertTrue(cfg["enabled_steps"]["step2_gui_chat_select"])
        self.assertTrue(cfg["enabled_steps"]["step3_keyboard_automation"])
        self.assertTrue(cfg["enabled_steps"]["step4_reporting"])

        self.assertTrue(cfg["antigravity"]["require_grill_me"])
        self.assertEqual(cfg["antigravity"]["active_hours"], 12.0)

        self.assertTrue(cfg["logging"]["verbose"])
        self.assertEqual(cfg["logging"]["log_file"], "complete_automation.log")

    def test_03_load_nonexistent_returns_default(self):
        """Verify loading from nonexistent path safely returns complete defaults."""
        non_existent = self.test_dir / "does_not_exist.json"
        cfg = load_runtime_config(non_existent)
        self.assertEqual(cfg["mode"], "production")
        self.assertEqual(cfg["timing"]["step0_poll_interval_prod_seconds"], 300.0)

    def test_04_save_and_reload_atomic(self):
        """Verify saving configuration using atomic replace and reloading."""
        test_cfg = get_default_runtime_config()
        test_cfg["mode"] = "test"
        test_cfg["timing"]["step0_poll_interval_test_seconds"] = 15.0
        test_cfg["antigravity"]["active_hours"] = 6.0
        test_cfg["enabled_steps"]["step2_gui_chat_select"] = False

        saved = save_runtime_config(test_cfg, self.custom_config_path)
        self.assertTrue(saved)
        self.assertTrue(self.custom_config_path.is_file())

        loaded = load_runtime_config(self.custom_config_path)
        self.assertEqual(loaded["mode"], "test")
        self.assertEqual(loaded["timing"]["step0_poll_interval_test_seconds"], 15.0)
        self.assertEqual(loaded["antigravity"]["active_hours"], 6.0)
        self.assertFalse(loaded["enabled_steps"]["step2_gui_chat_select"])
        # Unaltered defaults remain intact
        self.assertEqual(loaded["timing"]["step0_poll_interval_prod_seconds"], 300.0)

    def test_05_effective_poll_interval(self):
        """Verify polling interval changes dynamically based on mode."""
        prod_cfg = {"mode": "production", "timing": {"step0_poll_interval_prod_seconds": 240.0, "step0_poll_interval_test_seconds": 8.0}}
        self.assertEqual(get_effective_poll_interval(prod_cfg), 240.0)

        test_cfg = {"mode": "test", "timing": {"step0_poll_interval_prod_seconds": 240.0, "step0_poll_interval_test_seconds": 8.0}}
        self.assertEqual(get_effective_poll_interval(test_cfg), 8.0)

    def test_06_timing_helpers(self):
        """Verify settle delay and user activity delay helper functions."""
        cfg = {"timing": {"settle_delay_between_steps_seconds": 1.5, "step4_user_activity_delay_seconds": 20.0}}
        self.assertEqual(get_settle_delay(cfg), 1.5)
        self.assertEqual(get_user_activity_delay(cfg), 20.0)

    def test_07_is_step_enabled(self):
        """Verify step enabled check accepts integers and various string formats."""
        cfg = {
            "enabled_steps": {
                "step1_find_and_focus": True,
                "step2_gui_chat_select": False,
                "step3_keyboard_automation": True,
                "step4_reporting": False,
            }
        }
        self.assertTrue(is_step_enabled(1, cfg))
        self.assertFalse(is_step_enabled(2, cfg))
        self.assertTrue(is_step_enabled("step3", cfg))
        self.assertFalse(is_step_enabled("step4_reporting", cfg))

    def test_08_apply_logging_config(self):
        """Verify logging configuration applies level and attaches file handler."""
        test_logger = logging.getLogger("TestCustomLogger")
        cfg = {"logging": {"verbose": False, "log_file": "test_auto.log"}}
        apply_logging_config(cfg, test_logger, step_name="UnitTest")
        self.assertEqual(test_logger.level, logging.WARNING)

        cfg_verbose = {"logging": {"verbose": True, "log_file": "test_auto.log"}}
        apply_logging_config(cfg_verbose, test_logger, step_name="UnitTest")
        self.assertEqual(test_logger.level, logging.INFO)

    def test_09_all_granular_timing_helpers(self):
        """Verify all granular timing helpers return exact values."""
        cfg = {
            "timing": {
                "step0_poll_interval_prod_seconds": 120.0,
                "step0_poll_interval_test_seconds": 5.0,
                "settle_delay_between_steps_seconds": 1.2,
                "step4_user_activity_delay_seconds": 15.0,
                "step4_poll_interval_seconds": 0.05,
                "step1_window_focus_delay_seconds": 0.5,
                "step2_dom_click_settle_delay_seconds": 0.6,
                "step3_countdown_seconds": 2.0,
                "step3_key_hold_delay_ms": 60.0,
                "step3_post_keypress_delay_ms": 300.0,
                "step3_inter_question_delay_ms": 600.0,
                "step3_round_completion_pause_ms": 1500.0,
            }
        }
        self.assertEqual(get_settle_delay(cfg), 1.2)
        self.assertEqual(get_user_activity_delay(cfg), 15.0)
        self.assertEqual(get_window_focus_delay(cfg), 0.5)
        self.assertEqual(get_dom_click_settle_delay(cfg), 0.6)
        self.assertEqual(get_step4_poll_interval(cfg), 0.05)

        kb_timing = get_keyboard_timing(cfg)
        self.assertEqual(kb_timing["countdown"], 2.0)
        self.assertEqual(kb_timing["hold_delay_s"], 0.06)
        self.assertEqual(kb_timing["post_keypress_delay_s"], 0.3)
        self.assertEqual(kb_timing["inter_question_delay_s"], 0.6)
        self.assertEqual(kb_timing["round_completion_pause_s"], 1.5)

        s0 = get_step_timing(0, cfg)
        self.assertEqual(s0["step0_poll_interval_prod_seconds"], 120.0)
        s1 = get_step_timing(1, cfg)
        self.assertEqual(s1["step1_window_focus_delay_seconds"], 0.5)
        s2 = get_step_timing(2, cfg)
        self.assertEqual(s2["step2_dom_click_settle_delay_seconds"], 0.6)
        s3 = get_step_timing(3, cfg)
        self.assertEqual(s3["countdown"], 2.0)
        self.assertEqual(s3["post_keypress_delay_s"], 0.3)
        self.assertEqual(s3["round_completion_pause_s"], 1.5)
        s4 = get_step_timing(4, cfg)
        self.assertEqual(s4["step4_user_activity_delay_seconds"], 15.0)
        s9 = get_step_timing(9, cfg)
        self.assertEqual(s9["settle_delay_between_steps_seconds"], 1.2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
