#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Test Suite: Question Detection Subsystem
=============================================
Workspace: AutoSelect-Commander
Target Module: Question Detection/detect_questions.py

Tests:
- QuestionDetector instantiation and configuration defaults
- Deterministic simulation mode for N=1, N=2, N=3, N=5
- Text-based regex and pattern detection heuristics
- Fallback resolution when window is absent
- JSON output serialization and schema contract validation
- CLI argument parsing
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root and Question Detection to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QD_DIR = PROJECT_ROOT / "Question Detection"
if str(QD_DIR) not in sys.path:
    sys.path.insert(0, str(QD_DIR))

from detect_questions import (
    QuestionDetector,
    parse_arguments,
    DEFAULT_TARGET_WINDOW,
    DEFAULT_OUTPUT_FILENAME
)


class TestQuestionDetector(unittest.TestCase):
    """Test cases for QuestionDetector class."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_json = Path(self.temp_dir.name) / "test_question_count.json"
        self.detector = QuestionDetector(
            target_window="TestWindow",
            fallback_count=1,
            output_file=str(self.output_json),
            verbose=False
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detector_initialization(self):
        """Verify detector attributes on initialization."""
        self.assertEqual(self.detector.target_window, "TestWindow")
        self.assertEqual(self.detector.fallback_count, 1)
        self.assertEqual(self.detector.output_file, str(self.output_json))

    def test_simulation_single_question(self):
        """Verify simulation of N=1 question."""
        res = self.detector.simulate(1)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["question_count"], 1)
        self.assertEqual(res["mode"], "simulated")
        self.assertEqual(res["confidence"], 1.0)
        self.assertEqual(len(res["details"]["questions"]), 1)
        self.assertEqual(res["details"]["questions"][0]["index"], 1)

    def test_simulation_multi_questions(self):
        """Verify simulation of N=3 questions."""
        res = self.detector.simulate(3, reason="Test Runner")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["question_count"], 3)
        self.assertEqual(res["mode"], "simulated")
        self.assertEqual(len(res["details"]["questions"]), 3)
        self.assertEqual(res["details"]["reason"], "Test Runner")
        self.assertEqual(res["details"]["questions"][2]["index"], 3)

    def test_simulation_clamping(self):
        """Verify counts < 1 clamp gracefully to 1."""
        res = self.detector.simulate(0)
        self.assertEqual(res["question_count"], 1)

    def test_detect_from_text_explicit_total(self):
        """Verify pattern matching for 'Question 1 of 4'."""
        sample_text = "Please answer the following: Question 1 of 4: Which branch strategy to use?"
        match = self.detector.detect_from_text(sample_text)
        self.assertIsNotNone(match)
        self.assertEqual(match["count"], 4)
        self.assertEqual(match["method"], "text_pattern_total_of")

    def test_detect_from_text_sequential_headers(self):
        """Verify pattern matching for sequential 'Question 1', 'Question 2' headers."""
        sample_text = (
            "Interactive Quiz:\n"
            "Question 1: Select deployment environment\n"
            "1) Production  2) Staging\n"
            "Question 2: Select database engine\n"
            "1) PostgreSQL  2) SQLite\n"
        )
        match = self.detector.detect_from_text(sample_text)
        self.assertIsNotNone(match)
        self.assertEqual(match["count"], 2)
        self.assertEqual(match["method"], "text_pattern_sequential_headers")

    def test_detect_from_text_numbered_prompts(self):
        """Verify pattern matching for numbered questions ending in question marks."""
        sample_text = (
            "1. Would you like to enable logging?\n"
            "   (a) Yes  (b) No\n"
            "2. Would you like to run in background?\n"
            "   (a) Yes  (b) No\n"
        )
        match = self.detector.detect_from_text(sample_text)
        self.assertIsNotNone(match)
        self.assertEqual(match["count"], 2)

    def test_detect_from_text_empty_or_no_match(self):
        """Verify None returned for non-matching text."""
        self.assertIsNone(self.detector.detect_from_text(""))
        self.assertIsNone(self.detector.detect_from_text("Just plain text with no questions."))

    def test_detect_fallback_when_window_not_found(self):
        """Verify fallback behavior when target window does not exist."""
        # Use an impossible target window title
        detector = QuestionDetector(
            target_window="NonExistentWindow_9876543210_XYZ",
            fallback_count=2,
            output_file=str(self.output_json)
        )
        res = detector.detect()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["question_count"], 2)
        self.assertEqual(res["mode"], "fallback")
        self.assertEqual(res["details"]["method"], "window_not_found_fallback")

    def test_save_result(self):
        """Verify save_result writes valid, reloadable JSON."""
        res = self.detector.simulate(2)
        prim, sec = self.detector.save_result(res)
        
        self.assertTrue(prim.is_file())
        with open(prim, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["question_count"], 2)
        self.assertEqual(loaded["status"], "success")


class TestQuestionDetectionCLI(unittest.TestCase):
    """Test cases for argument parsing and CLI integration."""

    def test_cli_parsing_simulation(self):
        """Verify --simulate flag parsing."""
        test_args = ["--simulate", "4", "--output", "custom.json"]
        import sys
        orig_argv = sys.argv
        try:
            sys.argv = ["detect_questions.py"] + test_args
            args = parse_arguments()
            self.assertEqual(args.simulate, 4)
            self.assertEqual(args.output, "custom.json")
        finally:
            sys.argv = orig_argv

    def test_cli_parsing_detect_flag(self):
        """Verify --detect flag parsing."""
        test_args = ["--detect", "--fallback", "3"]
        import sys
        orig_argv = sys.argv
        try:
            sys.argv = ["detect_questions.py"] + test_args
            args = parse_arguments()
            self.assertTrue(args.detect)
            self.assertEqual(args.fallback, 3)
        finally:
            sys.argv = orig_argv


if __name__ == "__main__":
    unittest.main()
