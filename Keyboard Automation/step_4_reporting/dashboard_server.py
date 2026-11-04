#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Automation Control & Visual Dashboard Server (dashboard_server.py)
========================================================================
Pipeline Role: Local HTTP/REST API Control Server & Static Dashboard Host
Part of: AutoSelect-Commander Automation Suite
Standard: Department 06 (Backend & API Engineering) & Department 05 (Frontend Architecture)
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Responsibilities:
  1. Local HTTP Server: Serves `dashboard.html` and telemetry assets with zero external dependencies.
  2. RESTful Automation Control:
     - `POST /api/automation/start`: Spawns `complete_automation.py` in background, tracks PID & logs.
     - `POST /api/automation/stop`: Gracefully terminates the running automation process tree on Windows.
     - `GET  /api/automation/status`: Returns live process running state, PID, uptime, mode, and log output.
     - `GET  /api/config/get`: Fetches runtime configuration from `config.json`.
     - `POST /api/config/save`: Directly updates and persists runtime configuration to `config.json`.
     - `GET  /api/logs/tail`: Returns live tail of `complete_automation.log`.
     - `POST /api/dashboard/refresh`: Triggers synchronous re-generation of `dashboard.html`.
  3. Universal CORS Support: Full `Access-Control-Allow-Origin: *` support allowing `file:///` dashboards
     to safely communicate with the local control daemon.
  4. Zero-Hang Hygiene (Rule 26): Clean socket and subprocess teardown on shutdown.
"""

from __future__ import annotations

import os
import sys
import json
import time
import signal
import socket
import logging
import argparse
import webbrowser
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional, Tuple, List

# Workspace and Directory Anchors
_THIS_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _THIS_DIR.parent if _THIS_DIR.name == "step_4_reporting" else _THIS_DIR

# Ensure workspace root is in sys.path
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

# Core imports for unified config management
try:
    from core_engine.config_manager import (
        get_canonical_config_path,
        load_runtime_config as core_load_runtime_config,
        save_runtime_config as core_save_runtime_config,
        get_default_runtime_config,
    )
except ImportError:
    # Fail-safe local fallback if core_engine cannot be loaded
    def get_canonical_config_path(workspace: Optional[Path] = None) -> Path:
        base = workspace or _WORKSPACE_DIR
        return base / "step_9_complete_automation" / "config.json"

    def core_load_runtime_config(path: Optional[Path] = None) -> Dict[str, Any]:
        p = path or get_canonical_config_path()
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"mode": "production", "timing": {}, "enabled_steps": {}}

    def core_save_runtime_config(cfg: Dict[str, Any], path: Optional[Path] = None) -> bool:
        p = path or get_canonical_config_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

# Setup module logger
logger = logging.getLogger("DashboardServer")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [DashboardServer] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ============================================================================
# OS Process Utilities (Windows-Safe, Non-Destructive)
# ============================================================================

def is_pid_alive(pid: int) -> bool:
    """
    Check if a process with given PID is currently active.
    Uses Win32 API via ctypes on Windows for reliable non-destructive polling.
    """
    if not pid or pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            success = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            if success:
                return exit_code.value == STILL_ACTIVE
            return False
        except Exception:
            pass

    # Fallback for POSIX platforms
    try:
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError):
        return False


# ============================================================================
# Automation Process Lifecycle Manager
# ============================================================================

class AutomationProcessManager:
    """
    Manages the lifecycle of the background complete automation process (Step 9 / Step 0).
    Provides atomic process start, tree termination, PID file tracking, and log output.
    """

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else _WORKSPACE_DIR
        self.python_exe = self._resolve_python_exe()
        self.master_script = self.workspace_dir / "step_9_complete_automation" / "complete_automation.py"
        self.log_file = self.workspace_dir / "step_9_complete_automation" / "complete_automation.log"
        self.pid_file = self.workspace_dir / "step_4_reporting" / ".automation_process.json"
        
        self.proc: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None
        self.active_mode: str = "production"
        self._lock = threading.RLock()

        # Recover prior state if server was restarted while automation was running
        self._recover_state()

    def _resolve_python_exe(self) -> Path:
        """Locate the dedicated .venv python.exe or fall back to sys.executable."""
        venv_py = self.workspace_dir / ".venv" / "Scripts" / "python.exe"
        if venv_py.is_file():
            return venv_py
        return Path(sys.executable)

    def _cleanup_pid_file(self) -> None:
        """Safely remove the PID tracking file."""
        try:
            if self.pid_file.is_file():
                self.pid_file.unlink()
        except Exception:
            pass

    def _recover_state(self) -> None:
        """Check if an existing automation process is still alive from a previous run."""
        if not self.pid_file.is_file():
            return

        try:
            with open(self.pid_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            stored_pid = data.get("pid")
            stored_start = data.get("start_time")
            stored_mode = data.get("mode", "production")

            if stored_pid and is_pid_alive(stored_pid):
                self.start_time = stored_start
                self.active_mode = stored_mode
                logger.info(f"Discovered active background automation process (PID: {stored_pid}).")
            else:
                self._cleanup_pid_file()
        except Exception as e:
            logger.debug(f"Could not recover PID state: {e}")
            self._cleanup_pid_file()

    def is_running(self) -> bool:
        """Return True if the managed automation process is actively executing."""
        with self._lock:
            # 1. Directly managed Popen handle
            if self.proc is not None:
                if self.proc.poll() is None:
                    return True
                else:
                    self.proc = None
                    self._cleanup_pid_file()
                    return False

            # 2. Check recovered PID from file
            if self.pid_file.is_file():
                try:
                    with open(self.pid_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    pid = data.get("pid")
                    if pid and is_pid_alive(pid):
                        return True
                    else:
                        self._cleanup_pid_file()
                except Exception:
                    self._cleanup_pid_file()

            return False

    def get_pid(self) -> Optional[int]:
        """Return current automation PID if active."""
        if self.proc and self.proc.poll() is None:
            return self.proc.pid
        if self.pid_file.is_file():
            try:
                with open(self.pid_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pid = data.get("pid")
                if pid and is_pid_alive(pid):
                    return pid
            except Exception:
                pass
        return None

    def start(self, mode: Optional[str] = None, run_pipeline: bool = False) -> Dict[str, Any]:
        """
        Spawn the complete automation background process.
        """
        with self._lock:
            if self.is_running():
                current_pid = self.get_pid()
                return {
                    "running": True,
                    "pid": current_pid,
                    "message": f"Automation process is already running (PID: {current_pid}).",
                    "mode": self.active_mode,
                }

            # Ensure master script exists
            if not self.master_script.is_file():
                return {
                    "running": False,
                    "pid": None,
                    "message": f"Master automation script not found at: {self.master_script}",
                    "mode": mode or "production",
                }

            # Load mode from config if not specified
            eff_mode = mode
            if not eff_mode:
                cfg = core_load_runtime_config(get_canonical_config_path(self.workspace_dir))
                eff_mode = cfg.get("mode", "production")

            self.active_mode = eff_mode

            # Build command line
            cmd = [str(self.python_exe), str(self.master_script)]
            if eff_mode:
                cmd.extend(["--mode", str(eff_mode)])
            if run_pipeline:
                cmd.append("--run-pipeline")

            # Prepare log destination
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            log_fp = open(self.log_file, "a", encoding="utf-8")
            log_fp.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Dashboard Server Spawn: {' '.join(cmd)} ---\n")
            log_fp.flush()

            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.workspace_dir),
                    stdout=log_fp,
                    stderr=subprocess.STDOUT,
                    creationflags=creationflags,
                )
            finally:
                log_fp.close()

            try:
                self.start_time = time.time()

                # Persist state
                state_data = {
                    "pid": self.proc.pid,
                    "start_time": self.start_time,
                    "mode": eff_mode,
                    "cmd": cmd,
                }
                self.pid_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.pid_file, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=2)

                logger.info(f"Automation process launched successfully (PID: {self.proc.pid}, Mode: {eff_mode}).")
                return {
                    "running": True,
                    "pid": self.proc.pid,
                    "message": f"Automation process started successfully (PID: {self.proc.pid}).",
                    "mode": eff_mode,
                }
            except Exception as e:
                logger.error(f"Failed to spawn automation process: {e}")
                self.proc = None
                self._cleanup_pid_file()
                return {
                    "running": False,
                    "pid": None,
                    "message": f"Failed to start automation: {e}",
                    "mode": eff_mode,
                }

    def stop(self) -> Dict[str, Any]:
        """
        Gracefully terminate the automation process tree.
        On Windows, invokes `taskkill /F /T /PID` to cleanly clean child step processes.
        """
        with self._lock:
            pid = self.get_pid()
            if not pid and not self.proc:
                self._cleanup_pid_file()
                return {
                    "running": False,
                    "pid": None,
                    "message": "No automation process is currently running.",
                }

            target_pid = pid or (self.proc.pid if self.proc else None)
            logger.info(f"Initiating termination for automation process (PID: {target_pid})...")

            # 1. Kill entire Windows process tree if on Windows and PID is alive
            if sys.platform == "win32" and target_pid and is_pid_alive(target_pid):
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(target_pid)],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=3.0,
                    )
                except Exception as e:
                    logger.warning(f"taskkill execution failed: {e}")

            # 2. Popen handle termination if available
            if self.proc is not None:
                try:
                    self.proc.terminate()
                    self.proc.wait(timeout=2.0)
                except Exception:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass

            self.proc = None
            self.start_time = None
            self._cleanup_pid_file()
            logger.info(f"Automation process (PID: {target_pid}) stopped.")

            return {
                "running": False,
                "pid": None,
                "message": f"Automation process (PID: {target_pid}) stopped successfully.",
            }

    def get_log_tail(self, max_lines: int = 50) -> str:
        """Retrieve the last N lines of the automation log file."""
        if not self.log_file.is_file():
            return "No log file found."
        try:
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return "".join(lines[-max_lines:])
        except Exception as e:
            return f"Error reading logs: {e}"

    def get_status(self) -> Dict[str, Any]:
        """Compile a complete status summary dictionary."""
        running = self.is_running()
        pid = self.get_pid() if running else None
        uptime = (time.time() - self.start_time) if (running and self.start_time) else 0.0

        return {
            "running": running,
            "pid": pid,
            "uptime_seconds": round(uptime, 1),
            "mode": self.active_mode,
            "status_text": "Active" if running else "Inactive",
            "python_exe": str(self.python_exe),
            "master_script": str(self.master_script),
            "log_file": str(self.log_file),
            "last_log": self.get_log_tail(15),
        }


# ============================================================================
# HTTP Request Handler (Department 06 REST Standard & Universal CORS)
# ============================================================================

class DashboardRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP handler serving dashboard static assets and RESTful automation control endpoints.
    Enforces Department 06 response envelopes and cross-origin headers.
    """

    server_manager: AutomationProcessManager = None  # Injected by server
    workspace_dir: Path = _WORKSPACE_DIR
    reports_dir: Path = _WORKSPACE_DIR / "step_4_reporting" / "reports"
    dashboard_file: Path = _WORKSPACE_DIR / "step_4_reporting" / "reports" / "dashboard.html"

    def log_message(self, format: str, *args: Any) -> None:
        """Silence standard console noise for clean terminal output; log only errors."""
        if args and str(args[1]) in ("404", "500"):
            logger.warning(f"{self.client_address[0]} - {format % args}")

    def send_cors_headers(self) -> None:
        """Inject universal CORS headers allowing file:/// origin communication."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

    def send_json_response(self, data: Any, status: int = 200, success: bool = True) -> None:
        """Format and return Department 06 standardized JSON response envelope."""
        payload = {
            "success": success,
            "data": data if success else None,
            "error": None if success else data,
            "meta": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "server": "AutoSelect-Dashboard-Control/1.0",
            },
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests seamlessly."""
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests for static pages and telemetry endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"

        # 1. API: Process Status
        if path == "/api/automation/status":
            mgr = self.server_manager or AutomationProcessManager(self.workspace_dir)
            self.send_json_response(mgr.get_status())
            return

        # 2. API: Runtime Configuration
        if path == "/api/config/get":
            cfg_path = get_canonical_config_path(self.workspace_dir)
            cfg = core_load_runtime_config(cfg_path)
            self.send_json_response(cfg)
            return

        # 3. API: Log Output Tail
        if path == "/api/logs/tail":
            mgr = self.server_manager or AutomationProcessManager(self.workspace_dir)
            query = parse_qs(parsed.query)
            lines_count = int(query.get("lines", [50])[0])
            self.send_json_response({"logs": mgr.get_log_tail(lines_count)})
            return

        # 4. Static: Dashboard HTML
        if path in ("/", "/dashboard", "/dashboard.html", "/index.html"):
            if not self.dashboard_file.is_file():
                try:
                    from step_4_reporting.step4_reporting import Step4ReportingEngine
                    engine = Step4ReportingEngine(reports_dir=self.reports_dir)
                    engine.generate_html_dashboard()
                except Exception as e:
                    logger.error(f"Failed to generate dashboard HTML: {e}")

            if self.dashboard_file.is_file():
                try:
                    content = self.dashboard_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_cors_headers()
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    self.send_json_response({"message": f"Error reading dashboard file: {e}"}, status=500, success=False)
                    return

            self.send_json_response({"message": "Dashboard file not found and could not be generated."}, status=404, success=False)
            return

        # 5. Static Assets in reports/
        asset_rel = parsed.path.lstrip("/")
        potential_asset = self.reports_dir / asset_rel
        if potential_asset.is_file() and self.reports_dir in potential_asset.parents:
            content_type = "application/octet-stream"
            if potential_asset.suffix == ".html":
                content_type = "text/html; charset=utf-8"
            elif potential_asset.suffix == ".json":
                content_type = "application/json; charset=utf-8"
            elif potential_asset.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif potential_asset.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            elif potential_asset.suffix == ".svg":
                content_type = "image/svg+xml"

            try:
                data = potential_asset.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_cors_headers()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                self.send_json_response({"message": f"Error loading asset: {e}"}, status=500, success=False)
                return

        # Default: 404 Not Found
        self.send_json_response({"message": f"Resource not found: {self.path}"}, status=404, success=False)

    def do_POST(self) -> None:
        """Handle POST requests for automation action triggers and config updates."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        body: Dict[str, Any] = {}
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        mgr = self.server_manager or AutomationProcessManager(self.workspace_dir)

        # 1. API: Start Automation
        if path == "/api/automation/start":
            mode = body.get("mode")
            run_pipeline = bool(body.get("run_pipeline", False))
            result = mgr.start(mode=mode, run_pipeline=run_pipeline)
            self.send_json_response(result)
            return

        # 2. API: Stop Automation
        if path == "/api/automation/stop":
            result = mgr.stop()
            self.send_json_response(result)
            return

        # 3. API: Save Runtime Configuration
        if path == "/api/config/save":
            if not isinstance(body, dict) or not body:
                self.send_json_response({"message": "Invalid JSON configuration payload."}, status=400, success=False)
                return

            cfg_path = get_canonical_config_path(self.workspace_dir)
            ok = core_save_runtime_config(body, cfg_path)
            if ok:
                logger.info("Successfully updated runtime configuration in config.json.")
                self.send_json_response({"saved": True, "message": "Configuration successfully saved to config.json on disk."})
            else:
                self.send_json_response({"saved": False, "message": "Failed to persist configuration to disk."}, status=500, success=False)
            return

        # 4. API: Synchronous Dashboard HTML Refresh
        if path == "/api/dashboard/refresh":
            try:
                from step_4_reporting.step4_reporting import Step4ReportingEngine
                engine = Step4ReportingEngine(reports_dir=self.reports_dir)
                gen_path = engine.generate_html_dashboard()
                self.send_json_response({"refreshed": True, "path": str(gen_path)})
            except Exception as e:
                self.send_json_response({"refreshed": False, "message": f"Refresh failed: {e}"}, status=500, success=False)
            return

        # Default: 404
        self.send_json_response({"message": f"Endpoint not found: {self.path}"}, status=404, success=False)


# ============================================================================
# Threading HTTP Server & Port Finder
# ============================================================================

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server handling concurrent API polling and asset delivery."""
    daemon_threads = True
    allow_reuse_address = True


def find_available_port(host: str = "127.0.0.1", start_port: int = 8501, max_attempts: int = 15) -> int:
    """Find an unbound TCP port beginning at start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    return start_port


class DashboardServer:
    """
    Encapsulates the HTTP control daemon with programmatic start, stop,
    and automatic browser launch capabilities.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8501,
        workspace_dir: Optional[Path] = None,
    ):
        self.host = host
        self.requested_port = port
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else _WORKSPACE_DIR
        self.manager = AutomationProcessManager(self.workspace_dir)
        self.actual_port: int = find_available_port(self.host, self.requested_port)
        self.httpd: Optional[ThreadedHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, open_browser: bool = False, in_thread: bool = False) -> None:
        """Start the control server either synchronously or in a background daemon thread."""
        DashboardRequestHandler.server_manager = self.manager
        DashboardRequestHandler.workspace_dir = self.workspace_dir
        DashboardRequestHandler.reports_dir = self.workspace_dir / "step_4_reporting" / "reports"
        DashboardRequestHandler.dashboard_file = DashboardRequestHandler.reports_dir / "dashboard.html"

        server_address = (self.host, self.actual_port)
        self.httpd = ThreadedHTTPServer(server_address, DashboardRequestHandler)
        url = f"http://{self.host}:{self.actual_port}/"

        logger.info("=" * 70)
        logger.info("  AutoSelect-Commander - Local Control & Dashboard Server")
        logger.info(f"  Live URL    : {url}")
        logger.info(f"  API Base    : {url}api/automation/status")
        logger.info(f"  Workspace   : {self.workspace_dir}")
        logger.info("=" * 70)

        if open_browser:
            def _open():
                time.sleep(0.5)
                try:
                    webbrowser.open_new_tab(url)
                except Exception:
                    pass
            threading.Thread(target=_open, daemon=True).start()

        if in_thread:
            self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self._thread.start()
        else:
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Server received interrupt signal, shutting down cleanly...")
                self.shutdown()

    def shutdown(self) -> None:
        """Cleanly terminate server and enforce Universal Rule 26 zero-hang standard."""
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            self.httpd = None
            logger.info("Dashboard server shutdown complete.")


# ============================================================================
# CLI Launcher
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AutoSelect-Commander Dashboard & Automation Control Server"
    )
    parser.add_argument("--port", type=int, default=8501, help="HTTP port to bind (default: 8501)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    parser.add_argument("--mode", type=str, choices=["production", "test"], default=None, help="Operating mode override")

    args = parser.parse_args()

    server = DashboardServer(host=args.host, port=args.port)

    # Register clean signal handlers
    def _sig_handler(sig, frame):
        logger.info(f"Signal {sig} caught. Terminating server...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, _sig_handler)

    server.start(open_browser=not args.no_browser, in_thread=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
