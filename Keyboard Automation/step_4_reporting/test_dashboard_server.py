#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Test Suite: Dashboard Local Control Server (test_dashboard_server.py)
=========================================================================
Pipeline Role: Test Coverage for Local HTTP Control Server & REST API Endpoints
Part of: AutoSelect-Commander Automation Suite
Standard: Department 08 (QA & Testing) & Department 06 (Backend & API Engineering)
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Verifies:
  1. AutomationProcessManager lifecycle (start, stop, status, recovery).
  2. Mock subprocess Popen handling and PID persistence.
  3. REST API endpoints:
     - `GET  /api/automation/status`
     - `POST /api/automation/start`
     - `POST /api/automation/stop`
     - `GET  /api/config/get`
     - `POST /api/config/save`
     - `GET  /api/logs/tail`
     - `OPTIONS *` (CORS headers)
  4. Static file delivery for `/` (dashboard.html).
  5. Clean server shutdown (Universal Rule 26 hygiene).
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

# Base Directory Resolution
_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _THIS_DIR.parent if _THIS_DIR.name == "step_4_reporting" else _THIS_DIR

if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from step_4_reporting.dashboard_server import (
    AutomationProcessManager,
    DashboardServer,
    find_available_port,
    is_pid_alive,
)


class TestDashboardServer(unittest.TestCase):
    """Comprehensive test cases for dashboard HTTP control server and process manager."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_asc_server_")
        self.workspace_dir = Path(self.temp_dir)
        
        # Prepare mock directory tree
        self.step9_dir = self.workspace_dir / "step_9_complete_automation"
        self.step4_dir = self.workspace_dir / "step_4_reporting"
        self.reports_dir = self.step4_dir / "reports"
        self.step9_dir.mkdir(parents=True, exist_ok=True)
        self.step4_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Mock master automation script
        self.master_script = self.step9_dir / "complete_automation.py"
        self.master_script.write_text("# Mock complete_automation.py\nimport sys\nsys.exit(0)\n", encoding="utf-8")

        # Mock config.json
        self.config_file = self.step9_dir / "config.json"
        self.initial_config = {
            "mode": "production",
            "timing": {"step0_poll_interval_prod_seconds": 300.0},
            "enabled_steps": {"step1_find_and_focus": True}
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.initial_config, f, indent=2)

        # Mock dashboard.html
        self.dashboard_html = self.reports_dir / "dashboard.html"
        self.dashboard_html.write_text("<!DOCTYPE html><html><body><h1>Dashboard</h1></body></html>", encoding="utf-8")

        # Initialize manager and server
        self.manager = AutomationProcessManager(workspace_dir=self.workspace_dir)
        self.port = find_available_port("127.0.0.1", start_port=18501)
        self.server = DashboardServer(host="127.0.0.1", port=self.port, workspace_dir=self.workspace_dir)
        self.server.manager = self.manager
        self.server.start(open_browser=False, in_thread=True)
        time.sleep(0.2)  # Give server thread time to bind
        self.base_url = f"http://127.0.0.1:{self.server.actual_port}"

    def tearDown(self):
        # Shut down server cleanly
        if self.server:
            self.server.shutdown()
        # Clean up temp dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _http_request(self, method: str, path: str, data: dict = None) -> tuple[int, dict, dict]:
        """Helper to send HTTP requests to test server."""
        url = f"{self.base_url}{path}"
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                headers_dict = dict(response.getheaders())
                raw = response.read().decode("utf-8")
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = {"raw": raw}
                return status, headers_dict, payload
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"raw": raw}
            return e.code, dict(e.headers), payload

    # ========================================================================
    # Process Manager Unit Tests
    # ========================================================================

    def test_01_manager_initially_stopped(self):
        """Manager should report process is not running initially."""
        self.assertFalse(self.manager.is_running())
        self.assertIsNone(self.manager.get_pid())
        status = self.manager.get_status()
        self.assertFalse(status["running"])
        self.assertIsNone(status["pid"])
        self.assertEqual(status["status_text"], "Inactive")

    def test_02_manager_start_and_stop_mock(self):
        """Manager should spawn process and handle start/stop cycle."""
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.poll.return_value = None  # alive

        with patch("subprocess.Popen", return_value=mock_proc), patch("subprocess.run") as mock_run:
            res = self.manager.start(mode="test")
            self.assertTrue(res["running"])
            self.assertEqual(res["pid"], 99999)
            self.assertEqual(res["mode"], "test")
            self.assertTrue(self.manager.is_running())

            # Attempting to start again should return already running
            res2 = self.manager.start()
            self.assertTrue(res2["running"])
            self.assertIn("already running", res2["message"])

            # Stop
            stop_res = self.manager.stop()
            self.assertFalse(stop_res["running"])
            self.assertFalse(self.manager.is_running())

    def test_03_manager_log_tail(self):
        """Manager should retrieve the last N lines of complete_automation.log."""
        log_file = self.step9_dir / "complete_automation.log"
        lines = [f"Log line {i}\n" for i in range(100)]
        log_file.write_text("".join(lines), encoding="utf-8")

        tail = self.manager.get_log_tail(max_lines=10)
        self.assertIn("Log line 99", tail)
        self.assertIn("Log line 90", tail)
        self.assertNotIn("Log line 50", tail)

    # ========================================================================
    # REST API Endpoint Tests
    # ========================================================================

    def test_04_get_automation_status_endpoint(self):
        """GET /api/automation/status should return Department 06 envelope."""
        status, headers, body = self._http_request("GET", "/api/automation/status")
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertIn("running", body["data"])
        self.assertFalse(body["data"]["running"])
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")

    def test_05_options_cors_preflight(self):
        """OPTIONS request should return 204 with full CORS headers."""
        status, headers, body = self._http_request("OPTIONS", "/api/automation/status")
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_06_post_automation_start_and_stop_endpoints(self):
        """POST /api/automation/start and /stop should control manager."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.poll.return_value = None

        with patch("subprocess.Popen", return_value=mock_proc), patch("subprocess.run"):
            status, _, body = self._http_request("POST", "/api/automation/start", {"mode": "test"})
            self.assertEqual(status, 200)
            self.assertTrue(body["success"])
            self.assertTrue(body["data"]["running"])
            self.assertEqual(body["data"]["pid"], 12345)

            # Check status endpoint reflects running
            status_code, _, status_body = self._http_request("GET", "/api/automation/status")
            self.assertEqual(status_code, 200)
            self.assertTrue(status_body["data"]["running"])
            self.assertEqual(status_body["data"]["pid"], 12345)

            # Stop endpoint
            stop_code, _, stop_body = self._http_request("POST", "/api/automation/stop")
            self.assertEqual(stop_code, 200)
            self.assertTrue(stop_body["success"])
            self.assertFalse(stop_body["data"]["running"])

    def test_07_get_and_save_config_endpoints(self):
        """GET /api/config/get and POST /api/config/save should update config.json."""
        # 1. GET
        status, _, body = self._http_request("GET", "/api/config/get")
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["mode"], "production")

        # 2. POST Save updated config
        new_cfg = {
            "mode": "test",
            "timing": {"step0_poll_interval_prod_seconds": 120.0},
            "enabled_steps": {"step1_find_and_focus": True}
        }
        status_save, _, body_save = self._http_request("POST", "/api/config/save", new_cfg)
        self.assertEqual(status_save, 200)
        self.assertTrue(body_save["success"])
        self.assertTrue(body_save["data"]["saved"])

        # 3. Verify disk persistence
        with open(self.config_file, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        self.assertEqual(persisted["mode"], "test")
        self.assertEqual(persisted["timing"]["step0_poll_interval_prod_seconds"], 120.0)

    def test_08_get_dashboard_html_static(self):
        """GET / should serve dashboard.html with text/html content-type."""
        status, headers, body = self._http_request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("raw", body)
        self.assertIn("<!DOCTYPE html>", body["raw"])

    def test_09_get_logs_tail_endpoint(self):
        """GET /api/logs/tail should return log contents."""
        log_file = self.step9_dir / "complete_automation.log"
        log_file.write_text("2026-11-05 [INFO] Test line 1\n2026-11-05 [INFO] Test line 2\n", encoding="utf-8")

        status, _, body = self._http_request("GET", "/api/logs/tail?lines=5")
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertIn("Test line 1", body["data"]["logs"])

    def test_10_unknown_endpoint_returns_404(self):
        """Requests to unknown endpoints should return 404 with error message."""
        status, _, body = self._http_request("GET", "/non_existent_path")
        self.assertEqual(status, 404)
        self.assertFalse(body["success"])

    def test_11_manager_test_mode_process_completion_cleanup(self):
        """When test mode process completes, is_running() naturally returns False and cleans up PID file."""
        mock_proc = MagicMock()
        mock_proc.pid = 44444
        mock_proc.poll.return_value = None  # initially running

        with patch("subprocess.Popen", return_value=mock_proc):
            res = self.manager.start(mode="test")
            self.assertTrue(res["running"])
            self.assertEqual(res["pid"], 44444)
            self.assertEqual(res["mode"], "test")
            self.assertTrue(self.manager.is_running())
            self.assertTrue(self.manager.pid_file.is_file())

            # Now simulate single-run task completion (process exits with 0)
            mock_proc.poll.return_value = 0

            # Next check should detect process exit, clean up PID file, and return False
            self.assertFalse(self.manager.is_running())
            self.assertIsNone(self.manager.get_pid())
            self.assertFalse(self.manager.pid_file.is_file())

            status = self.manager.get_status()
            self.assertFalse(status["running"])
            self.assertIsNone(status["pid"])
            self.assertEqual(status["status_text"], "Inactive")

    def test_12_start_endpoint_accepts_modes_and_persists_config(self):
        """POST /api/automation/start accepts mode='test' and mode='production' and persists to config.json."""
        mock_proc = MagicMock()
        mock_proc.pid = 55555
        mock_proc.poll.return_value = None

        with patch("subprocess.Popen", return_value=mock_proc), patch("subprocess.run"):
            # 1. Start with test mode
            status, _, body = self._http_request("POST", "/api/automation/start", {"mode": "test"})
            self.assertEqual(status, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["mode"], "test")

            # Check config.json persisted mode
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.assertEqual(cfg["mode"], "test")

            # Stop
            self._http_request("POST", "/api/automation/stop")

            # 2. Start with production mode
            status, _, body = self._http_request("POST", "/api/automation/start", {"mode": "production"})
            self.assertEqual(status, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["mode"], "production")

            # Check config.json persisted mode
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.assertEqual(cfg["mode"], "production")

            # Stop
            self._http_request("POST", "/api/automation/stop")


if __name__ == "__main__":
    unittest.main()
