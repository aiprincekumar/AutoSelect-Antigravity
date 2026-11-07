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

    def test_execute_multi_question_n1_exact_keystroke_boundary(self):
        """Verify N=1 executes: FOCUS.1, FOCUS.2, OPT.1, OPT.2 (total 4 steps, zero Enter/Space)."""
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
        self.assertEqual(step_codes, ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2"])
        self.assertEqual(len(executed_steps), 4)
        self.assertIn("Ctrl + L", executed_steps[0][1])
        self.assertIn("Shift + Tab", executed_steps[1][1])
        self.assertIn("Option press 1/2", executed_steps[2][1])
        self.assertIn("Option press 2/2", executed_steps[3][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n2_exact_keystroke_boundary(self):
        """Verify N=2 executes: FOCUS.1, FOCUS.2, OPT.1, OPT.2, OPT.3 (total 5 steps, zero Enter/Space)."""
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
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3"]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 5)
        self.assertIn("Option press 1/3", executed_steps[2][1])
        self.assertIn("Option press 2/3", executed_steps[3][1])
        self.assertIn("Option press 3/3", executed_steps[4][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n3_exact_keystroke_boundary(self):
        """Verify N=3 executes: FOCUS.1, FOCUS.2, OPT.1, OPT.2, OPT.3, OPT.4 (total 6 steps, zero Enter/Space)."""
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
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3", "OPT.4"]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 6)
        self.assertIn("Option press 1/4", executed_steps[2][1])
        self.assertIn("Option press 2/4", executed_steps[3][1])
        self.assertIn("Option press 3/4", executed_steps[4][1])
        self.assertIn("Option press 4/4", executed_steps[5][1])
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
        """Verify N=4 dynamically executes FOCUS.1, FOCUS.2, OPT.1..OPT.5: total 7 steps, zero Enter/Space."""
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
        self.assertEqual(len(executed_steps), 7)
        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3", "OPT.4", "OPT.5"]
        self.assertEqual(step_codes, expected_codes)
        self.assertIn("Option press 1/5", executed_steps[2][1])
        self.assertIn("Option press 2/5", executed_steps[3][1])
        self.assertIn("Option press 3/5", executed_steps[4][1])
        self.assertIn("Option press 4/5", executed_steps[5][1])
        self.assertIn("Option press 5/5", executed_steps[6][1])
        for sc, d in executed_steps:
            self.assertNotIn("enter", d.lower())
            self.assertNotIn("space", d.lower())

    def test_execute_multi_question_n5_exact_keystroke_boundary(self):
        """Verify N=5 dynamically executes FOCUS.1, FOCUS.2, OPT.1..OPT.6: total 8 steps, zero Enter/Space."""
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
        self.assertEqual(len(executed_steps), 8)
        step_codes = [s[0] for s in executed_steps]
        expected_codes = ["FOCUS.1", "FOCUS.2", "OPT.1", "OPT.2", "OPT.3", "OPT.4", "OPT.5", "OPT.6"]
        self.assertEqual(step_codes, expected_codes)
        self.assertIn("Option press 1/6", executed_steps[2][1])
        self.assertIn("Option press 6/6", executed_steps[7][1])
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
        """Verify exact sequence: N=2 executes single focus (Ctrl+L, Shift+Tab) followed by 3 option presses, with zero Enter and zero Space."""
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
        # 2 focus steps + 3 option press steps = 5 steps
        self.assertEqual(len(executed_steps), 5)

        # Verify initial focus sequence (1st time only)
        self.assertIn("Ctrl + L", executed_steps[0][1])
        self.assertIn("Shift + Tab", executed_steps[1][1])

        # Verify option presses (2+1 = 3 presses)
        self.assertIn("[1]", executed_steps[2][1])
        self.assertIn("[1]", executed_steps[3][1])
        self.assertIn("[1]", executed_steps[4][1])

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
        self.assertTrue(any("Option press 1/4" in m for m in logged_messages))
        self.assertTrue(any("Option press 4/4" in m for m in logged_messages))
        self.assertFalse(any("enter" in m.lower() for m in logged_messages))

        # Ensure dispatch_key helper itself still functions if called directly
        automator.dispatch_key(VK_RETURN)
        self.assertEqual(dispatched_keys, [VK_RETURN])

    def test_single_question_n1_selects_option_and_submits_without_skipping(self):
        """Verify single question (N=1) flow executes FOCUS.1, FOCUS.2, OPT.1, OPT.2 without triggering Skip button, Enter, or Space."""
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
        self.assertEqual(len(executed_steps), 4)
        self.assertEqual(executed_steps[0][0], "FOCUS.1")
        self.assertEqual(executed_steps[1][0], "FOCUS.2")
        self.assertEqual(executed_steps[2][0], "OPT.1")
        self.assertIn("[1]", executed_steps[2][1])
        self.assertEqual(executed_steps[3][0], "OPT.2")
        self.assertIn("[1]", executed_steps[3][1])

        # Verify none of the steps activate or target Skip, Enter, or Space
        for sc, desc in executed_steps:
            self.assertNotIn("skip", desc.lower())
            self.assertNotIn("enter", desc.lower())
            self.assertNotIn("space", desc.lower())

    def test_execute_multi_question_n5_option_sequence_and_no_enter(self):
        """Verify N=5 flow executes FOCUS.1, FOCUS.2, and OPT.1..OPT.6 with 0 Enter/Space."""
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
        self.assertEqual(len(executed_steps), 8)

        step_map = {sc: d for sc, d in executed_steps}
        self.assertIn("Focus chat box", step_map["FOCUS.1"])
        self.assertIn("Move backward to question options", step_map["FOCUS.2"])
        self.assertIn("[1] (Option press 1/6)", step_map["OPT.1"])
        self.assertIn("[2] (Option press 2/6)", step_map["OPT.2"])
        self.assertIn("[3] (Option press 3/6)", step_map["OPT.3"])
        self.assertIn("[1] (Option press 4/6)", step_map["OPT.4"])
        self.assertIn("[2] (Option press 5/6)", step_map["OPT.5"])
        # (N+1)-th press repeats last option
        self.assertIn("[2] (Option press 6/6)", step_map["OPT.6"])

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
        self.assertEqual(len(executed_steps), 3)
        self.assertEqual(executed_steps[0][0], "FOCUS.2")
        self.assertEqual(executed_steps[1][0], "OPT.1")
        self.assertEqual(executed_steps[2][0], "OPT.2")

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
            self.assertEqual(len(executed_steps), 4)
            self.assertEqual(executed_steps[0][0], "FOCUS.1")
            self.assertEqual(executed_steps[1][0], "FOCUS.2")
            self.assertEqual(executed_steps[2][0], "OPT.1")
            self.assertEqual(executed_steps[3][0], "OPT.2")
            self.assertIn("Option press 2/2", executed_steps[3][1])

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

if __name__ == "__main__":
    unittest.main()

