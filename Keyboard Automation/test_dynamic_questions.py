#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test Suite for Dynamic Question Scaling & Keyboard Automation
========================================================================
Validates that GrillMeAutomator dynamically adapts to any number of questions N
(1, 2, 3, 4, 5, ... N), correctly executing:
  - Step 1: Ctrl + L
  - Step 2: Shift + Tab
  - Step 3: Select Option Key
  - Step 4: Enter Gate (Advances wizard on intermediate questions 1..N-1,
                        and submits confirmation on final question N).
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from keyboard_automation.automator import GrillMeAutomator


class TestDynamicQuestionAutomation(unittest.TestCase):
    """Unit and simulation tests for dynamic multi-question automation."""

    def test_question_detection_from_target_chat(self):
        """Verify that automator accurately extracts questions count and options from state file."""
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({
                "success": True,
                "data": {
                    "questions_count": 3,
                    "questions": [
                        {"recommended_option_index": 1},
                        {"recommended_option_index": 2},
                        {"recommended_option_index": 1},
                    ]
                }
            }, f)
            temp_path = f.name

        try:
            automator = GrillMeAutomator(
                questions="auto",
                state_file=temp_path,
                dry_run=True,
                auto_focus=False,
                auto_maximize=False,
                step_delay=0.01,
            )
            self.assertEqual(automator.total_questions, 3)
            self.assertEqual(len(automator.options_list), 3)
            self.assertEqual(automator.options_list, ["1", "2", "1"])
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # Also verify default state file auto-detection works when state_file is None
        default_automator = GrillMeAutomator(
            questions="auto",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertGreaterEqual(default_automator.total_questions, 1)

    def test_single_question_n1(self):
        """Verify N=1: Executes sequence and presses Enter on Question 1."""
        automator = GrillMeAutomator(
            questions=1,
            option="1",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 1)
        self.assertEqual(automator.options_list, ["1"])

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        # Expected: Q1.1 (Ctrl+L), Q1.2 (Shift+Tab), Q1.3 (Opt 1), Q1.4 (Enter)
        step_names = [s[0] for s in executed_steps]
        self.assertEqual(step_names, ["Q1.1", "Q1.2", "Q1.3", "Q1.4"])
        self.assertIn("Enter", executed_steps[-1][1])

    def test_two_questions_n2(self):
        """Verify N=2: Presses Enter on Q1 (Continue), presses Enter on Q2 (Submit)."""
        automator = GrillMeAutomator(
            questions=2,
            options_list=["1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 2)
        self.assertEqual(automator.options_list, ["1", "2"])

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        step_names = [s[0] for s in executed_steps]
        # Q1 has 4 steps (WITH Q1.4 Enter Continue), Q2 has 4 steps (WITH Q2.4 Enter Submit)
        self.assertEqual(step_names, ["Q1.1", "Q1.2", "Q1.3", "Q1.4", "Q2.1", "Q2.2", "Q2.3", "Q2.4"])
        self.assertIn("Select Option 1", executed_steps[2][1])
        self.assertIn("Continue to Question 2", executed_steps[3][1])
        self.assertIn("Select Option 2", executed_steps[6][1])
        self.assertIn("Submit ALL 2 answers", executed_steps[7][1])

    def test_three_questions_n3(self):
        """Verify N=3: Presses Enter on Q1 (Continue), Q2 (Continue), Q3 (Submit)."""
        automator = GrillMeAutomator(
            questions=3,
            options_list="1,1,1",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 3)

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        step_names = [s[0] for s in executed_steps]
        # Q1: 4 steps, Q2: 4 steps, Q3: 4 steps -> total 12 steps
        self.assertEqual(len(step_names), 12)
        self.assertEqual(step_names, [
            "Q1.1", "Q1.2", "Q1.3", "Q1.4",
            "Q2.1", "Q2.2", "Q2.3", "Q2.4",
            "Q3.1", "Q3.2", "Q3.3", "Q3.4"
        ])
        enter_steps = [s for s in executed_steps if "Enter" in s[1]]
        self.assertEqual(len(enter_steps), 3)
        self.assertIn("Continue to Question 2", enter_steps[0][1])
        self.assertIn("Continue to Question 3", enter_steps[1][1])
        self.assertIn("Submit ALL 3 answers", enter_steps[2][1])

    def test_four_questions_n4(self):
        """Verify N=4: Presses Enter on Q1..Q3 (Continue), and Enter on Q4 (Submit)."""
        automator = GrillMeAutomator(
            questions=4,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 4)
        self.assertEqual(automator.options_list, ["1", "1", "1", "1"])

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        step_names = [s[0] for s in executed_steps]
        # 4 questions * 4 steps = 16 steps
        self.assertEqual(len(step_names), 16)
        self.assertEqual(step_names[-1], "Q4.4")
        self.assertIn("Submit ALL 4 answers", executed_steps[-1][1])

    def test_five_questions_n5(self):
        """Verify N=5: Presses Enter on Q1..Q4 (Continue), and Enter on Q5 (Submit)."""
        automator = GrillMeAutomator(
            questions=5,
            options_list=["1", "2", "3", "1", "2"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 5)
        self.assertEqual(automator.options_list, ["1", "2", "3", "1", "2"])

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        step_names = [s[0] for s in executed_steps]
        # 5 questions * 4 steps = 20 steps
        self.assertEqual(len(step_names), 20)
        self.assertEqual(step_names[-1], "Q5.4")
        self.assertIn("Submit ALL 5 answers", executed_steps[-1][1])

    def test_six_questions_n6(self):
        """Verify N=6: Dynamically scales to 6 questions with 24 ordered steps."""
        automator = GrillMeAutomator(
            questions=6,
            options_list=["1", "2", "1", "2", "3", "1"],
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertEqual(automator.total_questions, 6)
        self.assertEqual(len(automator.options_list), 6)

        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        self.assertEqual(len(executed_steps), 24)
        self.assertEqual(executed_steps[-1][0], "Q6.4")
        self.assertIn("Submit ALL 6 answers", executed_steps[-1][1])
        # Verify intermediate questions advance with Continue
        self.assertIn("Continue to Question 2", executed_steps[3][1])
        self.assertIn("Continue to Question 6", executed_steps[19][1])

    def test_singular_question_payload_format(self):
        """Verify detector extracts question when tool args use singular {'question': '...', 'options': [...]}."""
        from step1_find_and_focus import GrillMeDetector
        detector = GrillMeDetector()
        args = {
            "question": "सिंगल क्वेश्चन टेस्ट: क्या यह फीचर एक्टिवेट है?",
            "options": ["(Recommended) हाँ, एक्टिवेट करें", "नहीं, छोड़ दें"]
        }
        extracted = detector._extract_question_payloads(args)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0].question_index, 1)
        self.assertIn("सिंगल क्वेश्चन टेस्ट", extracted[0].question)
        self.assertEqual(extracted[0].recommended_option_index, 1)

    def test_transcript_full_priority_on_large_questions(self):
        """Verify detector prioritizes transcript_full.jsonl over truncated transcript.jsonl for N >= 4."""
        from step1_find_and_focus import GrillMeDetector
        detector = GrillMeDetector()
        # Test on live repository conversation that has 4 questions in full transcript
        chats = detector.scan_transcripts()
        if chats:
            # Check newest chat (e0645f63) has 4 questions, not 0 or 2
            top_chat = [c for c in chats if c.conversation_id == "e0645f63-cc82-41f8-8385-2538e9e8f6bf"]
            if top_chat:
                self.assertEqual(top_chat[0].total_questions_count, 4)
                self.assertTrue(top_chat[0].is_multi_question)

    def test_dynamic_scaling_options_padding(self):
        """Verify options_list dynamically scales to ['1'] * N when not provided or partial."""
        automator = GrillMeAutomator(
            questions=5,
            options_list="2,3",
            option="1",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
        )
        self.assertEqual(automator.total_questions, 5)
        self.assertEqual(automator.options_list, ["2", "3", "1", "1", "1"])

    def test_skip_enter_flag(self):
        """Verify skip_enter suppresses Enter across all questions."""
        automator = GrillMeAutomator(
            questions=3,
            skip_enter=True,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        enter_steps = [s for s in executed_steps if "Enter" in s[1]]
        self.assertEqual(len(enter_steps), 0)
        self.assertEqual(len(executed_steps), 9)  # 3 questions * 3 steps each

    def test_skip_ctrl_l_flag(self):
        """Verify skip_ctrl_l omits Ctrl+L on every question."""
        automator = GrillMeAutomator(
            questions=2,
            skip_ctrl_l=True,
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        executed_steps = []
        def mock_step(step_num, desc, action):
            executed_steps.append((str(step_num), desc))

        with patch.object(automator, "_execute_step", side_effect=mock_step):
            ok = automator.execute()
            self.assertTrue(ok)

        ctrl_l_steps = [s for s in executed_steps if "Ctrl + L" in s[1]]
        self.assertEqual(len(ctrl_l_steps), 0)

    def test_step3_identity_and_backward_compatibility(self):
        """Verify Step 3 naming, constants, and grill_me_automation backward-compatible wrapper."""
        import step3_keyboard_automation as s3
        import grill_me_automation as gm
        from keyboard_automation import Step3KeyboardAutomator, STEP_ID, STEP_NUMBER, STEP_NAME

        # Verify constants
        self.assertEqual(STEP_ID, "step3")
        self.assertEqual(STEP_NUMBER, 3)
        self.assertEqual(STEP_NAME, "Step 3: Keyboard Automation")
        self.assertEqual(s3.STEP_ID, "step3")
        self.assertEqual(gm.STEP_ID, "step3")

        # Verify class equivalence
        self.assertIs(Step3KeyboardAutomator, GrillMeAutomator)
        self.assertIs(s3.Step3KeyboardAutomator, s3.GrillMeAutomator)
        self.assertIs(gm.Step3KeyboardAutomator, gm.GrillMeAutomator)

        # Verify dry run execution on Step3KeyboardAutomator
        s3_automator = Step3KeyboardAutomator(
            questions=1,
            option="1",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        self.assertTrue(s3_automator.execute())


if __name__ == "__main__":
    unittest.main()
