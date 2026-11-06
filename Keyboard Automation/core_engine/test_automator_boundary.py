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
        """Verify N=1 executes exactly 1 loop: Q1.1, Q1.2, Q1.3, Q1.4 with zero phantom steps."""
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
        self.assertEqual(step_codes, ["Q1.1", "Q1.2", "Q1.3", "Q1.4"])
        self.assertEqual(len(executed_steps), 4)
        # Verify final Enter description
        self.assertIn("Submit ALL 1 answers", executed_steps[3][1])

    def test_execute_multi_question_n2_exact_keystroke_boundary(self):
        """Verify N=2 executes Q1(1-4) and Q2(1-4), total 8 steps (Q1 advances with Continue, Q2 submits with Submit)."""
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
        expected_codes = ["Q1.1", "Q1.2", "Q1.3", "Q1.4", "Q2.1", "Q2.2", "Q2.3", "Q2.4"]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 8)
        # Verify intermediate Q1 executes Enter to Advance [Continue] to Question 2
        self.assertIn("Advance [Continue] to Question 2", executed_steps[3][1])
        # Verify final Q2 executes Enter to submit all answers
        self.assertIn("Submit ALL 2 answers", executed_steps[7][1])

    def test_execute_multi_question_n3_exact_keystroke_boundary(self):
        """Verify N=3 executes Q1(1-4), Q2(1-4), Q3(1-4): total 12 steps (Q1/Q2 Continue, Q3 Submit)."""
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
        expected_codes = [
            "Q1.1", "Q1.2", "Q1.3", "Q1.4",
            "Q2.1", "Q2.2", "Q2.3", "Q2.4",
            "Q3.1", "Q3.2", "Q3.3", "Q3.4"
        ]
        self.assertEqual(step_codes, expected_codes)
        self.assertEqual(len(executed_steps), 12)
        self.assertIn("Advance [Continue] to Question 2", executed_steps[3][1])
        self.assertIn("Advance [Continue] to Question 3", executed_steps[7][1])
        self.assertIn("Submit ALL 3 answers", executed_steps[11][1])

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
        """Verify N=4 dynamically executes Q1..Q3 (Continue) + Q4 (Submit): total 16 steps."""
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
        self.assertEqual(len(executed_steps), 16)
        step_codes = [s[0] for s in executed_steps]
        expected_codes = [
            "Q1.1", "Q1.2", "Q1.3", "Q1.4",
            "Q2.1", "Q2.2", "Q2.3", "Q2.4",
            "Q3.1", "Q3.2", "Q3.3", "Q3.4",
            "Q4.1", "Q4.2", "Q4.3", "Q4.4"
        ]
        self.assertEqual(step_codes, expected_codes)
        self.assertIn("Advance [Continue] to Question 2", executed_steps[3][1])
        self.assertIn("Advance [Continue] to Question 3", executed_steps[7][1])
        self.assertIn("Advance [Continue] to Question 4", executed_steps[11][1])
        self.assertIn("Submit ALL 4 answers", executed_steps[15][1])

    def test_execute_multi_question_n5_exact_keystroke_boundary(self):
        """Verify N=5 dynamically executes Q1..Q4 (Continue) + Q5 (Submit): total 20 steps."""
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
        self.assertEqual(len(executed_steps), 20)
        self.assertIn("Advance [Continue] to Question 2", executed_steps[3][1])
        self.assertIn("Advance [Continue] to Question 3", executed_steps[7][1])
        self.assertIn("Advance [Continue] to Question 4", executed_steps[11][1])
        self.assertIn("Advance [Continue] to Question 5", executed_steps[15][1])
        self.assertIn("Submit ALL 5 answers", executed_steps[19][1])

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
        """Verify exact sequence: Q1 has (Ctrl+L, Shift+Tab, Option, Continue Enter), Q2 has (Ctrl+L, Shift+Tab, Option, Submit Enter) without space."""
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
        # 4 steps for intermediate Q1 + 4 steps for final Q2 = 8 steps
        self.assertEqual(len(executed_steps), 8)

        # Verify Q1 sequence (Intermediate: Continue Enter)
        self.assertIn("Ctrl + L", executed_steps[0][1])
        self.assertIn("Shift + Tab", executed_steps[1][1])
        self.assertIn("[1]", executed_steps[2][1])
        self.assertIn("Advance [Continue] to Question 2", executed_steps[3][1])

        # Verify Q2 sequence (Final: Submit Enter)
        self.assertIn("Ctrl + L", executed_steps[4][1])
        self.assertIn("Shift + Tab", executed_steps[5][1])
        self.assertIn("[1]", executed_steps[6][1])
        self.assertIn("Submit ALL 2 answers", executed_steps[7][1])

        # Verify NO step executed space
        for sc, d in executed_steps:
            self.assertNotIn("space", d.lower())

    def test_enter_gate_dispatches_vk_return_on_all_questions(self):
        """Verify Enter Gate dispatches VK_RETURN on intermediate (Continue) and final (Submit) questions."""
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

        # VK_RETURN (0x0D) should have been dispatched exactly 3 times (Q1 Continue, Q2 Continue, Q3 Submit)
        from core_engine.constants import VK_RETURN
        self.assertEqual(dispatched_keys, [VK_RETURN, VK_RETURN, VK_RETURN])

        # Verify intermediate question logging confirmed Continue Enter
        self.assertTrue(any("Advance [Continue] to Question 2" in m for m in logged_messages))
        self.assertTrue(any("Advance [Continue] to Question 3" in m for m in logged_messages))
        # Verify final question logging confirmed submitting with Enter
        self.assertTrue(any("Submit ALL 3 answers on final question" in m for m in logged_messages))

    def test_single_question_n1_selects_option_and_submits_without_skipping(self):
        """Verify single question (N=1) flow selects option 1 and submits via Enter without triggering Skip button."""
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
        self.assertEqual(executed_steps[0][0], "Q1.1")
        self.assertEqual(executed_steps[1][0], "Q1.2")
        self.assertEqual(executed_steps[2][0], "Q1.3")
        self.assertIn("[1]", executed_steps[2][1])
        self.assertEqual(executed_steps[3][0], "Q1.4")
        self.assertIn("Submit ALL 1 answers", executed_steps[3][1])

        # Verify none of the steps activate or target Skip
        for sc, desc in executed_steps:
            self.assertNotIn("skip", desc.lower())

    def test_execute_multi_question_n5_intermediate_continue_and_final_submit(self):
        """Verify N=5 flow guarantees Q1->Continue, Q2->Continue, Q3->Continue, Q4->Continue, Q5->Submit."""
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
        self.assertEqual(len(executed_steps), 20)

        step_map = {sc: d for sc, d in executed_steps}
        # Check every intermediate question executes Continue
        self.assertIn("Advance [Continue] to Question 2", step_map["Q1.4"])
        self.assertIn("Advance [Continue] to Question 3", step_map["Q2.4"])
        self.assertIn("Advance [Continue] to Question 4", step_map["Q3.4"])
        self.assertIn("Advance [Continue] to Question 5", step_map["Q4.4"])
        # Check final question executes Submit
        self.assertIn("Submit ALL 5 answers", step_map["Q5.4"])

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
            self.assertIn("Submit ALL 1 answers", executed_steps[3][1])

if __name__ == "__main__":
    unittest.main()
