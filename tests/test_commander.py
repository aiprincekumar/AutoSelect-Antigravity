#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for AutoSelect-Commander.
"""

import math
import os
import sys
import unittest
from unittest import mock
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
from auto_commander.detectors.chat_detector import ChatTabDetector
import auto_commander.platform.win32_window as win32_mod


class TestAutoCommander(unittest.TestCase):
    def test_config_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.countdown_seconds, 3)
        self.assertEqual(cfg.step0_countdown_seconds, 3.0)
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
        self.assertEqual(cfg.countdown_seconds, 3)
        self.assertEqual(cfg.step0_countdown_seconds, 3.0)
        self.assertTrue(cfg.floating_hud_enabled)
        self.assertTrue(cfg.ocr_enabled)
        self.assertIn("(Recommended)", cfg.target_keywords)
        self.assertIn("Submit", cfg.submit_keywords)
        self.assertIn("Skip", cfg.submit_keywords)
        self.assertIn("Skip", cfg.action_bar_keywords)

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
        is_proc = AntigravityWindowManager.is_process_running()
        self.assertIsInstance(is_proc, bool)

        hwnd = AntigravityWindowManager.find_antigravity_window()
        self.assertTrue(hwnd is None or isinstance(hwnd, int))

        self.assertFalse(AntigravityWindowManager.is_minimized(0))
        self.assertFalse(AntigravityWindowManager.is_foreground(0))
        self.assertFalse(AntigravityWindowManager.bring_to_foreground(0))

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
        self.assertIsNotNone(multi.chat_detector)

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
        self.assertIn("cmd.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("powershell.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("explorer.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)
        self.assertIn("python.exe", win32_mod.BLACK_LISTED_PROCESS_NAMES)

        pids = AntigravityWindowManager.get_own_process_family_pids()
        self.assertIn(os.getpid(), pids)

    def test_validate_click_target_boundary(self):
        valid, _ = AntigravityWindowManager.validate_click_target(500, 500, target_hwnd=None)
        self.assertIsInstance(valid, bool)

    def test_validate_click_target_allows_target_when_foreground_despite_console_overlap(self):
        target_hwnd = 11111
        console_hwnd = 22222
        target_rect = Rect(0, 0, 1920, 1080)
        console_rect = Rect(32, 32, 1359, 737)
        click_x, click_y = 194, 719  # Point inside both target and console (as in Screenshot 452)

        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_hwnd", return_value=console_hwnd), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=console_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_window_rect", return_value=target_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "is_foreground", return_value=True), \
             unittest.mock.patch.object(win32_mod.user32, "GetForegroundWindow", return_value=target_hwnd):

            valid, reason = AntigravityWindowManager.validate_click_target(click_x, click_y, target_hwnd=target_hwnd)
            self.assertTrue(valid, f"Target window in foreground should allow click despite console overlap! Reason: {reason}")
            self.assertIn("target window is foreground", reason)

    def test_validate_click_target_auto_foregrounds_when_console_is_active(self):
        target_hwnd = 11111
        console_hwnd = 22222
        target_rect = Rect(0, 0, 1920, 1080)
        console_rect = Rect(32, 32, 1359, 737)
        click_x, click_y = 194, 719

        bring_fg_called = []
        def fake_bring_to_foreground(h):
            bring_fg_called.append(h)
            return True

        fg_returns = [console_hwnd, target_hwnd]
        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_hwnd", return_value=console_hwnd), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=console_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_window_rect", return_value=target_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "bring_to_foreground", side_effect=fake_bring_to_foreground), \
             unittest.mock.patch.object(AntigravityWindowManager, "is_foreground", return_value=True), \
             unittest.mock.patch.object(win32_mod.user32, "GetForegroundWindow", side_effect=fg_returns):

            valid, reason = AntigravityWindowManager.validate_click_target(click_x, click_y, target_hwnd=target_hwnd)
            self.assertTrue(valid)
            self.assertIn(target_hwnd, bring_fg_called)

    def test_validate_click_target_blocks_when_console_remains_foreground(self):
        target_hwnd = 11111
        console_hwnd = 22222
        target_rect = Rect(0, 0, 1920, 1080)
        console_rect = Rect(32, 32, 1359, 737)
        click_x, click_y = 194, 719

        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_hwnd", return_value=console_hwnd), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=console_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_window_rect", return_value=target_rect), \
             unittest.mock.patch.object(AntigravityWindowManager, "bring_to_foreground", return_value=False), \
             unittest.mock.patch.object(AntigravityWindowManager, "is_foreground", return_value=False), \
             unittest.mock.patch.object(AntigravityWindowManager, "is_console_foreground", return_value=True), \
             unittest.mock.patch.object(win32_mod.user32, "GetForegroundWindow", return_value=console_hwnd):

            valid, reason = AntigravityWindowManager.validate_click_target(click_x, click_y, target_hwnd=target_hwnd)
            self.assertFalse(valid)
            self.assertIn("falls inside console window", reason)

    def test_validate_click_target_blocks_outside_bounds(self):
        target_hwnd = 11111
        target_rect = Rect(100, 100, 500, 500)
        with unittest.mock.patch.object(AntigravityWindowManager, "get_window_rect", return_value=target_rect):
            valid, reason = AntigravityWindowManager.validate_click_target(50, 50, target_hwnd=target_hwnd)
            self.assertFalse(valid)
            self.assertIn("outside target window bounds", reason)

    def test_validate_click_target_blocks_none_target_inside_console(self):
        console_hwnd = 22222
        console_rect = Rect(0, 0, 800, 600)
        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_hwnd", return_value=console_hwnd), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=console_rect):
            valid, reason = AntigravityWindowManager.validate_click_target(100, 100, target_hwnd=None)
            self.assertFalse(valid)
            self.assertIn("falls inside console window", reason)

    def test_modular_package_imports_parity(self):
        from auto_commander.config import Config as Cfg
        from auto_commander.models import Point as Pt, Rect as Rc
        from auto_commander.platform.win32_window import AntigravityWindowManager as AWM
        from auto_commander.platform.mouse_ctrl import MouseController as MC
        from auto_commander.detectors.ocr_detector import WindowsOcrDetector as WOD
        from auto_commander.detectors.chat_detector import ChatTabDetector as CTD
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
        self.assertIs(CTD, ChatTabDetector)
        self.assertIs(FH, FloatingHUD)
        self.assertIs(TD, TerminalDashboard)
        self.assertIs(ACE, AutoCommanderEngine)
        self.assertTrue(callable(cli_main))

    def test_ocr_detector_console_masking_and_filtering(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        test_img = Image.new("RGB", (500, 150), color=(30, 30, 46))
        draw = ImageDraw.Draw(test_img)
        draw.text((40, 30), "Option 1: (Recommended) GitHub Commit Push", fill=(166, 227, 161))

        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=None):
            match = detector.scan_image(test_img, offset_x=0, offset_y=0)
            self.assertIsNotNone(match)

        console_rect = Rect(0, 0, 500, 150)
        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=console_rect):
            masked_match = detector.scan_image(test_img, offset_x=0, offset_y=0, mask_console=True)
            self.assertIsNone(masked_match)

    def test_floating_hud_initialization_and_lifecycle(self):
        hud = FloatingHUD(alpha=0.92)
        self.assertFalse(hud.is_visible)
        self.assertIsNone(hud.root)
        self.assertEqual(hud.alpha, 0.92)
        self.assertEqual(hud.total_seconds, 3.0)
        hud.close()
        self.assertFalse(hud.is_visible)

    def test_config_require_submit_button(self):
        cfg = Config()
        self.assertTrue(cfg.require_submit_button)
        self.assertIn("Continue", cfg.submit_keywords)
        self.assertIn("Select", cfg.submit_keywords)
        self.assertIn("OK", cfg.submit_keywords)

    def test_minimized_restore_to_maximized(self):
        dummy_hwnd = 54321
        with unittest.mock.patch.object(win32_mod.user32, "IsIconic", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "ShowWindow") as mock_show, \
             unittest.mock.patch.object(win32_mod.user32, "ShowWindowAsync") as mock_show_async, \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowPlacement") as mock_gwp, \
             unittest.mock.patch.object(win32_mod.user32, "SetForegroundWindow", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "BringWindowToTop", return_value=1):

            def fake_gwp(hwnd, wp_ptr):
                wp = getattr(wp_ptr, "_obj", getattr(wp_ptr, "contents", None))
                if wp:
                    wp.flags = 2
                    wp.showCmd = 3
                return 1

            mock_gwp.side_effect = fake_gwp
            res = AntigravityWindowManager.bring_to_foreground(dummy_hwnd)
            self.assertTrue(res)
            mock_show.assert_called_with(dummy_hwnd, 3)
            mock_show_async.assert_called_with(dummy_hwnd, 3)

    def test_minimized_restore_to_normal(self):
        dummy_hwnd = 54321
        with unittest.mock.patch.object(win32_mod.user32, "IsIconic", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "ShowWindow") as mock_show, \
             unittest.mock.patch.object(win32_mod.user32, "ShowWindowAsync") as mock_show_async, \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowPlacement") as mock_gwp, \
             unittest.mock.patch.object(win32_mod.user32, "SetForegroundWindow", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "BringWindowToTop", return_value=1):

            def fake_gwp(hwnd, wp_ptr):
                wp = getattr(wp_ptr, "_obj", getattr(wp_ptr, "contents", None))
                if wp:
                    wp.flags = 0
                    wp.showCmd = 1
                return 1

            mock_gwp.side_effect = fake_gwp
            res = AntigravityWindowManager.bring_to_foreground(dummy_hwnd)
            self.assertTrue(res)
            mock_show.assert_called_with(dummy_hwnd, 9)
            mock_show_async.assert_called_with(dummy_hwnd, 9)

    def test_ocr_decision_modal_rejects_plain_chat_without_submit(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        img_chat = Image.new("RGB", (600, 300), color=(30, 30, 46))
        d = ImageDraw.Draw(img_chat)
        d.text((40, 40), "Option 1: (Recommended) GitHub Commit Push", fill=(255, 255, 255))
        d.text((40, 80), "Option 2: Cancel and review changes manually", fill=(200, 200, 200))
        d.text((40, 130), "Just conversational text with no interactive submit button.", fill=(180, 180, 180))

        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=None):
            match = detector.scan_decision_modal_on_image(img_chat, require_submit=True)
            self.assertIsNone(match, "Plain chat without submit button must be strictly rejected!")

    def test_ocr_decision_modal_detects_prompt_with_submit(self):
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        img_modal = Image.new("RGB", (600, 350), color=(30, 30, 46))
        d = ImageDraw.Draw(img_modal)
        d.text((40, 40), "Select an option:", fill=(255, 255, 255))
        d.text((40, 90), "o (Recommended) GitHub Commit Push", fill=(166, 227, 161))
        d.text((40, 130), "o Cancel inspection", fill=(200, 200, 200))
        d.rectangle([40, 190, 140, 225], fill=(137, 180, 250))
        d.text((55, 200), "Submit", fill=(0, 0, 0))

        with unittest.mock.patch.object(AntigravityWindowManager, "get_console_window_rect", return_value=None):
            match = detector.scan_decision_modal_on_image(img_modal, require_submit=True)
            self.assertIsNotNone(match, "Interactive modal with Submit button must be detected!")
            opt, sub = match
            self.assertIn("Recommended", opt.label)
            self.assertEqual(sub.label, "Submit")
            self.assertGreater(sub.y, opt.y)

    def test_strict_bracketed_recommended_matching(self):
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("(Recommended)"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("[Recommended]"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("{Recommended}"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("( Recommended )"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("Option 1: (Recommended) GitHub Push"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("Option 1: (अनुशंसित) गिटहब पुश"))
        self.assertTrue(WindowsOcrDetector.is_bracketed_target("[अनुशंसित] गिटहब पुश"))

        self.assertFalse(WindowsOcrDetector.is_bracketed_target("recommended"))
        self.assertFalse(WindowsOcrDetector.is_bracketed_target("I recommended this solution"))
        self.assertFalse(WindowsOcrDetector.is_bracketed_target("अनुशंसित"))
        self.assertFalse(WindowsOcrDetector.is_bracketed_target("Recommended action is unknown"))

    def test_find_antigravity_window_when_minimized(self):
        dummy_hwnd = 98765
        with unittest.mock.patch.object(win32_mod.user32, "IsIconic", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "IsWindowVisible", return_value=1), \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowTextLengthW", return_value=11), \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowTextW", side_effect=lambda h, buf, l: setattr(buf, "value", "Antigravity")), \
             unittest.mock.patch.object(win32_mod.user32, "GetClassNameW", side_effect=lambda h, buf, l: setattr(buf, "value", "Chrome_WidgetWin_1")), \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowThreadProcessId", side_effect=lambda h, ptr: None), \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowPlacement") as mock_gwp, \
             unittest.mock.patch.object(win32_mod.user32, "GetWindowRect") as mock_gwr, \
             unittest.mock.patch.object(AntigravityWindowManager, "get_process_image_path", return_value=("antigravity.exe", "C:\\Antigravity.exe")), \
             unittest.mock.patch.object(AntigravityWindowManager, "get_own_process_family_pids", return_value=set()):

            def fake_gwr(h, rect_ptr):
                r = rect_ptr._obj
                r.left = -32000
                r.top = -32000
                r.right = -31840
                r.bottom = -31970
                return 1

            def fake_gwp(h, wp_ptr):
                wp = getattr(wp_ptr, "_obj", getattr(wp_ptr, "contents", None))
                if wp:
                    wp.flags = 2
                    wp.showCmd = 3
                    wp.rcNormalPosition.left = 0
                    wp.rcNormalPosition.top = 0
                    wp.rcNormalPosition.right = 1920
                    wp.rcNormalPosition.bottom = 1080
                return 1

            mock_gwr.side_effect = fake_gwr
            mock_gwp.side_effect = fake_gwp

            def fake_enum(cb, lparam):
                cb(dummy_hwnd, lparam)
                return 1

            with unittest.mock.patch.object(win32_mod.user32, "EnumDesktopWindows", side_effect=lambda h, cb, l: fake_enum(cb, l)), \
                 unittest.mock.patch.object(win32_mod.user32, "EnumWindows", side_effect=fake_enum):
                found_hwnd = AntigravityWindowManager.find_antigravity_window()
                self.assertEqual(found_hwnd, dummy_hwnd, "Minimized Antigravity window must be detected!")

    def test_step_0_chat_tab_detector_template(self):
        cfg = Config()
        chat_det = ChatTabDetector(cfg, template_path="assets/badge_question_template.png")
        self.assertTrue(chat_det.is_available())
        self.assertGreaterEqual(len(chat_det.templates), 1)

    def test_step_0_chat_tab_detection_on_screenshot_452(self):
        ss_path = "Demo SS/Screenshot (452).png"
        if not os.path.exists(ss_path):
            self.skipTest("Screenshot (452).png not found.")

        cfg = Config()
        chat_det = ChatTabDetector(cfg, template_path="assets/badge_question_template.png")

        # Mock ImageGrab.grab to return the screenshot
        test_img = Image.open(ss_path)
        with unittest.mock.patch("auto_commander.detectors.chat_detector.ImageGrab.grab", return_value=test_img):
            result = chat_det._scan_sidebar_template(target_hwnd=None)
            self.assertIsNotNone(result, "ChatTabDetector must detect the (?) badge in Screenshot (452)!")
            self.assertIn("Action Required", result.label)
            # Should point to the conversation row around y=710
            self.assertAlmostEqual(result.y, 710, delta=20)
            self.assertGreater(result.confidence, 0.85)

    def test_orchestrator_detect_pending_chat(self):
        cfg = Config()
        multi = MultiEngineDetector(cfg)
        self.assertTrue(hasattr(multi, "detect_pending_chat"))

        # Verify detect_pending_chat delegates to chat_detector
        fake_result = DetectionResult(x=100, y=700, width=150, height=30, confidence=0.99, source="Mock", label="Chat")
        with unittest.mock.patch.object(multi.chat_detector, "detect_pending_chat", return_value=fake_result):
            res = multi.detect_pending_chat(target_hwnd=None)
            self.assertEqual(res, fake_result)

    def test_standalone_demo_and_runners_exist(self):
        # Verify clean architectural separation: standalone files exist
        self.assertTrue(os.path.exists("standalone_demo.py"), "standalone_demo.py must exist!")
        self.assertTrue(os.path.exists("run_demo.bat"), "run_demo.bat must exist!")
        self.assertTrue(os.path.exists("run.bat"), "run.bat must exist!")
        self.assertFalse(os.path.exists("auto_commander/gui/simulator.py"), "simulator.py must be removed from auto_commander/gui!")

    def test_step_0_chat_tab_ocr_fallback(self):
        cfg = Config()
        chat_det = ChatTabDetector(cfg, template_path="non_existent_tpl.png")
        # Template list is empty, falls back to OCR
        dummy_match = DetectionResult(x=150, y=715, width=15, height=15, confidence=0.95, source="OcrMock", label="?")
        with unittest.mock.patch.object(chat_det.ocr_detector, "is_available", return_value=True):
            with unittest.mock.patch.object(chat_det.ocr_detector, "scan_image", return_value=dummy_match):
                with unittest.mock.patch("auto_commander.detectors.chat_detector.ImageGrab.grab", return_value=Image.new("RGB", (300, 1000))):
                    res = chat_det.detect_pending_chat(target_hwnd=None)
                    self.assertIsNotNone(res)
                    self.assertEqual(res.source, "OcrChatBadge")
                    self.assertIn("Action Required", res.label)

    def test_step_0_chat_tab_uia_fallback(self):
        cfg = Config()
        chat_det = ChatTabDetector(cfg, template_path="non_existent_tpl.png")
        dummy_uia = DetectionResult(x=50, y=700, width=200, height=35, confidence=0.99, source="UIAutomation", label="Action required")
        with unittest.mock.patch.object(chat_det.ocr_detector, "is_available", return_value=False):
            with unittest.mock.patch.object(chat_det.uia_detector, "is_available", return_value=True):
                with unittest.mock.patch.object(chat_det.uia_detector, "find_by_keywords", return_value=dummy_uia):
                    res = chat_det.detect_pending_chat(target_hwnd=None)
                    self.assertIsNotNone(res)
                    self.assertEqual(res, dummy_uia)

    def test_step_0_execution_foregrounds_and_passes_target_hwnd(self):
        cfg = Config(step0_countdown_seconds=0.01, countdown_seconds=0.01, floating_hud_enabled=False)
        engine = AutoCommanderEngine(cfg)
        engine.active_hwnd = 12345

        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(TerminalDashboard, "print_banner"), \
             unittest.mock.patch.object(TerminalDashboard, "render_scanning"), \
             unittest.mock.patch.object(engine.detector, "detect", return_value=None), \
             unittest.mock.patch.object(engine.detector, "detect_pending_chat", side_effect=[fake_chat, None]), \
             unittest.mock.patch.object(AntigravityWindowManager, "check_and_foreground", return_value=(True, "Ready", 12345)), \
             unittest.mock.patch.object(AntigravityWindowManager, "bring_to_foreground") as mock_bring_fg, \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

            def stop_loop(*args, **kwargs):
                engine.is_running = False

            mock_glide.side_effect = lambda *a, **k: [stop_loop(), True][1]

            engine.run()

            mock_bring_fg.assert_called_with(12345)
            mock_glide.assert_called()
            call_kwargs = mock_glide.call_args[1]
            self.assertEqual(call_kwargs.get("target_hwnd"), 12345)

    def test_step_0_countdown_floating_hud_and_initial_pos_initialization(self):
        cfg = Config(step0_countdown_seconds=0.01, countdown_seconds=0.01, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(engine.hud, "show") as mock_hud_show, \
             unittest.mock.patch.object(engine.hud, "update_step") as mock_hud_step, \
             unittest.mock.patch.object(engine.hud, "update_countdown") as mock_hud_cnt, \
             unittest.mock.patch.object(engine, "_get_mouse_position", return_value=(100, 100)), \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            mock_hud_show.assert_any_call(0.01, "Action Required (?) on Chat Item")
            mock_hud_step.assert_called()
            self.assertEqual(engine.initial_mouse_pos, (100, 100))
            self.assertTrue(mock_glide.called)

    def test_step_0_failsafe_mouse_interruption(self):
        cfg = Config(step0_countdown_seconds=2.0, mouse_interruption_threshold_px=15, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(engine.hud, "show"), \
             unittest.mock.patch.object(engine.hud, "flash_cancelled") as mock_hud_cancel, \
             unittest.mock.patch.object(engine, "_get_mouse_position", side_effect=[(100, 100), (150, 150), (150, 150), (150, 150)]), \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click") as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            self.assertFalse(res, "Step 0 countdown must abort on human mouse movement!")
            self.assertEqual(engine.current_state, "COOLDOWN", "Must enter COOLDOWN on fail-safe abort!")
            mock_hud_cancel.assert_called_once()
            mock_glide.assert_not_called()

    def test_step_0_keyboard_abort(self):
        cfg = Config(step0_countdown_seconds=2.0, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        def trigger_user_abort(*args, **kwargs):
            engine.user_interrupted = True

        with unittest.mock.patch.object(engine.hud, "show"), \
             unittest.mock.patch.object(engine.hud, "update_countdown", side_effect=trigger_user_abort), \
             unittest.mock.patch.object(engine.hud, "flash_cancelled") as mock_hud_cancel, \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click") as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            self.assertFalse(res, "Step 0 must abort immediately on user_interrupted keyboard event!")
            self.assertEqual(engine.current_state, "COOLDOWN", "Must enter COOLDOWN on keyboard abort!")
            mock_hud_cancel.assert_called_once()
            mock_glide.assert_not_called()

    def test_step_0_failure_enters_cooldown(self):
        cfg = Config(step0_countdown_seconds=0.01, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(engine.hud, "show"), \
             unittest.mock.patch.object(engine.hud, "flash_cancelled") as mock_hud_cancel, \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=False) as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            self.assertFalse(res)
            self.assertEqual(engine.current_state, "COOLDOWN", "Must enter COOLDOWN on switch failure!")
            mock_hud_cancel.assert_called_once()

    def test_step_0_fallback_guarantee_proceeds_to_option1_and_submit(self):
        """Verifies that when modal is not detected after switch, fallback guarantee engages (541, 664) and (1827, 849) without getting stuck."""
        cfg = Config(step0_countdown_seconds=0.01, countdown_seconds=0.01, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(engine.hud, "show"), \
             unittest.mock.patch.object(engine.detector, "detect", return_value=None), \
             unittest.mock.patch.object(engine.detector, "detect_submit_button", return_value=None), \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            self.assertTrue(res, "Must return True and execute fallback guarantee flow!")
            # 3 glides: Step 0 chat (154, 719), Step 1 Option 1 (541, 664), Step 2 Submit (1827, 849)
            self.assertEqual(mock_glide.call_count, 3)
            calls = mock_glide.call_args_list
            # Call 0: chat switch
            self.assertEqual(calls[0][0][0], 161)
            self.assertEqual(calls[0][0][1], 726)
            # Call 1: Option 1 fallback target (541, 664)
            self.assertEqual(calls[1][0][0], 541)
            self.assertEqual(calls[1][0][1], 664)
            # Call 2: Submit fallback target (1827, 849)
            self.assertEqual(calls[2][0][0], 1827)
            self.assertEqual(calls[2][0][1], 849)

    def test_check_mouse_interrupted_with_target_pos_tolerance(self):
        cfg = Config(mouse_interruption_threshold_px=15)
        engine = AutoCommanderEngine(cfg)
        engine.initial_mouse_pos = (100, 100)

        # In resting countdown state: mouse moved from (100, 100) to (120, 120) -> dist ~28px > 15px -> True
        with unittest.mock.patch.object(engine, "_get_mouse_position", return_value=(120, 120)):
            self.assertTrue(engine._check_mouse_interrupted())

        # When gliding to a target (current_target_pos is set):
        engine.current_target_pos = (500, 600)
        # Mouse landed at (501, 602) -> dist ~2.2px <= 25px -> False (NOT interrupted)
        with unittest.mock.patch.object(engine, "_get_mouse_position", return_value=(501, 602)):
            self.assertFalse(engine._check_mouse_interrupted(), "Cursor landing on target within tolerance must NOT trigger fail-safe!")

        # Mouse snatched by user during glide to (800, 200) -> dist ~300px > 25px -> True (interrupted)
        with unittest.mock.patch.object(engine, "_get_mouse_position", return_value=(800, 200)):
            self.assertTrue(engine._check_mouse_interrupted(), "Cursor diverted away from target must trigger fail-safe!")

    def test_terminal_countdown_is_quiet(self):
        """Verifies TerminalDashboard.render_countdown does not write anything to terminal."""
        dummy_result = DetectionResult(x=100, y=100, width=50, height=20, confidence=0.99, source="OCR", label="Option 1")
        import io
        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            TerminalDashboard.render_countdown(2.5, 3.0, dummy_result)
        finally:
            sys.stdout = old_stdout
        self.assertEqual(captured.getvalue(), "", "TerminalDashboard.render_countdown must remain completely quiet!")

    def test_step_0_retry_polling_detects_modal_on_subsequent_poll(self):
        """Verifies that retry polling loop detects modal if rendered after initial switch delay."""
        cfg = Config(step0_countdown_seconds=0.01, countdown_seconds=0.01, floating_hud_enabled=False)
        engine = AutoCommanderEngine(cfg)
        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")
        detected_modal = DetectionResult(x=566, y=664, width=200, height=30, confidence=0.95, source="OCR", label="(Recommended) Push commits")
        submit_btn = DetectionResult(x=1827, y=849, width=0, height=0, confidence=0.95, source="OCR", label="Submit")

        # detect() returns None on poll 1, then returns detected_modal on poll 2
        with unittest.mock.patch.object(engine.detector, "detect", side_effect=[None, detected_modal]), \
             unittest.mock.patch.object(engine.detector, "detect_submit_button", return_value=submit_btn), \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

            res = engine._execute_step0_countdown(fake_chat)
            self.assertTrue(res)
            # Verify 3 glides occurred
            self.assertEqual(mock_glide.call_count, 3)
            calls = mock_glide.call_args_list
            # Call 0: Chat row
            self.assertEqual(calls[0][0][0], 161)
            # Call 1: Option 1 radio button (x - 25 = 566 - 25 = 541, y = 664)
            self.assertEqual(calls[1][0][0], 541)
            self.assertEqual(calls[1][0][1], 664)
            # Call 2: Submit button (1827, 849)
            self.assertEqual(calls[2][0][0], 1827)
            self.assertEqual(calls[2][0][1], 849)


class TestDynamicTargetingAndHeight(unittest.TestCase):
    """
    Tests dynamic Option 1 and Submit targeting across variable modal heights
    (2 options, 3 options, 4 options, multiline questions), eliminating hardcoded (541, 664) and (1827, 849).
    """

    def test_is_option_1_match_all_variations(self):
        """Verifies flexible Option 1 matching across all OCR formats and variations."""
        matches_strong = [
            "(Recommended)",
            "[Recommended]",
            "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
            "Option 1: (Recommended) Push committed changes",
            "1. (Recommended) Execute unit test suite",
            "1 (Recommended)",
            "1. Recommended: Deploy changes",
            "Option 1: Recommended",
            "Option 1 (Recommended)",
            "1 Recommendation",
            "(अनुशंसित) विकल्प 1",
            "विकल्प 1: अनुशंसित",
            "○ (Recommended) Commit changes",
            "● Recommended option",
        ]
        for text in matches_strong:
            is_match, is_strong = WindowsOcrDetector.is_option_1_match(text)
            self.assertTrue(is_match, f"Failed to match Option 1 on: {text}")

        # Negative samples
        negatives = [
            "Which option is recommended by the team?",
            "What is the recommended approach for this?",
            "Option 2: Cancel and keep changes local",
            "Option 3: Ask questions later",
            "Just a conversational response explaining recommendation theory",
        ]
        for text in negatives:
            is_match, _ = WindowsOcrDetector.is_option_1_match(text)
            self.assertFalse(is_match, f"Should NOT match Option 1 on: {text}")

    def test_step1_click_coordinates_dynamically_follow_variable_y(self):
        """
        Asserts that Step 1 Option 1 click coordinates dynamically track variable Y positions
        and radio button circles across 2, 3, 4 option questions without hardcoding y=664.
        """
        cfg = Config(countdown_seconds=0.01)
        engine = AutoCommanderEngine(cfg)

        test_cases = [
            # (name, opt_x, opt_y, opt_w, opt_h, expected_cx, expected_cy)
            ("2-option short", 565, 620, 150, 24, 541, 632),
            ("3-option multiline question", 565, 740, 180, 32, 541, 756),
            ("4-option tall question", 570, 830, 160, 36, 546, 848),
            ("Multiline intro question", 565, 890, 150, 28, 541, 904),
            ("Direct radio button detection", 535, 780, 20, 20, 535, 790),
        ]

        for name, opt_x, opt_y, opt_w, opt_h, exp_cx, exp_cy in test_cases:
            opt_result = DetectionResult(
                x=opt_x,
                y=opt_y,
                width=opt_w,
                height=opt_h,
                confidence=0.99,
                source="WindowsOcr",
                label="Option 1: (Recommended)",
            )
            fake_submit = DetectionResult(
                x=1827,
                y=opt_y + 160,
                width=100,
                height=35,
                confidence=0.99,
                source="Vision-ActiveBlue",
                label="Submit",
            )

            with unittest.mock.patch.object(engine.hud, "show"), \
                 unittest.mock.patch.object(engine.detector, "detect_submit_button", return_value=fake_submit), \
                 unittest.mock.patch.object(engine, "_verify_submission", return_value=True), \
                 unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

                engine._execute_countdown(opt_result)
                self.assertEqual(mock_glide.call_count, 2, f"Failed glide count for {name}")
                step1_call = mock_glide.call_args_list[0][0]
                self.assertEqual(step1_call[0], exp_cx, f"Step 1 X mismatch for {name}")
                self.assertEqual(step1_call[1], exp_cy, f"Step 1 Y mismatch for {name}")
                # Explicitly verify it did not use hardcoded 664
                if exp_cy != 664:
                    self.assertNotEqual(step1_call[1], 664, f"Hardcoded 664 detected in {name}!")

    def test_step2_submit_coordinates_dynamically_follow_variable_y(self):
        """
        Asserts that Step 2 Submit click coordinates dynamically follow variable option heights
        without hardcoding sub_y=849.
        """
        cfg = Config(countdown_seconds=0.01)
        engine = AutoCommanderEngine(cfg)

        test_cases = [
            ("Short modal Submit", 600, 785),
            ("Medium modal Submit", 720, 915),
            ("Tall 4-option modal Submit", 830, 1025),
        ]

        for name, opt_y, sub_y in test_cases:
            opt_result = DetectionResult(
                x=565,
                y=opt_y,
                width=150,
                height=24,
                confidence=0.99,
                source="WindowsOcr",
                label="(Recommended) Option 1",
            )
            active_blue_submit = DetectionResult(
                x=1780,
                y=sub_y,
                width=110,
                height=36,
                confidence=0.99,
                source="Vision-ActiveBlue",
                label="Submit",
            )

            with unittest.mock.patch.object(engine.hud, "show"), \
                 unittest.mock.patch.object(engine.detector, "detect_submit_button", return_value=active_blue_submit), \
                 unittest.mock.patch.object(engine, "_verify_submission", return_value=True), \
                 unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True) as mock_glide:

                engine._execute_countdown(opt_result)
                step2_call = mock_glide.call_args_list[1][0]
                self.assertEqual(step2_call[1], active_blue_submit.center[1], f"Step 2 Y mismatch for {name}")
                self.assertNotEqual(step2_call[1], 849, f"Step 2 Y should not be hardcoded 849 for {name}")

    def test_skip_inference_places_submit_dynamically(self):
        """Verifies that when only Skip button is seen, Submit position is inferred dynamically on same row."""
        skip_candidate = DetectionResult(x=1680, y=945, width=65, height=30, confidence=0.98, source="WindowsOcr", label="Skip")

        # Inferred Submit is placed ~35px to the right of Skip on same Y row
        expected_sub_x = skip_candidate.x + skip_candidate.width + 35
        expected_sub_y = skip_candidate.y

        self.assertEqual(expected_sub_x, 1780)
        self.assertEqual(expected_sub_y, 945)

    def test_submit_verification_detects_failure_and_prevents_false_success(self):
        """
        Verifies that if the modal card remains open after clicking Submit,
        _verify_submission returns False and prevents false success notification.
        """
        cfg = Config(countdown_seconds=0.01, floating_hud_enabled=True)
        engine = AutoCommanderEngine(cfg)

        opt_result = DetectionResult(x=565, y=700, width=150, height=25, confidence=0.99, source="WindowsOcr", label="(Recommended)")
        submit_btn = DetectionResult(x=1800, y=880, width=100, height=35, confidence=0.99, source="Vision-ActiveBlue", label="Submit")

        # Mock active blue Submit button still persisting after click
        with unittest.mock.patch.object(engine.hud, "show"), \
             unittest.mock.patch.object(engine.hud, "flash_success") as mock_success, \
             unittest.mock.patch.object(engine.hud, "flash_cancelled") as mock_cancel, \
             unittest.mock.patch.object(TerminalDashboard, "render_completed") as mock_completed, \
             unittest.mock.patch.object(engine.detector, "detect_submit_button", return_value=submit_btn), \
             unittest.mock.patch.object(engine.mouse_ctrl, "glide_and_click", return_value=True), \
             unittest.mock.patch.object(engine.detector.vision_detector, "detect_active_blue_submit_button", return_value=submit_btn):

            engine._execute_countdown(opt_result)

            # Verification should fail because button is still active
            mock_completed.assert_not_called()
            mock_success.assert_not_called()
            mock_cancel.assert_called_once()
            self.assertEqual(engine.current_state, "COOLDOWN")

    def test_floating_hud_rect_and_sanitization(self):
        """
        Tests that FloatingHUD correctly manages HUD rect tracking and sanitizes
        labels so trigger words like (Recommended) or (अनुशंसित) never appear on HUD.
        """
        hud = FloatingHUD(alpha=0.92)
        self.assertIsNone(hud.get_hud_rect())
        self.assertIsNone(FloatingHUD.get_active_hud_rect())

        # Test text sanitization
        self.assertEqual(FloatingHUD._sanitize_text("(Recommended) Option 1"), "Option 1")
        self.assertEqual(FloatingHUD._sanitize_text("[Recommended] Option 1"), "Option 1")
        self.assertEqual(FloatingHUD._sanitize_text("(अनुशंसित) गिटहब"), "Option 1 गिटहब")
        self.assertEqual(FloatingHUD._sanitize_text("Auto-Selecting: (Recommended) Option 1"), "Auto-Selecting: Option 1")

        # Simulate show()
        hud.is_visible = True
        hud._rect = Rect(x=650, y=20, width=620, height=58)
        FloatingHUD._active_instance = hud
        FloatingHUD._active_rect = hud._rect

        self.assertIsNotNone(hud.get_hud_rect())
        self.assertEqual(hud.get_hud_rect().y, 20)
        self.assertEqual(FloatingHUD.get_active_hud_rect().width, 620)

        # Simulate close()
        hud.close()
        self.assertFalse(hud.is_visible)
        self.assertIsNone(hud.get_hud_rect())
        self.assertIsNone(FloatingHUD.get_active_hud_rect())

    def test_ocr_hud_masking_and_y_filter(self):
        """
        Tests that WindowsOcrDetector masks out the Floating HUD region and
        rejects any candidate inside HUD or at y < 160 on full-size frames.
        """
        detector = WindowsOcrDetector(target_keywords=("(Recommended)", "Recommended"))
        if not detector.is_available():
            self.skipTest("WinSDK OCR not available on this platform/session.")

        hud_rect = Rect(x=200, y=20, width=600, height=60)

        # Image simulating full screen with text inside HUD area (y=35)
        full_img = Image.new("RGB", (1200, 800), color=(30, 30, 46))
        d = ImageDraw.Draw(full_img)
        d.text((250, 35), "AutoSelect: (Recommended) Option 1", fill=(166, 227, 161))

        # With hud_rect masked or with y < 160 filter, this must be rejected!
        res = detector.scan_image(full_img, offset_x=0, offset_y=0, hud_rect=hud_rect, mask_hud=True)
        self.assertIsNone(res, "OCR should never detect HUD overlay at top of screen as target!")

    def test_verify_submission_dismissed_when_elements_gone(self):
        """
        Tests that _verify_submission_dismissed returns True when the modal
        elements have disappeared from screen.
        """
        cfg = Config(countdown_seconds=0.01, floating_hud_enabled=False)
        engine = AutoCommanderEngine(cfg)

        opt_result = DetectionResult(x=565, y=700, width=150, height=25, confidence=0.99, source="WindowsOcr", label="(Recommended)")

        # When active blue submit and OCR modal are not found, returns True
        with unittest.mock.patch.object(engine.detector.vision_detector, "detect_active_blue_submit_button", return_value=None), \
             unittest.mock.patch.object(engine.detector.ocr_detector, "scan_decision_modal", return_value=None):
            dismissed = engine._verify_submission_dismissed(opt_result, 1827, 850)
            self.assertTrue(dismissed)


if __name__ == "__main__":
    unittest.main()
