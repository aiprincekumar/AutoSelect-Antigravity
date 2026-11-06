"""
AutoSelect-Commander - AutoStart Subsystem Test Suite
======================================================
Tests: step_4_reporting/autostart.py and dashboard_server autostart integration
Standard: Department 08 (QA & Testing) / Universal Rule 4 & 5
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Features Verified:
  1. Safe startup directory resolution and APPDATA environment isolation.
  2. enable_autostart() creates .lnk shortcut in isolated temporary directory.
  3. is_autostart_enabled() accurate True/False reporting.
  4. disable_autostart() cleanly deletes .lnk file and operates idempotently.
  5. get_autostart_status() returns complete diagnostic payload.
  6. CLI commands (--enable-autostart, --disable-autostart, --status-autostart).
  7. Safe zero-pollution guarantee (real user Startup folder is never touched during tests).
"""

from __future__ import annotations

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Workspace root anchor
_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _THIS_DIR.parent if _THIS_DIR.name == "step_4_reporting" else _THIS_DIR
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from step_4_reporting.autostart import (
    DEFAULT_SHORTCUT_NAME,
    get_startup_folder,
    get_shortcut_path,
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    get_autostart_status,
    resolve_workspace_root,
    resolve_vbs_launcher,
)


class TestAutoStartSubsystem(unittest.TestCase):
    """Unit tests for Windows Auto-Start registration engine."""

    def setUp(self):
        """Create an isolated temporary environment before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_autostart_")
        self.temp_path = Path(self.temp_dir).resolve()
        self.mock_startup_dir = (self.temp_path / "Startup").resolve()
        self.mock_startup_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up isolated temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_startup_folder_override(self):
        """Verify startup folder override takes precedence."""
        res = get_startup_folder(override_dir=self.mock_startup_dir)
        self.assertEqual(res, self.mock_startup_dir.resolve())

    def test_get_startup_folder_respects_appdata(self):
        """Verify APPDATA environment variable is correctly used."""
        mock_appdata = str(self.temp_path / "Roaming")
        with patch.dict(os.environ, {"APPDATA": mock_appdata}):
            expected = Path(mock_appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            actual = get_startup_folder()
            self.assertEqual(actual, expected)

    def test_get_shortcut_path(self):
        """Verify shortcut path resolution with custom name."""
        sc = get_shortcut_path(shortcut_name="Custom_Test.lnk", startup_dir=self.mock_startup_dir)
        self.assertEqual(sc.resolve(), (self.mock_startup_dir / "Custom_Test.lnk").resolve())

    def test_is_autostart_enabled_initially_false(self):
        """Verify is_autostart_enabled returns False when shortcut does not exist."""
        self.assertFalse(
            is_autostart_enabled(shortcut_name=DEFAULT_SHORTCUT_NAME, startup_dir=self.mock_startup_dir)
        )

    def test_enable_autostart_lifecycle(self):
        """Verify full lifecycle: enable -> check status -> disable -> check status."""
        test_shortcut = "Test_Dashboard.lnk"
        
        # 1. Enable autostart in temporary directory
        res_enable = enable_autostart(
            shortcut_name=test_shortcut,
            startup_dir=self.mock_startup_dir,
            workspace_dir=_WORKSPACE_DIR
        )
        self.assertTrue(res_enable.get("success"), f"enable_autostart failed: {res_enable}")
        self.assertTrue((self.mock_startup_dir / test_shortcut).is_file())
        self.assertTrue(
            is_autostart_enabled(shortcut_name=test_shortcut, startup_dir=self.mock_startup_dir)
        )

        # 2. Query status
        status = get_autostart_status(shortcut_name=test_shortcut, startup_dir=self.mock_startup_dir)
        self.assertTrue(status.get("enabled"))
        self.assertTrue(status.get("exists"))
        self.assertEqual(status.get("shortcut_name"), test_shortcut)
        self.assertTrue(Path(status.get("vbs_launcher")).is_file())

        # 3. Disable autostart
        res_disable = disable_autostart(shortcut_name=test_shortcut, startup_dir=self.mock_startup_dir)
        self.assertTrue(res_disable.get("success"))
        self.assertTrue(res_disable.get("was_present"))
        self.assertFalse((self.mock_startup_dir / test_shortcut).exists())
        self.assertFalse(
            is_autostart_enabled(shortcut_name=test_shortcut, startup_dir=self.mock_startup_dir)
        )

        # 4. Verify disable idempotency
        res_disable_again = disable_autostart(shortcut_name=test_shortcut, startup_dir=self.mock_startup_dir)
        self.assertTrue(res_disable_again.get("success"))
        self.assertFalse(res_disable_again.get("was_present"))

    def test_appdata_monkeypatch_isolation(self):
        """Verify that monkeypatching APPDATA isolates execution without touching user Startup."""
        isolated_roaming = self.temp_path / "IsolatedAppData"
        with patch.dict(os.environ, {"APPDATA": str(isolated_roaming)}):
            res = enable_autostart(workspace_dir=_WORKSPACE_DIR)
            self.assertTrue(res.get("success"))
            
            created_path = Path(res.get("shortcut_path"))
            self.assertTrue(created_path.is_file())
            # Ensure the file was created inside the isolated temp directory
            self.assertTrue(str(isolated_roaming) in str(created_path))
            
            # Disable and verify removal
            dis_res = disable_autostart()
            self.assertTrue(dis_res.get("success"))
            self.assertFalse(created_path.exists())

    def test_resolve_vbs_launcher(self):
        """Verify VBS launcher resolver finds background launcher files."""
        vbs = resolve_vbs_launcher(workspace_dir=_WORKSPACE_DIR)
        self.assertTrue(vbs.is_file())
        self.assertTrue(vbs.name.endswith(".vbs"))

    def test_dashboard_server_cli_autostart_status(self):
        """Verify dashboard_server CLI --status-autostart executes cleanly."""
        from step_4_reporting.dashboard_server import main as server_main
        with patch.object(sys, "argv", ["dashboard_server.py", "--status-autostart"]):
            ret = server_main()
            self.assertEqual(ret, 0)

    def test_dashboard_server_cli_enable_and_disable(self):
        """Verify dashboard_server CLI --enable-autostart and --disable-autostart in isolated env."""
        from step_4_reporting.dashboard_server import main as server_main
        isolated_roaming = self.temp_path / "IsolatedCliAppData"
        with patch.dict(os.environ, {"APPDATA": str(isolated_roaming)}):
            with patch.object(sys, "argv", ["dashboard_server.py", "--enable-autostart"]):
                ret_enable = server_main()
                self.assertEqual(ret_enable, 0)
                
            expected_shortcut = (
                isolated_roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / DEFAULT_SHORTCUT_NAME
            )
            self.assertTrue(expected_shortcut.is_file())

            with patch.object(sys, "argv", ["dashboard_server.py", "--disable-autostart"]):
                ret_disable = server_main()
                self.assertEqual(ret_disable, 0)
                
            self.assertFalse(expected_shortcut.exists())


if __name__ == "__main__":
    unittest.main()
