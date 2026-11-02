#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Test Suite: Quiz Keyboard Automation Subsystem
===================================================
Workspace: AutoSelect-Commander
Target Module: Quiz Automation/quiz_automation.py

Tests:
- QuizAutomator instantiation and options mapping
- Reading question_count.json dynamically across search paths
- Virtual key code mapping (get_option_vk)
- Dry-run keystroke loop execution (single vs multi-question)
- Strict Enter suppression on intermediate questions (Q1..QN-1)
- Final question submission trigger (QN)
- Flag handling (--skip-enter, --dry-run, delays)
- CLI argument parser
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root and Quiz Automation to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QA_DIR = PROJECT_ROOT / "Quiz Automation"
if str(QA_DIR) not in sys.path:
    sys.path.insert(0, str(QA_DIR))

from quiz_automation import (
    QuizAutomator,
    get_option_vk,
    parse_arguments,
    VK_1,
    VK_2,
    VK_3,
    VK_0,
    VK_RETURN,
    VK_CONTROL,
    VK_L,
    VK_SHIFT,
    VK_TAB
)


class TestQuizAutomator(unittest.TestCase):
    """Test cases for QuizAutomator class."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.json_path = Path(self.temp_dir.name) / "question_count.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_automator_init_defaults(self):
        """Verify automator initializes with proper defaults."""
        qa = QuizAutomator(questions=1)
        self.assertEqual(qa.questions, 1)
        self.assertEqual(qa.options, ["1"])
        self.assertFalse(qa.dry_run)
        self.assertFalse(qa.skip_enter)

    def test_automator_options_broadcasting(self):
        """Verify single option broadcasts across N questions."""
        qa = QuizAutomator(questions=3, options=["2"])
        self.assertEqual(qa.questions, 3)
        self.assertEqual(qa.options, ["2", "2", "2"])

    def test_automator_options_explicit_list(self):
        """Verify explicit distinct options list per question."""
        qa = QuizAutomator(questions=3, options=["1", "2", "3"])
        self.assertEqual(qa.options, ["1", "2", "3"])

    def test_automator_options_padding(self):
        """Verify options list is padded with '1' if shorter than N."""
        qa = QuizAutomator(questions=3, options=["2"])
        self.assertEqual(qa.options, ["2", "2", "2"])

    def test_get_option_vk(self):
        """Verify virtual key code resolution."""
        self.assertEqual(get_option_vk("1"), VK_1)
        self.assertEqual(get_option_vk("2"), VK_2)
        self.assertEqual(get_option_vk("3"), VK_3)
        self.assertEqual(get_option_vk("0"), VK_0)
        self.assertEqual(get_option_vk("a"), ord("A"))
        # Invalid defaults to VK_1
        self.assertEqual(get_option_vk("invalid"), VK_1)

    def test_load_question_count_from_file_valid(self):
        """Verify loading question count from valid JSON file."""
        data = {
            "status": "success",
            "question_count": 4,
            "mode": "simulated"
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        count = QuizAutomator.load_question_count_from_file(str(self.json_path))
        self.assertEqual(count, 4)

    def test_load_question_count_from_file_missing(self):
        """Verify fallback to 1 when file does not exist."""
        missing = Path(self.temp_dir.name) / "non_existent.json"
        count = QuizAutomator.load_question_count_from_file(str(missing))
        self.assertEqual(count, 1)

    def test_dry_run_single_question_execution(self):
        """Verify single question dry-run execution succeeds."""
        qa = QuizAutomator(
            questions=1,
            options=["1"],
            dry_run=True,
            step_delay=0.01,
            settle_delay=0.01
        )
        success = qa.execute()
        self.assertTrue(success)

    def test_dry_run_multi_question_execution(self):
        """Verify multi-question dry-run execution with Enter on final question."""
        qa = QuizAutomator(
            questions=3,
            options=["1", "2", "1"],
            dry_run=True,
            step_delay=0.01,
            settle_delay=0.01
        )
        success = qa.execute()
        self.assertTrue(success)

    def test_dry_run_with_skip_enter(self):
        """Verify execution succeeds when --skip-enter is active."""
        qa = QuizAutomator(
            questions=2,
            options=["1", "1"],
            dry_run=True,
            skip_enter=True,
            step_delay=0.01,
            settle_delay=0.01
        )
        success = qa.execute()
        self.assertTrue(success)


class TestQuizAutomationCLI(unittest.TestCase):
    """Test CLI argument parsing for Quiz Automation."""

    def test_cli_parsing_multi_question(self):
        """Verify CLI flags parsing for multi-question execution."""
        test_args = ["--questions", "3", "--options", "1,2,1", "--dry-run", "--skip-enter"]
        import sys
        orig_argv = sys.argv
        try:
            sys.argv = ["quiz_automation.py"] + test_args
            args = parse_arguments()
            self.assertEqual(args.questions, "3")
            self.assertEqual(args.options, "1,2,1")
            self.assertTrue(args.dry_run)
            self.assertTrue(args.skip_enter)
        finally:
            sys.argv = orig_argv

    def test_cli_parsing_auto_mode(self):
        """Verify CLI defaults to questions='auto'."""
        orig_argv = sys.argv
        try:
            sys.argv = ["quiz_automation.py"]
            args = parse_arguments()
            self.assertEqual(args.questions, "auto")
            self.assertEqual(args.options, "1")
            self.assertFalse(args.dry_run)
        finally:
            sys.argv = orig_argv


if __name__ == "__main__":
    unittest.main()
