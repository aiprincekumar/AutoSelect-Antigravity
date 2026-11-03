#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector Core Engine
========================================================================
Modular Core Subsystem: AntiGravityDetector, DetectionResult & PipelineStep
Part of: AutoSelect-Commander Automation Pipeline
Workspace: Keyboard Automation (Step 0: Detector & Dynamic Pipeline Runner)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

Mission:
  1. Headless & Resilient Detection: Continuously or on-demand inspects running processes
     and open GUI windows to detect Google Antigravity IDE (Antigravity.exe / Chrome_WidgetWin_1).
  2. Browser Disqualification: Prevents false positives caused by web browser tabs (Chrome, Edge,
     Firefox, Brave) having "Antigravity" in their web page titles.
  3. Two-Factor Trigger Condition:
     - Factor 1: Is Google Anti-Gravity running/open?
     - Factor 2: Is there a pending Grill-Me chat requiring user input (ask_question tool call)?
     - When BOTH are met: Automatically launches the multi-step automation pipeline.
  4. Dynamic Multi-Step Pipeline Engine:
     - Step 1: `step_1_chat_identifier/step1_find_and_focus.py` (Identify & Focus)
     - Step 2: `step_2_chat_and_focus/step2_gui_chat_select.py` (CDP/DOM GUI Selection)
     - Step 3: `step_3_select_the_recommendation/step3_keyboard_automation.py` (Option Selection)
     - Step 4 (Future Reporting): `step_4_reporting/step4_reporting.py` (Gracefully bypassed if absent)
     - Dynamic discovery: Automatically registers and executes present steps sequentially.
       If Step 1 reports exit code 10 (no pending chats), remaining steps are cleanly cancelled.
  5. Execution Hygiene (Universal Rule 26): Detached headless background process management
     to eliminate zombie processes and background hangs upon completion.
"""

from __future__ import annotations

import os
import sys
import json
import time
import signal
import logging
import argparse
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, Union

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
DEFAULT_STEP_SETTLE_DELAY: float = 0.8          # 800ms between steps for GUI settle
EXIT_CODE_NO_PENDING_CHATS: int = 10            # Step 1 exit code indicating no chats need answering

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


def _fallback_scan_grill_me(convo_dirs: List[Path]) -> List[str]:
    """Fallback scanner for pending ask_question tool calls if GrillMeDetector is unavailable."""
    pending: List[str] = []
    for d in convo_dirs:
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
            mtimes = [f.stat().st_mtime for f in [t1, t2, d] if f.exists()]
            if mtimes and (now - max(mtimes)) <= (active_hours * 3600.0):
                active_count += 1

    total_count = len(valid_convos)
    inactive_count = max(0, total_count - active_count)

    pending_ids: List[str] = []
    try:
        if GrillMeDetector is not None:
            detector = GrillMeDetector(str(p))
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
class PipelineStep:
    """
    Representation of an automated pipeline step within AutoSelect-Commander.
    """
    step_index: int
    name: str
    script_path: Path
    is_optional: bool = False
    description: str = ""

    def exists(self) -> bool:
        """Check whether the step script physically exists on disk."""
        try:
            return self.script_path.is_file()
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "name": self.name,
            "script_path": str(self.script_path),
            "is_optional": self.is_optional,
            "exists": self.exists(),
            "description": self.description,
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


def discover_pipeline_steps(
    root_dir: Optional[Union[str, Path]] = None,
    include_future: bool = True,
    custom_scripts: Optional[Dict[int, Union[str, Path]]] = None
) -> List[PipelineStep]:
    """
    Discover all configured and dynamically available pipeline steps in the workspace.

    Standard Pipeline Architecture:
      - Step 1: step_1_chat_identifier/step1_find_and_focus.py (Required)
      - Step 2: step_2_chat_and_focus/step2_gui_chat_select.py (Required)
      - Step 3: step_3_select_the_recommendation/step3_keyboard_automation.py (Required)
      - Step 4: step_4_reporting/step4_reporting.py (Future Reporting - Optional)

    Dynamic Discovery:
      - Scans for any additional step_{N}_* directories (N >= 5) on disk.
      - If Step 4 is absent from disk, it is marked optional (is_optional=True, exists()=False)
        and will be gracefully bypassed without failing the pipeline.
      - Once Step 4 is created on disk, it is automatically executed!

    :param root_dir: Base workspace root directory.
    :param include_future: If True, includes defined optional steps (like Step 4) even if not yet on disk.
    :param custom_scripts: Optional mapping of step index to custom script paths.
    :return: List of PipelineStep instances sorted by step_index.
    """
    if root_dir is None:
        _this = Path(__file__).resolve().parent
        r_dir = _this.parent if _this.name.startswith("step_") else _this
    else:
        r_dir = Path(root_dir).resolve()

    custom = custom_scripts or {}
    steps: List[PipelineStep] = []

    # 1. Step 1: Chat Identifier & Window Focus (Required)
    p1 = custom.get(1)
    if p1:
        s1_path = Path(p1).resolve()
    else:
        c1 = [
            r_dir / "step_1_chat_identifier" / "step1_find_and_focus.py",
            r_dir / "step1_find_and_focus.py",
        ]
        s1_path = next((c for c in c1 if c.is_file()), c1[0])
    steps.append(PipelineStep(
        step_index=1,
        name="Step 1: Chat Identifier & Focus",
        script_path=s1_path,
        is_optional=False,
        description="Scans transcripts, identifies target chat, saves state, and focuses Antigravity window."
    ))

    # 2. Step 2: GUI Chat Select & Pane Focus (Required)
    p2 = custom.get(2)
    if p2:
        s2_path = Path(p2).resolve()
    else:
        c2 = [
            r_dir / "step_2_chat_and_focus" / "step2_gui_chat_select.py",
            r_dir / "step2_gui_chat_select.py",
        ]
        s2_path = next((c for c in c2 if c.is_file()), c2[0])
    steps.append(PipelineStep(
        step_index=2,
        name="Step 2: GUI Chat Select & Focus",
        script_path=s2_path,
        is_optional=False,
        description="Locates target chat in GUI sidebar via CDP/DOM, clicks, and focuses chat pane."
    ))

    # 3. Step 3: Keyboard Automation & Recommendation Selection (Required)
    p3 = custom.get(3)
    if p3:
        s3_path = Path(p3).resolve()
    else:
        c3 = [
            r_dir / "step_3_select_the_recommendation" / "step3_keyboard_automation.py",
            r_dir / "step3_keyboard_automation.py",
        ]
        s3_path = next((c for c in c3 if c.is_file()), c3[0])
    steps.append(PipelineStep(
        step_index=3,
        name="Step 3: Keyboard Automation",
        script_path=s3_path,
        is_optional=False,
        description="Injects keystrokes to select recommendation option and confirms response."
    ))

    # 4. Step 4: Reporting & Telemetry (Future Reporting - Optional)
    p4 = custom.get(4)
    if p4:
        s4_path = Path(p4).resolve()
    else:
        c4 = [
            r_dir / "step_4_reporting" / "step4_reporting.py",
            r_dir / "step_4_reporting" / "step4_report.py",
            r_dir / "step4_reporting.py",
        ]
        # Dynamically check for any .py script in step_4_* folder
        try:
            for d in r_dir.glob("step_4_*"):
                if d.is_dir():
                    for pyf in d.glob("*.py"):
                        if not pyf.name.startswith(("test_", "__", "setup")):
                            c4.insert(0, pyf)
        except Exception:
            pass
        s4_path = next((c for c in c4 if c.is_file()), c4[0])
    steps.append(PipelineStep(
        step_index=4,
        name="Step 4: Reporting & Telemetry",
        script_path=s4_path,
        is_optional=True,
        description="Automated execution reporting, audit trail logging, and telemetry dispatch."
    ))

    # 5. Dynamic Future Steps (step_{N}_* where N >= 5)
    try:
        for sub_dir in sorted(r_dir.glob("step_*_*")):
            if not sub_dir.is_dir():
                continue
            parts = sub_dir.name.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                idx = int(parts[1])
                if idx >= 5:
                    cand_scripts = [
                        p for p in sub_dir.glob("*.py")
                        if not p.name.startswith(("test_", "__", "setup"))
                    ]
                    if cand_scripts:
                        cand_scripts.sort(key=lambda x: (0 if f"step{idx}" in x.name.lower() else 1, len(x.name)))
                        chosen = cand_scripts[0]
                        steps.append(PipelineStep(
                            step_index=idx,
                            name=f"Step {idx}: {sub_dir.name}",
                            script_path=chosen,
                            is_optional=True,
                            description=f"Dynamically discovered pipeline step in {sub_dir.name}."
                        ))
    except Exception:
        pass

    if not include_future:
        steps = [s for s in steps if s.exists()]

    steps.sort(key=lambda s: s.step_index)
    return steps


class AntiGravityDetector:
    """
    स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector
    Modular, reusable engine for detecting Google Antigravity and orchestrating
    the multi-step automation pipeline (Steps 1 -> 2 -> 3 -> 4).
    Supports Two-Factor Trigger: Antigravity Open AND Pending Grill-Me Chat.
    """

    def __init__(
        self,
        poll_interval: float = DEFAULT_PRODUCTION_POLL_INTERVAL,
        headless: bool = False,
        verbose: bool = True,
        step1_script_path: Optional[str] = None,
        step2_script_path: Optional[str] = None,
        step3_script_path: Optional[str] = None,
        step4_script_path: Optional[str] = None,
        state_file_path: Optional[str] = None,
        python_exe_path: Optional[str] = None,
        log_file_path: Optional[str] = None,
        brain_dir: Optional[Union[str, Path]] = None,
        active_hours: float = DEFAULT_ACTIVE_HOURS,
        require_grill_me: bool = True,
        pipeline_steps: Optional[List[PipelineStep]] = None,
    ):
        """
        Initialize the AntiGravityDetector.

        :param poll_interval: Polling sleep interval in seconds (default: 300.0s for prod, 10.0s for test).
        :param headless: Run fully silent without printing logs to stdout.
        :param verbose: Enable detailed log output when not headless.
        :param step1_script_path: Explicit path to step1_find_and_focus.py (auto-detected if None).
        :param step2_script_path: Explicit path to step2_gui_chat_select.py (auto-detected if None).
        :param step3_script_path: Explicit path to step3_keyboard_automation.py (auto-detected if None).
        :param step4_script_path: Explicit path to step4_reporting.py (auto-detected if None).
        :param state_file_path: Explicit path to target_chat.json (auto-detected if None).
        :param python_exe_path: Explicit path to python interpreter in .venv (auto-detected if None).
        :param log_file_path: Optional file path to persist structured detection logs.
        :param brain_dir: Custom path to Antigravity brain directory (auto-detected if None).
        :param active_hours: Hours window to consider conversation active (default: 12.0).
        :param require_grill_me: If True, requires both Antigravity running AND pending Grill-Me chat to trigger pipeline.
        :param pipeline_steps: Optional explicit list of PipelineStep instances to override auto-discovery.
        """
        self.poll_interval = max(0.5, float(poll_interval))
        self.headless = headless
        self.verbose = verbose and not headless
        self.require_grill_me = require_grill_me
        self.brain_dir = brain_dir
        self.active_hours = active_hours
        self._stop_requested = False

        # Workspace base directory resolution
        self._this_dir = Path(__file__).resolve().parent
        self._root_dir = self._this_dir.parent if self._this_dir.name.startswith("step_") else self._this_dir

        # Auto-resolve state file and python interpreter
        self.state_file = self._resolve_state_file(state_file_path)
        self.python_exe = self._resolve_python_exe(python_exe_path)

        # Auto-resolve individual step scripts
        self.step1_script = self._resolve_step_script(1, ["step_1_chat_identifier/step1_find_and_focus.py"], step1_script_path)
        self.step2_script = self._resolve_step_script(2, ["step_2_chat_and_focus/step2_gui_chat_select.py"], step2_script_path)
        self.step3_script = self._resolve_step_script(3, ["step_3_select_the_recommendation/step3_keyboard_automation.py"], step3_script_path)
        self.step4_script = self._resolve_step_script(4, ["step_4_reporting/step4_reporting.py", "step_4_reporting/step4_report.py"], step4_script_path)

        # Dynamic pipeline discovery
        if pipeline_steps is not None:
            self.pipeline_steps = pipeline_steps
        else:
            self.pipeline_steps = self.discover_steps(include_future=True)

        # Logger configuration
        self.logger = logging.getLogger("Step0-AntiGravityDetector")
        self._setup_logger(log_file_path)

    def _setup_logger(self, log_file_path: Optional[str]):
        """Configure logging handlers based on headless/verbose settings."""
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

    def _resolve_step_script(
        self,
        step_num: int,
        default_rel_candidates: List[str],
        explicit_path: Optional[str] = None
    ) -> Path:
        """Resolve path to a specific step script."""
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.is_file():
                return p

        # Check default candidate paths
        for rel in default_rel_candidates:
            c = self._root_dir / rel
            if c.is_file():
                return c.resolve()
            c_parent = self._this_dir.parent / rel
            if c_parent.is_file():
                return c_parent.resolve()

        # Glob search step_{N}_*
        try:
            for d in self._root_dir.glob(f"step_{step_num}_*"):
                if d.is_dir():
                    for pyf in d.glob("*.py"):
                        if not pyf.name.startswith(("test_", "__", "setup")):
                            return pyf.resolve()
        except Exception:
            pass

        return (self._root_dir / default_rel_candidates[0]).resolve()

    def _resolve_step1_script(self, explicit_path: Optional[str]) -> Path:
        """Resolve path to Step 1 script (step1_find_and_focus.py) for backward compatibility."""
        return self._resolve_step_script(1, ["step_1_chat_identifier/step1_find_and_focus.py"], explicit_path)

    def _resolve_step2_script(self, explicit_path: Optional[str]) -> Path:
        """Resolve path to Step 2 script (step2_gui_chat_select.py)."""
        return self._resolve_step_script(2, ["step_2_chat_and_focus/step2_gui_chat_select.py"], explicit_path)

    def _resolve_step3_script(self, explicit_path: Optional[str]) -> Path:
        """Resolve path to Step 3 script (step3_keyboard_automation.py)."""
        return self._resolve_step_script(3, ["step_3_select_the_recommendation/step3_keyboard_automation.py"], explicit_path)

    def _resolve_step4_script(self, explicit_path: Optional[str]) -> Path:
        """Resolve path to Step 4 script (step4_reporting.py)."""
        return self._resolve_step_script(4, ["step_4_reporting/step4_reporting.py", "step_4_reporting/step4_report.py"], explicit_path)

    def discover_steps(self, include_future: bool = True) -> List[PipelineStep]:
        """Discover all configured and dynamically detected pipeline steps in the workspace."""
        custom_map = {
            1: self.step1_script,
            2: self.step2_script,
            3: self.step3_script,
            4: self.step4_script,
        }
        return discover_pipeline_steps(
            root_dir=self._root_dir,
            include_future=include_future,
            custom_scripts=custom_map,
        )

    def _resolve_state_file(self, explicit_path: Optional[str]) -> Path:
        """Resolve path to target_chat.json in workspace root."""
        if explicit_path:
            return Path(explicit_path).resolve()
        return (self._root_dir / "target_chat.json").resolve()

    def _resolve_python_exe(self, explicit_path: Optional[str]) -> Path:
        """Resolve dedicated virtual environment python.exe or sys.executable."""
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.is_file():
                return p

        candidates = [
            self._root_dir / ".venv" / "Scripts" / "python.exe",
            self._this_dir.parent / ".venv" / "Scripts" / "python.exe",
            Path(sys.executable),
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()

        return Path(sys.executable).resolve()

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
                        # Exclude zombies
                        status = proc.info.get("status")
                        if status == psutil.STATUS_ZOMBIE:
                            continue

                        pid = proc.info["pid"]
                        matching_pids.append(pid)
                        if not exe_path and pexe:
                            exe_path = pexe

                        cmdline = proc.info.get("cmdline") or []
                        is_helper = any("--type=" in arg for arg in cmdline)
                        if not is_helper and main_pid is None:
                            main_pid = pid

                        proc_list.append({
                            "pid": pid,
                            "name": proc.info.get("name"),
                            "exe": pexe,
                            "is_main": (pid == main_pid)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except ImportError:
            self.logger.warning("psutil not available; falling back to window enumeration.")

        # If main_pid not yet determined, select lowest PID
        if matching_pids and main_pid is None:
            main_pid = min(matching_pids)

        return matching_pids, main_pid, exe_path, proc_list

    def _scan_windows(self) -> List[Dict[str, Any]]:
        """
        Scan all top-level open Windows to find active Antigravity GUI windows.
        Disqualifies any browser processes that may have 'Antigravity' in a tab title.
        """
        if not IS_WINDOWS:
            return []

        ensure_input_desktop()
        candidates: List[Dict[str, Any]] = []

        def enum_cb(hwnd: int, lparam: int) -> bool:
            try:
                if not user32.IsWindow(hwnd):
                    return True

                visible = bool(user32.IsWindowVisible(hwnd))
                iconic = bool(user32.IsIconic(hwnd))
                if not visible and not iconic:
                    return True

                pid, pname, pexe = self._get_process_name_for_hwnd(hwnd)

                # Strict Disqualification: NEVER treat web browsers as Antigravity
                if pname in DISQUALIFIED_BROWSER_PROCS:
                    return True

                # Window Title
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()

                # Window Class
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                cls_name = cls_buf.value.strip()

                # Matching criteria
                is_proc_match = pname in ANTIGRAVITY_PROCESS_NAMES or "antigravity" in pname
                is_class_match = (cls_name == ANTIGRAVITY_WINDOW_CLASS)
                is_title_match = (ANTIGRAVITY_TITLE_KEYWORD in title.lower())

                # If process is antigravity.exe, it is a direct match
                # If title contains 'antigravity' and process is not a browser, it is a match
                if is_proc_match or (is_title_match and is_class_match) or (is_proc_match and (visible or iconic)):
                    score = 0
                    if is_proc_match:
                        score += 150
                    if is_class_match:
                        score += 50
                    if is_title_match:
                        score += 50
                    if visible:
                        score += 20
                    if iconic:
                        score += 10

                    candidates.append({
                        "hwnd": hwnd,
                        "title": title,
                        "class": cls_name,
                        "pid": pid,
                        "process_name": pname,
                        "process_exe": pexe,
                        "visible": visible,
                        "minimized": iconic,
                        "score": score,
                    })
            except Exception:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        # Sort candidates by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    # ========================================================================
    # Public Detection API (With Two-Factor Condition)
    # ========================================================================

    def detect(self, check_chat_stats: bool = True) -> DetectionResult:
        """
        Execute a single comprehensive detection check.
        Checks both process table and GUI window hierarchy, and evaluates
        the 2-factor trigger condition:
          Condition 1: Antigravity is open/running.
          Condition 2: (If require_grill_me is True) Pending Grill-Me chat > 0.
        """
        pids, main_pid, exe_path, proc_list = self._scan_processes()
        windows = self._scan_windows()

        is_process_running = len(pids) > 0
        has_window = len(windows) > 0
        is_detected = is_process_running or has_window

        top_window = windows[0] if windows else {}

        # If main_pid wasn't determined by psutil, prioritize the PID owning the top GUI window
        if top_window.get("pid"):
            main_pid = top_window["pid"]

        chat_stats: Dict[str, Any] = {}
        pending_count = 0
        has_pending = False

        if check_chat_stats:
            chat_stats = get_antigravity_chat_stats(
                brain_dir=self.brain_dir,
                active_hours=self.active_hours,
                is_antigravity_running=is_detected
            )
            pending_count = chat_stats.get("pending_grill_me_chats", 0)
            has_pending = chat_stats.get("has_pending_grill_me", False)

        # Two-factor trigger condition evaluation
        if self.require_grill_me:
            trigger_matched = bool(is_detected and has_pending)
        else:
            trigger_matched = bool(is_detected)

        result = DetectionResult(
            is_detected=is_detected,
            is_process_running=is_process_running,
            has_window=has_window,
            process_count=len(pids),
            pids=pids,
            main_pid=main_pid,
            exe_path=exe_path or top_window.get("process_exe"),
            window_hwnd=top_window.get("hwnd"),
            window_title=top_window.get("title"),
            window_class=top_window.get("class"),
            pending_grill_me_chats=pending_count,
            has_pending_grill_me=has_pending,
            trigger_matched=trigger_matched,
            chat_stats=chat_stats,
            details={
                "all_processes": proc_list,
                "all_windows": windows,
                "top_score": top_window.get("score", 0),
                "chat_stats": chat_stats,
            }
        )

        return result

    def is_antigravity_open(self) -> bool:
        """Convenience method returning True if Antigravity is detected."""
        res = self.detect(check_chat_stats=False)
        return res.is_detected

    # ========================================================================
    # Dynamic Multi-Step Pipeline Engine & Execution Hygiene (Universal Rule 26)
    # ========================================================================

    def execute_pipeline(
        self,
        extra_args: Optional[List[str]] = None,
        capture_output: bool = True,
        settle_delay: float = DEFAULT_STEP_SETTLE_DELAY,
        steps: Optional[List[PipelineStep]] = None,
    ) -> Tuple[bool, int, str, List[Dict[str, Any]]]:
        """
        Synchronously execute the multi-step automation pipeline in sequence:
          Step 1 -> [Exit 10: Clean Cancel] -> Settle (0.8s) ->
          Step 2 -> Settle (0.8s) ->
          Step 3 -> Settle (0.8s) ->
          Step 4 (Reporting - if present on disk; gracefully bypassed if absent).

        :param extra_args: Additional command-line flags forwarded to each step.
        :param capture_output: If True, captures/redirects child stdout and stderr so
                               the screen dashboard remains 100% clean.
        :param settle_delay: Settle delay in seconds between steps (default: 0.8s).
        :param steps: Optional override list of PipelineStep instances.
        :return: (success: bool, exit_code: int, summary_message: str, step_reports: List[Dict])
        """
        pipeline = steps if steps is not None else self.discover_steps(include_future=True)
        step_reports: List[Dict[str, Any]] = []

        self.logger.info("Starting multi-step automation pipeline (%d step(s) configured)...", len(pipeline))
        executed_count = 0

        for step in pipeline:
            # Check script existence on disk
            if not step.exists():
                if step.is_optional:
                    self.logger.info(
                        "Optional Step %d (%s) script not found at '%s'. Gracefully skipping.",
                        step.step_index, step.name, step.script_path
                    )
                    continue
                else:
                    err = f"Required Step {step.step_index} ({step.name}) script not found at: {step.script_path}"
                    self.logger.error(err)
                    return False, 1, err, step_reports

            # Settle delay before subsequent steps (calibrated for Windows GUI focus)
            if executed_count > 0 and settle_delay > 0:
                self.logger.debug("Settle delay (%.2fs) before Step %d...", settle_delay, step.step_index)
                time.sleep(settle_delay)

            # Build command with state file and forward extra arguments
            cmd = [
                str(self.python_exe),
                str(step.script_path),
                "--state-file",
                str(self.state_file),
            ]
            if extra_args:
                cmd.extend(extra_args)

            self.logger.info("Executing Step %d (%s): %s", step.step_index, step.name, " ".join(cmd))

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self._root_dir),
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    shell=False,
                )
            except Exception as e:
                err = f"Execution exception in Step {step.step_index} ({step.name}): {e}"
                self.logger.error(err)
                return False, 1, err, step_reports

            executed_count += 1
            step_report = {
                "step_index": step.step_index,
                "name": step.name,
                "script": str(step.script_path),
                "returncode": proc.returncode,
                "success": proc.returncode in (0, EXIT_CODE_NO_PENDING_CHATS if step.step_index == 1 else 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            step_reports.append(step_report)

            # Step 1 Exit Code 10 Check: No Pending Chats -> Cleanly cancel remaining steps
            if step.step_index == 1 and proc.returncode == EXIT_CODE_NO_PENDING_CHATS:
                msg = "Step 1: No pending Grill-Me chats found (exit 10). Remaining pipeline steps cancelled cleanly."
                self.logger.info(msg)
                return True, EXIT_CODE_NO_PENDING_CHATS, msg, step_reports

            # Any step failure (non-zero) aborts the remaining pipeline
            if proc.returncode != 0:
                msg = f"Step {step.step_index} ({step.name}) failed with exit code {proc.returncode}. Aborting pipeline."
                self.logger.error(msg)
                return False, proc.returncode, msg, step_reports

            self.logger.info("Step %d (%s) finished successfully (exit 0).", step.step_index, step.name)

        summary = f"Pipeline completed successfully ({executed_count} step(s) executed)."
        self.logger.info(summary)
        return True, 0, summary, step_reports

    def launch_pipeline(
        self,
        wait: bool = False,
        extra_args: Optional[List[str]] = None,
        capture_output: bool = True,
        settle_delay: float = DEFAULT_STEP_SETTLE_DELAY,
    ) -> Tuple[bool, int, str]:
        """
        Trigger the full automation pipeline (Steps 1, 2, 3, and dynamic future steps).

        :param wait: If True, waits for pipeline to complete sequentially and returns exit code.
                     If False (default for headless prod), spawns as a detached process
                     and returns immediately to allow clean exit with ZERO zombie processes.
        :param extra_args: Additional command-line flags forwarded to each step.
        :param capture_output: If True, captures/redirects child stdout and stderr.
        :param settle_delay: Settle delay in seconds between steps (default: 0.8s).
        :return: (success: bool, exit_code: int, message: str)
        """
        # Validate that required pipeline steps exist on disk upfront
        pipeline = self.discover_steps(include_future=True)
        for s in pipeline:
            if not s.is_optional and not s.exists():
                err = f"Required Step {s.step_index} ({s.name}) script not found at: {s.script_path}"
                self.logger.error(err)
                return False, 1, err

        if wait:
            ok, code, msg, _ = self.execute_pipeline(
                extra_args=extra_args,
                capture_output=capture_output,
                settle_delay=settle_delay,
                steps=pipeline,
            )
            return ok, code, msg

        # Asynchronous / Detached Headless Execution (Universal Rule 26)
        creation_flags = 0
        if IS_WINDOWS:
            # DETACHED_PROCESS (0x00000008) + CREATE_NEW_PROCESS_GROUP (0x00000200)
            creation_flags = 0x00000008 | 0x00000200

        cmd = [
            str(self.python_exe),
            str(self._this_dir / "antigravity_detector_core.py"),
            "--run-pipeline",
            "--state-file", str(self.state_file),
            "--settle-delay", str(settle_delay),
        ]
        if self.brain_dir:
            cmd.extend(["--brain-dir", str(self.brain_dir)])
        if extra_args:
            cmd.extend(extra_args)

        self.logger.info("Spawning detached pipeline runner: %s", " ".join(cmd))
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(self._root_dir),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL if capture_output else None,
                stderr=subprocess.DEVNULL if capture_output else None,
                close_fds=True,
                shell=False
            )
            msg = f"Automation pipeline launched asynchronously in background (PID: {proc.pid}). Step 0 exiting cleanly."
            self.logger.info(msg)
            return True, 0, msg
        except Exception as e:
            err = f"Failed to spawn detached pipeline runner: {e}"
            self.logger.error(err)
            return False, 1, err

    def launch_step1(
        self,
        wait: bool = False,
        extra_args: Optional[List[str]] = None,
        capture_output: bool = True
    ) -> Tuple[bool, int, str]:
        """
        Backward-compatible alias routing directly to launch_pipeline.
        Ensures that existing calls to launch_step1 automatically execute all
        sequential pipeline steps (Step 1 -> Step 2 -> Step 3) seamlessly.
        """
        return self.launch_pipeline(
            wait=wait,
            extra_args=extra_args,
            capture_output=capture_output
        )

    # ========================================================================
    # Continuous Polling Loop (Two-Factor Trigger Engine)
    # ========================================================================

    def stop(self):
        """Signal the polling loop to terminate gracefully."""
        self._stop_requested = True

    def run_loop(
        self,
        poll_interval: Optional[float] = None,
        max_checks: Optional[int] = None,
        auto_launch: bool = True,
        wait_for_step1: bool = False,
        wait_for_pipeline: Optional[bool] = None,
        on_check_callback: Optional[Callable[[int, DetectionResult], None]] = None,
        extra_step1_args: Optional[List[str]] = None,
        extra_pipeline_args: Optional[List[str]] = None,
        capture_step1_output: bool = True,
        capture_pipeline_output: Optional[bool] = None,
    ) -> Optional[DetectionResult]:
        """
        Execute continuous polling loop until the 2-factor trigger condition is met:
        Antigravity is open AND (if require_grill_me is True) pending Grill-Me chat > 0.

        :param poll_interval: Override polling interval (in seconds).
        :param max_checks: Maximum number of checks before returning None (None = infinite).
        :param auto_launch: When trigger condition is met, automatically launch pipeline.
        :param wait_for_step1: Backward-compatible wait flag (defaults to wait_for_pipeline).
        :param wait_for_pipeline: Wait for full pipeline completion before exiting loop.
        :param on_check_callback: Optional callback invoked after each check: callback(iteration, result).
        :param extra_step1_args: Backward-compatible extra args list.
        :param extra_pipeline_args: Additional command line flags forwarded to pipeline steps.
        :param capture_step1_output: Backward-compatible output capture flag.
        :param capture_pipeline_output: Suppress pipeline step output from terminal.
        :return: DetectionResult when triggered, or None if stopped/exceeded max_checks.
        """
        interval = float(poll_interval) if poll_interval is not None else self.poll_interval
        should_wait = wait_for_pipeline if wait_for_pipeline is not None else wait_for_step1
        pipeline_args = extra_pipeline_args if extra_pipeline_args is not None else extra_step1_args
        suppress_output = capture_pipeline_output if capture_pipeline_output is not None else capture_step1_output
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
            print(f"  Pipeline Steps   : {len(self.pipeline_steps)} steps configured")
            print(f"  Python Engine    : {self.python_exe}")
            print(f"  Require Grill-Me : {'YES (2-Factor Trigger)' if self.require_grill_me else 'NO (Trigger on Open)'}")
            print(f"  Auto-Trigger     : {'ENABLED (Launch Pipeline on Detection)' if auto_launch else 'DISABLED (Dry Run)'}")
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

                if auto_launch:
                    if not self.headless:
                        print(f"[{now_str}] Launching Complete Automation Pipeline (Steps 1 -> 2 -> 3)...")
                    ok, code, msg = self.launch_pipeline(
                        wait=should_wait,
                        extra_args=pipeline_args,
                        capture_output=suppress_output
                    )
                    result.details["pipeline_result"] = {
                        "success": ok,
                        "exit_code": code,
                        "message": msg
                    }
                    result.details["step1_result"] = result.details["pipeline_result"]

                # Return detection result and terminate loop cleanly (Universal Rule 26)
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
# Standalone CLI Entrypoint & Multi-Step Pipeline Runner
# ============================================================================

def main() -> int:
    """CLI Entrypoint for Antigravity Detector & Detached Pipeline Runner."""
    parser = argparse.ArgumentParser(
        description="Step 0 - AntiGravity Detector Core & Dynamic Multi-Step Pipeline Engine"
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Execute the complete multi-step automation pipeline sequentially (Steps 1 -> 2 -> 3 -> 4)"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Custom path to target_chat.json state file"
    )
    parser.add_argument(
        "--brain-dir",
        type=str,
        default=None,
        help="Custom path to Antigravity brain storage directory"
    )
    parser.add_argument(
        "--settle-delay",
        type=float,
        default=DEFAULT_STEP_SETTLE_DELAY,
        help="Settle delay between pipeline steps in seconds (default: 0.8s)"
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="List all configured and discovered pipeline steps and exit"
    )
    parser.add_argument(
        "--detect-once",
        action="store_true",
        help="Run a single Antigravity detection check and print JSON result"
    )

    args, extra = parser.parse_known_args()

    if args.list_steps:
        detector = AntiGravityDetector()
        steps = detector.discover_steps(include_future=True)
        print("\n" + "=" * 76)
        print("  AUTOCONNECT / GRILL-ME MULTI-STEP PIPELINE REGISTRY")
        print("=" * 76)
        for s in steps:
            status = "PRESENT" if s.exists() else ("OPTIONAL (Future Step)" if s.is_optional else "MISSING")
            print(f"  [{s.step_index}] {s.name:<32} : [{status}]")
            print(f"      Path: {s.script_path}")
            if s.description:
                print(f"      Note: {s.description}")
        print("=" * 76 + "\n")
        return 0

    if args.detect_once:
        detector = AntiGravityDetector(headless=True, brain_dir=args.brain_dir)
        res = detector.detect()
        print(json.dumps(res.to_json_envelope(), indent=2))
        return 0 if res.is_detected else 1

    if args.run_pipeline:
        detector = AntiGravityDetector(
            headless=True,
            state_file_path=args.state_file,
            brain_dir=args.brain_dir,
        )
        ok, code, msg, _ = detector.execute_pipeline(
            extra_args=extra,
            capture_output=False,
            settle_delay=args.settle_delay,
        )
        return code

    return 0


if __name__ == "__main__":
    sys.exit(main())
