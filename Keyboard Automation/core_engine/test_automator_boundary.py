#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Step 3 Loop Boundary & Keystrokes for Questions <= 3
===================================================================
Test Suite: core_engine/test_automator_boundary.py
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) / Dept 06 (Backend & API Engineering)
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name == "core_engine" else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from core_engine.automator import GrillMeAutomator


class TestAutomatorBoundary(unittest.TestCase):
    """Test suite verifying strict 1-to-1 loop boundary and question count ground truth."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_boundary_"))
        self.state_file = self.test_dir / "target_chat.json"

        # Root Cause 3 Hermetic Mock Isolation: Ensure NO physical keystrokes reach live OS windows
        self._patcher_send_single = patch("core_engine.automator.send_single_key", autospec=True)
        self._patcher_send_combo = patch("core_engine.automator.send_key_combo", autospec=True)
        self._patcher_inj_single = patch("core_engine.input_injector.send_single_key", autospec=True)
        self._patcher_inj_combo = patch("core_engine.input_injector.send_key_combo", autospec=True)
        self._patcher_inj_event = patch("core_engine.input_injector._send_key_event", return_value=True)

        self.mock_send_single_key = self._patcher_send_single.start()
        self.mock_send_key_combo = self._patcher_send_combo.start()
        self.mock_inj_send_single = self._patcher_inj_single.start()
        self.mock_inj_send_combo = self._patcher_inj_combo.start()
        self.mock_inj_send_event = self._patcher_inj_event.start()

        self.addCleanup(self._patcher_send_single.stop)
        self.addCleanup(self._patcher_send_combo.stop)
        self.addCleanup(self._patcher_inj_single.stop)
        self.addCleanup(self._patcher_inj_combo.stop)
        self.addCleanup(self._patcher_inj_event.stop)

        from core_engine.win32_api import user32
        if hasattr(user32, "SendInput"):
            self._patcher_user32_send = patch.object(user32, "SendInput", return_value=1)
            self._patcher_user32_send.start()
            self.addCleanup(self._patcher_user32_send.stop)
        if hasattr(user32, "keybd_event"):
            self._patcher_user32_kbd = patch.object(user32, "keybd_event", return_value=None)
            self._patcher_user32_kbd.start()
            self.addCleanup(self._patcher_user32_kbd.stop)

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_state_resolution_prioritizes_questions_list_over_scalars(self):
        """Verify len(questions) strictly overrides total_questions_count or candidate counts."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "test_cid",
                "questions": [
                    {"question": "Q1", "recommended_option_index": 1},
                    {"question": "Q2", "recommended_option_index": 2},
                ],
                "total_questions_count": 5,
                "questions_count": 4,
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

        automator = GrillMeAutomator(
            questions="auto",
            state_file=str(self.state_file),
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        self.assertEqual(automator.total_questions, 2)
        self.assertEqual(automator.options_list, ["1", "2"])

    def test_state_resolution_single_question_in_questions_list(self):
        """Verify N=1 question in state file resolves to exactly 1 question and 1 option."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "single_q",
                "questions": [
                    {"question": "Only Question", "recommended_option_index": 1}
                ],
                "total_questions_count": 99,
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

        automator = GrillMeAutomator(
            questions="auto",
            state_file=str(self.state_file),
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        self.assertEqual(automator.total_questions, 1)
        self.assertEqual(automator.options_list, ["1"])

    def test_state_resolution_fallback_to_selections(self):
        """Verify fallback to selections list when questions list is absent."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "selections_q",
                "questions": [],
                "selections": [
                    {"selected_option_index": 1},
                    {"selected_option_index": 3},
                    {"selected_option_index": 2},
                ],
                "total_questions_count": 10,
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

        automator = GrillMeAutomator(
            questions="auto",
            state_file=str(self.state_file),
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        self.assertEqual(automator.total_questions, 3)
        self.assertEqual(automator.options_list, ["1", "3", "2"])

    def test_state_resolution_fallback_to_scalar_when_no_lists(self):
        """Verify fallback to total_questions_count scalar when lists are empty."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "scalar_q",
                "total_questions_count": 3,
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

        automator = GrillMeAutomator(
            questions="auto",
            state_file=str(self.state_file),
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        self.assertEqual(automator.total_questions, 3)
        self.assertEqual(len(automator.options_list), 3)
        self.assertEqual(automator.options_list, ["1", "1", "1"])

    def test_execute_multi_question_n1_exact_keystroke_boundary(self):
        """Verify N=1 executes: FOCUS.1, FOCUS.2, OPT.1 (total 3 steps, zero Enter/Space, zero trailing leak)."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []

        def spy_execute_step(step_code, description, action_fn):
            executed_steps.append((step_code, description))

        automator._execute_step = spy_execute_step
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=1, options=["1"])
        self.assertTrue(ok)

        step_codes = [s[0] for s in executed_steps]
        self.assertEqual(step_codes, ["FOCUS.1", "FOCUS.2", "OPT.1"])
        self.assertEqual(len(executed_steps), 3)
        self.assertIn("Ctrl + L", executed_steps[0][1])
        self.assertIn("Shift + Tab", executed_steps[1][1])
        self.assertIn("Option press 1/1", executed_steps[2][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n2_exact_keystroke_boundary(self):
        """Verify N=2 executes: FOCUS.1, FOCUS.2, OPT.1, OPT.2 (total 4 steps, zero Enter/Space)."""
        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []

        def spy_execute_step(step_code, description, action_fn):
            executed_steps.append((step_code, description))

        automator._execute_step = spy_execute_step
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=2, options=["1", "2"])
        self.assertTrue(ok)

        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2"]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 4)
        self.assertIn("Option press 1/2", executed_steps[2][1])
        self.assertIn("Option press 2/2", executed_steps[3][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n3_exact_keystroke_boundary(self):
        """Verify N=3 executes: FOCUS.1, FOCUS.2, OPT.1, OPT.2, OPT.3 (total 5 steps, zero Enter/Space)."""
        automator = GrillMeAutomator(
            questions=3,
            options_list=["1", "2", "3"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []

        def spy_execute_step(step_code, description, action_fn):
            executed_steps.append((step_code, description))

        automator._execute_step = spy_execute_step
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=3, options=["1", "2", "3"])
        self.assertTrue(ok)

        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3"]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 5)
        self.assertIn("Option press 1/3", executed_steps[2][1])
        self.assertIn("Option press 2/3", executed_steps[3][1])
        self.assertIn("Option press 3/3", executed_steps[4][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_zero_questions_clean_exit(self):
        """Verify N=0 results in clean cancellation with 0 keystrokes executed."""
        automator = GrillMeAutomator(
            questions=0,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=0)
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 0)


    def test_execute_multi_question_n4_exact_keystroke_boundary(self):
        """Verify N=4 dynamically executes FOCUS.1, FOCUS.2, OPT.1..OPT.4: total 6 steps, zero Enter/Space."""
        automator = GrillMeAutomator(
            questions=4,
            options_list=["1", "2", "1", "3"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=4, options=["1", "2", "1", "3"])
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 6)
        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3", "OPT.4"]
        self.assertEqual(step_codes, expected_codes)
        self.assertIn("Option press 1/4", executed_steps[2][1])
        self.assertIn("Option press 2/4", executed_steps[3][1])
        self.assertIn("Option press 3/4", executed_steps[4][1])
        self.assertIn("Option press 4/4", executed_steps[5][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n5_exact_keystroke_boundary(self):
        """Verify N=5 dynamically executes FOCUS.1, FOCUS.2, OPT.1..OPT.5: total 7 steps, zero Enter/Space."""
        automator = GrillMeAutomator(
            questions=5,
            options_list=["1", "1", "2", "2", "1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=5, options=["1", "1", "2", "2", "1"])
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 7)
        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3", "OPT.4", "OPT.5"]
        self.assertEqual(step_codes, expected_codes)
        self.assertIn("Option press 1/5", executed_steps[2][1])
        self.assertIn("Option press 5/5", executed_steps[6][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_state_resolution_step2_metadata_keys(self):
        """Verify Step 3 dynamically resolves questions from Step 2 metadata keys (total_questions, question_count)."""
        for key, count in [("total_questions", 4), ("question_count", 5), ("total_questions_count", 3)]:
            state = {
                "success": True,
                "data": {
                    "conversation_id": f"test_{key}",
                    key: count,
                    "gui_chat_selected": True,
                }
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                import json
                json.dump(state, f)

            automator = GrillMeAutomator(
                questions="auto",
                state_file=str(self.state_file),
                dry_run=True,
                auto_focus=False,
                auto_maximize=False,
            )
            self.assertEqual(automator.total_questions, count)
            self.assertEqual(len(automator.options_list), count)
            self.assertEqual(automator.options_list, ["1"] * count)

    def test_convenience_execute_multi_question_auto_default(self):
        """Verify execute_multi_question() functional interface defaults to auto detection instead of forcing 1."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "auto_test",
                "total_questions_count": 4,
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            import json
            json.dump(state, f)

        from core_engine.automator import execute_multi_question
        with patch("core_engine.automator.GrillMeAutomator.execute", return_value=True) as mock_exec:
            ok = execute_multi_question(state_file=str(self.state_file), dry_run=True)
            self.assertTrue(ok)
            mock_exec.assert_called_once()


    def test_cdp_inspection_never_overrides_state_file_ground_truth(self):
        """Verify live CDP DOM inspection never overrides ground truth from state file."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "multi_q_test",
                "questions_count": 2,
                "total_questions_count": 2,
                "is_multi_question": True,
                "questions": [
                    {"question": "Q1", "recommended_option_index": 1},
                    {"question": "Q2", "recommended_option_index": 1},
                ],
                "selections": [
                    {"question_index": 1, "selected_option_index": 1},
                    {"question_index": 2, "selected_option_index": 1},
                ]
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)

        # Mock CDP to return 1 question (simulating live DOM single card view)
        mock_cdp_instance = MagicMock()
        mock_cdp_instance.is_available.return_value = True
        mock_cdp_instance.connect.return_value = True
        mock_cdp_instance.get_questionnaire_status.return_value = {
            "has_card": True,
            "options_count": 3,
            "total_questions": 1,  # Defective CDP return
        }

        with patch("core_engine.cdp_helper.AntigravityCDPClient", return_value=mock_cdp_instance):
            automator = GrillMeAutomator(
                questions="auto",
                state_file=str(self.state_file),
                dry_run=False,
                auto_focus=False,
                auto_maximize=False,
            )

        # Ground truth from state file MUST be preserved
        self.assertEqual(automator.total_questions, 2)
        self.assertEqual(automator.options_list, ["1", "1"])

    def test_multi_question_sequence_exact_keys_without_space(self):
        """Verify exact sequence: N=2 executes single focus (Ctrl+L, Shift+Tab) followed by 2 option presses, with zero Enter and zero Space."""
        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=2, options=["1", "1"])
        self.assertTrue(ok)
        # 2 focus steps + 2 option press steps = 4 steps
        self.assertEqual(len(executed_steps), 4)

        # Verify initial focus sequence (1st time only)
        self.assertIn("Ctrl + L", executed_steps[0][1])
        self.assertIn("Shift + Tab", executed_steps[1][1])

        # Verify option presses (exactly 2 presses for N=2)
        self.assertIn("[1]", executed_steps[2][1])
        self.assertIn("[1]", executed_steps[3][1])

        # Verify NO step executed Enter or Space
        for sc, d in executed_steps:
            self.assertNotIn("space", d.lower())
            self.assertNotIn("enter", d.lower())

    def test_sequence_eliminates_all_enter_and_space_keys(self):
        """Verify execute_multi_question completely eliminates Enter and Space keys across all questions."""
        automator = GrillMeAutomator(
            questions=3,
            options_list=["1", "2", "3"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        dispatched_keys = []
        automator.dispatch_key = lambda vk: dispatched_keys.append(vk)
        logged_messages = []
        automator.log = lambda msg: logged_messages.append(msg)

        # Mock _execute_step to run action_fn directly
        def mock_execute_step(sc, desc, fn):
            if fn:
                fn()

        automator._execute_step = mock_execute_step
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=3, options=["1", "2", "3"])
        self.assertTrue(ok)

        # Zero Enter (VK_RETURN) dispatched in execute_multi_question
        from core_engine.constants import VK_RETURN
        self.assertEqual(dispatched_keys, [])

        # Verify option presses logged without any Enter prompt
        self.assertTrue(any("Option press 1/3" in m for m in logged_messages))
        self.assertTrue(any("Option press 3/3" in m for m in logged_messages))
        self.assertFalse(any("enter" in m.lower() for m in logged_messages))

        # Ensure dispatch_key helper itself still functions if called directly
        automator.dispatch_key(VK_RETURN)
        self.assertEqual(dispatched_keys, [VK_RETURN])

    def test_single_question_n1_selects_option_and_submits_without_skipping(self):
        """Verify single question (N=1) flow executes FOCUS.1, FOCUS.2, OPT.1 without triggering Skip button, Enter, or Space."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=1, options=["1"])
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 3)
        self.assertEqual(executed_steps[0][0], "FOCUS.1")
        self.assertEqual(executed_steps[1][0], "FOCUS.2")
        self.assertEqual(executed_steps[2][0], "OPT.1")
        self.assertIn("[1]", executed_steps[2][1])

        # Verify none of the steps activate or target Skip, Enter, or Space
        for sc, desc in executed_steps:
            self.assertNotIn("skip", desc.lower())
            self.assertNotIn("enter", desc.lower())
            self.assertNotIn("space", desc.lower())

    def test_execute_multi_question_n5_option_sequence_and_no_enter(self):
        """Verify N=5 flow executes FOCUS.1, FOCUS.2, and OPT.1..OPT.5 with 0 Enter/Space."""
        automator = GrillMeAutomator(
            questions=5,
            options_list=["1", "2", "3", "1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=5, options=["1", "2", "3", "1", "2"])
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 7)

        step_map = {sc: d for sc, d in executed_steps}
        self.assertIn("Focus chat box", step_map["FOCUS.1"])
        self.assertIn("Move backward to question options", step_map["FOCUS.2"])
        self.assertIn("[1] (Option press 1/5)", step_map["OPT.1"])
        self.assertIn("[2] (Option press 2/5)", step_map["OPT.2"])
        self.assertIn("[3] (Option press 3/5)", step_map["OPT.3"])
        self.assertIn("[1] (Option press 4/5)", step_map["OPT.4"])
        self.assertIn("[2] (Option press 5/5)", step_map["OPT.5"])

        # Check zero Enter or Space
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_skip_ctrl_l(self):
        """Verify skip_ctrl_l=True bypasses FOCUS.1 step cleanly."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            skip_ctrl_l=True,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=1, options=["1"])
        self.assertTrue(ok)
        self.assertEqual(len(executed_steps), 2)
        self.assertEqual(executed_steps[0][0], "FOCUS.2")
        self.assertEqual(executed_steps[1][0], "OPT.1")

    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(1234, "Antigravity.exe", "Antigravity"))
    def test_hybrid_cdp_helper_interaction_when_available(self, mock_proc_info):
        """Verify hybrid CDP verification & assistance is actively called when CDP is available."""
        mock_cdp = MagicMock()
        mock_cdp.is_available.return_value = True
        mock_cdp.connect.return_value = True
        mock_cdp.get_questionnaire_status.return_value = {
            "has_card": True,
            "options_count": 2,
            "current_question": 1,
            "total_questions": 1,
            "continue_btn_disabled": False,
        }

        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=1, options=["1"])
        self.assertTrue(ok)

        # Assert hybrid CDP helper methods were called
        mock_cdp.ensure_skip_not_focused.assert_called()
        mock_cdp.select_option.assert_called_with(1)
        mock_cdp.wait_for_button_enabled.assert_called_with(timeout=1.5)
        mock_cdp.focus_action_button.assert_called()

    def test_hybrid_cdp_helper_interaction_when_offline(self):
        """Verify hybrid CDP offline fallback: execution cleanly succeeds via physical keystrokes with 0 exceptions."""
        mock_cdp = MagicMock()
        mock_cdp.is_available.return_value = False
        mock_cdp.connect.return_value = False

        with patch("core_engine.cdp_helper.AntigravityCDPClient", return_value=mock_cdp):
            automator = GrillMeAutomator(
                questions=1,
                options_list=["1"],
                dry_run=True,
                auto_focus=False,
                auto_maximize=False,
            )

            executed_steps = []
            automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
            automator.engine = "ctypes"

            ok = automator.execute_multi_question(total_questions=1, options=["1"])
            self.assertTrue(ok)
            self.assertEqual(len(executed_steps), 3)
            self.assertEqual(executed_steps[0][0], "FOCUS.1")
            self.assertEqual(executed_steps[1][0], "FOCUS.2")
            self.assertEqual(executed_steps[2][0], "OPT.1")
            self.assertIn("Option press 1/1", executed_steps[2][1])

    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(1234, "Antigravity.exe", "Antigravity"))
    def test_cdp_hybrid_multi_question_intermediate_continue_and_submit(self, mock_proc_info):
        """Verify N=2 multi-question in CDP Hybrid mode clicks Continue for Q1 and Submit for Q2."""
        mock_cdp = MagicMock()
        mock_cdp.is_available.return_value = True
        mock_cdp.connect.return_value = True
        mock_cdp.get_questionnaire_status.return_value = {
            "has_card": True,
            "options_count": 3,
            "current_question": 1,
            "total_questions": 2,
            "continue_btn_disabled": False,
            "chat_input_focused": False,
        }

        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        ok = automator.execute_multi_question(total_questions=2, options=["1", "2"])
        self.assertTrue(ok)

        # Q1 select option 1, click continue, wait advance
        # Q2 select option 2, click submit, wait close
        self.assertEqual(mock_cdp.select_option.call_count, 2)
        mock_cdp.select_option.assert_any_call(1)
        mock_cdp.select_option.assert_any_call(2)

        # Continue (Q1) and Submit (Q2) both call click_continue_or_submit
        self.assertEqual(mock_cdp.click_continue_or_submit.call_count, 2)

        # wait_for_advance_or_close called for Q1 (is_last=False) and Q2 (is_last=True)
        self.assertEqual(mock_cdp.wait_for_advance_or_close.call_count, 2)
        mock_cdp.wait_for_advance_or_close.assert_any_call(previous_question=1, is_last=False, timeout=unittest.mock.ANY)
        mock_cdp.wait_for_advance_or_close.assert_any_call(previous_question=2, is_last=True, timeout=unittest.mock.ANY)

    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(1234, "Antigravity.exe", "Antigravity"))
    def test_cdp_hybrid_stops_immediately_when_card_closed(self, mock_proc_info):
        """Verify CDP Hybrid mode immediately halts when has_card is False, never dispatching keystrokes."""
        mock_cdp = MagicMock()
        mock_cdp.is_available.return_value = True
        mock_cdp.connect.return_value = True
        mock_cdp.get_questionnaire_status.return_value = {
            "has_card": False,
            "current_question": 0,
            "total_questions": 0,
            "chat_input_focused": False,
        }
        mock_cdp.wait_for_question.return_value = False

        automator = GrillMeAutomator(
            questions=3,
            options_list=["1", "2", "1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        dispatched_keys = []
        automator.dispatch_key = lambda vk: dispatched_keys.append(vk)

        ok = automator.execute_multi_question(total_questions=3, options=["1", "2", "1"])
        self.assertTrue(ok)

        # Card was closed: select_option, click_continue_or_submit, and keystrokes MUST NOT be called!
        mock_cdp.select_option.assert_not_called()
        mock_cdp.click_continue_or_submit.assert_not_called()
        self.assertEqual(len(dispatched_keys), 0)

    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(1234, "Antigravity.exe", "Antigravity"))
    def test_cdp_hybrid_chat_input_pollution_guard(self, mock_proc_info):
        """Verify CDP Hybrid mode detects chat input focus and calls blur_chat_input to prevent pollution."""
        mock_cdp = MagicMock()
        mock_cdp.is_available.return_value = True
        mock_cdp.connect.return_value = True
        mock_cdp.is_chat_input_focused.return_value = True
        mock_cdp.get_questionnaire_status.return_value = {
            "has_card": True,
            "options_count": 2,
            "current_question": 1,
            "total_questions": 1,
            "continue_btn_disabled": False,
            "chat_input_focused": True,
        }

        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        dispatched_keys = []
        automator.dispatch_key = lambda vk: dispatched_keys.append(vk)

        ok = automator.execute_multi_question(total_questions=1, options=["1"])
        self.assertTrue(ok)

        # Verify blur_chat_input was called
        mock_cdp.blur_chat_input.assert_called()
        self.assertEqual(len(dispatched_keys), 0)

    @patch("core_engine.automator.user32.GetForegroundWindow", return_value=0x1111)
    @patch("core_engine.automator.user32.IsWindow", return_value=True)
    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(9999, "msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"))
    @patch("core_engine.automator.get_active_window_title", return_value="New Tab - Microsoft Edge")
    def test_foreground_disqualified_browser_aborts_execute_step(self, mock_title, mock_proc, mock_is_win, mock_fg):
        """Verify _execute_step immediately aborts and returns False without calling action when foreground is a browser."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
        )

        mock_action = MagicMock()
        ret = automator._execute_step("FOCUS.1", "Press Ctrl+L", mock_action)

        self.assertFalse(ret)
        mock_action.assert_not_called()

    @patch("core_engine.automator.user32.GetForegroundWindow", return_value=0x2222)
    @patch("core_engine.automator.user32.IsWindow", return_value=True)
    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(8888, "chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    @patch("core_engine.automator.get_active_window_title", return_value="Google - Google Chrome")
    def test_foreground_chrome_browser_aborts_pure_keyboard(self, mock_title, mock_proc, mock_is_win, mock_fg):
        """Verify _execute_pure_keyboard aborts immediately when foreground window is Chrome browser."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
        )

        dispatched_steps = []
        automator._execute_step = lambda sc, d, fn: dispatched_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=1, options=["1"])
        self.assertFalse(ret)
        self.assertEqual(len(dispatched_steps), 0)

    @patch("core_engine.automator.user32.GetForegroundWindow", return_value=0x3333)
    @patch("core_engine.automator.user32.IsWindow", return_value=True)
    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(7777, "notepad.exe", r"C:\Windows\notepad.exe"))
    @patch("core_engine.automator.get_active_window_title", return_value="Untitled - Notepad")
    def test_foreground_unrelated_process_not_target_aborts(self, mock_title, mock_proc, mock_is_win, mock_fg):
        """Verify _is_foreground_window_target_and_safe returns False when foreground window is an unrelated process."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
        )
        self.assertFalse(automator._is_foreground_window_target_and_safe())

    @patch("core_engine.automator.user32.GetForegroundWindow", return_value=0x4444)
    @patch("core_engine.automator.user32.IsWindow", return_value=True)
    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(6666, "Antigravity.exe", r"C:\Program Files\Antigravity\Antigravity.exe"))
    @patch("core_engine.automator.get_active_window_title", return_value="Antigravity 2.0 Harness")
    def test_foreground_antigravity_target_succeeds(self, mock_title, mock_proc, mock_is_win, mock_fg):
        """Verify _is_foreground_window_target_and_safe returns True when foreground is Antigravity."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
        )
        self.assertTrue(automator._is_foreground_window_target_and_safe())

    @patch("core_engine.automator.user32.GetForegroundWindow", return_value=0x5555)
    @patch("core_engine.automator.user32.IsWindow", return_value=True)
    @patch("core_engine.automator.get_process_info_for_hwnd", return_value=(5555, "msedge.exe", r"C:\Program Files\Microsoft\Edge\msedge.exe"))
    @patch("core_engine.automator.get_active_window_title", return_value="Microsoft Edge")
    def test_foreground_browser_allowed_only_when_explicitly_requested(self, mock_title, mock_proc, mock_is_win, mock_fg):
        """Verify browser is allowed only when user explicitly specifies it in target_window."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=False,
            auto_maximize=False,
            target_window="msedge.exe",
        )
        self.assertTrue(automator._is_foreground_window_target_and_safe())

    def test_pure_keyboard_stops_immediately_when_card_closed_before_focus(self):
        """Verify _execute_pure_keyboard halts cleanly (return True, exit code 0) if questionnaire card is closed before FOCUS.1."""
        mock_cdp = MagicMock()
        mock_cdp.get_questionnaire_status.return_value = {"has_card": False}

        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=2, options=["1", "2"], cdp=mock_cdp)
        self.assertTrue(ret)
        self.assertEqual(len(executed_steps), 0)

    def test_pure_keyboard_stops_immediately_when_card_closed_after_focus(self):
        """Verify _execute_pure_keyboard halts cleanly after FOCUS.2 if card closes before option loop."""
        mock_cdp = MagicMock()
        # Card present before FOCUS.1, closed after FOCUS.2
        mock_cdp.get_questionnaire_status.side_effect = [
            {"has_card": True, "chat_input_focused": False},  # before FOCUS.1
            {"has_card": False, "chat_input_focused": False}, # after FOCUS.2
        ]

        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=2, options=["1", "2"], cdp=mock_cdp)
        self.assertTrue(ret)
        self.assertEqual(executed_steps, ["FOCUS.1", "FOCUS.2"])

    def test_pure_keyboard_stops_immediately_when_card_closed_prior_to_option_k(self):
        """Verify _execute_pure_keyboard halts cleanly before option press 2 if card closed after option 1."""
        mock_cdp = MagicMock()
        # Present before FOCUS.1, after FOCUS.2, before opt 1, then closed before opt 2
        mock_cdp.get_questionnaire_status.side_effect = [
            {"has_card": True, "chat_input_focused": False},  # before FOCUS.1
            {"has_card": True, "chat_input_focused": False},  # after FOCUS.2
            {"has_card": True, "chat_input_focused": False},  # prior to opt 1
            {"has_card": False, "chat_input_focused": False}, # prior to opt 2
        ]

        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=2, options=["1", "2"], cdp=mock_cdp)
        self.assertTrue(ret)
        self.assertEqual(executed_steps, ["FOCUS.1", "FOCUS.2", "OPT.1"])

    def test_pure_keyboard_chat_input_pollution_guard_blurs_and_proceeds(self):
        """Verify _execute_pure_keyboard blurs chat input if focused and proceeds safely when unblurred."""
        mock_cdp = MagicMock()
        mock_cdp.get_questionnaire_status.return_value = {"has_card": True}
        # First reported focused, then blurred
        mock_cdp.is_chat_input_focused.side_effect = [True, False, False, False, False, False]

        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=1, options=["1"], cdp=mock_cdp)
        self.assertTrue(ret)
        mock_cdp.blur_chat_input.assert_called()
        self.assertEqual(executed_steps, ["FOCUS.1", "FOCUS.2", "OPT.1"])

    def test_pure_keyboard_chat_input_pollution_guard_aborts_when_trapped(self):
        """Verify _execute_pure_keyboard aborts (returns False) if active focus is trapped in chat input and cannot be blurred."""
        mock_cdp = MagicMock()
        mock_cdp.get_questionnaire_status.return_value = {"has_card": True}
        # Trapped in chat input (remains True after blur)
        mock_cdp.is_chat_input_focused.return_value = True

        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            cdp_client=mock_cdp,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append(sc)

        ret = automator._execute_pure_keyboard(total_questions=1, options=["1"], cdp=mock_cdp)
        self.assertFalse(ret)
        mock_cdp.blur_chat_input.assert_called()
        self.assertEqual(len(executed_steps), 0)

    def test_strict_option_selection_option_1_recommended_default(self):
        """Verify Option 1 (Recommended) is strictly respected by default across multi-question resolution."""
        state = {
            "success": True,
            "data": {
                "conversation_id": "strict_opt_test",
                "questions": [
                    {"question": "Q1", "recommended_option_index": 1},
                    {"question": "Q2", "recommended_option_index": 1},
                    {"question": "Q3", "recommended_option_index": 1},
                ],
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            import json
            json.dump(state, f)

        automator = GrillMeAutomator(
            questions="auto",
            state_file=str(self.state_file),
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        self.assertEqual(automator.total_questions, 3)
        self.assertEqual(automator.options_list, ["1", "1", "1"])

    def test_browser_disqualification_by_window_title_with_empty_process_name(self):
        """Verify is_browser_window detects browser by title even when process name is empty."""
        from core_engine.constants import is_browser_window
        self.assertTrue(is_browser_window(pname="", pexe="", title="Antigravity - Microsoft Edge"))
        self.assertTrue(is_browser_window(pname="", pexe="", title="Google - Google Chrome"))
        self.assertTrue(is_browser_window(pname="", pexe="", title="Mozilla Firefox"))
        self.assertTrue(is_browser_window(pname="", pexe="", title="New Tab - Edge"))
        self.assertTrue(is_browser_window(pname="", pexe="", title="GitHub - Brave"))
        # Non-browser window with 'knowledge' or 'antigravity' should NOT be false-positived
        self.assertFalse(is_browser_window(pname="Antigravity.exe", pexe=r"C:\Apps\Antigravity\Antigravity.exe", title="knowledge_base.py - Antigravity"))
        self.assertFalse(is_browser_window(pname="Antigravity.exe", pexe=r"C:\Apps\Antigravity\Antigravity.exe", title="Antigravity 2.0 Harness"))

    def test_select_target_window_disqualifies_browser_with_antigravity_in_title(self):
        """Verify select_target_window never selects browser tab even if title contains 'Antigravity'."""
        from core_engine.window_manager import select_target_window

        fake_candidates = [
            {
                "hwnd": 0x9999,
                "title": "Antigravity Project Docs - Microsoft Edge",
                "class": "Chrome_WidgetWin_1",
                "pid": 5555,
                "process_name": "",  # Empty process name simulation
                "process_exe": "",
                "visible": True,
                "minimized": False,
                "maximized": True,
                "width": 1920,
                "height": 1080,
                "rect": (0, 0, 1920, 1080),
                "is_browser": True,
            }
        ]

        with patch("core_engine.window_manager.find_all_candidate_windows", return_value=fake_candidates):
            matched = select_target_window("Antigravity")
            self.assertIsNone(matched, "Browser tab with 'Antigravity' in title MUST be disqualified!")

    def test_prepare_target_window_fails_closed_when_window_not_found(self):
        """Verify prepare_target_window returns False and target_hwnd is None when no match found (fail-closed)."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=True,
            auto_maximize=True,
        )

        with patch("core_engine.automator.select_target_window", return_value=None):
            result = automator.prepare_target_window()
            self.assertFalse(result)
            self.assertIsNone(automator.target_hwnd)
            self.assertIsNone(automator.target_title)

    def test_ensure_window_ready_fails_closed_without_blind_fallback(self):
        """Verify _ensure_window_ready returns False when target window cannot be verified as Antigravity."""
        automator = GrillMeAutomator(
            questions=1,
            options_list=["1"],
            dry_run=False,
            auto_focus=True,
            auto_maximize=True,
        )

        with patch.object(automator, "prepare_target_window", return_value=False):
            result = automator._ensure_window_ready()
            self.assertFalse(result)
            self.assertIsNone(automator.target_hwnd)

    def test_execute_multi_question_aborts_when_ensure_window_ready_fails(self):
        """Verify execute_multi_question aborts immediately with 0 keystrokes when _ensure_window_ready returns False."""
        automator = GrillMeAutomator(
            questions=3,
            options_list=["1", "2", "3"],
            dry_run=False,
            auto_focus=True,
            auto_maximize=True,
        )

        dispatched_keys = []
        automator.dispatch_key = lambda vk: dispatched_keys.append(vk)

        with patch.object(automator, "_ensure_window_ready", return_value=False):
            ok = automator.execute_multi_question(total_questions=3, options=["1", "2", "3"])
            self.assertFalse(ok)
            self.assertEqual(len(dispatched_keys), 0)

    def test_pure_keyboard_exact_3_presses_for_3_questions_no_1233(self):
        """Verify fix for '1233' defect: 3 questions dispatch exactly ['1', '2', '3'] with 0 repeated last option."""
        automator = GrillMeAutomator(
            questions=3,
            options_list=["1", "2", "3"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )

        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator.execute_multi_question(total_questions=3, options=["1", "2", "3"])
        self.assertTrue(ok)

        # Expected: FOCUS.1, FOCUS.2, OPT.1 ('1'), OPT.2 ('2'), OPT.3 ('3') -> exactly 5 steps
        step_codes = [s[0] for s in executed_steps]
        self.assertEqual(step_codes, ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3"])
        self.assertEqual(len(executed_steps), 5)

        opt_descriptions = [s[1] for s in executed_steps if s[0].startswith("OPT.")]
        self.assertEqual(len(opt_descriptions), 3)
        self.assertIn("[1]", opt_descriptions[0])
        self.assertIn("[2]", opt_descriptions[1])
        self.assertIn("[3]", opt_descriptions[2])

        # Verify NO 4th press exists (which would have repeated [3])
        self.assertFalse(any("OPT.4" in s[0] for s in executed_steps))
        self.assertFalse(any("Option press 4" in s[1] for s in executed_steps))

    @patch("step_2_chat_and_focus.step2_gui_chat_select.user32.GetForegroundWindow", return_value=0x9999)
    @patch("step_2_chat_and_focus.step2_gui_chat_select.user32.IsWindow", return_value=True)
    @patch("step_2_chat_and_focus.step2_gui_chat_select.get_process_info_for_hwnd", return_value=(9999, "msedge.exe", r"C:\Edge\msedge.exe"))
    def test_step2_gui_chat_select_blocks_ctrl_l_on_browser_window(self, mock_proc, mock_is_win, mock_fg):
        """Verify Step 2 select_chat aborts and refuses to dispatch Ctrl+L when foreground is a browser."""
        from step_2_chat_and_focus.step2_gui_chat_select import AntigravityGUISelector

        res = AntigravityGUISelector.select_chat(
            target_cid="test_cid",
            hwnd=0x1234,  # Antigravity HWND
            dry_run=False,
        )

        self.assertFalse(res["success"])
        self.assertFalse(res["chat_focused"])


    def test_multi_question_defaults_option_1_for_all_n(self):
        """Verify for N=1..5, all questions select Option 1, with zero option 2 on last question and zero '3 3'."""
        for n in range(1, 6):
            automator = GrillMeAutomator(
                questions=n,
                dry_run=True,
                auto_focus=False,
                auto_maximize=False,
            )
            self.assertEqual(automator.total_questions, n)
            self.assertEqual(automator.options_list, ["1"] * n)

            executed_steps = []
            automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
            automator.engine = "ctypes"

            ok = automator.execute_multi_question(total_questions=n, options=automator.options_list)
            self.assertTrue(ok)

            opt_steps = [s[1] for s in executed_steps if s[0].startswith("OPT.")]
            self.assertEqual(len(opt_steps), n)
            for opt_desc in opt_steps:
                self.assertIn("[1]", opt_desc)
                self.assertNotIn("[2]", opt_desc)
                self.assertNotIn("[3]", opt_desc)

    def test_padding_strictly_with_1_never_repeats_last_option(self):
        """Verify padding strictly appends '1', never repeating last option (e.g. ['1', '3'] -> ['1', '3', '1', '1'])."""
        automator = GrillMeAutomator(
            questions=4,
            options_list=["1", "3"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )
        self.assertEqual(automator.options_list, ["1", "3", "1", "1"])
        self.assertNotEqual(automator.options_list, ["1", "3", "3", "3"])

        # Also verify in _execute_pure_keyboard
        executed_steps = []
        automator._execute_step = lambda sc, d, fn: executed_steps.append((sc, d))
        automator.engine = "ctypes"

        ok = automator._execute_pure_keyboard(total_questions=4, options=["1", "3"])
        self.assertTrue(ok)
        opt_steps = [s[1] for s in executed_steps if s[0].startswith("OPT.")]
        self.assertEqual(len(opt_steps), 4)
        self.assertIn("[1]", opt_steps[0])
        self.assertIn("[3]", opt_steps[1])
        self.assertIn("[1]", opt_steps[2])  # Strictly '1', NEVER repeated '3'
        self.assertIn("[1]", opt_steps[3])  # Strictly '1', NEVER repeated '3'

    def test_cdp_hybrid_strictly_pads_with_1_never_repeats_last_option(self):
        """Verify _execute_cdp_hybrid pads with '1' and never repeats opts[-1] (prevents '3 3' repeats)."""
        automator = GrillMeAutomator(
            questions=4,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )
        mock_cdp = MagicMock()
        mock_cdp.get_questionnaire_status.return_value = {"has_card": True}
        mock_cdp.is_chat_input_focused.return_value = False

        selected_options = []
        mock_cdp.select_option.side_effect = lambda idx: selected_options.append(idx)

        # Pass options with fewer items than tq=4: e.g. ['1', '2']
        ok = automator._execute_cdp_hybrid(mock_cdp, total_questions=4, options=["1", "2"])
        self.assertTrue(ok)
        # Must select 1, 2, 1, 1 (NOT 1, 2, 2, 2!)
        self.assertEqual(selected_options, [1, 2, 1, 1])

    def test_step2_preserves_transcript_question_count_against_dom_inflation(self):
        """Verify Step 2 preserves ground truth questions list count and does not let DOM inflate it."""
        from step_2_chat_and_focus.step2_gui_chat_select import run_step2
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            st_path = Path(tmpdir) / "target_chat.json"
            initial_state = {
                "success": True,
                "data": {
                    "conversation_id": "test_ground_truth_cid",
                    "questions_count": 2,
                    "total_questions_count": 2,
                    "questions": [
                        {"question_index": 1, "question": "Q1", "options": ["(Recommended) A", "B"]},
                        {"question_index": 2, "question": "Q2", "options": ["(Recommended) X", "Y"]},
                    ],
                    "selections": [
                        {"question_index": 1, "selected_option_index": 1},
                        {"question_index": 2, "selected_option_index": 1},
                    ]
                }
            }
            with open(st_path, "w", encoding="utf-8") as f:
                json.dump(initial_state, f)

            with patch("step_2_chat_and_focus.step2_gui_chat_select.AntigravityGUISelector.select_chat") as mock_sel:
                # Simulate DOM reporting 5 questions (e.g. falsely inflated DOM count)
                mock_sel.return_value = {
                    "success": True,
                    "method": "cdp_mock",
                    "total_questions": 5,
                    "options_count": 3,
                    "current_question": 1,
                    "screen_coordinates": None,
                }
                ret = run_step2(state_file=str(st_path), dry_run=True)
                self.assertEqual(ret, 0)

            with open(st_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                saved_data = saved["data"]

            # Ground truth 2 questions must NOT be overwritten by DOM's 5!
            self.assertEqual(saved_data["total_questions_count"], 2)
            self.assertEqual(saved_data["questions_count"], 2)

    def test_step1_question_payload_strict_default_option_1(self):
        """Verify QuestionPayload defaults recommended_option_index to 1 when no option is marked recommended."""
        from step_1_chat_identifier.step1_find_and_focus import QuestionPayload
        payload = QuestionPayload(
            question_index=1,
            question="Unmarked Question",
            options=["Option A (Normal)", "Option B (Another)", "Option C (Third)"]
        )
        self.assertEqual(payload.recommended_option_index, 1)
        self.assertEqual(payload.recommended_option_text, "Option A (Normal)")

if __name__ == "__main__":
    unittest.main()

