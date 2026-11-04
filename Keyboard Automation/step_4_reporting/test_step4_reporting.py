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

    def test_13_three_tab_navigation_structure(self):
        """Verify dashboard HTML contains the three horizontal tabs (Overview, Chats, Questions) and dedicated search filters."""
        history = AutomationHistory(
            total_pipeline_runs=1,
            total_questions_answered=3,
            total_runtime_seconds=10.0,
            total_unique_chats=1,
            chats={
                "chat_tab_test": {
                    "conversation_id": "chat_tab_test",
                    "topic_summary": "Horizontal Tab Test",
                    "run_count": 1,
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_test_tab",
                            "timestamp": "2026-11-04T05:00:00Z",
                            "duration_seconds": 10.0,
                            "questions_count": 1,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Tab layout verified?",
                                    "options": ["(Recommended) Yes", "No"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) Yes",
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

        # 1. Verify Horizontal Tab Navigation bar & role attributes
        self.assertIn('<nav class="tab-nav" role="tablist"', content)

        # 2. Verify Tab 1 button: Overview
        self.assertIn('id="tab-btn-overview"', content)
        self.assertIn('data-tab="overview"', content)
        self.assertIn('<span class="tab-label">Overview</span>', content)

        # 3. Verify Tab 2 button: Chats with count badge
        self.assertIn('id="tab-btn-chats"', content)
        self.assertIn('data-tab="chats"', content)
        self.assertIn('<span class="tab-label">Chats</span>', content)
        self.assertIn('id="tab-chats-badge">1</span>', content)

        # 4. Verify Tab 3 button: Questions with question count badge
        self.assertIn('id="tab-btn-questions"', content)
        self.assertIn('data-tab="questions"', content)
        self.assertIn('<span class="tab-label">Questions</span>', content)
        self.assertIn('id="tab-questions-badge">3</span>', content)

        # 5. Verify Tab 1 panel: Overview (Single-row KPIs + SVG charts)
        self.assertIn('id="tab-overview" class="tab-panel active"', content)

        # 6. Verify Tab 2 panel: Chats (Summary stats + Search + Breakdown Table)
        self.assertIn('id="tab-chats" class="tab-panel"', content)
        self.assertIn('id="search-chats"', content)
        self.assertIn('id="summary-table"', content)
        self.assertIn('id="summary-tbody"', content)
        self.assertIn('📊 Chat-wise Automation Breakdown', content)

        # 7. Verify Tab 3 panel: Questions (Search + Questions Ledger)
        self.assertIn('id="tab-questions" class="tab-panel"', content)
        self.assertIn('id="search-questions"', content)
        self.assertIn('📝 Questions & Answers Ledger', content)
        self.assertIn('id="details-container"', content)

        # 8. Verify fallback compatibility for search hooks
        self.assertIn('id="search-box"', content)
        self.assertIn('id="search-overview"', content)

        # 9. Verify localStorage tab persistence logic in client script
        self.assertIn("localStorage.setItem('asc_dashboard_tab'", content)
        self.assertIn("localStorage.getItem('asc_dashboard_tab')", content)

    def test_14_eight_kpis_two_rows_and_dynamic_svg_visualizations(self):
        """Verify all 8 KPIs are present in exactly two balanced rows (4x2) and dynamic SVG charts render correctly."""
        history = AutomationHistory(
            total_pipeline_runs=4,
            total_questions_answered=8,
            total_runtime_seconds=24.0,
            total_unique_chats=2,
            chats={
                "chat_alpha": {
                    "conversation_id": "chat_alpha",
                    "topic_summary": "Alpha Microservice",
                    "run_count": 2,
                    "total_questions": 4,
                    "runs": [
                        {
                            "run_id": "run_01",
                            "timestamp": "2026-11-04T05:00:00Z",
                            "duration_seconds": 6.0,
                            "questions_count": 2,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Deploy target?",
                                    "options": ["(Recommended) Production", "Staging"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) Production",
                                    "is_recommended": True
                                }
                            ]
                        }
                    ]
                },
                "chat_beta": {
                    "conversation_id": "chat_beta",
                    "topic_summary": "Beta Frontend",
                    "run_count": 2,
                    "total_questions": 4,
                    "runs": [
                        {
                            "run_id": "run_02",
                            "timestamp": "2026-11-04T05:10:00Z",
                            "duration_seconds": 6.0,
                            "questions_count": 2,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Build tool?",
                                    "options": ["(Recommended) Vite", "Webpack"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) Vite",
                                    "is_recommended": True
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

        # 1. Verify Exactly Two Balanced Rows Layout Mandate (CSS repeat(4, 1fr))
        self.assertIn(".metrics-grid-2rows", content)
        self.assertIn("grid-template-columns: repeat(4, 1fr)", content)

        # 2. Verify Anti-Truncation CSS Rule (no clipping, white-space normal)
        self.assertIn("white-space: normal;", content)

        # 3. Verify all 8 KPI cards
        # Row 1: Primary Activity & Scale
        self.assertIn("Total Pipeline Runs", content)  # KPI 1
        self.assertIn('<div class="metric-value">4</div>', content)

        self.assertIn("Questions Answered", content)     # KPI 2
        self.assertIn('<div class="metric-value">8</div>', content)

        self.assertIn("Cumulative Runtime", content)     # KPI 3
        self.assertIn('<div class="metric-value">24.0s</div>', content)

        self.assertIn("Unique Chats Automated", content)  # KPI 4
        self.assertIn('<div class="metric-value">2</div>', content)

        # Row 2: Performance, Density & Speed
        self.assertIn("Mean Run Latency", content)       # KPI 5
        self.assertIn('<div class="metric-value">6.0s</div>', content)

        self.assertIn("Questions per Run", content)      # KPI 6
        self.assertIn("2.0", content)
        self.assertIn("Qs/run", content)

        self.assertIn("Questions per Chat", content)     # KPI 7
        self.assertIn("4.0", content)
        self.assertIn("Qs/chat", content)

        self.assertIn("Execution Speed", content)        # KPI 8
        self.assertIn("3.0s", content)
        self.assertIn("s/Q", content)

        # 4. Verify Pure Inline SVG Pipeline Diagram (Step 0 -> Step 4)
        self.assertIn("Step 0: Detector", content)
        self.assertIn("Step 1: Identifier", content)
        self.assertIn("Step 2: Focus", content)
        self.assertIn("Step 3: Selector", content)
        self.assertIn("Step 4: Reporter", content)
        self.assertIn('id="pipeline-arrow"', content)

        # 5. Verify Pure Inline SVG Bar Chart
        self.assertIn('barRunsGrad', content)
        self.assertIn('barQsGrad', content)
        self.assertIn("Chat Automation &amp; Questions Distribution", content.replace("&", "&amp;"))

        # 6. Verify Pure Inline SVG Workload & Topic Share Donut Chart
        self.assertIn("Chat Workload &amp; Topic Share", content.replace("&", "&amp;"))
        self.assertIn("TOTAL QS", content)

        # 7. Verify Pure Inline SVG Run Latency Trend Chart
        self.assertIn("Run Latency &amp; Performance Trend", content.replace("&", "&amp;"))
        self.assertIn("Mean Latency", content)
        self.assertIn("latencyLineGrad", content)
        self.assertIn("latencyAreaGrad", content)

    def test_15_interactive_multi_dimensional_filter_toolbar(self):
        """Verify the interactive multi-dimensional filter toolbar and client-side filter logic."""
        history = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=3,
            total_runtime_seconds=12.0,
            total_unique_chats=1,
            chats={
                "chat_filter_test": {
                    "conversation_id": "chat_filter_test",
                    "topic_summary": "Filter Test Chat",
                    "run_count": 2,
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_01",
                            "timestamp": "2026-11-04T02:00:00Z",
                            "duration_seconds": 4.5,
                            "questions_count": 1,
                            "questions": []
                        }
                    ]
                }
            }
        )
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        # 1. Filter toolbar container & header
        self.assertIn('<section class="filter-toolbar"', content)
        self.assertIn('id="filter-stats-badge"', content)
        self.assertIn('id="filter-count">2</span>', content)
        self.assertIn('id="filter-total">2</span>', content)

        # 2. Date Range filter inputs & presets
        self.assertIn('id="filter-date-from"', content)
        self.assertIn('id="filter-date-to"', content)
        self.assertIn('data-preset="all"', content)
        self.assertIn('data-preset="today"', content)
        self.assertIn('data-preset="7d"', content)

        # 3. Multi-dimensional dropdown selects
        self.assertIn('id="filter-chat"', content)
        self.assertIn('id="filter-complexity"', content)
        self.assertIn('id="filter-speed"', content)

        # 4. Reset Button
        self.assertIn('id="filter-reset-btn"', content)
        self.assertIn("Reset Filters", content)

        # 5. Client JavaScript filter engine functions
        self.assertIn("function runMatchesFilters", content)
        self.assertIn("function applyFilters", content)

    def test_16_svg_generator_methods_direct(self):
        """Directly test the SVG generation methods for edge cases (empty and populated)."""
        empty_history = AutomationHistory()
        # Empty trend SVG
        empty_trend = Step4ReportingEngine.build_latency_trend_svg(empty_history)
        self.assertIn("<svg", empty_trend)
        self.assertIn("No Run Latency Data Yet", empty_trend)

        # Empty topic share SVG
        empty_topic = Step4ReportingEngine.build_topic_share_svg(empty_history)
        self.assertIn("<svg", empty_topic)
        self.assertIn("No Workload Distribution Yet", empty_topic)

        # Populated history with runs
        history = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=3,
            total_runtime_seconds=15.0,
            total_unique_chats=1,
            chats={
                "chat_x": {
                    "conversation_id": "chat_x",
                    "topic_summary": "Architecture Review",
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_01",
                            "timestamp": "2026-11-04T01:00:00Z",
                            "duration_seconds": 7.0,
                            "questions_count": 1,
                        },
                        {
                            "run_id": "run_02",
                            "timestamp": "2026-11-04T02:00:00Z",
                            "duration_seconds": 8.0,
                            "questions_count": 2,
                        }
                    ]
                }
            }
        )
        pop_trend = Step4ReportingEngine.build_latency_trend_svg(history)
        self.assertIn("latencyLineGrad", pop_trend)
        self.assertIn("Mean: 7.5s", pop_trend)
        self.assertIn("R1", pop_trend)
        self.assertIn("R2", pop_trend)

        pop_topic = Step4ReportingEngine.build_topic_share_svg(history)
        self.assertIn("Architecture Review", pop_topic)
        self.assertIn("3 Qs", pop_topic)
        self.assertIn("100.0% share", pop_topic)

    def test_17_filter_toolbar_row_inversion_and_extended_presets(self):
        """Verify the Filter Toolbar row inversion ('Up वाला Down, Down वाला Up') and 7 rich presets."""
        history = AutomationHistory(
            total_pipeline_runs=3,
            total_questions_answered=5,
            total_runtime_seconds=18.0,
            total_unique_chats=1,
            chats={
                "chat_preset_test": {
                    "conversation_id": "chat_preset_test",
                    "topic_summary": "Filter Presets Test",
                    "run_count": 3,
                    "total_questions": 5,
                    "runs": []
                }
            }
        )
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        # 1. Verify Row Inversion: .filter-presets-row appears BEFORE .filter-controls-row
        pos_presets_row = content.find('class="filter-presets-row"')
        pos_controls_row = content.find('class="filter-controls-row"')
        self.assertNotEqual(pos_presets_row, -1, "filter-presets-row must exist")
        self.assertNotEqual(pos_controls_row, -1, "filter-controls-row must exist")
        self.assertLess(
            pos_presets_row,
            pos_controls_row,
            "filter-presets-row (Quick Presets Bar) must be placed on top before filter-controls-row"
        )

        # 2. Verify all 7 rich preset buttons with exact labels & data attributes
        presets_expected = [
            ('data-preset="all"', 'All Time'),
            ('data-preset="today"', 'Today'),
            ('data-preset="yesterday"', 'Yesterday'),
            ('data-preset="7d"', 'Last 7 Days'),
            ('data-preset="30d"', 'Last 30 Days'),
            ('data-preset="week"', 'This Week'),
            ('data-preset="month"', 'This Month'),
        ]
        for attr, label in presets_expected:
            self.assertIn(attr, content, f"Missing preset attribute {attr}")
            self.assertIn(label, content, f"Missing preset label {label}")

        # 3. Verify Filter Toolbar Header has Status Badge AND Collapse Button
        self.assertIn('id="filter-stats-badge"', content)
        self.assertIn('id="filter-collapse-btn"', content)
        self.assertIn('id="filter-toolbar-body"', content)

        # 4. Verify Granular Custom Controls in Row 2
        self.assertIn('id="filter-date-from"', content)
        self.assertIn('id="filter-date-to"', content)
        self.assertIn('id="filter-chat"', content)
        self.assertIn('id="filter-complexity"', content)
        self.assertIn('id="filter-speed"', content)
        self.assertIn('id="filter-reset-btn"', content)

        # 5. Verify JavaScript date math logic for all 7 presets
        self.assertIn("preset === 'yesterday'", content)
        self.assertIn("preset === '30d'", content)
        self.assertIn("preset === 'week'", content)
        self.assertIn("preset === 'month'", content)
        self.assertIn("function formatDate", content)

    def test_18_collapsible_sections_and_accordion_architecture(self):
        """Verify collapsible sections across the dashboard (Toolbar, Architecture, Charts, Chats, Questions)."""
        history = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=3,
            total_runtime_seconds=12.0,
            total_unique_chats=1,
            chats={
                "chat_accordion_test": {
                    "conversation_id": "chat_accordion_test",
                    "topic_summary": "Accordion Architecture Test",
                    "run_count": 2,
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_acc_01",
                            "timestamp": "2026-11-04T06:00:00Z",
                            "duration_seconds": 5.0,
                            "questions_count": 1,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Accordion collapsible verified?",
                                    "options": ["(Recommended) Yes", "No"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) Yes",
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

        # 1. Verify Filter Toolbar Collapsible
        self.assertIn('id="filter-collapse-btn"', content)
        self.assertIn('aria-controls="filter-toolbar-body"', content)

        # 2. Verify Pipeline Architecture Diagram Card Collapsible
        self.assertIn('id="card-architecture"', content)
        self.assertIn('data-target="architecture-body"', content)
        self.assertIn('id="architecture-body"', content)
        self.assertIn('card-collapsible-body', content)

        # 3. Verify Overview Charts Collapsible Cards
        self.assertIn('id="chart-card-distribution"', content)
        self.assertIn('data-target="chart-body-distribution"', content)
        self.assertIn('id="chart-body-distribution"', content)

        self.assertIn('id="chart-card-topic"', content)
        self.assertIn('data-target="chart-body-topic"', content)
        self.assertIn('id="chart-body-topic"', content)

        self.assertIn('id="chart-card-latency"', content)
        self.assertIn('data-target="chart-body-latency"', content)
        self.assertIn('id="chart-body-latency"', content)

        # 4. Verify Chats Tab Collapsible Table Section
        self.assertIn('id="chats-breakdown-section"', content)
        self.assertIn('data-target="chats-table-container"', content)
        self.assertIn('id="chats-table-container"', content)

        # 5. Verify Questions Tab Global Controls (Expand All / Collapse All)
        self.assertIn('id="btn-expand-all-questions"', content)
        self.assertIn('id="btn-collapse-all-questions"', content)
        self.assertIn("Expand All", content)
        self.assertIn("Collapse All", content)

        # 6. Verify CSS & JS Collapsible / Accordion Mechanics
        self.assertIn(".collapsible-header", content)
        self.assertIn(".collapse-icon", content)
        self.assertIn(".collapsed", content)
        self.assertIn("btnExpandAll.addEventListener", content)
        self.assertIn("btnCollapseAll.addEventListener", content)
        self.assertIn("collapsible-header[data-target]", content)



    def test_19_dashboard_configuration_modal_and_controls(self):
        """Verify the in-dashboard configuration modal, form controls, toast notification, and settings JS engine."""
        history = AutomationHistory(
            total_pipeline_runs=1,
            total_questions_answered=2,
            total_runtime_seconds=8.0,
            total_unique_chats=1,
            chats={"chat_cfg": {"conversation_id": "chat_cfg", "topic_summary": "Cfg Test", "run_count": 1, "runs": []}}
        )
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        # 1. Header Action Controls & Auto-Refresh Tag in Single Clean Row (Config Button Removed, Tab Retained)
        self.assertNotIn('id="config-toggle-btn"', content)
        self.assertIn('id="tab-btn-config"', content)
        self.assertIn('id="dashboard-status-pill"', content)
        self.assertIn('⚪ Inactive', content)
        self.assertIn('id="automation-toggle-btn"', content)
        self.assertIn('id="btn-header-refresh"', content)
        self.assertIn('id="auto-refresh-tag"', content)
        self.assertIn('id="refresh-countdown"', content)

        # 2. Modal Backdrop and Content
        self.assertIn('id="config-modal"', content)
        self.assertIn('class="modal-backdrop"', content)
        self.assertIn('class="modal-content"', content)
        self.assertIn('id="config-close-btn"', content)
        self.assertIn('Dashboard &amp; Automation Settings', content.replace("&", "&amp;"))

        # 3. All 6 Configurable Setting Inputs
        self.assertIn('id="cfg-auto-refresh"', content)
        self.assertIn('id="cfg-activity-delay"', content)
        self.assertIn('id="cfg-default-tab"', content)
        self.assertIn('id="cfg-selection-policy"', content)
        self.assertIn('id="cfg-visual-effects"', content)
        self.assertIn('id="cfg-sound-notify"', content)

        # 4. Data Action Buttons & Modal Action Buttons
        self.assertIn('id="cfg-export-btn"', content)
        self.assertIn('id="cfg-reset-btn"', content)
        self.assertIn('id="config-cancel-btn"', content)
        self.assertIn('id="config-save-btn"', content)
        self.assertIn('id="cfg-status-badge"', content)

        # 5. Toast Notification Container
        self.assertIn('id="toast-notify"', content)
        self.assertIn('class="toast-notification"', content)

        # 6. Client Script Configuration Engine Logic
        self.assertIn("DEFAULT_CONFIG", content)
        self.assertIn("asc_dashboard_config", content)
        self.assertIn("function showToast", content)
        self.assertIn("function playSoundChime", content)
        self.assertIn("function syncFormWithConfig", content)
        self.assertIn("function applyDynamicSettings", content)
        self.assertIn("function openConfigModal", content)
        self.assertIn("function closeConfigModal", content)

    def test_20_advanced_svg_diagrams_and_telemetry_suite(self):
        """Directly verify the upgraded topology diagram and 4 advanced SVG telemetry charts."""
        # 1. System Component Topology SVG
        topo_svg = Step4ReportingEngine.build_topology_svg()
        self.assertIn("<svg", topo_svg)
        self.assertIn("Antigravity IDE / Brain", topo_svg)
        self.assertIn("Step 0: Detector", topo_svg)
        self.assertIn("Step 1: Identifier", topo_svg)
        self.assertIn("Step 2: Focus", topo_svg)
        self.assertIn("Step 3: Selector", topo_svg)
        self.assertIn("Step 4: Reporter", topo_svg)
        self.assertIn("ONLINE", topo_svg)
        self.assertIn("Win32 HOOK ACTIVE", topo_svg)
        self.assertIn("100% INTEGRITY", topo_svg)
        self.assertIn("PERSISTENT JSON", topo_svg)
        self.assertIn("animateMotion", topo_svg)
        self.assertIn("topoBusGrad", topo_svg)

        # 2. Test empty history behavior for the 4 new charts
        empty_hist = AutomationHistory()
        empty_vel = Step4ReportingEngine.build_velocity_timeline_svg(empty_hist)
        self.assertIn("No Velocity Timeline Data Yet", empty_vel)

        empty_prod = Step4ReportingEngine.build_productivity_gauge_svg(empty_hist)
        self.assertIn("prodGaugeGrad", empty_prod)
        self.assertIn("MANUAL TIME SAVED", empty_prod)

        empty_heat = Step4ReportingEngine.build_time_heatmap_svg(empty_hist)
        self.assertIn("Activity Intensity:", empty_heat)
        self.assertIn("Morning", empty_heat)
        self.assertIn("Night", empty_heat)

        empty_opt = Step4ReportingEngine.build_option_breakdown_svg(empty_hist)
        self.assertIn("Option 1 Recommended Adherence Rate", empty_opt)

        # 3. Test populated history behavior
        pop_hist = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=4,
            total_runtime_seconds=16.0,
            total_unique_chats=1,
            chats={
                "chat_full": {
                    "conversation_id": "chat_full",
                    "topic_summary": "Full Telemetry Test",
                    "run_count": 2,
                    "total_questions": 4,
                    "runs": [
                        {
                            "run_id": "run_a",
                            "timestamp": "2026-11-04T08:30:00Z",
                            "duration_seconds": 6.5,
                            "questions_count": 2,
                            "questions": [
                                {"question_index": 1, "selected_option_index": 1, "is_recommended": True},
                                {"question_index": 2, "selected_option_index": 1, "is_recommended": True},
                            ]
                        },
                        {
                            "run_id": "run_b",
                            "timestamp": "2026-11-04T14:45:00Z",
                            "duration_seconds": 9.5,
                            "questions_count": 2,
                            "questions": [
                                {"question_index": 1, "selected_option_index": 1, "is_recommended": True},
                                {"question_index": 2, "selected_option_index": 2, "is_recommended": False},
                            ]
                        }
                    ]
                }
            }
        )

        pop_vel = Step4ReportingEngine.build_velocity_timeline_svg(pop_hist)
        self.assertIn("velDurGrad", pop_vel)
        self.assertIn("velBarGrad", pop_vel)
        self.assertIn("Questions Velocity", pop_vel)

        pop_prod = Step4ReportingEngine.build_productivity_gauge_svg(pop_hist)
        self.assertIn("Productivity ROI", pop_prod)
        self.assertIn("Estimated Human Time:", pop_prod)
        self.assertIn("Faster", pop_prod)

        pop_heat = Step4ReportingEngine.build_time_heatmap_svg(pop_hist)
        self.assertIn("08h", pop_heat)
        self.assertIn("Hour 14:00", pop_heat)

        pop_opt = Step4ReportingEngine.build_option_breakdown_svg(pop_hist)
        self.assertIn("Option 1 (Recommended)", pop_opt)
        self.assertIn("Option 2 (Alternate)", pop_opt)

    def test_21_overview_tab_cards_and_accordions_integrity(self):
        """Verify all 8 Overview collapsible cards and their data-target bindings."""
        history = AutomationHistory(
            total_pipeline_runs=1,
            total_questions_answered=1,
            total_runtime_seconds=5.0,
            total_unique_chats=1,
            chats={"chat_ov": {"conversation_id": "chat_ov", "topic_summary": "Overview Test", "run_count": 1, "runs": []}}
        )
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        cards_targets = [
            ("card-architecture", "architecture-body"),
            ("chart-card-velocity", "chart-body-velocity"),
            ("chart-card-productivity", "chart-body-productivity"),
            ("chart-card-heatmap", "chart-body-heatmap"),
            ("chart-card-option-breakdown", "chart-body-option-breakdown"),
            ("chart-card-distribution", "chart-body-distribution"),
            ("chart-card-topic", "chart-body-topic"),
            ("chart-card-latency", "chart-body-latency"),
        ]

        for card_id, target_id in cards_targets:
            self.assertIn(f'id="{card_id}"', content, f"Missing card ID: {card_id}")
            self.assertIn(f'data-target="{target_id}"', content, f"Missing data-target: {target_id}")
            self.assertIn(f'id="{target_id}"', content, f"Missing collapsible body ID: {target_id}")


    def test_22_config_tab_navigation_and_order(self):
        """Verify the 4th tab (Config) is present, correctly ordered as the LAST tab, and wired to navigation."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        content = html_path.read_text(encoding="utf-8")

        # 1. Tab navigation bar contains all 4 tabs in strict order
        idx_overview = content.find('id="tab-btn-overview"')
        idx_chats = content.find('id="tab-btn-chats"')
        idx_questions = content.find('id="tab-btn-questions"')
        idx_config = content.find('id="tab-btn-config"')

        self.assertNotEqual(idx_overview, -1, "tab-btn-overview not found")
        self.assertNotEqual(idx_chats, -1, "tab-btn-chats not found")
        self.assertNotEqual(idx_questions, -1, "tab-btn-questions not found")
        self.assertNotEqual(idx_config, -1, "tab-btn-config not found")

        # Strict order verification: Overview < Chats < Questions < Config (ALWAYS the last tab)
        self.assertTrue(idx_overview < idx_chats < idx_questions < idx_config, "Tabs are not in strict order with Config as last tab")

        # 2. Config tab button attributes
        self.assertIn('data-tab="config"', content)
        self.assertIn('⚙️', content)
        self.assertIn('aria-controls="tab-config"', content)

        # 3. Main tab panel for Config
        self.assertIn('id="tab-config"', content)
        self.assertIn('class="tab-panel"', content)
        self.assertIn('aria-labelledby="tab-btn-config"', content)

        # 4. JavaScript tab registration includes 'config' and switches via Config tab
        self.assertIn("'config'", content)
        self.assertIn("tab-btn-config", content)

    def test_23_system_runtime_configuration_section(self):
        """Verify Section 1 (System Runtime Configuration) UI controls, live values, and CLI generator."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        content = html_path.read_text(encoding="utf-8")

        # 1. Section Header & Badges
        self.assertIn('id="runtime-config-section"', content)
        self.assertIn('System Runtime Configuration', content)
        self.assertIn('step_9_complete_automation/config.json', content)

        # 2. Execution Mode Pills
        self.assertIn('id="cfg-mode-prod-btn"', content)
        self.assertIn('id="cfg-mode-test-btn"', content)
        self.assertIn('id="cfg-runtime-mode"', content)
        self.assertIn('Production Mode', content)
        self.assertIn('Test Mode', content)

        # 3. Pipeline Steps Toggles
        self.assertIn('id="cfg-step1-enabled"', content)
        self.assertIn('id="cfg-step2-enabled"', content)
        self.assertIn('id="cfg-step3-enabled"', content)
        self.assertIn('id="cfg-step4-enabled"', content)
        self.assertIn('Find &amp; Focus Target Window', content)
        self.assertIn('GUI Chat Select &amp; Focus', content)
        self.assertIn('Keyboard Recommendation Selector', content)
        self.assertIn('Visual Reporting &amp; Telemetry', content)

        # 4. Timing & Delays Engine Inputs
        self.assertIn('id="cfg-timing-prod-poll"', content)
        self.assertIn('id="cfg-timing-test-poll"', content)
        self.assertIn('id="cfg-timing-settle"', content)
        self.assertIn('id="cfg-timing-activity-delay"', content)
        self.assertIn('id="cfg-timing-step4-poll"', content)
        self.assertIn('id="cfg-timing-step1-focus"', content)
        self.assertIn('id="cfg-timing-step2-dom-settle"', content)
        self.assertIn('id="cfg-timing-step3-countdown"', content)
        self.assertIn('id="cfg-timing-step3-hold-ms"', content)
        self.assertIn('id="cfg-timing-step3-post-ms"', content)
        self.assertIn('id="cfg-timing-step3-inter-q-ms"', content)
        self.assertIn('id="cfg-timing-step3-round-ms"', content)

        # 5. AntiGravity Governance Rules
        self.assertIn('id="cfg-antigravity-require-grillme"', content)
        self.assertIn('id="cfg-antigravity-active-hours"', content)

        # 6. Logging & Telemetry
        self.assertIn('id="cfg-logging-verbose"', content)
        self.assertIn('id="cfg-logging-file"', content)

        # 7. Action Buttons & CLI Command Generator
        self.assertIn('id="btn-save-runtime-cfg"', content)
        self.assertIn('id="btn-copy-cli-cmd"', content)
        self.assertIn('id="btn-download-runtime-cfg"', content)
        self.assertIn('id="btn-toggle-json-preview"', content)
        self.assertIn('id="btn-reset-runtime-cfg"', content)

        # 8. Live Preview Drawer & Script Data Store
        self.assertIn('id="runtime-json-drawer"', content)
        self.assertIn('id="runtime-json-preview"', content)
        self.assertIn('id="runtime-config-data"', content)

        # 9. Client JS Functions
        self.assertIn('function buildRuntimeConfigFromForm', content)
        self.assertIn('function updateRuntimeJsonPreview', content)
        self.assertIn('function copyTextToClipboard', content)

    def test_24_dashboard_ui_configuration_section(self):
        """Verify Section 2 (Dashboard UI Configuration) presentation, sound test, and landing tab options."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        content = html_path.read_text(encoding="utf-8")

        # 1. Section Header
        self.assertIn('id="dashboard-config-section"', content)
        self.assertIn('Dashboard UI Configuration', content)

        # 2. Form Controls & Selects
        self.assertIn('id="cfg-auto-refresh"', content)
        self.assertIn('id="cfg-activity-delay"', content)
        self.assertIn('id="cfg-default-tab"', content)
        self.assertIn('id="cfg-selection-policy"', content)
        self.assertIn('id="cfg-visual-effects"', content)
        self.assertIn('id="cfg-sound-notify"', content)

        # 3. Dedicated Sound Chime Test Button
        self.assertIn('id="btn-test-chime"', content)
        self.assertIn('Test Chime', content)

        # 4. Default Landing Tab includes Config
        self.assertIn('<option value="config">Config (Master System &amp; Dashboard Settings)</option>', content)

        # 5. Data Actions & Save
        self.assertIn('id="cfg-export-btn"', content)
        self.assertIn('id="cfg-reset-btn"', content)
        self.assertIn('id="config-save-btn"', content)
        self.assertIn('id="cfg-status-badge"', content)

    def test_25_engine_runtime_config_methods(self):
        """Verify Python engine methods for discovering, loading, and saving runtime config."""
        # 1. Path discovery
        cfg_path = self.engine.get_runtime_config_path()
        self.assertIsInstance(cfg_path, Path)
        self.assertEqual(cfg_path.name, "config.json")

        # 2. Default loading
        cfg = self.engine.load_runtime_config()
        self.assertIn("mode", cfg)
        self.assertIn("timing", cfg)
        self.assertIn("enabled_steps", cfg)
        self.assertIn("antigravity", cfg)
        self.assertIn("logging", cfg)
        self.assertIn("step0_poll_interval_prod_seconds", cfg["timing"])
        self.assertIn("step1_find_and_focus", cfg["enabled_steps"])

        # 3. Save to custom file
        temp_dest = self.test_dir / "custom_config.json"
        cfg["mode"] = "test"
        cfg["timing"]["step0_poll_interval_test_seconds"] = 5.0
        success = self.engine.save_runtime_config(cfg, target_path=temp_dest)
        self.assertTrue(success)
        self.assertTrue(temp_dest.is_file())

        # 4. Verify persisted contents
        with open(temp_dest, "r", encoding="utf-8") as f:
            loaded_back = json.load(f)
        self.assertEqual(loaded_back["mode"], "test")
        self.assertEqual(loaded_back["timing"]["step0_poll_interval_test_seconds"], 5.0)

    def test_26_collapsible_sections_in_config_tab(self):
        """Verify Collapsible Accordions and Expand/Collapse All controls in Config tab UI."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        html_text = html_path.read_text(encoding="utf-8")

        # 1. Global Expand / Collapse All Controls
        self.assertIn('id="btn-expand-all-config"', html_text)
        self.assertIn('id="btn-collapse-all-config"', html_text)
        self.assertIn('Expand All Sections', html_text)
        self.assertIn('Collapse All Sections', html_text)

        # 2. Card 1 Collapsible Header & 6 Sub-Accordions
        self.assertIn('id="header-runtime-config"', html_text)
        self.assertIn('id="acc-runtime-mode"', html_text)
        self.assertIn('id="acc-runtime-steps"', html_text)
        self.assertIn('id="acc-runtime-timing"', html_text)
        self.assertIn('id="acc-runtime-governance"', html_text)
        self.assertIn('id="acc-runtime-logging"', html_text)
        self.assertIn('id="acc-runtime-actions"', html_text)

        # 3. Card 2 Collapsible Header & 4 Sub-Accordions
        self.assertIn('id="header-dashboard-config"', html_text)
        self.assertIn('id="acc-dash-timers"', html_text)
        self.assertIn('id="acc-dash-visual"', html_text)
        self.assertIn('id="acc-dash-audio"', html_text)
        self.assertIn('id="acc-dash-data"', html_text)

        # 4. Accessibility Attributes & Chevrons
        self.assertIn('aria-expanded="true"', html_text)
        self.assertIn('accordion-chevron', html_text)
        self.assertIn('subaccordion-chevron', html_text)
        self.assertIn('collapsible-card-header', html_text)
        self.assertIn('config-subgroup-header', html_text)

        # 5. JavaScript Controllers
        self.assertIn('function setElementCollapsed', html_text)
        self.assertIn('function toggleHeader', html_text)

    def test_27_unified_config_cross_step_integration(self):
        """Verify cross-step configuration synchronization using core_engine.config_manager."""
        import core_engine.config_manager as cm
        cfg = cm.load_runtime_config()
        self.assertIn("mode", cfg)
        self.assertIn("timing", cfg)
        self.assertIn("enabled_steps", cfg)
        self.assertIn("antigravity", cfg)
        self.assertIn("logging", cfg)

        # Verify step enabling
        self.assertTrue(cm.is_step_enabled(1, cfg))
        self.assertTrue(cm.is_step_enabled(2, cfg))
        self.assertTrue(cm.is_step_enabled(3, cfg))
        self.assertTrue(cm.is_step_enabled(4, cfg))

        # Verify effective polling interval
        prod_interval = cm.get_effective_poll_interval({"mode": "production", "timing": {"step0_poll_interval_prod_seconds": 300.0}})
        test_interval = cm.get_effective_poll_interval({"mode": "test", "timing": {"step0_poll_interval_test_seconds": 10.0}})
        self.assertEqual(prod_interval, 300.0)
        self.assertEqual(test_interval, 10.0)

        # Verify all granular timing keys
        kb_timing = cm.get_keyboard_timing(cfg)
        self.assertIn("countdown", kb_timing)
        self.assertIn("hold_delay_s", kb_timing)
        self.assertIn("post_keypress_delay_s", kb_timing)
        self.assertIn("inter_question_delay_s", kb_timing)
        self.assertIn("round_completion_pause_s", kb_timing)
        self.assertEqual(kb_timing["countdown"], 3.0)
        self.assertEqual(kb_timing["hold_delay_s"], 0.05)
        self.assertEqual(kb_timing["post_keypress_delay_s"], 0.25)
        self.assertEqual(kb_timing["inter_question_delay_s"], 0.5)
        self.assertEqual(kb_timing["round_completion_pause_s"], 1.0)

    def test_28_dynamic_automation_start_stop_control(self):
        """Verify dynamic Start/Stop automation toggle button, modal drawer, and JS logic."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        # 1. Header Button & Status Pill
        self.assertIn('id="automation-toggle-btn"', content)
        self.assertIn('btn-automation-toggle', content)
        self.assertIn('id="control-icon"', content)
        self.assertIn('id="control-label"', content)
        self.assertIn('id="dashboard-status-pill"', content)
        self.assertIn('⚪ Inactive', content)
        self.assertIn('🟢 Active', content)

        # 2. Automation Modal & 1-Click Execution Drawer
        self.assertIn('id="automation-modal"', content)
        self.assertIn('AutoSelect-Commander Automation', content)
        self.assertIn('id="btn-copy-automation-cmd"', content)
        self.assertIn('id="btn-copy-automation-bat"', content)
        self.assertIn('id="btn-copy-automation-dry-run"', content)

        # 3. Dynamic JavaScript State Machine
        self.assertIn('asc_automation_running', content)
        self.assertIn('updateAutomationUI', content)
        self.assertIn('startLivePolling', content)
        self.assertIn('stopLivePolling', content)

    def test_29_accordion_single_expansion_and_default_collapsed_behavior(self):
        """Verify default-collapsed state and mutual-exclusion accordion mechanics across dashboard."""
        history = AutomationHistory(
            total_pipeline_runs=2,
            total_questions_answered=3,
            total_runtime_seconds=12.0,
            total_unique_chats=1,
            chats={
                "chat_accordion_test": {
                    "conversation_id": "chat_accordion_test",
                    "topic_summary": "Accordion Single Expansion Test",
                    "run_count": 2,
                    "total_questions": 3,
                    "runs": [
                        {
                            "run_id": "run_acc_01",
                            "timestamp": "2026-11-04T06:00:00Z",
                            "duration_seconds": 5.0,
                            "questions_count": 1,
                            "questions": [
                                {
                                    "question_index": 1,
                                    "question": "Mutual exclusion accordion test?",
                                    "options": ["(Recommended) Yes", "No"],
                                    "selected_option_index": 1,
                                    "selected_option_text": "(Recommended) Yes",
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

        # 1. Overview Tab: All 8 collapsible cards must be default-collapsed
        overview_cards = [
            ("architecture-body", "card-architecture"),
            ("chart-body-velocity", "chart-card-velocity"),
            ("chart-body-productivity", "chart-card-productivity"),
            ("chart-body-heatmap", "chart-card-heatmap"),
            ("chart-body-option-breakdown", "chart-card-option-breakdown"),
            ("chart-body-distribution", "chart-card-distribution"),
            ("chart-body-topic", "chart-card-topic"),
            ("chart-body-latency", "chart-card-latency"),
        ]
        for body_id, card_id in overview_cards:
            self.assertIn(f'data-target="{body_id}" role="button" tabindex="0" aria-expanded="false"', content)
            self.assertIn(f'class="card-collapsible-body collapsed" id="{body_id}"', content)

        # 2. Chats Tab: Table section must be default-collapsed
        self.assertIn('data-target="chats-table-container" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('class="card-collapsible-body collapsed" id="chats-table-container"', content)

        # 3. Config Tab: Section cards and all 10 subgroups must be default-collapsed
        self.assertIn('id="header-runtime-config" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('id="body-runtime-config"', content)
        self.assertIn('class="config-section-body collapsible-card-body collapsed" id="body-runtime-config"', content)

        self.assertIn('id="header-dashboard-config" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('class="config-section-body collapsible-card-body collapsed" id="body-dashboard-config"', content)

        subgroups = [
            "subbody-runtime-mode",
            "subbody-runtime-steps",
            "subbody-runtime-timing",
            "subbody-runtime-governance",
            "subbody-runtime-logging",
            "subbody-runtime-actions",
            "subbody-dash-timers",
            "subbody-dash-visual",
            "subbody-dash-audio",
            "subbody-dash-data",
        ]
        for sub_id in subgroups:
            self.assertIn(f'aria-expanded="false" aria-controls="{sub_id}"', content)
            self.assertIn(f'class="config-subgroup-body collapsed" id="{sub_id}"', content)

        # 4. Filter Toolbar: Must remain separate and independent (exempt from mutual exclusion)
        self.assertIn('id="filter-collapse-btn"', content)
        self.assertIn('aria-controls="filter-toolbar-body"', content)
        self.assertIn('id="filter-toolbar-body"', content)

        # 5. Global Expand All / Collapse All controls must exist and remain functional
        self.assertIn('id="btn-expand-all-questions"', content)
        self.assertIn('id="btn-collapse-all-questions"', content)
        self.assertIn('id="btn-expand-all-config"', content)
        self.assertIn('id="btn-collapse-all-config"', content)

        # 6. Questions Tab dynamic rendering templates must specify collapsed state
        self.assertIn('class="question-prompt collapsible-header" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('class="options-list collapsed"', content)
        self.assertIn('class="run-header collapsible-header" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('class="run-body collapsed"', content)
        self.assertIn('class="chat-card-header collapsible-header" role="button" tabindex="0" aria-expanded="false"', content)
        self.assertIn('class="chat-card-body collapsed"', content)

        # 7. JavaScript mutual exclusion routines must be embedded in page script
        self.assertIn("collapsible-card-header", content)
        self.assertIn("config-subgroup-header", content)
        self.assertIn("otherHeader !== header", content)
        self.assertIn("otherCard !== qCard", content)
        self.assertIn("otherRun !== runBlock", content)
        self.assertIn("otherChat !== chatCard", content)

    def test_30_mode_switch_dedicated_tab_and_no_global_banner(self):
        """Verify Mode Switch dedicated tab, no global banner outside tabs, and interactive controls."""
        history = AutomationHistory(total_pipeline_runs=1, total_questions_answered=1, total_runtime_seconds=5.0, total_unique_chats=1)
        html_path = self.engine.generate_html_dashboard(history)
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")

        # 1. Tab navigation bar contains all 5 tabs in strict order: Overview < Chats < Questions < Modes < Config
        idx_overview = content.find('id="tab-btn-overview"')
        idx_chats = content.find('id="tab-btn-chats"')
        idx_questions = content.find('id="tab-btn-questions"')
        idx_modes = content.find('id="tab-btn-modes"')
        idx_config = content.find('id="tab-btn-config"')

        self.assertNotEqual(idx_overview, -1, "tab-btn-overview not found")
        self.assertNotEqual(idx_chats, -1, "tab-btn-chats not found")
        self.assertNotEqual(idx_questions, -1, "tab-btn-questions not found")
        self.assertNotEqual(idx_modes, -1, "tab-btn-modes not found")
        self.assertNotEqual(idx_config, -1, "tab-btn-config not found")

        self.assertTrue(idx_overview < idx_chats < idx_questions < idx_modes < idx_config, "Tabs are not in strict 5-tab order")

        # 2. Tab button attributes for Mode Switch
        self.assertIn('data-tab="modes"', content)
        self.assertIn('aria-controls="tab-modes"', content)
        self.assertIn('id="tab-modes-badge"', content)
        self.assertIn('🎛️', content)
        self.assertIn('Mode Switch', content)

        # 3. Dedicated Tab Panel for Modes
        self.assertIn('id="tab-modes"', content)
        self.assertIn('class="tab-panel"', content)
        self.assertIn('aria-labelledby="tab-btn-modes"', content)
        self.assertIn('Execution Mode Control &amp; Lifecycle Standard', content)
        self.assertIn('मोड स्विच एवं कार्यप्रणाली', content)

        # 4. Mode Switcher & Rich Mode Cards inside Mode Switch Tab
        self.assertIn('id="banner-mode-test-btn"', content)
        self.assertIn('id="banner-mode-prod-btn"', content)
        self.assertIn('id="banner-card-test"', content)
        self.assertIn('id="banner-card-prod"', content)

        # 5. Quick Process Control inside Mode Switch Tab
        self.assertIn('id="modes-automation-toggle-btn"', content)
        self.assertIn('id="modes-status-pill"', content)

        # 6. Operational Parameters Comparison Table
        self.assertIn('modes-comparison-table', content)
        self.assertIn('Operational Lifecycle &amp; Parameters Comparison', content)

        # 7. Global banner is REMOVED from outside the tab panels
        nav_end = content.find('</nav>')
        first_main = content.find('<main')
        between_nav_and_main = content[nav_end:first_main]
        self.assertNotIn('mode-lifecycle-banner', between_nav_and_main, "Global banner should not appear outside tab panels")

        # 8. JavaScript tab registration includes 'modes'
        self.assertIn("'modes'", content)
        self.assertIn("modesAutomationToggleBtn", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
