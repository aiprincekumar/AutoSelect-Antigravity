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


if __name__ == "__main__":
    unittest.main()
