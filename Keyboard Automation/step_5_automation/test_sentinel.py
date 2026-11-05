#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and Integration Test Suite for Antigravity Lifecycle Sentinel
==================================================================
Subsystem: Step 5 Automation
Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
"""

import os
import sys
import json
import time
import socket
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Workspace Anchors
_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _THIS_DIR.parent
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from step_5_automation.antigravity_lifecycle_sentinel import (
    AntigravityLifecycleSentinel,
    is_antigravity_running,
    is_port_listening,
    api_get_status,
    api_post_command,
    STATE_FILE,
)


class TestAntigravityLifecycleSentinel(unittest.TestCase):
    """Test suite for Step 5 Lifecycle Sentinel daemon and API triggers."""

    def setUp(self):
        self.sentinel = AntigravityLifecycleSentinel(
            workspace_dir=_WORKSPACE_DIR,
            port=8599,  # Use a mock test port
            poll_interval=0.1,
            default_mode="test",
        )

    def test_process_detection(self):
        """is_antigravity_running should execute in sub-millisecond and return boolean."""
        res = is_antigravity_running()
        self.assertIsInstance(res, bool)

    def test_port_listening_check(self):
        """is_port_listening should report false for unbound ports and true for bound sockets."""
        # Unbound port
        self.assertFalse(is_port_listening("127.0.0.1", 59998))

        # Bound test socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        test_port = sock.getsockname()[1]
        try:
            self.assertTrue(is_port_listening("127.0.0.1", test_port))
        finally:
            sock.close()

    def test_sentinel_initialization(self):
        """Sentinel should resolve valid paths and executables."""
        self.assertEqual(self.sentinel.port, 8599)
        self.assertEqual(self.sentinel.poll_interval, 0.1)
        self.assertEqual(self.sentinel.default_mode, "test")
        self.assertTrue(self.sentinel.python_exe.exists())
        self.assertTrue(self.sentinel.server_script.exists())

    def test_update_state_file(self):
        """Sentinel should persist clean JSON telemetry state."""
        test_state = {"status": "TESTING", "antigravity_running": True}
        self.sentinel.update_state_file(test_state)
        self.assertTrue(STATE_FILE.is_file())
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["status"], "TESTING")
        self.assertTrue(data["antigravity_running"])
        self.assertEqual(data["port"], 8599)
        self.assertIn("timestamp", data)

    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_antigravity_running", return_value=False)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_port_listening", return_value=False)
    def test_single_cycle_when_antigravity_closed(self, mock_port, mock_ag):
        """When Antigravity is closed and port is quiet, action should be NONE."""
        res = self.sentinel.run_single_cycle()
        self.assertFalse(res["antigravity_running"])
        self.assertFalse(res["server_listening"])
        self.assertFalse(res["automation_running"])
        self.assertEqual(res["action_taken"], "NONE")

    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_antigravity_running", return_value=True)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_port_listening", return_value=True)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.api_get_status")
    @patch("step_5_automation.antigravity_lifecycle_sentinel.api_post_command", return_value=True)
    def test_single_cycle_when_antigravity_open_and_automation_idle(self, mock_post, mock_status, mock_port, mock_ag):
        """When Antigravity is open and auto_start_pipeline is True, start automation."""
        self.sentinel.auto_start_pipeline = True
        mock_status.return_value = {"running": False, "pid": None}
        res = self.sentinel.run_single_cycle()
        self.assertTrue(res["antigravity_running"])
        self.assertTrue(res["server_listening"])
        self.assertEqual(res["action_taken"], "STARTED_AUTOMATION")
        mock_post.assert_called_once_with("start", port=8599, payload={"mode": "test", "run_pipeline": False})

    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_antigravity_running", return_value=True)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_port_listening", return_value=True)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.api_get_status")
    @patch("step_5_automation.antigravity_lifecycle_sentinel.api_post_command", return_value=True)
    def test_single_cycle_when_antigravity_open_and_auto_start_pipeline_false(self, mock_post, mock_status, mock_port, mock_ag):
        """When auto_start_pipeline is False (default), do not start downstream automation."""
        self.sentinel.auto_start_pipeline = False
        mock_status.return_value = {"running": False, "pid": None}
        res = self.sentinel.run_single_cycle()
        self.assertTrue(res["antigravity_running"])
        self.assertTrue(res["server_listening"])
        self.assertEqual(res["action_taken"], "NONE")
        mock_post.assert_not_called()

    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_antigravity_running", return_value=False)
    @patch("step_5_automation.antigravity_lifecycle_sentinel.is_port_listening", return_value=True)
    @patch.object(AntigravityLifecycleSentinel, "stop_dashboard_server", return_value=True)
    def test_single_cycle_when_antigravity_closes_with_server_open(self, mock_stop, mock_port, mock_ag):
        """When Antigravity closes while server was open, trigger stop_dashboard_server."""
        res = self.sentinel.run_single_cycle()
        self.assertFalse(res["antigravity_running"])
        self.assertTrue(res["server_listening"])
        self.assertEqual(res["action_taken"], "STOPPED_ALL")
        mock_stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
