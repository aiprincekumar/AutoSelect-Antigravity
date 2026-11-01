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
        self.assertEqual(hud.total_seconds, 10.0)
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
        cfg = Config()
        engine = AutoCommanderEngine(cfg)
        engine.active_hwnd = 12345

        fake_chat = DetectionResult(x=194, y=719, width=15, height=15, confidence=0.95, source="ChatTab", label="Action Required (?)")

        with unittest.mock.patch.object(TerminalDashboard, "print_banner"), \
             unittest.mock.patch.object(TerminalDashboard, "render_scanning"), \
             unittest.mock.patch.object(engine.detector, "detect", side_effect=[None, None]), \
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


if __name__ == "__main__":
    unittest.main()
