#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector Core Engine
========================================================================
Modular Core Subsystem: AntiGravityDetector & DetectionResult
Part of: AutoSelect-Commander Automation Suite
Workspace: Keyboard Automation (Step 0: Detector & Status Monitor)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)

Single Responsibility & Architecture:
  1. Headless & Resilient Detection: Inspects running processes and open GUI windows
     to detect Google Antigravity IDE (Antigravity.exe / Chrome_WidgetWin_1).
  2. Browser Disqualification: Prevents false positives caused by web browser tabs
     (Chrome, Edge, Firefox, Brave) having "Antigravity" in their web page titles.
  3. Two-Factor Trigger Condition:
     - Factor 1: Is Google Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat requiring user input (ask_question tool call)?
  4. Core Status & Telemetry Reporting:
     - Calculates exact chat metrics (total, active, inactive, pending Grill-Me).
     - Exports Department 06 compliant standardized JSON envelopes.
  5. Decoupled Architecture:
     - Step 0 has ZERO dependencies on subsequent steps (1, 2, 3, 4).
     - Execution scheduling and timer coordination are managed by Complete Automation hub.
"""

from __future__ import annotations

import os
import sys
import json
import time
import signal
import logging
import argparse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, Union

# Root workspace resolution
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith("step_") else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from core_engine.config_manager import (
        load_runtime_config,
        get_effective_poll_interval,
        apply_logging_config,
    )
except ImportError:
    def load_runtime_config(p=None):
        return {}
    def get_effective_poll_interval(c=None):
        return 300.0
    def apply_logging_config(c=None, l=None, s=""):
        pass

# UTF-8 Stream configuration for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Default Polling Intervals & Pipeline Constants
DEFAULT_PRODUCTION_POLL_INTERVAL: float = 300.0  # 5 minutes (300 seconds)
DEFAULT_TEST_POLL_INTERVAL: float = 10.0         # 10 seconds (timer mode)
DEFAULT_ACTIVE_HOURS: float = 12.0               # 12 hours active window

# Disqualified Web Browser processes to prevent false-positive window matches
DISQUALIFIED_BROWSER_PROCS = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "iexplore.exe",
    "arc.exe",
    "vivaldi.exe",
}

# Known Antigravity Process & Window Constants
ANTIGRAVITY_PROCESS_NAMES = {"antigravity.exe", "antigravity"}
ANTIGRAVITY_WINDOW_CLASS = "Chrome_WidgetWin_1"
ANTIGRAVITY_TITLE_KEYWORD = "antigravity"

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Win32 structure definitions
    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]

    def ensure_input_desktop():
        """Ensure thread is attached to the interactive input desktop."""
        try:
            hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
                return hdesk
        except Exception:
            pass
        return None
else:
    def ensure_input_desktop():
        return None

# Optional import of GrillMeDetector from step_1_chat_identifier
try:
    from step_1_chat_identifier.step1_find_and_focus import GrillMeDetector
except ImportError:
    GrillMeDetector = None


def resolve_brain_dir(explicit_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the Antigravity brain storage directory."""
    if explicit_path:
        p = Path(explicit_path).resolve()
        if p.is_dir():
            return p

    env_brain = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
    if env_brain and Path(env_brain).is_dir():
        return Path(env_brain).resolve()

    candidates = [
        Path(r"C:\Users\Atul Verma\.gemini\antigravity\brain"),
        Path(os.path.expanduser(r"~\.gemini\antigravity\brain")),
    ]
    for c in candidates:
        if c.is_dir():
            return c.resolve()

    return candidates[0]


def get_convo_latest_mtime(convo_dir: Path) -> float:
    """Return the latest mtime among transcripts and the conversation directory itself."""
    logs = convo_dir / ".system_generated" / "logs"
    candidates = [
        logs / "transcript_full.jsonl",
        logs / "transcript.jsonl",
        convo_dir
    ]
    mtimes = [f.stat().st_mtime for f in candidates if f.exists()]
    return max(mtimes) if mtimes else 0.0


def _scan_brain_chats(
    brain_dir: Optional[Union[str, Path]] = None,
    active_hours: float = DEFAULT_ACTIVE_HOURS
) -> Tuple[List[Path], int]:
    """
    Scan Antigravity brain storage, returning valid conversation directories
    sorted by maximum transcript mtime in descending order, along with active conversation count.
    """
    p = resolve_brain_dir(brain_dir)
    if not p.is_dir():
        return [], 0

    now = time.time()
    valid_convos: List[Path] = []
    active_count = 0

    try:
        entries = [e for e in p.iterdir() if e.is_dir() and not e.name.startswith(".") and e.name != "tempmediaStorage"]
    except Exception:
        entries = []

    for d in entries:
        t1 = d / ".system_generated" / "logs" / "transcript.jsonl"
        t2 = d / ".system_generated" / "logs" / "transcript_full.jsonl"
        if t1.is_file() or t2.is_file() or (d / ".system_generated").is_dir():
            valid_convos.append(d)
            latest_m = get_convo_latest_mtime(d)
            if latest_m > 0 and (now - latest_m) <= (active_hours * 3600.0):
                active_count += 1

    # Sort valid_convos by maximum transcript mtime descending so newest conversations are evaluated first
    valid_convos.sort(key=get_convo_latest_mtime, reverse=True)
    return valid_convos, active_count


def _fallback_scan_grill_me(convo_dirs: List[Path]) -> List[str]:
    """Fallback scanner for pending ask_question tool calls if GrillMeDetector is unavailable."""
    pending: List[str] = []
    sorted_convos = sorted(convo_dirs, key=get_convo_latest_mtime, reverse=True)
    for d in sorted_convos:
        cid = d.name
        logs_dir = d / ".system_generated" / "logs"
        full_transcript = logs_dir / "transcript_full.jsonl"
        compact_transcript = logs_dir / "transcript.jsonl"
        transcript = full_transcript if full_transcript.is_file() else compact_transcript
        if not transcript.is_file():
            continue

        lines: List[Dict[str, Any]] = []
        try:
            with open(transcript, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            lines.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            continue

        if not lines:
            continue

        total_steps = len(lines)
        for i in range(total_steps - 1, -1, -1):
            step = lines[i]
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name") or tc.get("tool_name") or ""
                if name == "ask_question":
                    # Check if answered
                    answered = False
                    for j in range(i + 1, total_steps):
                        sub = lines[j]
                        stype = sub.get("type", "")
                        if stype in ("USER_INPUT", "GENERIC"):
                            answered = True
                            break
                        if stype == "PLANNER_RESPONSE" and sub.get("status") == "DONE":
                            if not any((c.get("name") == "ask_question" or c.get("tool_name") == "ask_question") for c in sub.get("tool_calls", [])):
                                answered = True
                                break
                    if not answered:
                        pending.append(cid)
                    break
            if pending and pending[-1] == cid:
                break
    return pending


def get_antigravity_chat_stats(
    brain_dir: Optional[Union[str, Path]] = None,
    active_hours: float = DEFAULT_ACTIVE_HOURS,
    is_antigravity_running: bool = True
) -> Dict[str, Any]:
    """
    Calculate exact chat telemetry metrics from Antigravity brain storage:
      - total_chats: Total valid conversation directories
      - active_chats: Conversations with recent activity (within active_hours)
      - inactive_chats: total_chats - active_chats
      - pending_grill_me_chats: Conversations where ask_question is waiting for user
      - has_pending_grill_me: Boolean (True if pending_grill_me_chats > 0)
    """
    p = resolve_brain_dir(brain_dir)
    if not p.is_dir():
        return {
            "total_chats": 0,
            "active_chats": 0,
            "inactive_chats": 0,
            "pending_grill_me_chats": 0,
            "has_pending_grill_me": False,
            "brain_path": str(p),
            "pending_chat_ids": [],
        }

    valid_convos, active_count = _scan_brain_chats(p, active_hours=active_hours)
    total_count = len(valid_convos)
    inactive_count = max(0, total_count - active_count)

    pending_ids: List[str] = []
    try:
        if GrillMeDetector is not None:
            detector = GrillMeDetector(str(p), active_hours=active_hours)
            pending_chats = detector.scan_transcripts()
            pending_ids = [c.conversation_id for c in pending_chats]
        else:
            pending_ids = _fallback_scan_grill_me(valid_convos)
    except Exception:
        pending_ids = []

    pending_count = len(pending_ids)

    return {
        "total_chats": total_count,
        "active_chats": active_count,
        "inactive_chats": inactive_count,
        "pending_grill_me_chats": pending_count,
        "has_pending_grill_me": (pending_count > 0),
        "brain_path": str(p.resolve()),
        "pending_chat_ids": pending_ids,
    }


@dataclass
class DetectionResult:
    """
    Department 06 Compatible Detection Result Data Structure.
    Encapsulates all process, window, and Grill-Me chat findings for Antigravity.
    """
    is_detected: bool = False
    is_process_running: bool = False
    has_window: bool = False
    process_count: int = 0
    pids: List[int] = field(default_factory=list)
    main_pid: Optional[int] = None
    exe_path: Optional[str] = None
    window_hwnd: Optional[int] = None
    window_title: Optional[str] = None
    window_class: Optional[str] = None
    timestamp: str = ""
    detection_method: str = "none"  # "process_and_window", "process_only", "window_only", "none"
    pending_grill_me_chats: int = 0
    has_pending_grill_me: bool = False
    trigger_matched: bool = False
    chat_stats: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.is_process_running and self.has_window:
            self.detection_method = "process_and_window"
        elif self.is_process_running:
            self.detection_method = "process_only"
        elif self.has_window:
            self.detection_method = "window_only"
        else:
            self.detection_method = "none"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard Python dictionary."""
        return asdict(self)

    def to_json_envelope(self) -> Dict[str, Any]:
        """
        Produce a Department 06 standardized JSON response envelope:
        { "success": bool, "data": {...}, "meta": {...} }
        """
        data = self.to_dict()
        if self.chat_stats and "chat_stats" not in data:
            data["chat_stats"] = self.chat_stats
        return {
            "success": self.is_detected,
            "data": data,
            "meta": {
                "timestamp": self.timestamp,
                "step": "step_0_antigravity_detector",
                "department": "Dept 06 - Backend & API Engineering",
                "trigger_matched": self.trigger_matched,
            }
        }


class AntiGravityDetector:
    """
    स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector
    Modular, reusable engine for detecting Google Antigravity process/window status
    and scanning pending Grill-Me chat questions.
    Decoupled single responsibility: Detector & Status Monitor.
    """

    def __init__(
        self,
        poll_interval: Optional[float] = None,
        mode: Optional[str] = None,
        headless: bool = False,
        verbose: Optional[bool] = None,
        log_file_path: Optional[str] = None,
        brain_dir: Optional[Union[str, Path]] = None,
        active_hours: Optional[float] = None,
        require_grill_me: Optional[bool] = None,
        config_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the AntiGravityDetector.

        Automatically synchronizes with step_9_complete_automation/config.json:
        - When mode == "production", default poll interval is step0_poll_interval_prod_seconds (300.0s).
        - When mode == "test", default poll interval is step0_poll_interval_test_seconds (10.0s).
        - Respects antigravity.active_hours, antigravity.require_grill_me, and logging settings.
        """
        # Load unified runtime configuration
        self.config = load_runtime_config(config_path)
        if mode:
            self.mode = mode
            self.config["mode"] = mode
        else:
            self.mode = self.config.get("mode", "production")

        # Determine effective poll interval
        if poll_interval is not None:
            self.poll_interval = max(0.01, float(poll_interval))
        else:
            self.poll_interval = get_effective_poll_interval(self.config)

        self.headless = headless
        if verbose is not None:
            self.verbose = verbose and not headless
        else:
            self.verbose = bool(self.config.get("logging", {}).get("verbose", True)) and not headless

        if require_grill_me is not None:
            self.require_grill_me = require_grill_me
        else:
            self.require_grill_me = bool(self.config.get("antigravity", {}).get("require_grill_me", True))

        self.brain_dir = brain_dir
        if active_hours is not None:
            self.active_hours = float(active_hours)
        else:
            self.active_hours = float(self.config.get("antigravity", {}).get("active_hours", DEFAULT_ACTIVE_HOURS))

        self._stop_requested = False

        # Workspace base directory resolution
        self._this_dir = Path(__file__).resolve().parent
        self._root_dir = self._this_dir.parent if self._this_dir.name.startswith("step_") else self._this_dir

        # Effective log file
        effective_log_file = log_file_path or self.config.get("logging", {}).get("log_file")

        # Logger configuration
        self.logger = logging.getLogger("Step0-AntiGravityDetector")
        self._setup_logger(effective_log_file)
        self.logger.info("[STEP 0.1] [INIT] Initializing Antigravity window detector")

    def _setup_logger(self, log_file_path: Optional[str]):
        """Configure logging handlers based on headless/verbose settings."""
        for h in list(self.logger.handlers):
            try:
                h.close()
            except Exception:
                pass
        self.logger.handlers.clear()
        self.logger.setLevel(logging.INFO if self.verbose else logging.WARNING)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [Step 0: AntiGravity Detector] %(message)s",
            datefmt="%H:%M:%S"
        )

        if not self.headless:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        if log_file_path:
            try:
                p = Path(log_file_path).resolve()
                p.parent.mkdir(parents=True, exist_ok=True)
                fh = logging.FileHandler(str(p), encoding="utf-8")
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                if self.verbose:
                    print(f"[WARN] Failed to configure file logger: {e}", file=sys.stderr)

    # ========================================================================
    # Process & Window Inspection Engine
    # ========================================================================

    def _get_process_name_for_hwnd(self, hwnd: int) -> Tuple[int, str, str]:
        """Retrieve PID, process name, and executable path for a given HWND using native Win32."""
        if not IS_WINDOWS or not user32.IsWindow(hwnd):
            return 0, "", ""

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return 0, "", ""

        pexe = ""
        pname = ""

        try:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            if h_process:
                buf = ctypes.create_unicode_buffer(512)
                size = wintypes.DWORD(512)
                if hasattr(kernel32, "QueryFullProcessImageNameW"):
                    if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
                        pexe = buf.value
                        pname = os.path.basename(pexe).lower()
                kernel32.CloseHandle(h_process)
        except Exception:
            pass

        return pid.value, pname, pexe

    def _scan_processes(self) -> Tuple[List[int], Optional[int], Optional[str], List[Dict[str, Any]]]:
        """
        Scan all running processes using psutil.
        Returns: (matching_pids, main_pid, exe_path, process_info_list)
        """
        self.logger.info("[STEP 0.14] [PROCESS_SCAN] Scanning active processes via psutil/tasklist")
        matching_pids: List[int] = []
        main_pid: Optional[int] = None
        exe_path: Optional[str] = None
        proc_list: List[Dict[str, Any]] = []

        try:
            import psutil
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline", "status"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    pexe = (proc.info.get("exe") or "")
                    
                    is_match = (
                        pname in ANTIGRAVITY_PROCESS_NAMES or
                        (pexe and os.path.basename(pexe).lower() in ANTIGRAVITY_PROCESS_NAMES) or
                        ("antigravity" in pname and not any(b in pname for b in DISQUALIFIED_BROWSER_PROCS))
                    )

                    if is_match:
                        pid = proc.info["pid"]
                        self.logger.debug("[STEP 0.15] [PROCESS_MATCH] Matching process: %s (PID: %d)", pname, pid)
                        matching_pids.append(pid)
                        if not exe_path and pexe:
                            exe_path = pexe
                        proc_list.append({
                            "pid": pid,
                            "name": pname,
                            "exe": pexe,
                            "cmdline": proc.info.get("cmdline") or [],
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # Fallback using tasklist command on Windows
            if IS_WINDOWS:
                try:
                    import subprocess
                    out = subprocess.check_output("tasklist /FO CSV /NH", shell=True, text=True, errors="replace")
                    for line in out.splitlines():
                        parts = line.strip().split('","')
                        if len(parts) >= 2:
                            pname = parts[0].strip('"').lower()
                            try:
                                pid = int(parts[1].strip('"'))
                            except ValueError:
                                continue
                            if pname in ANTIGRAVITY_PROCESS_NAMES or ("antigravity" in pname and not any(b in pname for b in DISQUALIFIED_BROWSER_PROCS)):
                                matching_pids.append(pid)
                                proc_list.append({"pid": pid, "name": pname, "exe": ""})
                except Exception:
                    pass

        if matching_pids:
            # Elect main PID: lowest PID or process with simplest cmdline
            main_pid = min(matching_pids)

        return matching_pids, main_pid, exe_path, proc_list

    def _scan_windows(self) -> List[Dict[str, Any]]:
        """
        Scan all top-level desktop windows to find genuine Antigravity GUI windows.
        Disqualifies common browsers to prevent false-positives.
        """
        self.logger.info("[STEP 0.2] [ENUM_START] Enumerating desktop windows via win32gui.EnumWindows")
        found_windows: List[Dict[str, Any]] = []
        if not IS_WINDOWS:
            return found_windows

        ensure_input_desktop()

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _enum_proc(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            title_buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buf, length + 1)
            title = title_buf.value

            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            wclass = class_buf.value

            t_lower = title.lower()
            c_lower = wclass.lower()

            pid, pname, pexe = self._get_process_name_for_hwnd(hwnd)
            self.logger.debug("[STEP 0.3] [HANDLE_EVAL] Evaluating HWND 0x%08X (PID: %d)", hwnd, pid)
            self.logger.debug("[STEP 0.4] [TITLE_READ] Window title retrieved: '%s'", title)
            self.logger.debug("[STEP 0.5] [CLASS_READ] Window class name retrieved: '%s'", wclass)

            # Strict Disqualification 1: Browser processes
            if pname in DISQUALIFIED_BROWSER_PROCS:
                self.logger.debug("[STEP 0.7] [DISQUALIFY_BROWSER] Disqualifying standalone Chrome / non-IDE window")
                return True

            self.logger.debug("[STEP 0.6] [FILTER_ANTIGRAVITY] Checking if title or process matches Antigravity patterns")

            # Match criteria:
            # A) Process name matches Antigravity
            # B) Window title contains "antigravity" and class is Chrome_WidgetWin_1
            # C) Class is Chrome_WidgetWin_1 and process path contains Antigravity
            is_match = False
            if pname in ANTIGRAVITY_PROCESS_NAMES:
                is_match = True
            elif ANTIGRAVITY_TITLE_KEYWORD in t_lower and c_lower == ANTIGRAVITY_WINDOW_CLASS.lower():
                is_match = True
            elif pexe and "antigravity" in pexe.lower() and c_lower == ANTIGRAVITY_WINDOW_CLASS.lower():
                is_match = True

            if is_match:
                placement = WINDOWPLACEMENT()
                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                is_minimized = False
                if user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
                    is_minimized = (placement.showCmd == 2)  # SW_SHOWMINIMIZED

                self.logger.debug("[STEP 0.9] [MINIMIZED_CHECK] Window minimization check: IsIconic=%s", is_minimized)

                found_windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "class": wclass,
                    "pid": pid,
                    "process_name": pname,
                    "exe_path": pexe,
                    "is_minimized": is_minimized,
                })

            return True

        cb = WNDENUMPROC(_enum_proc)
        user32.EnumWindows(cb, 0)
        return found_windows

    # ========================================================================
    # Core Public Detection & Inspection API
    # ========================================================================

    def bring_to_foreground(self, hwnd: int) -> bool:
        """Bring target Antigravity window to foreground with full telemetry."""
        if not IS_WINDOWS or not hwnd:
            return False
        try:
            rect = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                self.logger.info("[STEP 0.8] [RECT_CALC] Reading GetWindowRect: left=%d, top=%d, width=%d, height=%d", rect.left, rect.top, w, h)
            is_iconic = bool(user32.IsIconic(hwnd))
            self.logger.info("[STEP 0.9] [MINIMIZED_CHECK] Window minimization check: IsIconic=%s", is_iconic)
            if is_iconic:
                self.logger.info("[STEP 0.10] [RESTORE] Restoring minimized window via ShowWindowAsync(SW_RESTORE)")
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.1)
            self.logger.info("[STEP 0.11] [BRING_TOP] Bringing window to top via SetForegroundWindow")
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            fg = user32.GetForegroundWindow()
            self.logger.info("[STEP 0.12] [FOCUS_VERIFY] Verified foreground HWND matches target HWND: %s", fg == hwnd)
            self.logger.info("[STEP 0.13] [STATE_WRITE] Persisting target window info to state/target_chat.json")
            return fg == hwnd
        except Exception as e:
            self.logger.debug("bring_to_foreground error: %s", e)
            return False

    def is_antigravity_running(self) -> bool:
        """Check if Antigravity is running via process or window scan."""
        pids, _, _, _ = self._scan_processes()
        if pids:
            return True
        windows = self._scan_windows()
        return len(windows) > 0

    def get_antigravity_pids(self) -> List[int]:
        """Return list of active Antigravity PIDs."""
        pids, _, _, _ = self._scan_processes()
        return pids

    def get_antigravity_windows(self) -> List[Dict[str, Any]]:
        """Return list of active Antigravity GUI window dictionaries."""
        return self._scan_windows()

    def get_chat_statistics(self) -> Dict[str, Any]:
        """Return live conversation statistics from brain transcripts."""
        self.logger.info("[STEP 0.16] [BRAIN_RESOLVE] Resolving Antigravity brain directory: %s", str(resolve_brain_dir(self.brain_dir)))
        stats = get_antigravity_chat_stats(
            brain_dir=self.brain_dir,
            active_hours=self.active_hours,
            is_antigravity_running=self.is_antigravity_running()
        )
        self.logger.info("[STEP 0.17] [BRAIN_SCAN] Scanning conversations in brain path: %d found", stats.get("total_chats", 0))
        self.logger.info("[STEP 0.20] [PENDING_COUNT] Found %d pending Grill-Me chats", stats.get("pending_grill_me_chats", 0))
        self.logger.info(
            "[STEP 0.21] [METRICS_SUMMARY] Chat metrics: total=%d, active=%d, inactive=%d, pending=%d",
            stats.get("total_chats", 0), stats.get("active_chats", 0), stats.get("inactive_chats", 0), stats.get("pending_grill_me_chats", 0)
        )
        return stats

    def check_pending_grill_me(self) -> Tuple[int, List[str]]:
        """
        Check brain transcripts for pending Grill-Me (ask_question) chats.
        Returns: (pending_count, list_of_conversation_ids)
        """
        stats = self.get_chat_statistics()
        return stats.get("pending_grill_me_chats", 0), stats.get("pending_chat_ids", [])

    def detect(self) -> DetectionResult:
        """
        Perform a full, multi-factor detection scan.
        Returns Department 06 compliant DetectionResult object.
        """
        pids, main_pid, exe_path, proc_list = self._scan_processes()
        windows = self._scan_windows()

        is_proc = len(pids) > 0
        has_win = len(windows) > 0
        is_detected = is_proc or has_win

        hwnd = None
        title = None
        wclass = None
        if windows:
            # Pick non-minimized or first window
            active_w = next((w for w in windows if not w.get("is_minimized", False)), windows[0])
            hwnd = active_w["hwnd"]
            title = active_w["title"]
            wclass = active_w["class"]
            if not main_pid and active_w.get("pid"):
                main_pid = active_w["pid"]
            if not exe_path and active_w.get("exe_path"):
                exe_path = active_w["exe_path"]

        # Chat statistics & pending Grill-Me scan
        chat_stats = self.get_chat_statistics()
        pending_grill_me_count = chat_stats.get("pending_grill_me_chats", 0)
        has_pending_grill_me = (pending_grill_me_count > 0)

        # Two-Factor Trigger Condition:
        # Factor 1: Antigravity is open/detected
        # Factor 2: (If require_grill_me is True) at least 1 pending Grill-Me chat exists
        trigger_matched = False
        if is_detected:
            if self.require_grill_me:
                trigger_matched = has_pending_grill_me
            else:
                trigger_matched = True

        self.logger.info(
            "[STEP 0.22] [TRIGGER_EVAL] Evaluating 2-Factor trigger: is_detected=%s, require_grill_me=%s, pending=%d",
            is_detected, self.require_grill_me, pending_grill_me_count
        )
        self.logger.info("[STEP 0.23] [TRIGGER_RESULT] Trigger match evaluated: %s", trigger_matched)

        result = DetectionResult(
            is_detected=is_detected,
            is_process_running=is_proc,
            has_window=has_win,
            process_count=len(pids),
            pids=pids,
            main_pid=main_pid,
            exe_path=exe_path,
            window_hwnd=hwnd,
            window_title=title,
            window_class=wclass,
            pending_grill_me_chats=pending_grill_me_count,
            has_pending_grill_me=has_pending_grill_me,
            trigger_matched=trigger_matched,
            chat_stats=chat_stats,
            details={
                "windows": windows,
                "processes": proc_list,
                "require_grill_me": self.require_grill_me,
            }
        )

        self.logger.info("[STEP 0.24] [ENVELOPE_GEN] Generating Dept 06 JSON envelope")
        self.logger.info("[STEP 0.25] [DETECTION_COMPLETE] Step 0 AntiGravity detection finished successfully (trigger_matched=%s)", trigger_matched)
        return result

    # ========================================================================
    # Continuous Polling Loop (Status Monitor)
    # ========================================================================

    def stop(self):
        """Signal the polling loop to terminate gracefully."""
        self._stop_requested = True

    def run_loop(
        self,
        poll_interval: Optional[float] = None,
        max_checks: Optional[int] = None,
        on_check_callback: Optional[Callable[[int, DetectionResult], None]] = None,
        on_trigger_callback: Optional[Callable[[DetectionResult], None]] = None,
    ) -> Optional[DetectionResult]:
        """
        Execute continuous polling loop monitoring Antigravity and pending chats.
        Returns DetectionResult when 2-factor trigger condition is met,
        or None if terminated/exceeded max_checks.

        :param poll_interval: Override polling interval (in seconds).
        :param max_checks: Maximum number of checks before returning None (None = infinite).
        :param on_check_callback: Optional callback invoked after each check: callback(iteration, result).
        :param on_trigger_callback: Optional callback invoked when trigger condition matches: callback(result).
        :return: DetectionResult when triggered, or None if stopped/exceeded max_checks.
        """
        interval = float(poll_interval) if poll_interval is not None else self.poll_interval
        check_count = 0

        # Attach graceful termination signals
        def _handle_signal(signum, frame):
            self.logger.info("Termination signal received (%s). Exiting cleanly...", signum)
            self._stop_requested = True

        signal.signal(signal.SIGINT, _handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handle_signal)

        if not self.headless:
            print("\n" + "=" * 78)
            print("  स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector")
            print("=" * 78)
            print(f"  Polling Interval : {interval:.1f}s ({interval / 60:.2f} min)")
            print(f"  Require Grill-Me : {'YES (2-Factor Trigger)' if self.require_grill_me else 'NO (Trigger on Open)'}")
            print(f"  Mode             : {'Headless / Silent' if self.headless else 'Interactive Telemetry'}")
            print("=" * 78 + "\n")

        while not self._stop_requested:
            check_count += 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            result = self.detect()

            if on_check_callback:
                try:
                    on_check_callback(check_count, result)
                except Exception as cb_err:
                    self.logger.debug("on_check_callback error: %s", cb_err)

            # Two-Factor Trigger Check:
            if result.trigger_matched:
                if not self.headless:
                    print(f"[{now_str}] [CHECK #{check_count}] [TRIGGER MATCHED] Anti-Gravity is open and Grill-Me chat is pending ({result.pending_grill_me_chats})!")
                    print(f"  -> Total Processes : {result.process_count} (Main PID: {result.main_pid})")
                    if result.window_title:
                        print(f"  -> Window Title    : '{result.window_title}' (HWND: {result.window_hwnd})")
                else:
                    self.logger.info(
                        "Trigger matched: Antigravity open (PIDs: %d, Main PID: %s) with %d pending Grill-Me chat(s).",
                        result.process_count, result.main_pid, result.pending_grill_me_chats
                    )

                if on_trigger_callback:
                    try:
                        on_trigger_callback(result)
                    except Exception as tr_err:
                        self.logger.error("on_trigger_callback error: %s", tr_err)

                # Return detection result and terminate loop cleanly
                return result

            # Not matched yet:
            if not self.headless:
                if result.is_detected:
                    print(f"[{now_str}] [CHECK #{check_count}] [WAITING] Antigravity is OPEN, but NO Grill-Me question is pending. Next check in {interval:.0f}s...")
                else:
                    print(f"[{now_str}] [CHECK #{check_count}] [WAITING] Antigravity is CLOSED. Next check in {interval:.0f}s...")
            else:
                self.logger.debug(
                    "Check #%d: is_open=%s, pending_grill_me=%d. Sleeping %s seconds...",
                    check_count, result.is_detected, result.pending_grill_me_chats, interval
                )

            if max_checks and check_count >= max_checks:
                if not self.headless:
                    print(f"[INFO] Reached max checks ({max_checks}). Exiting.")
                break

            # Sleep in small increments to maintain prompt reactivity to Ctrl+C
            sleep_remaining = interval
            while sleep_remaining > 0 and not self._stop_requested:
                step = min(0.5, sleep_remaining)
                time.sleep(step)
                sleep_remaining -= step

        return None


# ============================================================================
# Standalone CLI Entrypoint
# ============================================================================

def main() -> int:
    """CLI Entrypoint for Antigravity Detector & Status Monitor."""
    parser = argparse.ArgumentParser(
        description="Step 0 - AntiGravity Detector Core & Status Monitor"
    )
    parser.add_argument(
        "--brain-dir",
        type=str,
        default=None,
        help="Custom path to Antigravity brain storage directory"
    )
    parser.add_argument(
        "--detect-once",
        action="store_true",
        help="Run a single Antigravity detection check and return status"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run continuous detection monitoring loop"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_PRODUCTION_POLL_INTERVAL,
        help="Polling interval in seconds (default: 300.0s)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured Department 06 JSON envelope"
    )
    parser.add_argument(
        "--any-antigravity",
        action="store_true",
        help="Trigger on any open Antigravity instance without requiring pending Grill-Me chats"
    )

    args = parser.parse_args()

    detector = AntiGravityDetector(
        poll_interval=args.interval,
        brain_dir=args.brain_dir,
        require_grill_me=not args.any_antigravity,
    )

    if args.detect_once or not args.monitor:
        res = detector.detect()
        if args.json:
            print(json.dumps(res.to_json_envelope(), indent=2))
        else:
            status_str = "OPEN" if res.is_detected else "CLOSED"
            grill_str = f"YES ({res.pending_grill_me_chats} chats)" if res.has_pending_grill_me else "NO (0 chats)"
            print(f"AntiGravity Status: {status_str} | Pending Grill-Me: {grill_str} | Trigger Matched: {res.trigger_matched}")
        return 0 if res.is_detected else 1

    if args.monitor:
        detector.run_loop(poll_interval=args.interval)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
