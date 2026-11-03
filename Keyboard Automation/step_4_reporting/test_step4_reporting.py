#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
यूनिट टेस्ट - स्टेप 4 रिपोर्टिंग एवं डैशबोर्ड / Unit Tests for Step 4 Reporting & Visual Dashboard
=================================================================================================
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 4 Testing Suite)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 08 (QA & Testing) & Department 06 (Backend & API Engineering)
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure parent root and step_4_reporting are in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith("step_") else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

from step4_reporting import (
    Step4ReportingEngine,
    AutomationHistory,
    RunRecord,
    ChatHistory,
    QuestionDetail,
    get_last_input_tick,
    watch_for_user_input,
)
import importlib.util
_ca_path = _root_dir / "step_9_complete_automation" / "complete_automation.py"
if not _ca_path.is_file():
    _ca_path = _root_dir / "Complete Automation" / "complete_automation.py"
_ca_spec = importlib.util.spec_from_file_location(
    "complete_automation",
    str(_ca_path)
)
_ca_mod = importlib.util.module_from_spec(_ca_spec)
sys.modules["complete_automation"] = _ca_mod
_ca_spec.loader.exec_module(_ca_mod)
discover_pipeline_steps = _ca_mod.discover_pipeline_steps


class TestStep4Reporting(unittest.TestCase):
    """Thorough unit test suite for Step 4 reporting and visual dashboard engine."""

    def setUp(self):
        """Create an isolated temporary workspace for testing."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_step4_"))
        self.reports_dir = self.test_dir / "reports"
        self.history_file = self.reports_dir / "automation_history.json"
        self.state_file = self.test_dir / "target_chat.json"

        self.engine = Step4ReportingEngine(
            workspace_dir=self.test_dir,
            state_file_path=self.state_file,
            reports_dir=self.reports_dir,
            history_file_path=self.history_file,
        )

    def tearDown(self):
        """Clean up temporary test artifacts."""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_01_load_empty_history(self):
        """Test loading history when no file exists yet initializes zeroed metrics."""
        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 0)
        self.assertEqual(history.total_questions_answered, 0)
        self.assertEqual(history.total_runtime_seconds, 0.0)
        self.assertEqual(history.total_unique_chats, 0)
        self.assertEqual(len(history.chats), 0)

    def test_02_save_and_reload_history(self):
        """Test serializing history to Department 06 JSON envelope and reloading."""
        history = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=3,
            total_runtime_seconds=12.5,
            total_unique_chats=1,
            chats={
                "chat_101": {
                    "conversation_id": "chat_101",
                    "topic_summary": "Architecture Review",
                    "run_count": 2,
                    "total_questions": 3,
                    "runs": [],
                }
            }
        )
        saved = self.engine.save_history(history)
        self.assertTrue(saved)
        self.assertTrue(self.history_file.is_file())

        # Inspect raw JSON file for Dept 06 envelope compliance
        with open(self.history_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.assertTrue(raw.get("success"))
        self.assertIn("data", raw)
        self.assertIn("meta", raw)
        self.assertEqual(raw["data"]["total_pipeline_runs"], 2)

        # Reload through engine
        reloaded = self.engine.load_history()
        self.assertEqual(reloaded.total_pipeline_runs, 2)
        self.assertEqual(reloaded.total_questions_answered, 3)
        self.assertEqual(reloaded.total_unique_chats, 1)

    def test_03_ingest_no_pending_chats(self):
        """Verify that NO_PENDING_CHATS state does not increment run count."""
        state_data = {
            "success": False,
            "data": {
                "conversation_id": None,
                "status": "NO_PENDING_CHATS",
                "questions_count": 0,
                "questions": [],
            },
            "meta": {"timestamp": "2026-11-04T00:00:00Z"}
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        recorded, msg, run = self.engine.ingest_current_run()
        self.assertFalse(recorded)
        self.assertIsNone(run)

        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 0)
        self.assertEqual(history.total_questions_answered, 0)

    def test_04_ingest_single_question_run(self):
        """Verify ingesting a valid single-question run updates metrics and chat history."""
        state_data = {
            "success": True,
            "data": {
                "conversation_id": "conv_alpha_01",
                "topic_summary": "Step 4 Reporting Engine Design",
                "last_user_prompt": "Please build step 4 visual reporting",
                "selected_at": "2026-11-04T01:00:00+00:00",
                "status": "READY_FOR_GUI_SELECTION",
                "questions_count": 1,
                "total_questions_count": 1,
                "is_multi_question": False,
                "questions": [
                    {
                        "question_index": 1,
                        "question": "Which architecture department standard applies to reporting?",
                        "options": [
                            "(Recommended) Department 06 & Department 04",
                            "Department 01 only",
                            "Ad-hoc scripts"
                        ],
                        "recommended_option_index": 1,
                        "recommended_option_text": "(Recommended) Department 06 & Department 04",
                        "is_multi_select": False
                    }
                ],
                "selections": [
                    {
                        "question_index": 1,
                        "question": "Which architecture department standard applies to reporting?",
                        "selected_option_index": 1,
                        "selected_option_text": "(Recommended) Department 06 & Department 04",
                        "is_multi_select": False,
                        "total_options": 3,
                        "is_recommended": True
                    }
                ]
            },
            "meta": {
                "timestamp": "2026-11-04T01:00:00+00:00"
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        recorded, msg, run = self.engine.ingest_current_run(default_duration=5.2)
        self.assertTrue(recorded)
        self.assertIsNotNone(run)
        self.assertEqual(run.questions_count, 1)

        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 1)
        self.assertEqual(history.total_questions_answered, 1)
        self.assertGreater(history.total_runtime_seconds, 0)
        self.assertEqual(history.total_unique_chats, 1)
        self.assertIn("conv_alpha_01", history.chats)

        chat = history.chats["conv_alpha_01"]
        self.assertEqual(chat["run_count"], 1)
        self.assertEqual(chat["total_questions"], 1)
        self.assertEqual(len(chat["runs"]), 1)

        q0 = chat["runs"][0]["questions"][0]
        self.assertEqual(q0["selected_option_index"], 1)
        self.assertEqual(q0["selected_option_text"], "(Recommended) Department 06 & Department 04")
        self.assertEqual(len(q0["options"]), 3)

    def test_05_ingest_multi_question_run(self):
        """Verify ingesting multi-question run preserves all questions and options."""
        state_data = {
            "success": True,
            "data": {
                "conversation_id": "conv_multi_02",
                "topic_summary": "Grill-Me Multi-Option Questionnaire",
                "last_user_prompt": "Help configure deployment",
                "selected_at": "2026-11-04T01:30:00+00:00",
                "status": "READY_FOR_GUI_SELECTION",
                "questions_count": 2,
                "total_questions_count": 2,
                "is_multi_question": True,
                "questions": [
                    {
                        "question_index": 1,
                        "question": "Select target deployment tier:",
                        "options": ["(Recommended) Production", "Staging", "Local"],
                        "recommended_option_index": 1,
                        "recommended_option_text": "(Recommended) Production",
                        "is_multi_select": False
                    },
                    {
                        "question_index": 2,
                        "question": "Enable automated reporting?",
                        "options": ["(Recommended) Yes", "No"],
                        "recommended_option_index": 1,
                        "recommended_option_text": "(Recommended) Yes",
                        "is_multi_select": False
                    }
                ],
                "selections": [
                    {
                        "question_index": 1,
                        "question": "Select target deployment tier:",
                        "selected_option_index": 1,
                        "selected_option_text": "(Recommended) Production",
                    },
                    {
                        "question_index": 2,
                        "question": "Enable automated reporting?",
                        "selected_option_index": 1,
                        "selected_option_text": "(Recommended) Yes",
                    }
                ]
            },
            "meta": {"timestamp": "2026-11-04T01:30:00+00:00"}
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        recorded, msg, run = self.engine.ingest_current_run(default_duration=4.8)
        self.assertTrue(recorded)
        self.assertEqual(run.questions_count, 2)

        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 1)
        self.assertEqual(history.total_questions_answered, 2)

    def test_06_cumulative_multi_chat_runs(self):
        """Test chat-wise accumulation across multiple runs and distinct conversations."""
        # Run 1 on Chat A
        s1 = {
            "success": True,
            "data": {
                "conversation_id": "chat_A",
                "topic_summary": "First Chat",
                "selected_at": "2026-11-04T01:00:00+00:00",
                "status": "COMPLETED",
                "questions_count": 1,
                "questions": [{"question_index": 1, "question": "Q1?", "options": ["A", "B"], "recommended_option_index": 1}],
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(s1, f)
        self.engine.ingest_current_run(default_duration=3.0)

        # Run 2 on Chat A (second run with different selected_at)
        s2 = {
            "success": True,
            "data": {
                "conversation_id": "chat_A",
                "topic_summary": "First Chat Followup",
                "selected_at": "2026-11-04T01:05:00+00:00",
                "status": "COMPLETED",
                "questions_count": 1,
                "questions": [{"question_index": 1, "question": "Q2?", "options": ["X", "Y"], "recommended_option_index": 2}],
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(s2, f)
        self.engine.ingest_current_run(default_duration=4.0)

        # Run 3 on Chat B (new chat)
        s3 = {
            "success": True,
            "data": {
                "conversation_id": "chat_B",
                "topic_summary": "Second Chat",
                "selected_at": "2026-11-04T01:10:00+00:00",
                "status": "COMPLETED",
                "questions_count": 2,
                "questions": [
                    {"question_index": 1, "question": "QB1?", "options": ["1", "2"], "recommended_option_index": 1},
                    {"question_index": 2, "question": "QB2?", "options": ["3", "4"], "recommended_option_index": 1},
                ],
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(s3, f)
        self.engine.ingest_current_run(default_duration=5.0)

        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 3)
        self.assertEqual(history.total_questions_answered, 4)
        self.assertEqual(history.total_unique_chats, 2)
        self.assertEqual(history.chats["chat_A"]["run_count"], 2)
        self.assertEqual(history.chats["chat_B"]["run_count"], 1)

    def test_07_html_dashboard_generation(self):
        """Verify dashboard.html is correctly generated with Department 04 styling and tokens."""
        history = AutomationHistory(
            total_pipeline_runs=5,
            total_questions_answered=8,
            total_runtime_seconds=42.7,
            total_unique_chats=2,
            chats={
                "chat_101": {
                    "conversation_id": "chat_101",
                    "topic_summary": "Database Migration Plan",
                    "run_count": 2,
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_001",
                            "timestamp": "2026-11-04T01:00:00Z",
                            "duration_seconds": 6.2,
                            "questions_count": 1,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Which database engine should be targeted?",
                                    "options": ["(Recommended) PostgreSQL 16", "SQLite 3", "MySQL 8"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) PostgreSQL 16",
                                }
                            ]
                        }
                    ]
                }
            }
        )
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())

        content = html_path.read_text(encoding="utf-8")
        # Check title and doctype
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("AutoSelect-Commander • Telemetry Dashboard", content)

        # Check Department 04 CSS design tokens
        self.assertIn("--bg-primary: #0b0f17;", content)
        self.assertIn("--accent-emerald: #10b981;", content)
        self.assertIn("--accent-indigo: #6366f1;", content)

        # Check Summary Metrics
        self.assertIn('<div class="metric-value">5</div>', content)  # Total runs
        self.assertIn('<div class="metric-value">8</div>', content)  # Total questions
        self.assertIn('<div class="metric-value">2</div>', content)  # Total chats

        # Check embedded JSON store
        self.assertIn('id="history-data"', content)
        self.assertIn("Database Migration Plan", content)
        self.assertIn("(Recommended) PostgreSQL 16", content)

        # Check badge formatting
        self.assertIn("✓ Selected (Recommended)", content)

    def test_08_get_last_input_tick(self):
        """Test Win32 GetLastInputInfo returns a valid integer tick count."""
        tick = get_last_input_tick()
        self.assertIsInstance(tick, int)
        self.assertGreater(tick, 0)

    @patch("step4_reporting.get_last_input_tick")
    def test_09_watch_for_user_input_timeout(self, mock_tick):
        """Verify watch_for_user_input times out safely when no user movement occurs."""
        mock_tick.return_value = 5000000
        detected = watch_for_user_input(timeout=0.1, poll_interval=0.02)
        self.assertFalse(detected)

    @patch("step4_reporting.get_last_input_tick")
    def test_09b_watch_for_user_input_detects_activity(self, mock_tick):
        """Verify watch_for_user_input detects movement when tick changes."""
        mock_tick.side_effect = [1000, 1000, 2000]
        detected = watch_for_user_input(timeout=1.0, poll_interval=0.01)
        self.assertTrue(detected)

    @patch("webbrowser.open_new_tab")
    def test_10_open_dashboard_manual_mode(self, mock_browser):
        """Verify open_dashboard generates HTML and triggers browser."""
        mock_browser.return_value = True
        opened = self.engine.open_dashboard()
        self.assertTrue(opened)
        self.assertTrue(self.engine.dashboard_file.is_file())
        mock_browser.assert_called_once()

    def test_11_step0_pipeline_discovery_recognizes_step4(self):
        """Verify Step 0's discover_pipeline_steps automatically detects Step 4 as PRESENT."""
        steps = discover_pipeline_steps(root_dir=_root_dir, include_future=True)
        step_map = {s.step_index: s for s in steps}
        self.assertIn(4, step_map)
        step4 = step_map[4]
        self.assertTrue(step4.exists(), f"Step 4 script should exist at {step4.script_path}")
        self.assertEqual(step4.name, "Step 4: Reporting & Telemetry")

    def test_12_idempotency_guard_skips_same_selected_at(self):
        """Verify duplicate calls with identical selected_at timestamp are skipped."""
        s = {
            "success": True,
            "data": {
                "conversation_id": "chat_idem_01",
                "topic_summary": "Idempotency Test",
                "selected_at": "2026-11-04T03:00:00+00:00",
                "status": "COMPLETED",
                "questions_count": 1,
                "questions": [{"question_index": 1, "question": "Q?", "options": ["A"], "recommended_option_index": 1}],
            }
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(s, f)

        # First call records run
        rec1, msg1, _ = self.engine.ingest_current_run()
        self.assertTrue(rec1)

        # Second call with exact same state file is skipped
        rec2, msg2, _ = self.engine.ingest_current_run()
        self.assertTrue(rec2)
        self.assertIn("idempotent", msg2.lower())

        history = self.engine.load_history()
        self.assertEqual(history.total_pipeline_runs, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
