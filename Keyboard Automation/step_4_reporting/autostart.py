"""
AutoSelect-Commander - Windows Auto-Start Manager
=================================================
Subsystem: Step 4: Reporting & Visual Telemetry Local Server
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 04 (Automation & Tooling) & Department 06 (Backend Engineering)

Description:
    Provides automated Windows startup registration for the Dashboard Server.
    Creates, queries, and removes a persistent background launcher shortcut
    in the Windows user Startup folder (%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup).
    Ensures 100% headless daemon launch with no flashing console windows
    and no disruptive browser popups on Windows user login.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Configure logging
logger = logging.getLogger("AutoStartManager")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [AutoStart] %(message)s",
        datefmt="%H:%M:%S"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

DEFAULT_SHORTCUT_NAME = "Keyboard_Automation_Dashboard.lnk"


def get_startup_folder(override_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Resolve the Windows user Startup directory.
    Uses override_dir if provided, otherwise respects %APPDATA%,
    falling back to standard user profile path.
    """
    if override_dir:
        return Path(override_dir).resolve()
    
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def get_shortcut_path(
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
    startup_dir: Optional[Union[str, Path]] = None
) -> Path:
    """Get the full resolved path of the startup shortcut."""
    folder = get_startup_folder(override_dir=startup_dir)
    return folder / shortcut_name


def resolve_workspace_root(start_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Dynamically locate the Keyboard Automation workspace root directory.
    Searches upward from the current file location or provided start_path.
    """
    current = Path(start_path).resolve() if start_path else Path(__file__).resolve().parent
    
    # Check current directory and its parents
    check_dirs = [current] + list(current.parents)
    for directory in check_dirs:
        # Check if directory contains step_4_reporting and launchers
        if (directory / "step_4_reporting").is_dir() and (directory / "launchers").is_dir():
            return directory
        # Check if directory is the Keyboard Automation directory itself
        if (directory / "dashboard_server.py").is_file() and (directory / "launchers").is_dir():
            return directory

    # Fallback to parent of step_4_reporting
    return Path(__file__).resolve().parent.parent


def resolve_vbs_launcher(
    workspace_dir: Optional[Union[str, Path]] = None,
    prefer_silent_wrapper: bool = True
) -> Path:
    """
    Locate the VBScript background launcher for the dashboard server.
    Prefers autostart_dashboard_silent.vbs, with fallback to start_dashboard_background.vbs.
    """
    ws = Path(workspace_dir).resolve() if workspace_dir else resolve_workspace_root()
    
    candidates = []
    if prefer_silent_wrapper:
        candidates.extend([
            ws / "launchers" / "autostart_dashboard_silent.vbs",
            ws / "step_4_reporting" / "autostart_dashboard_silent.vbs",
        ])
    
    candidates.extend([
        ws / "launchers" / "start_dashboard_background.vbs",
        ws / "step_4_reporting" / "start_dashboard_background.vbs",
    ])
    
    for candidate in candidates:
        if candidate.is_file():
            return candidate
            
    # Default fallback
    return ws / "launchers" / "start_dashboard_background.vbs"


def is_autostart_enabled(
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
    startup_dir: Optional[Union[str, Path]] = None
) -> bool:
    """Check whether the Windows Auto-Start shortcut currently exists on disk."""
    sc_path = get_shortcut_path(shortcut_name=shortcut_name, startup_dir=startup_dir)
    return sc_path.is_file()


def enable_autostart(
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
    startup_dir: Optional[Union[str, Path]] = None,
    workspace_dir: Optional[Union[str, Path]] = None,
    vbs_path: Optional[Union[str, Path]] = None,
    silent_args: str = "--no-browser",
    description: str = "AutoSelect Antigravity - Dashboard Control Server Background Auto-Start"
) -> Dict[str, Any]:
    """
    Register the Dashboard Server into Windows Startup.
    Creates a shortcut (.lnk) targeting wscript.exe with the background launcher VBScript.
    Ensures 100% silent, headless execution without browser popup on login.

    Returns:
        Dict with status, shortcut_path, target_path, arguments, working_dir, success.
    """
    ws = Path(workspace_dir).resolve() if workspace_dir else resolve_workspace_root()
    folder = get_startup_folder(override_dir=startup_dir)
    folder.mkdir(parents=True, exist_ok=True)
    
    sc_path = folder / shortcut_name
    launcher = Path(vbs_path).resolve() if vbs_path else resolve_vbs_launcher(workspace_dir=ws)
    
    # Target executable: wscript.exe (guarantees windowless execution)
    target_exe = "wscript.exe"
    
    # Arguments: quoted launcher path followed by silent flag
    # If the launcher is already autostart_dashboard_silent.vbs, passing --no-browser is still safe
    arguments = f'"{launcher}" {silent_args}'.strip()
    working_directory = str(ws)

    # Use PowerShell to construct the COM shortcut with WScript.Shell
    # Escape quotes and backslashes for PowerShell execution
    ps_cmd = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$sc = $ws.CreateShortcut('{sc_path}'); "
        f"$sc.TargetPath = '{target_exe}'; "
        f"$sc.Arguments = [char]34 + '{launcher}' + [char]34 + ' {silent_args}'; "
        f"$sc.WorkingDirectory = '{working_directory}'; "
        f"$sc.Description = '{description}'; "
        f"$sc.WindowStyle = 7; "
        f"$sc.Save();"
    )

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        if proc.returncode != 0:
            logger.error(f"PowerShell error creating shortcut: {proc.stderr}")
            return {
                "success": False,
                "action": "enable",
                "error": proc.stderr.strip() or "PowerShell returned non-zero exit code",
                "shortcut_path": str(sc_path),
                "exists": sc_path.is_file()
            }
    except Exception as exc:
        logger.exception(f"Failed to execute PowerShell shortcut creation: {exc}")
        return {
            "success": False,
            "action": "enable",
            "error": str(exc),
            "shortcut_path": str(sc_path),
            "exists": sc_path.is_file()
        }

    exists = sc_path.is_file()
    if exists:
        logger.info(f"Windows Auto-Start shortcut successfully created: {sc_path}")
    else:
        logger.error(f"Shortcut file not found after creation attempt: {sc_path}")

    return {
        "success": exists,
        "action": "enable",
        "shortcut_name": shortcut_name,
        "shortcut_path": str(sc_path),
        "target_path": target_exe,
        "arguments": arguments,
        "working_directory": working_directory,
        "vbs_launcher": str(launcher),
        "exists": exists,
        "message": f"Successfully registered Auto-Start: {sc_path}" if exists else "Failed to register Auto-Start shortcut."
    }


def disable_autostart(
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
    startup_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Remove the Auto-Start shortcut from the Windows Startup folder.
    This operation is strictly idempotent (safe to call even if not present).

    Returns:
        Dict with status, shortcut_path, was_present, exists, success.
    """
    sc_path = get_shortcut_path(shortcut_name=shortcut_name, startup_dir=startup_dir)
    was_present = sc_path.is_file()

    if was_present:
        try:
            sc_path.unlink(missing_ok=True)
            logger.info(f"Windows Auto-Start shortcut successfully removed: {sc_path}")
            return {
                "success": True,
                "action": "disable",
                "shortcut_name": shortcut_name,
                "shortcut_path": str(sc_path),
                "was_present": True,
                "exists": False,
                "message": f"Successfully removed Auto-Start shortcut: {sc_path}"
            }
        except Exception as exc:
            logger.exception(f"Failed to delete shortcut file {sc_path}: {exc}")
            return {
                "success": False,
                "action": "disable",
                "error": str(exc),
                "shortcut_path": str(sc_path),
                "was_present": True,
                "exists": sc_path.is_file()
            }

    logger.info(f"Windows Auto-Start shortcut was not present: {sc_path}")
    return {
        "success": True,
        "action": "disable",
        "shortcut_name": shortcut_name,
        "shortcut_path": str(sc_path),
        "was_present": False,
        "exists": False,
        "message": "Auto-Start shortcut was not present (already disabled)."
    }


def get_autostart_status(
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
    startup_dir: Optional[Union[str, Path]] = None,
    workspace_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Query the status of Windows Auto-Start registration.
    Returns details on shortcut existence, paths, and configured targets.
    """
    ws = Path(workspace_dir).resolve() if workspace_dir else resolve_workspace_root()
    folder = get_startup_folder(override_dir=startup_dir)
    sc_path = folder / shortcut_name
    exists = sc_path.is_file()
    vbs_path = resolve_vbs_launcher(workspace_dir=ws)

    details: Dict[str, Any] = {
        "enabled": exists,
        "shortcut_name": shortcut_name,
        "shortcut_path": str(sc_path),
        "startup_folder": str(folder),
        "workspace_directory": str(ws),
        "vbs_launcher": str(vbs_path),
        "exists": exists,
    }

    # If shortcut exists, inspect its COM properties for full transparency
    if exists and sys.platform == "win32":
        try:
            inspect_cmd = (
                f"$ws = New-Object -ComObject WScript.Shell; "
                f"$sc = $ws.CreateShortcut('{sc_path}'); "
                f"Write-Host ($sc.TargetPath + '|||' + $sc.Arguments + '|||' + $sc.WorkingDirectory);"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", inspect_cmd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if proc.returncode == 0 and "|||" in proc.stdout:
                parts = proc.stdout.strip().split("|||")
                if len(parts) >= 3:
                    details["target_path"] = parts[0]
                    details["arguments"] = parts[1]
                    details["configured_working_dir"] = parts[2]
        except Exception as exc:
            logger.debug(f"Could not read shortcut properties: {exc}")

    return details


# ============================================================================
# CLI Command Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AutoSelect Antigravity Windows Auto-Start Manager"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--enable", action="store_true", help="Enable Windows Auto-Start on user login")
    group.add_argument("--disable", action="store_true", help="Disable Windows Auto-Start")
    group.add_argument("--status", action="store_true", help="Query current Windows Auto-Start status")
    
    parser.add_argument("--json", action="store_true", help="Output result as JSON format")
    args = parser.parse_args()

    if args.enable:
        res = enable_autostart()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[{'SUCCESS' if res.get('success') else 'ERROR'}] {res.get('message', res)}")
        return 0 if res.get("success") else 1

    elif args.disable:
        res = disable_autostart()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[{'SUCCESS' if res.get('success') else 'ERROR'}] {res.get('message', res)}")
        return 0 if res.get("success") else 1

    elif args.status:
        st = get_autostart_status()
        if args.json:
            print(json.dumps(st, indent=2))
        else:
            state_str = "ENABLED" if st.get("enabled") else "DISABLED"
            print(f"Windows Auto-Start Status: [{state_str}]")
            print(f"  Shortcut Path: {st.get('shortcut_path')}")
            print(f"  Target Script: {st.get('vbs_launcher')}")
            print(f"  Workspace    : {st.get('workspace_directory')}")
            if "arguments" in st:
                print(f"  Arguments    : {st.get('arguments')}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
