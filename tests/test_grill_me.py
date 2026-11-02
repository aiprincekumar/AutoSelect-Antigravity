#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Grill Me Keyboard Automation suite.
Targeting Antigravity 2.0 Harness, Win32 window management, and input pipeline.
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
        self.assertIn("class", info)
        self.assertIn("process_name", info)
        self.assertIn("pid", info)
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

    def test_multi_keyword_target_parsing(self):
        """Test parsing and searching via multi-keyword strings."""
        automator = grill_me.GrillMeAutomator(
            target_window="Antigravity 2.0,Harness,AutoSelect-Commander",
            dry_run=True,
        )
        self.assertIn("Antigravity 2.0", automator.target_window)
        self.assertIn("Harness", automator.target_window)

    def test_candidate_enumeration_type(self):
        """Test candidate window enumeration returns list of structured dicts."""
        candidates = grill_me.find_all_candidate_windows()
        self.assertIsInstance(candidates, list)
        for c in candidates:
            self.assertIn("hwnd", c)
            self.assertIn("title", c)
            self.assertIn("class", c)
            self.assertIn("process_name", c)

    def test_browser_disqualification_and_antigravity_priority(self):
        """
        Verify that web browsers (Chrome, Edge) are strictly disqualified even
        with window class Chrome_WidgetWin_1, and Antigravity.exe is prioritized.
        """
        mock_candidates = [
            {
                "hwnd": 1001,
                "title": "Google Search - Google Chrome",
                "class": "Chrome_WidgetWin_1",
                "pid": 4001,
                "process_name": "chrome.exe",
                "process_exe": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            },
            {
                "hwnd": 1002,
                "title": "Microsoft Edge Browser",
                "class": "Chrome_WidgetWin_1",
                "pid": 4002,
                "process_name": "msedge.exe",
                "process_exe": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            },
            {
                "hwnd": 2001,
                "title": "AutoSelect-Commander Workspace - Antigravity",
                "class": "Chrome_WidgetWin_1",
                "pid": 5001,
                "process_name": "Antigravity.exe",
                "process_exe": "C:\\Users\\Atul Verma\\AppData\\Local\\Programs\\antigravity\\Antigravity.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            },
        ]

        original_find = grill_me.find_all_candidate_windows
        try:
            grill_me.find_all_candidate_windows = lambda: mock_candidates
            selected = grill_me.select_target_window()
            self.assertIsNotNone(selected)
            self.assertEqual(selected[0], 2001)
            self.assertIn("Antigravity", selected[1])
        finally:
            grill_me.find_all_candidate_windows = original_find

    def test_browsers_strictly_rejected_when_no_antigravity(self):
        """
        Verify that if only Chrome and Edge are running, select_target_window returns None
        and NEVER selects the browser.
        """
        mock_candidates = [
            {
                "hwnd": 1001,
                "title": "Google Search - AutoSelect-Commander",
                "class": "Chrome_WidgetWin_1",
                "pid": 4001,
                "process_name": "chrome.exe",
                "process_exe": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            },
            {
                "hwnd": 1002,
                "title": "Microsoft Edge - AutoSelect-Commander",
                "class": "Chrome_WidgetWin_1",
                "pid": 4002,
                "process_name": "msedge.exe",
                "process_exe": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            },
        ]

        original_find = grill_me.find_all_candidate_windows
        try:
            grill_me.find_all_candidate_windows = lambda: mock_candidates
            selected = grill_me.select_target_window()
            self.assertIsNone(selected)
        finally:
            grill_me.find_all_candidate_windows = original_find

    def test_explicit_browser_target_allowed(self):
        """
        Verify that if the user explicitly specifies 'chrome' in CLI target,
        it is permitted through the filter.
        """
        mock_candidates = [
            {
                "hwnd": 1001,
                "title": "Google Chrome Window",
                "class": "Chrome_WidgetWin_1",
                "pid": 4001,
                "process_name": "chrome.exe",
                "process_exe": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
            }
        ]

        original_find = grill_me.find_all_candidate_windows
        try:
            grill_me.find_all_candidate_windows = lambda: mock_candidates
            selected = grill_me.select_target_window("chrome")
            self.assertIsNotNone(selected)
            self.assertEqual(selected[0], 1001)
        finally:
            grill_me.find_all_candidate_windows = original_find

    def test_automator_aborts_on_browser_foreground(self):
        """
        Verify that if the foreground window is chrome.exe, GrillMeAutomator
        aborts execution to protect the user's browser.
        """
        original_proc_info = grill_me.get_process_info_for_hwnd
        try:
            grill_me.get_process_info_for_hwnd = lambda hwnd: (4001, "chrome.exe", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            automator = grill_me.GrillMeAutomator(
                engine="ctypes",
                auto_focus=False,
                auto_maximize=False,
                dry_run=False,
            )
            success = automator.execute()
            self.assertFalse(success)
        finally:
            grill_me.get_process_info_for_hwnd = original_proc_info

    # ------------------------------------------------------------------------
    # Direct Modular Sub-Package Tests (Industry-Standard Architecture)
    # ------------------------------------------------------------------------
    def test_modular_package_direct_import(self):
        """Test importing the modular package keyboard_automation directly."""
        pkg_path = Path(__file__).resolve().parent.parent / "Keyboard Automation"
        if str(pkg_path) not in sys.path:
            sys.path.insert(0, str(pkg_path))

        import keyboard_automation as ka
        self.assertTrue(hasattr(ka, "GrillMeAutomator"))
        self.assertTrue(hasattr(ka, "select_target_window"))
        self.assertTrue(hasattr(ka, "get_window_info"))
        self.assertTrue(hasattr(ka, "send_key_combo"))
        self.assertTrue(hasattr(ka, "DISQUALIFIED_BROWSER_PROCS"))
        self.assertIn("chrome.exe", ka.DISQUALIFIED_BROWSER_PROCS)

    def test_modular_constants_integrity(self):
        """Test constants module definitions and completeness."""
        from keyboard_automation import constants as c
        self.assertEqual(c.VK_SHIFT, 0x10)
        self.assertEqual(c.VK_CONTROL, 0x11)
        self.assertEqual(c.VK_RETURN, 0x0D)
        self.assertEqual(c.VK_TAB, 0x09)
        self.assertEqual(c.VK_L, 0x4C)
        self.assertIn("msedge.exe", c.DISQUALIFIED_BROWSER_PROCS)
        self.assertIn("powershell.exe", c.BLACK_LISTED_SHELL_PROCS)

    def test_modular_input_injector(self):
        """Test input_injector option key resolution directly."""
        from keyboard_automation import input_injector as inj
        self.assertEqual(inj.get_option_vk("1"), 0x31)
        self.assertEqual(inj.get_option_vk("5"), 0x35)
        self.assertEqual(inj.get_option_vk("Z"), ord("Z"))

    def test_modular_window_manager_invalid_hwnd(self):
        """Test window_manager get_window_info with invalid handle."""
        from keyboard_automation import window_manager as wm
        info = wm.get_window_info(0)
        self.assertIsInstance(info, dict)
        self.assertFalse(info["exists"])
        self.assertEqual(info["hwnd"], 0)

    def test_modular_automator_instantiation(self):
        """Test direct instantiation of GrillMeAutomator from automator module."""
        from keyboard_automation.automator import GrillMeAutomator
        automator = GrillMeAutomator(
            step_delay=0.1,
            hold_delay=0.02,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )
        self.assertTrue(automator.dry_run)
        self.assertFalse(automator.auto_focus)
        self.assertEqual(automator.step_delay, 0.1)

    def test_modular_cli_argument_parser(self):
        """Test CLI argument parser from cli module."""
        from keyboard_automation.cli import parse_arguments
        # Test with dummy args
        test_args = ["-t", "Antigravity", "-o", "2", "--dry-run", "--no-countdown"]
        original_argv = sys.argv
        try:
            sys.argv = ["grill_me_automation.py"] + test_args
            parsed = parse_arguments()
            self.assertEqual(parsed.target_window, "Antigravity")
            self.assertEqual(parsed.option, "2")
            self.assertTrue(parsed.dry_run)
            self.assertTrue(parsed.no_countdown)
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
