#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Grill Me Keyboard Automation suite.
"""

import sys
import unittest
import importlib.util
from pathlib import Path

# Load grill_me_automation module dynamically
module_path = Path(__file__).resolve().parent.parent / "Keyboard Automation" / "grill_me_automation.py"
spec = importlib.util.spec_from_file_location("grill_me_automation", module_path)
grill_me = importlib.util.module_from_spec(spec)
sys.modules["grill_me_automation"] = grill_me
spec.loader.exec_module(grill_me)


class TestGrillMeAutomation(unittest.TestCase):
    """Test suite for Keyboard Automation components."""

    def test_option_key_mapping(self):
        """Test option string to virtual key conversion."""
        self.assertEqual(grill_me.get_option_vk("1"), 0x31)
        self.assertEqual(grill_me.get_option_vk("2"), 0x32)
        self.assertEqual(grill_me.get_option_vk("9"), 0x39)
        self.assertEqual(grill_me.get_option_vk("0"), 0x30)
        self.assertEqual(grill_me.get_option_vk("a"), ord("A"))
        self.assertEqual(grill_me.get_option_vk("unknown"), 0x31)

    def test_active_window_detection(self):
        """Test foreground window title retrieval."""
        title = grill_me.get_active_window_title()
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) > 0)

    def test_dry_run_execution(self):
        """Test end-to-end execution in dry-run mode."""
        automator = grill_me.GrillMeAutomator(
            engine="ctypes",
            step_delay=0.01,
            hold_delay=0.01,
            option="1",
            dry_run=True,
        )
        self.assertEqual(automator.engine, "ctypes")
        self.assertTrue(automator.dry_run)
        success = automator.execute()
        self.assertTrue(success)

    def test_dry_run_with_skips(self):
        """Test dry-run with skip_ctrl_l and skip_enter options."""
        automator = grill_me.GrillMeAutomator(
            engine="ctypes",
            step_delay=0.01,
            hold_delay=0.01,
            option="2",
            skip_ctrl_l=True,
            skip_enter=True,
            dry_run=True,
        )
        self.assertTrue(automator.skip_ctrl_l)
        self.assertTrue(automator.skip_enter)
        success = automator.execute()
        self.assertTrue(success)

    def test_countdown_zero(self):
        """Test that countdown with 0 seconds completes without error."""
        automator = grill_me.GrillMeAutomator(dry_run=True)
        # Should not throw any exception
        automator.run_countdown(seconds=0)

    def test_window_info_structure(self):
        """Test structure of get_window_info dictionary."""
        info = grill_me.get_window_info(0)
        self.assertIsInstance(info, dict)
        self.assertIn("hwnd", info)
        self.assertIn("title", info)
        self.assertIn("exists", info)
        self.assertIn("visible", info)
        self.assertIn("minimized", info)
        self.assertIn("maximized", info)
        self.assertIn("rect", info)
        self.assertIn("width", info)
        self.assertIn("height", info)
        self.assertFalse(info["exists"])

    def test_find_windows_by_title_empty_or_absent(self):
        """Test search for non-existent window title returns empty list."""
        matches = grill_me.find_windows_by_title(["__definitely_non_existent_window_keyword_99999__"])
        self.assertIsInstance(matches, list)
        self.assertEqual(len(matches), 0)

    def test_select_target_window_nonexistent(self):
        """Test select_target_window returns None when no matches exist."""
        match = grill_me.select_target_window("__definitely_non_existent_window_keyword_99999__")
        self.assertIsNone(match)

    def test_ensure_window_on_screen_invalid(self):
        """Test ensure_window_on_screen returns False on invalid HWND."""
        result = grill_me.ensure_window_on_screen(0)
        self.assertFalse(result)

    def test_automator_auto_focus_maximize_configuration(self):
        """Test GrillMeAutomator configuration parameters for auto-targeting."""
        automator = grill_me.GrillMeAutomator(
            target_window="TestWindow",
            auto_focus=True,
            auto_maximize=True,
            settle_delay=0.1,
            dry_run=True,
        )
        self.assertEqual(automator.target_window, "TestWindow")
        self.assertTrue(automator.auto_focus)
        self.assertTrue(automator.auto_maximize)
        self.assertEqual(automator.settle_delay, 0.1)

    def test_automator_disabled_auto_focus_maximize(self):
        """Test prepare_target_window when auto-focus and auto-maximize are disabled."""
        automator = grill_me.GrillMeAutomator(
            auto_focus=False,
            auto_maximize=False,
            dry_run=True,
        )
        self.assertFalse(automator.auto_focus)
        self.assertFalse(automator.auto_maximize)
        res = automator.prepare_target_window()
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
