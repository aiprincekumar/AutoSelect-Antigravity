#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Activating Grill Me Chat in Antigravity (Method 1).
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
import importlib.util
from pathlib import Path

# Load activating_grill_me module dynamically
module_path = (
    Path(__file__).resolve().parent.parent
    / "Activating Grill Me Chat in anti-gravity"
    / "activating_grill_me.py"
)
spec = importlib.util.spec_from_file_location("activating_grill_me", module_path)
agm = importlib.util.module_from_spec(spec)
sys.modules["activating_grill_me"] = agm
spec.loader.exec_module(agm)


class TestActivatingGrillMe(unittest.TestCase):
    """Test suite for Method 1 Transcript Parsing & Selection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_agm_brain_")
        self.brain_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_conversation(
        self,
        cid: str,
        steps: list,
        use_full_transcript: bool = False
    ) -> Path:
        """Helper to create a mock conversation folder with transcript.jsonl."""
        cdir = self.brain_path / cid / ".system_generated" / "logs"
        cdir.mkdir(parents=True, exist_ok=True)
        fname = "transcript_full.jsonl" if use_full_transcript else "transcript.jsonl"
        tfile = cdir / fname
        with open(tfile, "w", encoding="utf-8") as f:
            for step in steps:
                f.write(json.dumps(step) + "\n")
        return tfile

    def test_question_payload_recommended_detection(self):
        """Test auto-detection of recommended options."""
        # Case 1: (Recommended) in option 1
        q1 = agm.QuestionPayload(
            question_index=1,
            question="Choose option",
            options=["(Recommended) Option A", "Option B", "Option C"]
        )
        self.assertEqual(q1.recommended_option_index, 1)
        self.assertEqual(q1.recommended_option_text, "(Recommended) Option A")

        # Case 2: (Recommended) in option 2
        q2 = agm.QuestionPayload(
            question_index=2,
            question="Choose option",
            options=["Option 1", "(Recommended) Option 2", "Option 3"]
        )
        self.assertEqual(q2.recommended_option_index, 2)
        self.assertEqual(q2.recommended_option_text, "(Recommended) Option 2")

        # Case 3: No explicit recommended tag, fallback to 1
        q3 = agm.QuestionPayload(
            question_index=3,
            question="Choose option",
            options=["First Choice", "Second Choice"]
        )
        self.assertEqual(q3.recommended_option_index, 1)
        self.assertEqual(q3.recommended_option_text, "First Choice")

    def test_detect_pending_grill_me_chat(self):
        """Test detecting a conversation with an unanswered ask_question."""
        cid = "conv-pending-1234"
        steps = [
            {
                "step_index": 0,
                "type": "USER_INPUT",
                "content": "<USER_REQUEST>Run Grill Me Interview</USER_REQUEST>"
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-11-01T20:00:00Z",
                "tool_calls": [
                    {
                        "name": "ask_question",
                        "args": {
                            "questions": [
                                {
                                    "question": "Which architecture pattern?",
                                    "options": ["(Recommended) Monolith", "Microservices"],
                                    "is_multi_select": False
                                }
                            ]
                        }
                    }
                ]
            }
        ]
        self._create_mock_conversation(cid, steps)

        detector = agm.GrillMeDetector(brain_dir=str(self.brain_path))
        pending_list = detector.scan_transcripts()

        self.assertEqual(len(pending_list), 1)
        chat = pending_list[0]
        self.assertEqual(chat.conversation_id, cid)
        self.assertEqual(chat.step_index, 1)
        self.assertEqual(chat.topic_summary, "Run Grill Me Interview")
        self.assertEqual(len(chat.questions), 1)
        self.assertEqual(chat.questions[0].recommended_option_index, 1)

    def test_ignore_already_answered_ask_question(self):
        """Test that already answered ask_question is NOT detected as pending."""
        cid = "conv-answered-5678"
        steps = [
            {
                "step_index": 0,
                "type": "USER_INPUT",
                "content": "Please start"
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-11-01T20:00:00Z",
                "tool_calls": [
                    {
                        "name": "ask_question",
                        "args": {
                            "questions": [
                                {
                                    "question": "Approve changes?",
                                    "options": ["(Recommended) Yes", "No"]
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "step_index": 2,
                "type": "GENERIC",
                "status": "DONE",
                "content": "Created At: 2026-11-01T20:00:01Z\nCompleted At: 2026-11-01T20:00:05Z\nA1: (Recommended) Yes"
            },
            {
                "step_index": 3,
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "content": "Continuing execution..."
            }
        ]
        self._create_mock_conversation(cid, steps)

        detector = agm.GrillMeDetector(brain_dir=str(self.brain_path))
        pending_list = detector.scan_transcripts()
        self.assertEqual(len(pending_list), 0)

    def test_string_encoded_questions_argument(self):
        """Test parsing when questions argument is serialized as a JSON string."""
        cid = "conv-json-string-args"
        questions_json_str = json.dumps([
            {
                "question": "Deploy now?",
                "options": ["(Recommended) Deploy to Staging", "Cancel"],
                "is_multi_select": False
            }
        ])
        steps = [
            {
                "step_index": 0,
                "type": "USER_INPUT",
                "content": "Deploy app"
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-11-01T21:00:00Z",
                "tool_calls": [
                    {
                        "name": "ask_question",
                        "args": {
                            "questions": questions_json_str
                        }
                    }
                ]
            }
        ]
        self._create_mock_conversation(cid, steps)

        detector = agm.GrillMeDetector(brain_dir=str(self.brain_path))
        pending_list = detector.scan_transcripts()
        self.assertEqual(len(pending_list), 1)
        self.assertEqual(len(pending_list[0].questions), 1)
        self.assertEqual(pending_list[0].questions[0].question, "Deploy now?")

    def test_selector_auto_select_and_prepare(self):
        """Test Step 2 Selection preparation with custom option selection."""
        cid = "conv-selector-test"
        steps = [
            {
                "step_index": 0,
                "type": "USER_INPUT",
                "content": "Test workflow"
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-11-01T21:30:00Z",
                "tool_calls": [
                    {
                        "name": "ask_question",
                        "args": {
                            "questions": [
                                {
                                    "question": "Target Environment?",
                                    "options": ["(Recommended) Dev", "Staging", "Prod"]
                                }
                            ]
                        }
                    }
                ]
            }
        ]
        self._create_mock_conversation(cid, steps)

        detector = agm.GrillMeDetector(brain_dir=str(self.brain_path))
        selector = agm.GrillMeSelector(detector=detector)

        # Auto-select latest
        chat = selector.select_conversation(auto_latest=True)
        self.assertIsNotNone(chat)
        self.assertEqual(chat.conversation_id, cid)

        # Test preparation with recommended option
        res_rec = selector.prepare_selection(chat, use_recommended=True, dry_run=True)
        self.assertEqual(res_rec.status, "READY_FOR_CONFIRMATION")
        self.assertEqual(res_rec.selections[0]["selected_option_index"], 1)
        self.assertTrue(res_rec.selections[0]["is_recommended"])

        # Test preparation with explicit option override (Option 2: Staging)
        res_opt2 = selector.prepare_selection(chat, chosen_option_index=2, dry_run=True)
        self.assertEqual(res_opt2.selections[0]["selected_option_index"], 2)
        self.assertEqual(res_opt2.selections[0]["selected_option_text"], "Staging")

    def test_export_selection_state_json(self):
        """Test saving selection state to JSON and verifying Dept 06 envelope."""
        cid = "conv-export-test"
        chat = agm.PendingGrillMeChat(
            conversation_id=cid,
            step_index=1,
            created_at="2026-11-01T21:00:00Z",
            topic_summary="Sample topic",
            last_user_prompt="Sample prompt",
            questions=[
                agm.QuestionPayload(1, "Proceed?", ["(Recommended) Yes", "No"])
            ]
        )
        selector = agm.GrillMeSelector()
        result = selector.prepare_selection(chat, dry_run=True)

        out_json = self.brain_path / "export_test.json"
        saved_file = selector.export_selection_state(result, str(out_json))
        self.assertTrue(saved_file.is_file())

        with open(saved_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertTrue(data.get("success"))
        self.assertIn("data", data)
        self.assertIn("meta", data)
        self.assertEqual(data["data"]["conversation_id"], cid)
        self.assertEqual(data["data"]["status"], "READY_FOR_CONFIRMATION")

    def test_live_brain_detector_resolution(self):
        """Test that default brain directory resolves to existing directory on developer machine."""
        default_detector = agm.GrillMeDetector()
        self.assertTrue(default_detector.is_valid_brain_dir())

    def test_focus_manager_window_finder_api(self):
        """Test that AntigravityFocusManager find_antigravity_window runs and returns valid tuple or None."""
        match = agm.AntigravityFocusManager.find_antigravity_window()
        if match is not None:
            hwnd, title, info = match
            self.assertIsInstance(hwnd, int)
            self.assertGreater(hwnd, 0)
            self.assertIsInstance(title, str)
            self.assertIsInstance(info, dict)
            self.assertIn("class", info)
            self.assertIn("process_name", info)

    def test_gui_selector_calibrated_coordinates(self):
        """Test loading calibrated coordinates or sensible default fallback."""
        x, y = agm.AntigravityGuiSelector.load_calibrated_coordinates()
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)

    def test_gui_selector_dry_run(self):
        """Test GUI selector in dry-run mode returns True without modifying system state."""
        success = agm.AntigravityGuiSelector.select_chat_in_gui(
            hwnd=12345,
            target_cid="mock-cid-001",
            topic="Mock Topic",
            dry_run=True,
            select_option_number=1,
            auto_submit=False
        )
        self.assertTrue(success)

    def test_selection_result_includes_gui_fields(self):
        """Test SelectionResult data model includes window_focused and gui_chat_selected flags."""
        res = agm.SelectionResult(
            conversation_id="conv-123",
            selected_at="2026-11-01T22:00:00Z",
            status="READY_FOR_CONFIRMATION",
            questions_count=1,
            selections=[],
            window_focused=True,
            gui_chat_selected=True,
            dry_run=False
        )
        d = res.to_dict()
        self.assertTrue(d["window_focused"])
        self.assertTrue(d["gui_chat_selected"])
        self.assertFalse(d["dry_run"])


if __name__ == "__main__":
    unittest.main()
