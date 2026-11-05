#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern and Interactive Dashboard Verification Test Suite (test_modern_dashboard.py)
==================================================================================
Subsystem: Step 4 Reporting & Visual Dashboard Subsystem
Role: Quality Assurance & Independent Verification Gate (Department 08 QA Standards)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import unittest
import urllib.request
from pathlib import Path
from typing import Dict, Any

_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _THIS_DIR.parent if _THIS_DIR.name == "step_4_reporting" else _THIS_DIR
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from step_4_reporting.dashboard_server import DashboardServer, ThreadedHTTPServer, DashboardRequestHandler
from step_4_reporting.step4_reporting import Step4ReportingEngine


class TestModernDashboardSuite(unittest.TestCase):
    """Rigorous verification of the Modern and Interactive Dashboard subsystem."""

    @classmethod
    def setUpClass(cls):
        cls.workspace_dir = _WORKSPACE_DIR
        cls.step4_dir = cls.workspace_dir / "step_4_reporting"
        cls.modern_dir = cls.step4_dir / "Modern and Interactive Dashboard"
        cls.classic_dir = cls.step4_dir / "Simple and Classic Dashboard"
        cls.reports_dir = cls.step4_dir / "reports"

        # Generate fresh modern dashboard
        import importlib.util
        gen_path = cls.modern_dir / "generate_modern_dashboard.py"
        spec = importlib.util.spec_from_file_location("generate_modern_dashboard", str(gen_path))
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)
        cls.modern_html_path = gen_mod.generate_and_save_modern_dashboard(cls.workspace_dir)

    def test_01_directories_and_files_exist(self):
        """Verify both Simple and Classic and Modern and Interactive folders exist with dashboards."""
        self.assertTrue(self.classic_dir.is_dir(), "Simple and Classic Dashboard directory must exist.")
        self.assertTrue((self.classic_dir / "dashboard.html").is_file(), "Classic dashboard.html must exist.")
        self.assertTrue((self.classic_dir / "README.md").is_file(), "Classic README.md must exist.")

        self.assertTrue(self.modern_dir.is_dir(), "Modern and Interactive Dashboard directory must exist.")
        self.assertTrue((self.modern_dir / "dashboard.html").is_file(), "Modern dashboard.html must exist.")
        self.assertTrue((self.modern_dir / "README.md").is_file(), "Modern README.md must exist.")
        self.assertTrue((self.modern_dir / "generate_modern_dashboard.py").is_file(), "Generator script must exist.")

        self.assertTrue((self.reports_dir / "modern_dashboard.html").is_file(), "reports/modern_dashboard.html must exist.")
        self.assertTrue((self.reports_dir / "classic_dashboard.html").is_file(), "reports/classic_dashboard.html must exist.")

    def test_02_modern_html_features(self):
        """Verify all modern UI/UX innovations are embedded in the modern dashboard HTML."""
        content = (self.modern_dir / "dashboard.html").read_text(encoding="utf-8")

        # 1. Header Dual Clusters
        self.assertIn("health-cluster", content, "Header must have health-cluster.")
        self.assertIn("action-cluster", content, "Header must have action-cluster.")
        self.assertIn("btn-classic-switch", content, "Must have switcher to classic dashboard.")

        # 2. Live Pulse Ticker Strip
        self.assertIn("live-ticker-strip", content, "Must have live pulse ticker strip.")
        self.assertIn("ticker-beacon", content, "Must have ticker beacon.")

        # 3. Slide-Up Live Console Logs Drawer
        self.assertIn('id="logs-drawer"', content, "Must have slide-up logs drawer.")
        self.assertIn('id="btn-toggle-logs"', content, "Must have logs toggle button.")

        # 4. Visual Hierarchy: 2 North Star KPIs
        self.assertIn("hero-kpis-grid", content, "Must have hero-kpis-grid.")
        self.assertIn("card-questions", content, "Must have questions hero card.")
        self.assertIn("card-runs", content, "Must have runs hero card.")
        self.assertIn("counter-value", content, "Must have number counter animation hook.")

        # 5. Context-Aware Filter Toolbar & Active Chips
        self.assertIn('id="contextual-filter-toolbar"', content, "Must have contextual filter toolbar.")
        self.assertIn("active-chips-row", content, "Must have active filter dismiss chips.")

        # 6. Interactive Floating SVG Tooltip
        self.assertIn('id="chart-floating-tooltip"', content, "Must have floating SVG chart tooltip container.")

        # 7. Questions Tab 1-Click Copy Q&A
        self.assertIn("btn-copy-qa", content, "Must have copy Q&A button.")
        self.assertIn("badge-selected", content, "Must have selected badge.")
        self.assertIn("badge-recommended", content, "Must have recommended badge.")

        # 8. Mode Switch Visual Diff
        self.assertIn('id="mode-card-prod"', content, "Must have production mode card.")
        self.assertIn('id="mode-card-test"', content, "Must have test mode card.")
        self.assertIn("diff-table", content, "Must have diff comparison table.")

        # 9. Config Tab Search & Unsaved Changes Dock
        self.assertIn('id="search-config"', content, "Must have config search input.")
        self.assertIn('id="unsaved-changes-dock"', content, "Must have floating unsaved changes dock.")

        # 10. Web Audio API Synthesizer
        self.assertIn("playChime", content, "Must have Web Audio synthesizer playChime.")
        self.assertIn("AudioContext", content, "Must utilize AudioContext.")

        # 11. Keyboard Shortcuts HUD Modal
        self.assertIn('id="shortcuts-modal"', content, "Must have shortcuts HUD modal.")

    def test_03_server_routes_classic_and_modern(self):
        """Verify dashboard server serves /classic and /modern endpoints cleanly."""
        # Find free ephemeral port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        server = DashboardServer(host="127.0.0.1", port=port, workspace_dir=self.workspace_dir)
        server.start(open_browser=False, in_thread=True)
        time.sleep(0.4)

        try:
            # 1. GET /modern
            req_modern = urllib.request.Request(f"http://127.0.0.1:{port}/modern")
            with urllib.request.urlopen(req_modern, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                self.assertIn("MODERN & INTERACTIVE", body)

            # 2. GET /classic
            req_classic = urllib.request.Request(f"http://127.0.0.1:{port}/classic")
            with urllib.request.urlopen(req_classic, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                self.assertIn("AutoSelect-Commander", body)

            # 3. GET / (default should serve modern)
            req_root = urllib.request.Request(f"http://127.0.0.1:{port}/")
            with urllib.request.urlopen(req_root, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                self.assertIn("MODERN & INTERACTIVE", body)

        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
