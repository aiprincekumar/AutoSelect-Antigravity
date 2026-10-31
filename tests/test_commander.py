#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for AutoSelect-Commander.
"""

import math
import os
import sys
import unittest
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auto_commander import (
    Config,
    Point,
    Rect,
    DetectionResult,
    WindowsOcrDetector,
    UIAutomationDetector,
    VisionDetector,
    MultiEngineDetector,
    DualModeDetector,
    FloatingHUD,
    TerminalDashboard,
    MouseController,
    AntigravityWindowManager,
    AutoCommanderEngine,
    WINSDK_OCR_AVAILABLE,
)
import auto_commander.platform.win32_window as win32_mod


class TestAutoCommander(unittest.TestCase):
    def test_config_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.countdown_seconds, 10)
        self.assertEqual(cfg.check_interval_ms, 1000)
        self.assertEqual(cfg.mouse_interruption_threshold_px, 15)
        self.assertEqual(cfg.smooth_glide_duration_s, 0.8)
        self.assertTrue(cfg.failsafe_enabled)
        self.assertTrue(cfg.floating_hud_enabled)
        self.assertTrue(cfg.ocr_enabled)
        self.assertEqual(cfg.window_title_filter, "")
        self.assertIn("(Recommended)", cfg.target_keywords)
        self.assertIn("Submit", cfg.submit_keywords)
        self.assertIn("पुष्टि करें", cfg.submit_keywords)

    def test_config_load_from_json(self):
        cfg = Config.load("config.json")
        self.assertEqual(cfg.countdown_seconds, 10)
        self.assertTrue(cfg.floating_hud_enabled)
        self.assertTrue(cfg.ocr_enabled)
        self.assertIn("Recommended", cfg.target_keywords)
        self.assertIn("Submit", cfg.submit_keywords)

    def test_detection_result_center(self):
        result = DetectionResult(
            x=100,
            y=200,
            width=80,
            height=40,
            confidence=0.95,
            source="Test",
            label="(Recommended)",
        )
        self.assertEqual(result.center, (140, 220))

    def test_failsafe_euclidean_distance(self):
        start_x, start_y = 500, 500
        threshold = 15

        # Minor drift (within threshold) -> No fail-safe trigger
        drift_x, drift_y = 508, 506
        dist = math.hypot(drift_x - start_x, drift_y - start_y)
        self.assertLess(dist, threshold)

        # Human intentional movement -> Triggers fail-safe (> 15px)
        human_x, human_y = 515, 515
        dist_human = math.hypot(human_x - start_x, human_y - start_y)
        self.assertGreater(dist_human, threshold)

    def test_antigravity_window_manager(self):
        # Verify process checking returns a boolean without throwing
        is_proc = AntigravityWindowManager.is_process_running()
        self.assertIsInstance(is_proc, bool)

        # Window handle lookup returns None or an int
        hwnd = AntigravityWindowManager.find_antigravity_window()
        self.assertTrue(hwnd is None or isinstance(hwnd, int))

        # Safe null handle checks
        self.assertFalse(AntigravityWindowManager.is_minimized(0))
        self.assertFalse(AntigravityWindowManager.is_foreground(0))
        self.assertFalse(AntigravityWindowManager.bring_to_foreground(0))

        # Orchestrated check returns valid 3-tuple
        is_ready, msg, win_hwnd = AntigravityWindowManager.check_and_foreground()
        self.assertIsInstance(is_ready, bool)
        self.assertIsInstance(msg, str)
        self.assertTrue(win_hwnd is None or isinstance(win_hwnd, int))

    def test_mouse_controller_firm_click(self):
        mouse_ctrl = MouseController(glide_duration=0.8, failsafe_enabled=True)
        self.assertTrue(hasattr(mouse_ctrl, "firm_click"))
        self.assertTrue(callable(mouse_ctrl.firm_click))

    def test_detect_submit_button_inference(self):
        cfg = Config()
        multi = MultiEngineDetector(cfg)
        opt = DetectionResult(
            x=150,
            y=250,
            width=400,
            height=50,
            confidence=0.99,
            source="UIAutomation",
            label="Option 1: (Recommended)",
        )
        submit_res = multi.detect_submit_button(option_result=opt)
        self.assertIsNotNone(submit_res)
        self.assertGreater(submit_res.y, opt.y)
        self.assertEqual(submit_res.label, "Submit / पुष्टि करें")

    def test_ocr_detector_initialization(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        self.assertEqual(detector.is_available(), WINSDK_OCR_AVAILABLE)

    def test_ocr_detector_scan_image(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        test_img = Image.new("RGB", (500, 100), color=(30, 30, 46))
        draw = ImageDraw.Draw(test_img)
        draw.text((40, 30), "Option 1: (Recommended) GitHub Commit Push", fill=(166, 227, 161))

        match = detector.scan_image(test_img, offset_x=100, offset_y=200)
        self.assertIsNotNone(match)
        self.assertIn("WindowsOcr", match.source)
        self.assertGreater(match.x, 100)
        self.assertGreater(match.y, 200)

    def test_vision_detector_templates(self):
        detector = VisionDetector(templates_dir="assets/templates")
        self.assertTrue(os.path.exists("assets/templates"))
        self.assertGreaterEqual(len(detector.templates), 1)

    def test_multi_engine_detector_initialization(self):
        cfg = Config()
        multi = MultiEngineDetector(cfg)
        self.assertIsNotNone(multi.ocr_detector)
        self.assertIsNotNone(multi.uia_detector)
        self.assertIsNotNone(multi.vision_detector)

    def test_dual_mode_detector_alias(self):
        self.assertIs(DualModeDetector, MultiEngineDetector)

    def test_models_point_and_rect(self):
        p1 = Point(100, 200)
        p2 = Point(130, 240)
        self.assertEqual(p1.distance_to(p2), 50.0)
        self.assertEqual(p1.as_tuple(), (100, 200))

        rect = Rect(50, 100, 200, 150)
        self.assertEqual(rect.left, 50)
        self.assertEqual(rect.top, 100)
        self.assertEqual(rect.right, 250)
        self.assertEqual(rect.bottom, 250)
        self.assertEqual(rect.center, (150, 175))
        self.assertTrue(rect.contains(100, 150))
        self.assertFalse(rect.contains(300, 150))

    def test_self_exclusion_blacklist(self):
        # Verify blacklisted process set contains critical shell/system tools
        self.assertIn("cmd.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("powershell.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("explorer.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("python.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)

        # Current process PID must be in self process family
        pids = AntigravityWindowManager.get_own_process_family_pids()
        self.assertIn(os.getpid(), pids)

    def test_validate_click_target_boundary(self):
        # Click target inside valid dummy rect
        valid, _ = AntigravityWindowManager.validate_click_target(500, 500, target_hwnd=None)
        self.assertIsInstance(valid, bool)

    def test_modular_package_imports_parity(self):
        from auto_commander.config import Config as Cfg
        from auto_commander.models import Point as Pt, Rect as Rc
        from auto_commander.platform.win32_window import AntigravityWindowManager as AWM
        from auto_commander.platform.mouse_ctrl import MouseController as MC
        from auto_commander.detectors.ocr_detector import WindowsOcrDetector as WOD
        from auto_commander.gui.hud import FloatingHUD as FH
        from auto_commander.gui.dashboard import TerminalDashboard as TD
        from auto_commander.core.engine import AutoCommanderEngine as ACE
        from auto_commander.cli import main as cli_main

        self.assertIs(Cfg, Config)
        self.assertIs(Pt, Point)
        self.assertIs(Rc, Rect)
        self.assertIs(AWM, AntigravityWindowManager)
        self.assertIs(MC, MouseController)
        self.assertIs(WOD, WindowsOcrDetector)
        self.assertIs(FH, FloatingHUD)
        self.assertIs(TD, TerminalDashboard)
        self.assertIs(ACE, AutoCommanderEngine)
        self.assertTrue(callable(cli_main))

    def test_floating_hud_initialization_and_lifecycle(self):
        hud = FloatingHUD(alpha=0.92)
        self.assertFalse(hud.is_visible)
        self.assertIsNone(hud.root)
        self.assertEqual(hud.alpha, 0.92)
        self.assertEqual(hud.total_seconds, 10.0)
        # Verify safe close when uninitialized
        hud.close()
        self.assertFalse(hud.is_visible)


if __name__ == "__main__":
    unittest.main()
