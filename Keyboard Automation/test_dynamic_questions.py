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
  - Step 4: Enter Gate (Strictly SUPPRESSED on intermediate questions 1..N-1,
                        and strictly FIRED ONLY on the final question N).
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
        """Verify that automator accurately extracts questions count and options from target_chat.json."""
        automator = GrillMeAutomator(
            questions="auto",
            dry_run=True,
            auto_focus=False,
            auto_maximize=False,
            step_delay=0.01,
        )
        # target_chat.json in Identify Chat currently has 3 questions
        self.assertEqual(automator.total_questions, 3)
        self.assertEqual(len(automator.options_list), 3)
        self.assertEqual(automator.options_list, ["1", "1", "1"])

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
        """Verify N=2: Suppresses Enter on Q1, presses Enter on Q2."""
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
        # Q1 has 3 steps (NO Q1.4 Enter), Q2 has 4 steps (WITH Q2.4 Enter)
        self.assertEqual(step_names, ["Q1.1", "Q1.2", "Q1.3", "Q2.1", "Q2.2", "Q2.3", "Q2.4"])
        self.assertIn("Select Option 1", executed_steps[2][1])
        self.assertIn("Select Option 2", executed_steps[5][1])
        self.assertIn("Enter", executed_steps[6][1])

    def test_three_questions_n3(self):
        """Verify N=3: Suppresses Enter on Q1 and Q2, presses Enter ONLY on Q3."""
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
        # Q1: 3 steps, Q2: 3 steps, Q3: 4 steps -> total 10 steps
        self.assertEqual(len(step_names), 10)
        self.assertEqual(step_names, [
            "Q1.1", "Q1.2", "Q1.3",
            "Q2.1", "Q2.2", "Q2.3",
            "Q3.1", "Q3.2", "Q3.3", "Q3.4"
        ])
        # Only the very last step is Enter
        enter_steps = [s for s in executed_steps if "Enter" in s[1]]
        self.assertEqual(len(enter_steps), 1)
        self.assertEqual(enter_steps[0][0], "Q3.4")

    def test_four_questions_n4(self):
        """Verify N=4: Suppresses Enter on Q1..Q3, presses Enter ONLY on Q4."""
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
        # Q1..Q3: 3 steps each (9) + Q4: 4 steps = 13 steps
        self.assertEqual(len(step_names), 13)
        self.assertEqual(step_names[-1], "Q4.4")
        self.assertIn("Enter", executed_steps[-1][1])

    def test_five_questions_n5(self):
        """Verify N=5: Suppresses Enter on Q1..Q4, presses Enter ONLY on Q5."""
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
        # Q1..Q4: 3 steps each (12) + Q5: 4 steps = 16 steps
        self.assertEqual(len(step_names), 16)
        self.assertEqual(step_names[-1], "Q5.4")
        self.assertIn("Enter", executed_steps[-1][1])

    def test_dynamic_scaling_options_padding(self):
        """Verify options_list dynamically scales to ['1'] * N when not provided or partial."""
        # Partial options provided: '2,3' for 5 questions
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
        """Verify skip_enter suppresses Enter even on the final question."""
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

        # No step should be Enter
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


if __name__ == "__main__":
    unittest.main()
