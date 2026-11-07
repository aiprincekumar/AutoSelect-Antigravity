#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 4 - रिपोर्टिंग एवं विजुअल डैशबोर्ड / Step 4 - Reporting & Visual Dashboard
==============================================================================
Part of: AutoSelect Antigravity Automation Pipeline
Workspace: Keyboard Automation (Step 4: Reporting & Visual Dashboard Engine)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 04 (UI/UX Design System)

Mission:
  1. Persistent Execution Ledger: Ingests `target_chat.json` and accumulates
     lifetime telemetry into `reports/automation_history.json`:
       - Point 1: Total pipeline runs (completed Steps 1 -> 2 -> 3).
       - Point 2: Total questions answered across all chats.
       - Point 3: Total cumulative script runtime & per-run durations.
       - Point 4: Total unique chats automated.
       - Point 5: Chat-wise automation breakdown (run count per chat).
       - Point 6: Crystal-clear question details with options and selected/recommended badges.
       - Point 7: Visual-only dashboard presentation (zero terminal clutter).
  2. Two-Way Operation Engine:
     - Automated Pipeline Mode:
       * Silently ingests state & generates `reports/dashboard.html`.
       * Zero terminal clutter.
       * Monitors Windows keyboard & mouse movement via `GetLastInputInfo` (ctypes User32).
       * When user activity is detected, waits exactly 10 seconds, then opens the dashboard.
       * If user is idle and never moves input, GUI is never launched, preserving silence.
     - Manual Mode (`run_step4.bat` or `--show` / `--manual`):
       * Instantly opens `dashboard.html` without waiting for input or 10-second delay.
"""

from __future__ import annotations

import os
import sys
import json
import time
import signal
import logging
import argparse
import webbrowser
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Root workspace resolution
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith("step_") else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from core_engine.config_manager import (
    get_canonical_config_path,
    get_default_runtime_config,
    load_runtime_config as core_load_runtime_config,
    save_runtime_config as core_save_runtime_config,
    get_effective_poll_interval,
    get_settle_delay,
    get_user_activity_delay,
    get_window_focus_delay,
    get_dom_click_settle_delay,
    get_step4_poll_interval,
    get_step4_timeout,
    get_keyboard_timing,
    get_step_timing,
    apply_logging_config,
)

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

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("dwTime", wintypes.DWORD),
        ]


# ============================================================================
# User Activity Detection (Win32 GetLastInputInfo)
# ============================================================================

def get_last_input_tick() -> int:
    """
    Query Windows User32 GetLastInputInfo to obtain the millisecond tick count
    of the most recent mouse movement, click, or keyboard keystroke.
    """
    if not IS_WINDOWS:
        return int(time.time() * 1000)

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if user32.GetLastInputInfo(ctypes.byref(lii)):
        return int(lii.dwTime)
    return int(time.time() * 1000)


def watch_for_user_input(
    timeout: Optional[float] = None,
    poll_interval: float = 0.25,
    stop_event: Optional[Any] = None
) -> bool:
    """
    Block until user activity (keyboard keystroke or mouse movement) is detected.

    :param timeout: Maximum seconds to wait before giving up (None = wait forever).
    :param poll_interval: Sleep interval between checks in seconds.
    :param stop_event: Optional threading.Event or object with is_set() to abort wait.
    :return: True if user input was detected, False if timed out or stopped.
    """
    initial_tick = get_last_input_tick()
    start_time = time.time()

    while True:
        if stop_event and hasattr(stop_event, "is_set") and stop_event.is_set():
            return False

        if timeout is not None and (time.time() - start_time) >= timeout:
            return False

        time.sleep(poll_interval)
        current_tick = get_last_input_tick()

        # If tick count changed, physical or synthetic user input occurred
        if current_tick != initial_tick:
            return True


# ============================================================================
# Data Models (Department 06 Architecture)
# ============================================================================

@dataclass
class QuestionDetail:
    question_index: int
    question: str
    options: List[str]
    selected_option_index: Optional[int] = None
    selected_option_text: Optional[str] = None
    is_multi_select: bool = False
    is_recommended: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunRecord:
    run_id: str
    timestamp: str
    duration_seconds: float
    questions_count: int
    questions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "COMPLETED"
    selected_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChatHistory:
    conversation_id: str
    topic_summary: str
    last_user_prompt: str
    run_count: int = 0
    total_questions: int = 0
    last_run_timestamp: str = ""
    runs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AutomationHistory:
    total_pipeline_runs: int = 0
    total_questions_answered: int = 0
    total_runtime_seconds: float = 0.0
    total_unique_chats: int = 0
    last_updated: str = ""
    chats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AutomationHistory:
        data = d.get("data", d)
        return cls(
            total_pipeline_runs=int(data.get("total_pipeline_runs", 0)),
            total_questions_answered=int(data.get("total_questions_answered", 0)),
            total_runtime_seconds=float(data.get("total_runtime_seconds", 0.0)),
            total_unique_chats=int(data.get("total_unique_chats", 0)),
            last_updated=str(data.get("last_updated", "")),
            chats=dict(data.get("chats", {})),
        )


# ============================================================================
# Core Reporting Engine
# ============================================================================

logger = logging.getLogger("Step4Reporting")


class Step4ReportingEngine:
    """
    Core reporting and visual dashboard subsystem for AutoSelect Antigravity.
    Manages persistent JSON history and generates self-contained HTML dashboards.
    """

    def __init__(
        self,
        workspace_dir: Optional[Union[str, Path]] = None,
        state_file_path: Optional[Union[str, Path]] = None,
        reports_dir: Optional[Union[str, Path]] = None,
        history_file_path: Optional[Union[str, Path]] = None,
    ):
        self._this_dir = Path(__file__).resolve().parent
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir).resolve()
        else:
            self.workspace_dir = (
                self._this_dir.parent
                if self._this_dir.name.startswith("step_")
                else self._this_dir
            )

        # State file path (target_chat.json)
        if state_file_path:
            self.state_file = Path(state_file_path).resolve()
        else:
            state_primary = self.workspace_dir / "state" / "target_chat.json"
            state_fallback = self.workspace_dir / "target_chat.json"
            if state_primary.is_file():
                self.state_file = state_primary.resolve()
            elif state_fallback.is_file():
                self.state_file = state_fallback.resolve()
            else:
                self.state_file = state_primary.resolve()

        # Reports directory
        if reports_dir:
            self.reports_dir = Path(reports_dir).resolve()
        else:
            self.reports_dir = self._this_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Persistent history file path
        if history_file_path:
            self.history_file = Path(history_file_path).resolve()
        else:
            self.history_file = self.reports_dir / "automation_history.json"

        # Dashboard HTML output path
        self.dashboard_file = self.reports_dir / "dashboard.html"
        self.session_lock_file = self.reports_dir / ".dashboard_launched.lock"

        # System runtime configuration file path (step_9_complete_automation/config.json)
        self.runtime_config_file = self.get_runtime_config_path()
        self.config = core_load_runtime_config(self.runtime_config_file)
        try:
            apply_logging_config(self.config, logger, step_name="Step 4: Reporting and Telemetry")
            apply_logging_config(self.config, logging.getLogger("Step4Reporting"), step_name="Step 4: Reporting and Telemetry")
        except Exception:
            pass
        logger.info("[STEP 4.1] [ENGINE_INIT] Step 4 Reporting Engine initialized (Workspace: %s)", self.workspace_dir)
        logger.info("[STEP 4.2] [CFG_LOAD] Loaded runtime configuration from %s", self.runtime_config_file)
        logger.info("[STEP 4.3] [LOGGING_ATTACH] Centralized logging attached to complete_automation.log")

        # Ensure history file exists on disk
        if not self.history_file.is_file():
            self.save_history(self.load_history())

    # ========================================================================
    # History Ledger Storage (Load / Save)
    # ========================================================================

    def load_history(self) -> AutomationHistory:
        logger.info("[STEP 4.8] [HISTORY_LOCATE] Locating persistent history file: %s", self.history_file)
        logger.info("[STEP 4.9] [HISTORY_LOAD] Ingesting existing history records and cumulative metrics")
        """Load persistent automation history from disk."""
        if not self.history_file.is_file():
            return AutomationHistory(
                total_pipeline_runs=0,
                total_questions_answered=0,
                total_runtime_seconds=0.0,
                total_unique_chats=0,
                last_updated=datetime.now(timezone.utc).isoformat(),
                chats={},
            )

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return AutomationHistory.from_dict(payload)
        except Exception:
            return AutomationHistory(
                total_pipeline_runs=0,
                total_questions_answered=0,
                total_runtime_seconds=0.0,
                total_unique_chats=0,
                last_updated=datetime.now(timezone.utc).isoformat(),
                chats={},
            )

    def save_history(self, history: AutomationHistory) -> bool:
        """Save persistent history adhering to Department 06 JSON response standard."""
        history.total_unique_chats = len(history.chats)
        history.last_updated = datetime.now(timezone.utc).isoformat()

        envelope = {
            "success": True,
            "data": history.to_dict(),
            "meta": {
                "timestamp": history.last_updated,
                "step": "step_4_reporting",
                "department": "Dept 06 - Backend & API Engineering & Dept 04 - UI/UX Design System",
                "format_version": "1.0.0",
            },
        }

        try:
            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(envelope, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.history_file)
            logger.info("[STEP 4.14] [HISTORY_SAVE] Persisted history atomically to %s (runs: %d)", self.history_file, history.total_pipeline_runs)
            return True
        except Exception:
            return False

    # ========================================================================
    # Runtime Automation Engine Configuration (config.json)
    # ========================================================================

    def get_runtime_config_path(self) -> Path:
        """Locate step_9_complete_automation/config.json using core_engine.config_manager."""
        return get_canonical_config_path(self.workspace_dir)

    def load_runtime_config(self) -> Dict[str, Any]:
        """Load system runtime configuration from disk with fail-safe defaults via core_engine."""
        return core_load_runtime_config(self.get_runtime_config_path())

    def save_runtime_config(
        self,
        config_dict: Dict[str, Any],
        target_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Save system runtime configuration to disk with atomic replacement via core_engine."""
        dest = Path(target_path).resolve() if target_path else self.get_runtime_config_path()
        return core_save_runtime_config(config_dict, dest)

    # ========================================================================
    # State Ingestion (target_chat.json)
    # ========================================================================

    def ingest_current_run(
        self,
        state_file: Optional[Union[str, Path]] = None,
        default_duration: float = 6.5
    ) -> Tuple[bool, str, Optional[RunRecord]]:
        """
        Ingest the latest run recorded in target_chat.json and update automation history.

        :param state_file: Optional path override for target_chat.json.
        :param default_duration: Default duration in seconds if timestamps are missing.
        :return: (was_recorded: bool, message: str, run_record: Optional[RunRecord])
        """
        p_state = Path(state_file).resolve() if state_file else self.state_file
        if not p_state.is_file() and not state_file:
            alt = (
                self.workspace_dir / "target_chat.json"
                if p_state.parent.name == "state"
                else self.workspace_dir / "state" / "target_chat.json"
            )
            if alt.is_file():
                p_state = alt.resolve()
        logger.info("[STEP 4.4] [STATE_LOCATE] Resolving state file: %s", p_state)
        if not p_state.is_file():
            return False, f"State file not found at: {p_state}", None

        try:
            with open(p_state, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            return False, f"Failed to parse state file: {e}", None

        logger.info("[STEP 4.5] [STATE_READ] Reading runtime state from: %s", p_state)
        data = raw.get("data", {})
        status = data.get("status", "")
        cid = data.get("conversation_id")
        logger.info("[STEP 4.6] [STATUS_EVAL] Evaluated state status: '%s' (success: %s, CID: %s)", status, raw.get("success"), cid)

        # If no pending chat was found, or cancelled, do not increment runs
        if not raw.get("success") or status == "NO_PENDING_CHATS" or not cid:
            # Still re-generate dashboard so existing data is accessible
            self.generate_html_dashboard()
            return False, "No active automated run in target_chat.json (status: NO_PENDING_CHATS).", None

        # Extract question details
        raw_questions = data.get("questions", [])
        raw_selections = data.get("selections", [])
        topic = data.get("topic_summary") or "Antigravity Automated Chat"
        prompt = data.get("last_user_prompt") or ""
        selected_at = data.get("selected_at") or raw.get("meta", {}).get("timestamp") or datetime.now(timezone.utc).isoformat()

        # Build list of QuestionDetails
        questions_list: List[Dict[str, Any]] = []
        for idx, q in enumerate(raw_questions):
            q_text = q.get("question", f"Question #{idx + 1}")
            opts = q.get("options", [])
            sel_opt_idx = q.get("recommended_option_index")
            sel_opt_txt = q.get("recommended_option_text")

            # Match with selections if available
            for sel in raw_selections:
                if sel.get("question_index") == q.get("question_index", idx + 1):
                    sel_opt_idx = sel.get("selected_option_index", sel_opt_idx)
                    sel_opt_txt = sel.get("selected_option_text", sel_opt_txt)
                    break

            qd = QuestionDetail(
                question_index=q.get("question_index", idx + 1),
                question=q_text,
                options=opts,
                selected_option_index=sel_opt_idx,
                selected_option_text=sel_opt_txt,
                is_multi_select=bool(q.get("is_multi_select", False)),
                is_recommended=True,
            )
            questions_list.append(qd.to_dict())

        logger.info("[STEP 4.7] [PAYLOAD_PARSE] Parsed conversation %s, topic '%s', %d question(s)", cid, topic, len(questions_list))
        # Calculate run duration
        duration = default_duration
        try:
            t0 = datetime.fromisoformat(selected_at.replace("Z", "+00:00"))
            t_now = datetime.now(timezone.utc)
            diff = (t_now - t0).total_seconds()
            if 0.5 <= diff <= 300.0:
                duration = round(diff, 2)
        except Exception:
            duration = default_duration

        now_utc = datetime.now(timezone.utc).isoformat()
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        record = RunRecord(
            run_id=run_id,
            timestamp=now_utc,
            duration_seconds=duration,
            questions_count=len(questions_list),
            questions=questions_list,
            status="COMPLETED",
            selected_at=selected_at,
        )

        history = self.load_history()

        # Idempotency guard: Prevent duplicate recording of the exact same state file
        logger.info("[STEP 4.10] [IDEMPOTENCY_CHECK] Checking run timestamp for CID %s (selected_at: %s)", cid, selected_at)
        existing_chat = history.chats.get(cid)
        if existing_chat:
            runs = existing_chat.get("runs", [])
            if runs:
                last_run = runs[-1]
                # If selected_at matches the last recorded run, it is the exact same execution
                if selected_at and last_run.get("selected_at") == selected_at:
                    self.generate_html_dashboard(history)
                    return True, "Run was already recorded for this state timestamp (idempotent skip).", record

        # Update cumulative metrics
        history.total_pipeline_runs += 1
        history.total_questions_answered += len(questions_list)
        history.total_runtime_seconds = round(history.total_runtime_seconds + duration, 2)
        logger.info("[STEP 4.11] [METRICS_UPDATE] Cumulative metrics: runs=%d, questions=%d, runtime=%.2fs", history.total_pipeline_runs, history.total_questions_answered, history.total_runtime_seconds)

        # Update chat-wise breakdown
        if cid not in history.chats:
            history.chats[cid] = ChatHistory(
                conversation_id=cid,
                topic_summary=topic,
                last_user_prompt=prompt,
                run_count=1,
                total_questions=len(questions_list),
                last_run_timestamp=now_utc,
                runs=[record.to_dict()],
            ).to_dict()
        else:
            chat_data = history.chats[cid]
            chat_data["run_count"] = int(chat_data.get("run_count", 0)) + 1
            chat_data["total_questions"] = int(chat_data.get("total_questions", 0)) + len(questions_list)
            chat_data["last_run_timestamp"] = now_utc
            if topic and not chat_data.get("topic_summary"):
                chat_data["topic_summary"] = topic
            if prompt:
                chat_data["last_user_prompt"] = prompt
            chat_data.setdefault("runs", []).append(record.to_dict())
        logger.info("[STEP 4.12] [CHAT_BREAKDOWN] Updated chat history for conversation %s", cid)
        logger.info("[STEP 4.13] [RECORD_CREATE] Created RunRecord %s (duration: %.2fs)", run_id, duration)

        self.save_history(history)
        self.generate_html_dashboard(history)

        return True, f"Successfully recorded run {run_id} for chat {cid}.", record

    # ========================================================================
    # SVG Vector Visualizations (Department 04 UI/UX & Zero Dependencies)
    # ========================================================================

    @staticmethod
    def build_topology_svg() -> str:
        """
        Generate pure inline vector SVG showing the full System Component Topology & Health Architecture:
        [Antigravity IDE / Brain] -> [Step 0: Detector (Win32 Hook)] -> [Step 1: Chat Identifier]
        -> [Step 2: Focus & Activation] -> [Step 3: Selector] -> [Step 4: Reporting Subsystem]
        with animated pulse bus lines, component health badges, and Department 04 design tokens.
        """
        nodes = [
            ("BRAIN", "Antigravity IDE / Brain", "Session Transcripts", "ONLINE", "#10b981", "#34d399"),
            ("STEP 0", "Step 0: Detector", "Win32 Hook Active", "Win32 HOOK ACTIVE", "#6366f1", "#818cf8"),
            ("STEP 1", "Step 1: Identifier", "Target Chat Ingestion", "100% INTEGRITY", "#06b6d4", "#22d3ee"),
            ("STEP 2", "Step 2: Focus", "Precision Window Focus", "ACTIVE TARGET", "#a855f7", "#c084fc"),
            ("STEP 3", "Step 3: Selector", "Option 1 Auto-Select", "AUTONOMOUS", "#f59e0b", "#fbbf24"),
            ("STEP 4", "Step 4: Reporter", "Telemetry & Visual HUD", "PERSISTENT JSON", "#10b981", "#34d399"),
        ]

        svg_parts = [
            '<svg viewBox="0 0 1180 130" width="100%" height="130" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow:visible;">',
            '  <defs>',
            '    <marker id="pipeline-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#6366f1" />',
            '    </marker>',
            '    <marker id="topo-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#06b6d4" />',
            '    </marker>',
            '    <linearGradient id="pipeArrowGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#6366f1" />',
            '      <stop offset="100%" stop-color="#10b981" />',
            '    </linearGradient>',
            '    <linearGradient id="topoBusGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#6366f1" />',
            '      <stop offset="50%" stop-color="#06b6d4" />',
            '      <stop offset="100%" stop-color="#10b981" />',
            '    </linearGradient>',
            '    <filter id="topoGlow" x="-20%" y="-20%" width="140%" height="140%">',
            '      <feGaussianBlur stdDeviation="3" result="blur" />',
            '      <feComposite in="SourceGraphic" in2="blur" operator="over" />',
            '    </filter>',
            '  </defs>',
        ]

        node_w = 166
        spacing = 30
        start_x = 18
        y = 18
        h = 88

        # Draw connecting bus lines and animated glowing pulse dots
        for i in range(5):
            x1 = start_x + i * (node_w + spacing) + node_w
            x2 = start_x + (i + 1) * (node_w + spacing)
            mid_y = y + h / 2
            svg_parts.extend([
                f'  <!-- Bus connection {i} -> {i+1} -->',
                f'  <line x1="{x1}" y1="{mid_y}" x2="{x2}" y2="{mid_y}" stroke="url(#topoBusGrad)" stroke-width="2.5" stroke-dasharray="4 2" marker-end="url(#topo-arrow)" />',
                f'  <circle r="3.5" fill="#38bdf8" filter="url(#topoGlow)">',
                f'    <animateMotion path="M {x1} {mid_y} L {x2 - 6} {mid_y}" dur="2s" repeatCount="indefinite" />',
                f'  </circle>',
            ])

        # Draw step node boxes
        for i, (tag, title, subtitle, badge_status, primary_color, text_color) in enumerate(nodes):
            x = start_x + i * (node_w + spacing)
            r_c = int(primary_color[1:3], 16)
            g_c = int(primary_color[3:5], 16)
            b_c = int(primary_color[5:7], 16)
            badge_bg = f"rgba({r_c}, {g_c}, {b_c}, 0.15)"
            svg_parts.extend([
                f'  <g class="pipeline-step-node topology-node" transform="translate({x}, {y})">',
                f'    <rect width="{node_w}" height="{h}" rx="10" fill="var(--bg-surface-elevated)" stroke="var(--border-subtle)" stroke-width="1.5" />',
                f'    <rect x="8" y="10" width="48" height="18" rx="4" fill="{badge_bg}" />',
                f'    <text x="32" y="23" font-size="9" font-weight="700" font-family="var(--font-mono)" fill="{text_color}" text-anchor="middle">{tag}</text>',
                f'    <rect x="{node_w - 92}" y="10" width="84" height="18" rx="4" fill="rgba(16, 185, 129, 0.12)" stroke="rgba(16, 185, 129, 0.3)" stroke-width="0.8" />',
                f'    <text x="{node_w - 50}" y="22.5" font-size="7.5" font-weight="700" font-family="var(--font-mono)" fill="#10b981" text-anchor="middle">{badge_status}</text>',
                f'    <text x="8" y="48" font-size="11" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">{title}</text>',
                f'    <text x="8" y="66" font-size="9" font-family="var(--font-family)" fill="var(--text-secondary)">{subtitle}</text>',
                f'    <circle cx="{node_w - 10}" cy="{h - 10}" r="3" fill="{primary_color}" />',
                f'  </g>',
            ])

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    @staticmethod
    def build_pipeline_svg() -> str:
        """
        Backward compatible alias for build_topology_svg showing the full 6-node architecture.
        """
        return Step4ReportingEngine.build_topology_svg()

    @staticmethod
    def build_chat_distribution_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG bar chart showing pipeline runs and questions
        per conversation.
        """
        chats_list = list(history.chats.values())
        if not chats_list:
            return (
                '<svg viewBox="0 0 640 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">'
                '  <rect width="640" height="240" rx="8" fill="transparent" />'
                '  <text x="320" y="115" font-size="28" text-anchor="middle" fill="#64748b">📊</text>'
                '  <text x="320" y="145" font-size="13" font-weight="600" text-anchor="middle" fill="#94a3b8">No Conversation Telemetry Yet</text>'
                '  <text x="320" y="165" font-size="11" text-anchor="middle" fill="#64748b">Run complete_automation.py to record live chat telemetry</text>'
                '</svg>'
            )

        # Plot up to 5 most recent conversations
        chats_to_plot = chats_list[:5]
        max_val = max(
            [c.get("run_count", 0) for c in chats_to_plot] +
            [c.get("total_questions", 0) for c in chats_to_plot] + [4]
        )

        svg = [
            '<svg viewBox="0 0 640 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="barRunsGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="#818cf8" />',
            '      <stop offset="100%" stop-color="#4f46e5" />',
            '    </linearGradient>',
            '    <linearGradient id="barQsGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="#34d399" />',
            '      <stop offset="100%" stop-color="#059669" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Legend -->',
            '  <g transform="translate(440, 14)">',
            '    <rect x="0" y="0" width="12" height="12" rx="3" fill="url(#barRunsGrad)" />',
            '    <text x="18" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Runs</text>',
            '    <rect x="70" y="0" width="12" height="12" rx="3" fill="url(#barQsGrad)" />',
            '    <text x="88" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Questions</text>',
            '  </g>',
        ]

        # Horizontal grid lines
        for y in [40, 80, 120, 160, 200]:
            svg.append(f'  <line x1="50" y1="{y}" x2="620" y2="{y}" stroke="var(--border-subtle)" stroke-width="1" />')

        # Baseline axis
        svg.append('  <line x1="50" y1="200" x2="620" y2="200" stroke="var(--border-subtle)" stroke-width="1.5" />')

        n = len(chats_to_plot)
        slot_width = (620 - 60) / n

        for i, c in enumerate(chats_to_plot):
            cid = str(c.get("conversation_id", f"Chat-{i+1}"))
            label = cid[:8] + ".." if len(cid) > 8 else cid

            runs = int(c.get("run_count", 0))
            qs = int(c.get("total_questions", 0))

            h_runs = max(4, int((runs / max_val) * 150))
            h_qs = max(4, int((qs / max_val) * 150))

            cx = 60 + (i + 0.5) * slot_width
            bar_w = min(22.0, slot_width * 0.26)

            x_runs = cx - bar_w - 3
            y_runs = 200 - h_runs

            x_qs = cx + 3
            y_qs = 200 - h_qs

            # Bar 1: Runs
            svg.append(f'  <rect x="{x_runs:.1f}" y="{y_runs:.1f}" width="{bar_w:.1f}" height="{h_runs:.1f}" rx="3" fill="url(#barRunsGrad)"><title>Runs: {runs}</title></rect>')
            svg.append(f'  <text x="{x_runs + bar_w/2:.1f}" y="{y_runs - 4:.1f}" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#818cf8" text-anchor="middle">{runs}</text>')

            # Bar 2: Questions
            svg.append(f'  <rect x="{x_qs:.1f}" y="{y_qs:.1f}" width="{bar_w:.1f}" height="{h_qs:.1f}" rx="3" fill="url(#barQsGrad)"><title>Questions: {qs}</title></rect>')
            svg.append(f'  <text x="{x_qs + bar_w/2:.1f}" y="{y_qs - 4:.1f}" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#34d399" text-anchor="middle">{qs}</text>')

            # X-axis label
            svg.append(f'  <text x="{cx:.1f}" y="222" font-size="10" font-family="var(--font-mono)" fill="var(--text-secondary)" text-anchor="middle">{label}</text>')

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def build_donut_gauge_svg(recommendation_rate: float = 100.0) -> str:
        """
        Generate pure inline vector SVG donut gauge showing Option 1 recommendation accuracy.
        (Retained for backward compatibility).
        """
        rate = max(0.0, min(100.0, float(recommendation_rate)))
        rate_str = f"{int(round(rate))}%" if rate.is_integer() or round(rate, 1) == round(rate) else f"{rate:.1f}%"
        # Radius 70: circumference = 2 * pi * 70 = 439.82
        circ = 439.82
        offset = circ * (1.0 - (rate / 100.0))

        svg = [
            '<svg viewBox="0 0 280 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="gaugeEmeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
            '      <stop offset="0%" stop-color="#10b981" />',
            '      <stop offset="100%" stop-color="#06b6d4" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Background Circle Track -->',
            '  <circle cx="140" cy="110" r="70" fill="none" stroke="var(--bg-surface-elevated)" stroke-width="16" />',
            '  <!-- Progress Arc -->',
            f'  <circle cx="140" cy="110" r="70" fill="none" stroke="url(#gaugeEmeraldGrad)" stroke-width="16" stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" transform="rotate(-90 140 110)" />',
            '  <!-- Center Metrics -->',
            f'  <text x="140" y="106" font-size="34" font-weight="800" font-family="var(--font-mono)" fill="#10b981" text-anchor="middle">{rate_str}</text>',
            '  <text x="140" y="128" font-size="9.5" font-weight="700" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="middle" letter-spacing="1">OPTION 1 ACCURACY</text>',
            '  <!-- Subtitle Summary -->',
            f'  <text x="140" y="202" font-size="12" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)" text-anchor="middle">{rate_str} Option 1 Adherence</text>',
            '  <text x="140" y="222" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)" text-anchor="middle">Autonomous Selection • Zero Deviations</text>',
            '</svg>',
        ]
        return "\n".join(svg)

    @staticmethod
    def build_latency_trend_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG line/area trend chart showing the duration of recent runs
        in seconds with an average latency reference line.
        """
        all_runs = []
        for cid, chat in history.chats.items():
            topic = chat.get("topic_summary", "")
            for run in chat.get("runs", []):
                all_runs.append({
                    "run_id": run.get("run_id", "run"),
                    "timestamp": run.get("timestamp", ""),
                    "duration": float(run.get("duration_seconds", 0.0)),
                    "questions_count": int(run.get("questions_count", 0)),
                    "cid": cid,
                    "topic": topic,
                })

        # Sort chronologically by timestamp
        all_runs.sort(key=lambda r: r.get("timestamp", ""))

        if not all_runs:
            return (
                '<svg viewBox="0 0 640 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="display:block;">'
                '  <rect width="640" height="220" rx="8" fill="transparent" />'
                '  <text x="320" y="105" font-size="28" text-anchor="middle" fill="#64748b">⚡</text>'
                '  <text x="320" y="135" font-size="13" font-weight="600" text-anchor="middle" fill="#94a3b8">No Run Latency Data Yet</text>'
                '  <text x="320" y="155" font-size="11" text-anchor="middle" fill="#64748b">Run complete_automation.py to record latency telemetry</text>'
                '</svg>'
            )

        # Show up to 10 most recent runs
        recent_runs = all_runs[-10:]
        durations = [r["duration"] for r in recent_runs]
        mean_dur = sum(durations) / len(durations) if durations else 0.0
        max_dur = max(durations + [mean_dur, 5.0]) * 1.25

        left = 55.0
        right = 610.0
        top = 35.0
        bottom = 180.0
        chart_w = right - left
        chart_h = bottom - top

        svg = [
            '<svg viewBox="0 0 640 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="latencyLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#06b6d4" />',
            '      <stop offset="50%" stop-color="#6366f1" />',
            '      <stop offset="100%" stop-color="#10b981" />',
            '    </linearGradient>',
            '    <linearGradient id="latencyAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="rgba(99, 102, 241, 0.35)" />',
            '      <stop offset="100%" stop-color="rgba(99, 102, 241, 0.0)" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Legend -->',
            '  <g transform="translate(370, 12)">',
            '    <line x1="0" y1="6" x2="20" y2="6" stroke="#06b6d4" stroke-width="2.5" />',
            '    <circle cx="10" cy="6" r="3" fill="#06b6d4" />',
            '    <text x="26" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Run Duration (s)</text>',
            '    <line x1="140" y1="6" x2="160" y2="6" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4 2" />',
            '    <text x="166" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Mean Latency</text>',
            '  </g>',
        ]

        # Horizontal grid lines
        for step_idx in range(5):
            val = max_dur * (step_idx / 4.0)
            y = bottom - (step_idx / 4.0) * chart_h
            svg.append(f'  <line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="var(--border-subtle)" stroke-width="1" />')
            svg.append(f'  <text x="{left - 8}" y="{y + 3:.1f}" font-size="9.5" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="end">{val:.1f}s</text>')

        # Calculate coordinates for points
        n = len(recent_runs)
        coords = []
        for i, r in enumerate(recent_runs):
            if n == 1:
                cx = left + chart_w / 2.0
            else:
                cx = left + (i / (n - 1)) * chart_w
            cy = bottom - (r["duration"] / max_dur) * chart_h
            coords.append((cx, cy, r))

        # Area polygon under line
        area_points = [f"{coords[0][0]:.1f},{bottom:.1f}"]
        for cx, cy, _ in coords:
            area_points.append(f"{cx:.1f},{cy:.1f}")
        area_points.append(f"{coords[-1][0]:.1f},{bottom:.1f}")
        svg.append(f'  <polygon points="{" ".join(area_points)}" fill="url(#latencyAreaGrad)" />')

        # Line path
        line_d = " ".join([f"{'M' if idx == 0 else 'L'} {cx:.1f} {cy:.1f}" for idx, (cx, cy, _) in enumerate(coords)])
        svg.append(f'  <path d="{line_d}" fill="none" stroke="url(#latencyLineGrad)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')

        # Mean duration reference line
        y_mean = bottom - (mean_dur / max_dur) * chart_h
        svg.append(f'  <line x1="{left}" y1="{y_mean:.1f}" x2="{right}" y2="{y_mean:.1f}" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.9" />')
        svg.append(f'  <text x="{right}" y="{y_mean - 6:.1f}" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#f59e0b" text-anchor="end">Mean: {mean_dur:.1f}s</text>')

        # Draw point nodes and labels
        for idx, (cx, cy, r) in enumerate(coords):
            dur = r["duration"]
            run_lbl = f"R{idx + 1}"
            svg.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="var(--bg-primary)" stroke="#06b6d4" stroke-width="2.5"><title>{r["run_id"]}: {dur:.2f}s ({r["questions_count"]} Qs)</title></circle>')
            svg.append(f'  <text x="{cx:.1f}" y="{cy - 8:.1f}" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="var(--text-primary)" text-anchor="middle">{dur:.1f}s</text>')
            svg.append(f'  <text x="{cx:.1f}" y="{bottom + 16:.1f}" font-size="9.5" font-weight="600" font-family="var(--font-mono)" fill="var(--text-secondary)" text-anchor="middle">{run_lbl}</text>')

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def build_topic_share_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG donut chart showing the percentage distribution
        of questions across different conversation topics/chats.
        """
        import math
        chats_list = list(history.chats.values())
        total_qs = max(1, sum(c.get("total_questions", 0) for c in chats_list))

        if not chats_list or history.total_questions_answered == 0:
            return (
                '<svg viewBox="0 0 460 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">'
                '  <rect width="460" height="240" rx="8" fill="transparent" />'
                '  <text x="230" y="115" font-size="28" text-anchor="middle" fill="#64748b">🥧</text>'
                '  <text x="230" y="145" font-size="13" font-weight="600" text-anchor="middle" fill="#94a3b8">No Workload Distribution Yet</text>'
                '  <text x="230" y="165" font-size="11" text-anchor="middle" fill="#64748b">Run automation to populate conversation shares</text>'
                '</svg>'
            )

        # Sort chats by total_questions descending
        sorted_chats = sorted(chats_list, key=lambda c: c.get("total_questions", 0), reverse=True)

        # Take up to 4 distinct topics, group rest into Other
        slices_data = []
        if len(sorted_chats) <= 4:
            for c in sorted_chats:
                qs = c.get("total_questions", 0)
                if qs > 0:
                    topic = c.get("topic_summary") or c.get("conversation_id", "Chat")
                    slices_data.append((topic, qs, (qs / total_qs) * 100.0))
        else:
            for c in sorted_chats[:3]:
                qs = c.get("total_questions", 0)
                if qs > 0:
                    topic = c.get("topic_summary") or c.get("conversation_id", "Chat")
                    slices_data.append((topic, qs, (qs / total_qs) * 100.0))
            other_qs = sum(c.get("total_questions", 0) for c in sorted_chats[3:])
            if other_qs > 0:
                slices_data.append(("Other Chats", other_qs, (other_qs / total_qs) * 100.0))

        if not slices_data:
            slices_data.append(("Automated Chat", total_qs, 100.0))

        palette = [
            "#6366f1",  # Indigo
            "#06b6d4",  # Cyan
            "#10b981",  # Emerald
            "#f59e0b",  # Amber
            "#a855f7",  # Purple
            "#ec4899",  # Rose
        ]

        radius = 62.0
        circ = 2.0 * math.pi * radius  # ~389.56
        center_x = 95.0
        center_y = 115.0

        svg = [
            '<svg viewBox="0 0 460 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <!-- Background Donut Track -->',
            f'  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" stroke="var(--bg-surface-elevated)" stroke-width="20" />',
        ]

        # Draw donut slices
        accumulated_offset = 0.0
        for idx, (topic, qs, pct) in enumerate(slices_data):
            color = palette[idx % len(palette)]
            dash_len = (pct / 100.0) * circ
            dash_gap = circ - dash_len
            svg.append(
                f'  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" stroke="{color}" stroke-width="20" '
                f'stroke-dasharray="{dash_len:.2f} {dash_gap:.2f}" stroke-dashoffset="{-accumulated_offset:.2f}" '
                f'transform="rotate(-90 {center_x} {center_y})" />'
            )
            accumulated_offset += dash_len

        # Center summary
        svg.extend([
            f'  <text x="{center_x}" y="{center_y - 2}" font-size="24" font-weight="800" font-family="var(--font-mono)" fill="var(--text-primary)" text-anchor="middle">{total_qs}</text>',
            f'  <text x="{center_x}" y="{center_y + 16}" font-size="8.5" font-weight="700" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="middle" letter-spacing="1">TOTAL QS</text>',
        ])

        # Legend on the right side
        legend_start_y = 35.0
        row_height = 42.0
        for idx, (topic, qs, pct) in enumerate(slices_data):
            color = palette[idx % len(palette)]
            y = legend_start_y + idx * row_height
            clean_topic = topic[:22] + ".." if len(topic) > 22 else topic
            svg.extend([
                f'  <circle cx="205" cy="{y + 6}" r="5" fill="{color}" />',
                f'  <text x="218" y="{y + 10}" font-size="11" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">{clean_topic}</text>',
                f'  <text x="218" y="{y + 24}" font-size="9.5" font-family="var(--font-mono)" fill="var(--text-secondary)">{qs} Qs • {pct:.1f}% share</text>',
            ])

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def build_velocity_timeline_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG dual-axis timeline chart showing:
        - Primary Left Axis: Run Latency (duration in seconds) with smooth area gradient.
        - Secondary Right Axis: Question Count Velocity (questions answered per run).
        """
        all_runs = []
        for cid, chat in history.chats.items():
            for run in chat.get("runs", []):
                all_runs.append({
                    "run_id": run.get("run_id", "run"),
                    "timestamp": run.get("timestamp", ""),
                    "duration": float(run.get("duration_seconds", 0.0)),
                    "questions_count": int(run.get("questions_count", 0)),
                    "cid": cid,
                })

        all_runs.sort(key=lambda r: r.get("timestamp", ""))

        if not all_runs:
            return (
                '<svg viewBox="0 0 640 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">'
                '  <rect width="640" height="240" rx="8" fill="transparent" />'
                '  <text x="320" y="115" font-size="28" text-anchor="middle" fill="#64748b">📈</text>'
                '  <text x="320" y="145" font-size="13" font-weight="600" text-anchor="middle" fill="#94a3b8">No Velocity Timeline Data Yet</text>'
                '  <text x="320" y="165" font-size="11" text-anchor="middle" fill="#64748b">Run automation pipeline to record dual-axis velocity telemetry</text>'
                '</svg>'
            )

        recent_runs = all_runs[-10:]
        durations = [r["duration"] for r in recent_runs]
        q_counts = [r["questions_count"] for r in recent_runs]

        max_dur = max(durations + [5.0]) * 1.25
        max_q = max(q_counts + [2])

        left = 55.0
        right = 585.0
        top = 40.0
        bottom = 190.0
        chart_w = right - left
        chart_h = bottom - top

        svg = [
            '<svg viewBox="0 0 640 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="velDurGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#06b6d4" />',
            '      <stop offset="100%" stop-color="#6366f1" />',
            '    </linearGradient>',
            '    <linearGradient id="velAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="rgba(6, 182, 212, 0.35)" />',
            '      <stop offset="100%" stop-color="rgba(6, 182, 212, 0.0)" />',
            '    </linearGradient>',
            '    <linearGradient id="velBarGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="#34d399" />',
            '      <stop offset="100%" stop-color="#059669" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Legend -->',
            '  <g transform="translate(320, 14)">',
            '    <line x1="0" y1="6" x2="18" y2="6" stroke="#06b6d4" stroke-width="2.5" />',
            '    <circle cx="9" cy="6" r="3" fill="#06b6d4" />',
            '    <text x="24" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Duration (s)</text>',
            '    <rect x="130" y="0" width="12" height="12" rx="3" fill="url(#velBarGrad)" />',
            '    <text x="148" y="10" font-size="11" font-family="var(--font-family)" fill="var(--text-secondary)">Questions Velocity</text>',
            '  </g>',
        ]

        # Left Y-Axis Grid & Labels (Duration)
        for i in range(5):
            val = max_dur * (i / 4.0)
            y_pos = bottom - (i / 4.0) * chart_h
            svg.append(f'  <line x1="{left}" y1="{y_pos:.1f}" x2="{right}" y2="{y_pos:.1f}" stroke="var(--border-subtle)" stroke-width="1" />')
            svg.append(f'  <text x="{left - 8}" y="{y_pos + 3:.1f}" font-size="9" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="end">{val:.1f}s</text>')

        # Right Y-Axis Labels (Questions count)
        for i in range(5):
            val_q = int(round(max_q * (i / 4.0)))
            y_pos = bottom - (i / 4.0) * chart_h
            svg.append(f'  <text x="{right + 8}" y="{y_pos + 3:.1f}" font-size="9" font-family="var(--font-mono)" fill="#34d399" text-anchor="start">{val_q} Qs</text>')

        n = len(recent_runs)
        coords = []
        bar_w = min(16.0, (chart_w / max(1, n)) * 0.3)

        # Plot bars for questions velocity
        for i, r in enumerate(recent_runs):
            cx = left + (chart_w / 2.0) if n == 1 else left + (i / (n - 1)) * chart_w
            cy_dur = bottom - (r["duration"] / max_dur) * chart_h
            coords.append((cx, cy_dur, r))

            q_h = (r["questions_count"] / max(1, max_q)) * chart_h * 0.85
            q_x = cx - bar_w / 2
            q_y = bottom - q_h

            svg.append(f'  <rect x="{q_x:.1f}" y="{q_y:.1f}" width="{bar_w:.1f}" height="{q_h:.1f}" rx="2" fill="url(#velBarGrad)" opacity="0.85"><title>{r["run_id"]}: {r["questions_count"]} Questions</title></rect>')
            svg.append(f'  <text x="{cx:.1f}" y="{q_y - 4:.1f}" font-size="8.5" font-weight="700" font-family="var(--font-mono)" fill="#34d399" text-anchor="middle">{r["questions_count"]}Q</text>')

        # Draw Duration Area Polygon
        area_pts = [f"{coords[0][0]:.1f},{bottom:.1f}"]
        for cx, cy, _ in coords:
            area_pts.append(f"{cx:.1f},{cy:.1f}")
        area_pts.append(f"{coords[-1][0]:.1f},{bottom:.1f}")
        svg.append(f'  <polygon points="{" ".join(area_pts)}" fill="url(#velAreaGrad)" />')

        # Draw Duration Line
        line_d = " ".join([f"{'M' if idx == 0 else 'L'} {cx:.1f} {cy:.1f}" for idx, (cx, cy, _) in enumerate(coords)])
        svg.append(f'  <path d="{line_d}" fill="none" stroke="url(#velDurGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />')

        # Draw Duration Nodes & X Labels
        for idx, (cx, cy, r) in enumerate(coords):
            dur = r["duration"]
            run_lbl = f"R{idx + 1}"
            svg.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="var(--bg-primary)" stroke="#06b6d4" stroke-width="2"><title>{r["run_id"]}: {dur:.2f}s latency</title></circle>')
            svg.append(f'  <text x="{cx:.1f}" y="{bottom + 16:.1f}" font-size="9.5" font-weight="600" font-family="var(--font-mono)" fill="var(--text-secondary)" text-anchor="middle">{run_lbl}</text>')

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def build_productivity_gauge_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG speedometer/radial gauge showing Developer Productivity
        and Manual Time Saved (~30s per question automated vs actual script runtime).
        """
        import math
        total_qs = history.total_questions_answered
        auto_sec = history.total_runtime_seconds
        manual_sec = total_qs * 30.0
        saved_sec = max(0.0, manual_sec - auto_sec)

        if total_qs > 0 and auto_sec > 0:
            velocity_mult = max(1.0, manual_sec / auto_sec)
        else:
            velocity_mult = 12.5

        if saved_sec >= 3600.0:
            saved_str = f"{saved_sec / 3600.0:.1f} hrs"
        elif saved_sec >= 60.0:
            m = int(saved_sec // 60)
            s = int(saved_sec % 60)
            saved_str = f"{m}m {s}s"
        else:
            saved_str = f"{saved_sec:.1f}s"

        cx, cy, r = 150.0, 120.0, 72.0
        arc_len = 2.0 * math.pi * r * (220.0 / 360.0)
        ratio = min(1.0, saved_sec / 600.0) if saved_sec > 0 else 0.85
        offset = arc_len * (1.0 - ratio)

        svg = [
            '<svg viewBox="0 0 460 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="prodGaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
            '      <stop offset="0%" stop-color="#10b981" />',
            '      <stop offset="50%" stop-color="#06b6d4" />',
            '      <stop offset="100%" stop-color="#6366f1" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Background Arc Track (220 deg) -->',
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--bg-surface-elevated)" stroke-width="16" stroke-linecap="round" stroke-dasharray="{arc_len:.2f} 400" transform="rotate(160 {cx} {cy})" />',
            '  <!-- Progress Arc -->',
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#prodGaugeGrad)" stroke-width="16" stroke-linecap="round" stroke-dasharray="{arc_len:.2f} 400" stroke-dashoffset="{offset:.2f}" transform="rotate(160 {cx} {cy})" />',
            '  <!-- Center Readout -->',
            f'  <text x="{cx}" y="{cy - 2}" font-size="28" font-weight="800" font-family="var(--font-mono)" fill="#10b981" text-anchor="middle">{saved_str}</text>',
            f'  <text x="{cx}" y="{cy + 18}" font-size="8.5" font-weight="700" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="middle" letter-spacing="1">MANUAL TIME SAVED</text>',
            '  <!-- Velocity Pill -->',
            f'  <rect x="{cx - 68}" y="{cy + 34}" width="136" height="22" rx="11" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" stroke-width="1" />',
            f'  <text x="{cx}" y="{cy + 49}" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#10b981" text-anchor="middle">⚡ {velocity_mult:.1f}x Faster</text>',
            '  <!-- Right Side Summary Statistics -->',
            '  <g transform="translate(260, 45)">',
            '    <text x="0" y="0" font-size="12" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">Productivity ROI</text>',
            '    <line x1="0" y1="10" x2="180" y2="10" stroke="var(--border-subtle)" stroke-width="1" />',
            '    <text x="0" y="32" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)">Estimated Human Time:</text>',
            f'    <text x="180" y="32" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="var(--text-primary)" text-anchor="end">{manual_sec:.1f}s</text>',
            '    <text x="0" y="56" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)">Script Automated Time:</text>',
            f'    <text x="180" y="56" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#06b6d4" text-anchor="end">{auto_sec:.1f}s</text>',
            '    <text x="0" y="80" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)">Efficiency Velocity:</text>',
            f'    <text x="180" y="80" font-size="10" font-weight="700" font-family="var(--font-mono)" fill="#10b981" text-anchor="end">~{velocity_mult:.1f}x</text>',
            '    <text x="0" y="104" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)">Standard Baseline:</text>',
            '    <text x="180" y="104" font-size="10" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="end">30s / question</text>',
            '    <rect x="0" y="122" width="180" height="26" rx="6" fill="var(--bg-surface-elevated)" />',
            f'    <text x="90" y="139" font-size="9.5" font-weight="700" font-family="var(--font-family)" fill="var(--text-secondary)" text-anchor="middle">✓ {total_qs} Questions Automated</text>',
            '  </g>',
            '</svg>',
        ]
        return "\n".join(svg)

    @staticmethod
    def build_time_heatmap_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG hourly activity heatmap and 4-quarter day matrix
        showing when automation runs occur across 24 hours.
        """
        hours = [0] * 24
        quarter_morning = 0    # 06:00 - 12:00
        quarter_afternoon = 0  # 12:00 - 18:00
        quarter_evening = 0    # 18:00 - 24:00
        quarter_night = 0      # 00:00 - 06:00

        for chat in history.chats.values():
            for run in chat.get("runs", []):
                ts = run.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        h = dt.hour
                        if 0 <= h < 24:
                            hours[h] += 1
                            if 6 <= h < 12:
                                quarter_morning += 1
                            elif 12 <= h < 18:
                                quarter_afternoon += 1
                            elif 18 <= h < 24:
                                quarter_evening += 1
                            else:
                                quarter_night += 1
                    except Exception:
                        pass

        svg = [
            '<svg viewBox="0 0 640 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="heatCellGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
            '      <stop offset="0%" stop-color="#818cf8" />',
            '      <stop offset="100%" stop-color="#4f46e5" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Heatmap Scale Legend -->',
            '  <g transform="translate(420, 14)">',
            '    <text x="0" y="10" font-size="10" font-family="var(--font-mono)" fill="var(--text-muted)">Activity Intensity:</text>',
            '    <rect x="110" y="1" width="10" height="10" rx="2" fill="var(--bg-surface-elevated)" />',
            '    <rect x="125" y="1" width="10" height="10" rx="2" fill="rgba(99, 102, 241, 0.4)" />',
            '    <rect x="140" y="1" width="10" height="10" rx="2" fill="rgba(99, 102, 241, 0.75)" />',
            '    <rect x="155" y="1" width="10" height="10" rx="2" fill="#6366f1" />',
            '    <text x="175" y="10" font-size="10" font-family="var(--font-mono)" fill="var(--text-secondary)">High</text>',
            '  </g>',
            '  <!-- 24 Hourly Grid Blocks (00h to 23h) -->',
        ]

        start_x = 34.0
        cell_w = 20.0
        cell_gap = 4.0
        y_pos = 45.0
        cell_h = 44.0

        for h in range(24):
            count = hours[h]
            cx = start_x + h * (cell_w + cell_gap)

            if count == 0:
                fill_color = "var(--bg-surface-elevated)"
                stroke_color = "var(--border-subtle)"
            elif count <= 2:
                fill_color = "rgba(99, 102, 241, 0.4)"
                stroke_color = "rgba(99, 102, 241, 0.6)"
            elif count <= 5:
                fill_color = "rgba(99, 102, 241, 0.75)"
                stroke_color = "#6366f1"
            else:
                fill_color = "#6366f1"
                stroke_color = "#818cf8"

            svg.extend([
                f'  <rect x="{cx:.1f}" y="{y_pos:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" rx="4" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1">',
                f'    <title>Hour {h:02d}:00: {count} run(s)</title>',
                f'  </rect>',
            ])
            if count > 0:
                svg.append(f'  <text x="{cx + cell_w/2:.1f}" y="{y_pos + cell_h/2 + 4:.1f}" font-size="9" font-weight="700" font-family="var(--font-mono)" fill="#ffffff" text-anchor="middle">{count}</text>')

            if h % 4 == 0 or h == 23:
                svg.append(f'  <text x="{cx + cell_w/2:.1f}" y="{y_pos + cell_h + 16:.1f}" font-size="9" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="middle">{h:02d}h</text>')

        quarters = [
            ("🌅 Morning", "06:00 - 12:00", quarter_morning, "#f59e0b"),
            ("☀️ Afternoon", "12:00 - 18:00", quarter_afternoon, "#06b6d4"),
            ("🌆 Evening", "18:00 - 24:00", quarter_evening, "#6366f1"),
            ("🌙 Night", "00:00 - 06:00", quarter_night, "#a855f7"),
        ]

        card_y = 145.0
        card_w = 135.0
        card_h = 70.0
        card_gap = 12.0
        q_start_x = 34.0

        for idx, (title, timerange, count, color) in enumerate(quarters):
            qx = q_start_x + idx * (card_w + card_gap)
            svg.extend([
                f'  <g transform="translate({qx:.1f}, {card_y:.1f})">',
                f'    <rect width="{card_w:.1f}" height="{card_h:.1f}" rx="8" fill="var(--bg-surface-elevated)" stroke="var(--border-subtle)" stroke-width="1" />',
                f'    <rect x="0" y="0" width="{card_w:.1f}" height="3" rx="1.5" fill="{color}" />',
                f'    <text x="12" y="24" font-size="11" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">{title}</text>',
                f'    <text x="12" y="40" font-size="8.5" font-family="var(--font-mono)" fill="var(--text-muted)">{timerange}</text>',
                f'    <text x="{card_w - 12:.1f}" y="48" font-size="18" font-weight="800" font-family="var(--font-mono)" fill="{color}" text-anchor="end">{count}</text>',
                f'    <text x="{card_w - 12:.1f}" y="60" font-size="8" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="end">runs</text>',
                f'  </g>',
            ])

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def build_option_breakdown_svg(history: AutomationHistory) -> str:
        """
        Generate pure inline vector SVG showing the Option Selection Distribution Breakdown
        (Option 1 Recommended vs Option 2 vs Others) with horizontal stacked progress.
        """
        opt1_count = 0
        opt2_count = 0
        other_count = 0

        for chat in history.chats.values():
            for run in chat.get("runs", []):
                for q in run.get("questions", []):
                    idx = q.get("selected_option_index")
                    if idx == 1 or q.get("is_recommended", False):
                        opt1_count += 1
                    elif idx == 2:
                        opt2_count += 1
                    elif idx is not None:
                        other_count += 1

        total = opt1_count + opt2_count + other_count
        if total == 0:
            p1, p2, po = 100.0, 0.0, 0.0
            display_total = 0
        else:
            p1 = (opt1_count / total) * 100.0
            p2 = (opt2_count / total) * 100.0
            po = (other_count / total) * 100.0
            display_total = total

        bar_w = 390.0
        w1 = max(4.0, (p1 / 100.0) * bar_w) if p1 > 0 else 0.0
        w2 = max(4.0, (p2 / 100.0) * bar_w) if p2 > 0 else 0.0
        wo = max(4.0, (po / 100.0) * bar_w) if po > 0 else 0.0

        svg = [
            '<svg viewBox="0 0 460 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg" style="display:block;">',
            '  <defs>',
            '    <linearGradient id="opt1Grad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#10b981" />',
            '      <stop offset="100%" stop-color="#059669" />',
            '    </linearGradient>',
            '    <linearGradient id="opt2Grad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#6366f1" />',
            '      <stop offset="100%" stop-color="#4f46e5" />',
            '    </linearGradient>',
            '    <linearGradient id="optOtherGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#f59e0b" />',
            '      <stop offset="100%" stop-color="#d97706" />',
            '    </linearGradient>',
            '  </defs>',
            '  <!-- Header Summary Metric -->',
            '  <g transform="translate(35, 30)">',
            f'    <text x="0" y="0" font-size="28" font-weight="800" font-family="var(--font-mono)" fill="#10b981">{p1:.1f}%</text>',
            '    <text x="0" y="18" font-size="10.5" font-weight="700" font-family="var(--font-family)" fill="var(--text-secondary)">Option 1 Recommended Adherence Rate</text>',
            f'    <text x="390" y="0" font-size="14" font-weight="700" font-family="var(--font-mono)" fill="var(--text-primary)" text-anchor="end">{display_total} Total</text>',
            '    <text x="390" y="18" font-size="9" font-family="var(--font-mono)" fill="var(--text-muted)" text-anchor="end">Questions Evaluated</text>',
            '  </g>',
            '  <!-- Stacked Horizontal Progress Bar -->',
            '  <g transform="translate(35, 75)">',
            f'    <rect width="{bar_w}" height="20" rx="10" fill="var(--bg-surface-elevated)" stroke="var(--border-subtle)" stroke-width="1" />',
        ]

        cur_x = 0.0
        if w1 > 0:
            svg.append(f'    <rect x="{cur_x:.1f}" y="0" width="{w1:.1f}" height="20" rx="10" fill="url(#opt1Grad)"><title>Option 1: {opt1_count} Qs ({p1:.1f}%)</title></rect>')
            cur_x += w1
        if w2 > 0:
            svg.append(f'    <rect x="{cur_x:.1f}" y="0" width="{w2:.1f}" height="20" rx="6" fill="url(#opt2Grad)"><title>Option 2: {opt2_count} Qs ({p2:.1f}%)</title></rect>')
            cur_x += w2
        if wo > 0:
            svg.append(f'    <rect x="{cur_x:.1f}" y="0" width="{wo:.1f}" height="20" rx="6" fill="url(#optOtherGrad)"><title>Others: {other_count} Qs ({po:.1f}%)</title></rect>')

        svg.append('  </g>')

        options_data = [
            ("✓ Option 1 (Recommended)", opt1_count, p1, "#10b981", "Autonomous Selection Priority"),
            ("• Option 2 (Alternate)", opt2_count, p2, "#818cf8", "Secondary Choice Selection"),
            ("• Option 3+ / Others", other_count, po, "#fbbf24", "Custom / Third Option Choice"),
        ]

        list_y = 120.0
        row_h = 34.0
        for idx, (label, count, pct, color, desc) in enumerate(options_data):
            y = list_y + idx * row_h
            svg.extend([
                f'  <g transform="translate(35, {y:.1f})">',
                f'    <rect width="390" height="28" rx="6" fill="var(--bg-surface-elevated)" stroke="var(--border-subtle)" stroke-width="0.8" />',
                f'    <circle cx="14" cy="14" r="5" fill="{color}" />',
                f'    <text x="28" y="18" font-size="10.5" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">{label}</text>',
                f'    <text x="210" y="18" font-size="9" font-family="var(--font-family)" fill="var(--text-muted)">{desc}</text>',
                f'    <text x="375" y="18" font-size="10.5" font-weight="700" font-family="var(--font-mono)" fill="{color}" text-anchor="end">{count} Qs ({pct:.1f}%)</text>',
                f'  </g>',
            ])

        svg.append('</svg>')
        return "\n".join(svg)

    # ========================================================================
    # Visual Dashboard Generation (Department 04 UI/UX Design System)
    # ========================================================================

    def generate_html_dashboard(self, history: Optional[AutomationHistory] = None) -> Path:
        logger.info("[STEP 4.15] [DASHBOARD_GEN_START] Generating HTML dashboard in %s", self.dashboard_file)
        logger.info("[STEP 4.16] [TOPOLOGY_SVG_BUILD] Generating 5-Step Pipeline Topology SVG")
        logger.info("[STEP 4.17] [PIPELINE_SVG_BUILD] Generating Pipeline Health Bus SVG")
        logger.info("[STEP 4.18] [CHARTS_RENDER] Compiling SVG telemetry charts")
        """
        Generate a self-contained, modern, responsive HTML dashboard in reports/dashboard.html.
        Zero external CSS/JS dependencies. Adheres to Department 04 design tokens.
        """
        if history is None:
            history = self.load_history()

        history_dict = history.to_dict()
        history_json_str = json.dumps(history_dict, ensure_ascii=False)

        # Formatting helpers
        total_runs = history.total_pipeline_runs
        total_questions = history.total_questions_answered
        total_chats = max(history.total_unique_chats, len(history.chats))
        total_seconds = history.total_runtime_seconds

        if total_seconds >= 60.0:
            mins = int(total_seconds // 60)
            secs = int(total_seconds % 60)
            runtime_fmt = f"{mins}m {secs}s"
        else:
            runtime_fmt = f"{total_seconds:.1f}s"

        # KPI 5: Mean Run Latency
        avg_duration = (total_seconds / total_runs) if total_runs > 0 else 0.0
        avg_duration_fmt = f"{avg_duration:.1f}s"

        # KPI 6: Qs / Run Density
        qs_density = (total_questions / total_runs) if total_runs > 0 else 0.0
        qs_density_fmt = f"{qs_density:.1f}"

        # KPI 7: Questions per Chat Depth
        avg_qs_per_chat = (total_questions / total_chats) if total_chats > 0 else 0.0
        avg_qs_per_chat_fmt = f"{avg_qs_per_chat:.1f}"

        # KPI 8: Execution Speed (Sec / Question Resolved)
        sec_per_question = (total_seconds / total_questions) if total_questions > 0 else 0.0
        sec_per_question_fmt = f"{sec_per_question:.1f}s"

        # Recommendation Rate (Option 1 Adherence)
        total_qs_checked = 0
        recommended_qs_matched = 0
        for chat in history.chats.values():
            for run in chat.get("runs", []):
                for q in run.get("questions", []):
                    total_qs_checked += 1
                    if q.get("is_recommended", True) or q.get("selected_option_index") == 1:
                        recommended_qs_matched += 1

        recommendation_rate = (
            (recommended_qs_matched / total_qs_checked * 100.0)
            if total_qs_checked > 0 else 100.0
        )
        recommendation_rate_fmt = f"{int(round(recommendation_rate))}%"

        # Chat-specific summary stats
        avg_runs_per_chat = (total_runs / total_chats) if total_chats > 0 else 0.0

        # Chat options for filter dropdown
        chat_options = []
        for cid, chat in history.chats.items():
            topic = chat.get("topic_summary") or "Untitled Conversation"
            trunc_topic = topic[:32] + ".." if len(topic) > 32 else topic
            short_cid = cid[:8] + ".." if len(cid) > 8 else cid
            chat_options.append(f'<option value="{cid}">{trunc_topic} ({short_cid})</option>')
        chat_options_html = "\n            ".join(chat_options)

        # SVG Visualizations
        topology_svg = self.build_topology_svg()
        pipeline_svg = topology_svg
        velocity_svg = self.build_velocity_timeline_svg(history)
        productivity_svg = self.build_productivity_gauge_svg(history)
        heatmap_svg = self.build_time_heatmap_svg(history)
        option_breakdown_svg = self.build_option_breakdown_svg(history)
        distribution_svg = self.build_chat_distribution_svg(history)
        latency_trend_svg = self.build_latency_trend_svg(history)
        topic_share_svg = self.build_topic_share_svg(history)
        donut_svg = self.build_donut_gauge_svg(recommendation_rate)

        last_updated_display = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Load System Runtime Configuration (step_9_complete_automation/config.json)
        runtime_cfg = self.load_runtime_config()
        runtime_config_json_str = json.dumps(runtime_cfg, indent=2, ensure_ascii=False)

        cfg_mode_val = str(runtime_cfg.get("mode", "production")).lower()
        is_prod = (cfg_mode_val == "production")
        mode_prod_active_class = "active" if is_prod else ""
        mode_test_active_class = "active" if not is_prod else ""
        banner_prod_active_class = mode_prod_active_class
        banner_test_active_class = mode_test_active_class
        card_prod_active_class = "active-mode-card" if is_prod else ""
        card_test_active_class = "active-mode-card" if not is_prod else ""
        tab_modes_badge_text = "Prod" if is_prod else "Test"
        tab_modes_badge_class = "tab-badge-prod" if is_prod else "tab-badge-test"
        header_badge_bg = 'rgba(16, 185, 129, 0.15)' if is_prod else 'rgba(245, 158, 11, 0.15)'
        header_badge_color = '#34d399' if is_prod else '#fbbf24'
        header_badge_border = 'rgba(16, 185, 129, 0.35)' if is_prod else 'rgba(245, 158, 11, 0.35)'
        header_badge_icon = '⚡' if is_prod else '🧪'
        header_badge_text = 'LIVE' if is_prod else 'TEST'
        header_badge_title = 'Operating in Continuous Live Mode (Continuous Loop) • Click to toggle to TEST' if is_prod else 'Operating in Single-Run Test Mode (Auto-Stop on Completion) • Click to toggle to LIVE'

        enabled_steps = runtime_cfg.get("enabled_steps", {})
        step1_checked = "checked" if enabled_steps.get("step1_find_and_focus", True) else ""
        step2_checked = "checked" if enabled_steps.get("step2_gui_chat_select", True) else ""
        step3_checked = "checked" if enabled_steps.get("step3_keyboard_automation", True) else ""
        step4_checked = "checked" if enabled_steps.get("step4_reporting", True) else ""

        timing_cfg = runtime_cfg.get("timing", {})
        step0_poll_prod = timing_cfg.get("step0_poll_interval_prod_seconds", 300.0)
        step0_poll_test = timing_cfg.get("step0_poll_interval_test_seconds", 10.0)
        settle_delay = timing_cfg.get("settle_delay_between_steps_seconds", 0.8)
        step4_delay = timing_cfg.get("step4_user_activity_delay_seconds", 10.0)
        step4_poll = timing_cfg.get("step4_poll_interval_seconds", 0.1)
        step1_focus = timing_cfg.get("step1_window_focus_delay_seconds", 0.2)
        step2_dom_settle = timing_cfg.get("step2_dom_click_settle_delay_seconds", 0.3)
        step3_countdown = timing_cfg.get("step3_countdown_seconds", 3.0)
        step3_hold_ms = timing_cfg.get("step3_key_hold_delay_ms", 50.0)
        step3_post_ms = timing_cfg.get("step3_post_keypress_delay_ms", 250.0)
        step3_inter_q_ms = timing_cfg.get("step3_inter_question_delay_ms", 500.0)
        step3_round_ms = timing_cfg.get("step3_round_completion_pause_ms", 1000.0)

        antigravity_cfg = runtime_cfg.get("antigravity", {})
        require_grill_me_checked = "checked" if antigravity_cfg.get("require_grill_me", True) else ""
        active_hours = antigravity_cfg.get("active_hours", 12.0)

        logging_cfg = runtime_cfg.get("logging", {})
        verbose_checked = "checked" if logging_cfg.get("verbose", True) else ""
        log_file_val = logging_cfg.get("log_file", "complete_automation.log")

        html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoSelect Antigravity Dashboard</title>
  <style>
    :root {{
      --bg-primary: #0b0f17;
      --bg-surface: #131926;
      --bg-surface-elevated: #1a2336;
      --bg-surface-highlight: #232e47;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.4);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-indigo: #6366f1;
      --accent-indigo-glow: rgba(99, 102, 241, 0.25);
      --accent-emerald: #10b981;
      --accent-emerald-bg: rgba(16, 185, 129, 0.12);
      --accent-emerald-border: #059669;
      --accent-cyan: #06b6d4;
      --accent-purple: #a855f7;
      --accent-amber: #f59e0b;
      --accent-rose: #ec4899;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    [data-theme="light"] {{
      --bg-primary: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #f1f5f9;
      --bg-surface-highlight: #e2e8f0;
      --border-subtle: rgba(0, 0, 0, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-muted: #94a3b8;
      --accent-emerald-bg: rgba(16, 185, 129, 0.1);
      --accent-indigo-glow: rgba(99, 102, 241, 0.15);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-primary);
      color: var(--text-primary);
      font-family: var(--font-family);
      line-height: 1.5;
      padding: 24px 20px 48px;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.3s ease, color 0.3s ease;
    }}

    .container {{
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
    }}

    /* Header */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 24px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }}

    .header-left {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .logo-badge {{
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--accent-indigo), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      box-shadow: 0 0 16px var(--accent-indigo-glow);
    }}

    .header-titles h1 {{
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}

    .header-titles p {{
      font-size: 0.85rem;
      color: var(--text-secondary);
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: nowrap;
      flex-shrink: 0;
    }}

    @media (max-width: 768px) {{
      header {{
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;
      }}
      .header-actions {{
        flex-wrap: wrap;
        width: 100%;
      }}
    }}

    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      transition: all 0.25s ease;
      white-space: nowrap;
    }}

    .status-pill::before {{
      display: none;
    }}

    .status-pill.status-idle {{
      background: rgba(148, 163, 184, 0.12);
      color: var(--text-muted, #94a3b8);
      border: 1px solid rgba(148, 163, 184, 0.3);
    }}

    .status-pill.status-idle::before {{
      background: #94a3b8;
      box-shadow: none;
      animation: none;
    }}

    .status-pill.status-paused {{
      background: rgba(245, 158, 11, 0.12);
      color: #f59e0b;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }}

    .status-pill.status-paused::before {{
      background: #f59e0b;
      box-shadow: 0 0 8px #f59e0b;
      animation: pulse 1.5s infinite;
    }}

    .status-pill.status-active {{
      background: var(--accent-emerald-bg, rgba(16, 185, 129, 0.12));
      color: var(--accent-emerald, #10b981);
      border: 1px solid var(--accent-emerald-border, #059669);
    }}

    .status-pill.status-active::before {{
      background: var(--accent-emerald, #10b981);
      box-shadow: 0 0 8px var(--accent-emerald, #10b981);
      animation: pulse 2s infinite;
    }}

    .status-pill.status-bridge-online {{
      background: var(--accent-emerald-bg, rgba(16, 185, 129, 0.12));
      color: var(--accent-emerald, #10b981);
      border: 1px solid var(--accent-emerald-border, #059669);
    }}

    .status-pill.status-bridge-online::before {{
      background: var(--accent-emerald, #10b981);
      box-shadow: 0 0 8px var(--accent-emerald, #10b981);
      animation: pulse 2s infinite;
    }}

    .status-pill.status-bridge-offline {{
      background: rgba(239, 68, 68, 0.12);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.35);
    }}

    .status-pill.status-mode-badge {{
      cursor: pointer;
      user-select: none;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      font-weight: 700;
    }}
    .status-pill.status-mode-badge:hover {{
      filter: brightness(1.25);
      transform: translateY(-1px);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
    }}

    .status-pill.status-bridge-offline::before {{
      background: #ef4444;
      box-shadow: none;
      animation: none;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.4; }}
    }}

    /* Dynamic Start/Stop Automation Header Button (Dept 04 Aesthetic) */
    .btn-automation-toggle {{
      font-weight: 600;
      border-radius: var(--radius-md);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 7px 13px;
      font-size: 0.85rem;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    .btn-automation-toggle.state-stopped {{
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent-emerald, #10b981);
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}

    .btn-automation-toggle.state-stopped:hover {{
      background: rgba(16, 185, 129, 0.22);
      border-color: var(--accent-emerald, #10b981);
      box-shadow: 0 0 14px rgba(16, 185, 129, 0.3);
      transform: translateY(-1px);
    }}

    .btn-automation-toggle.state-running {{
      background: rgba(244, 63, 94, 0.12);
      color: var(--accent-rose, #f43f5e);
      border: 1px solid rgba(244, 63, 94, 0.4);
      animation: automationPulse 2.5s infinite;
    }}

    .btn-automation-toggle.state-running:hover {{
      background: rgba(244, 63, 94, 0.22);
      border-color: var(--accent-rose, #f43f5e);
      box-shadow: 0 0 14px rgba(244, 63, 94, 0.35);
      transform: translateY(-1px);
    }}

    @keyframes automationPulse {{
      0%, 100% {{ box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.25); }}
      50% {{ box-shadow: 0 0 12px 2px rgba(244, 63, 94, 0.35); }}
    }}

    .btn {{
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
      padding: 7px 12px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    .btn-modern-switch {{
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
      border: 1px solid rgba(99, 102, 241, 0.5);
      color: #c7d2fe;
      font-weight: 600;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .btn-modern-switch:hover {{
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.35), rgba(168, 85, 247, 0.35));
      border-color: #818cf8;
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    }}

    .btn:hover {{
      background: var(--bg-surface-highlight);
      border-color: var(--accent-indigo);
    }}

    /* Horizontal Tab Navigation (Department 04 Standard - 3 Intuitive Tabs) */
    .tab-nav {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      margin-bottom: 24px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
      position: relative;
    }}

    .tab-btn {{
      background: transparent;
      color: var(--text-secondary);
      border: 1px solid transparent;
      padding: 10px 22px;
      border-radius: var(--radius-md);
      font-size: 0.92rem;
      font-weight: 600;
      font-family: var(--font-family);
      cursor: pointer;
      transition: var(--transition);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      position: relative;
      user-select: none;
      outline: none;
    }}

    .tab-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-elevated);
    }}

    .tab-btn:focus-visible {{
      box-shadow: 0 0 0 2px var(--accent-indigo);
    }}

    .tab-btn.active {{
      color: #ffffff;
      background: var(--accent-indigo);
      border-color: var(--accent-indigo);
      box-shadow: 0 2px 12px var(--accent-indigo-glow);
    }}

    .tab-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.2);
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 700;
      font-family: var(--font-mono);
      padding: 2px 8px;
      border-radius: 9999px;
      line-height: 1;
      margin-left: 2px;
    }}

    .tab-btn:not(.active) .tab-badge {{
      background: var(--bg-surface-highlight);
      color: var(--text-secondary);
    }}

    .tab-badge.tab-badge-test,
    .tab-btn:not(.active) .tab-badge.tab-badge-test {{
      background: rgba(245, 158, 11, 0.16);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.35);
    }}

    .tab-badge.tab-badge-prod,
    .tab-btn:not(.active) .tab-badge.tab-badge-prod {{
      background: rgba(16, 185, 129, 0.16);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.35);
    }}

    .tab-btn.active .tab-badge.tab-badge-test {{
      background: #f59e0b;
      color: #0f172a;
      border-color: #fbbf24;
    }}

    .tab-btn.active .tab-badge.tab-badge-prod {{
      background: #10b981;
      color: #0f172a;
      border-color: #34d399;
    }}

    /* ==========================================================================
       Execution Mode Lifecycle Banner & Callouts (Dept 04 & 05 Standards)
       ========================================================================== */
    .mode-lifecycle-banner {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-top: 2px solid var(--accent-indigo);
      border-bottom: 2px solid var(--accent-indigo);
      border-radius: var(--radius-lg);
      padding: 18px 22px;
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
      transition: var(--transition);
      position: relative;
    }}

    .mode-lifecycle-banner:hover {{
      border-top-color: #818cf8;
      border-bottom-color: #818cf8;
      box-shadow: 0 6px 24px rgba(99, 102, 241, 0.15);
    }}

    .mode-lifecycle-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .mode-lifecycle-title-group {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .mode-lifecycle-title-group .title-icon {{
      font-size: 1.25rem;
      line-height: 1;
    }}

    .mode-lifecycle-title-group .title-main {{
      font-size: 1.02rem;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }}

    .mode-lifecycle-title-group .title-sep {{
      color: var(--text-muted);
      font-weight: 400;
    }}

    .mode-lifecycle-title-group .title-sub {{
      font-size: 0.86rem;
      font-weight: 600;
      color: var(--text-secondary);
    }}

    .banner-mode-controls {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .banner-controls-label {{
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .banner-mode-switcher {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: var(--bg-surface-elevated);
      padding: 4px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    .banner-mode-btn {{
      padding: 7px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      font-family: var(--font-family);
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-secondary);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: var(--transition);
      outline: none;
    }}

    .banner-mode-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-highlight);
    }}

    .banner-mode-btn:focus-visible {{
      box-shadow: 0 0 0 2px var(--accent-indigo);
    }}

    .banner-mode-btn.active {{
      background: var(--accent-indigo);
      color: #ffffff;
      border-color: var(--accent-indigo);
      box-shadow: 0 2px 10px var(--accent-indigo-glow);
    }}

    .banner-mode-btn[data-mode="production"].active {{
      background: #059669;
      border-color: #059669;
      box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
    }}

    .banner-mode-btn[data-mode="test"].active {{
      background: #d97706;
      border-color: #d97706;
      box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
    }}

    .banner-mode-indicator {{
      font-size: 0.72rem;
      padding: 1px 6px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.2);
      font-family: var(--font-mono);
    }}

    .mode-lifecycle-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }}

    .lifecycle-card {{
      background: var(--bg-surface-elevated);
      border: 1.5px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      cursor: pointer;
      transition: var(--transition);
      position: relative;
      outline: none;
    }}

    .lifecycle-card:hover {{
      border-color: var(--border-accent);
      background: var(--bg-surface-highlight);
      transform: translateY(-1px);
    }}

    .lifecycle-card:focus-visible {{
      box-shadow: 0 0 0 2px var(--accent-indigo);
    }}

    .lifecycle-card.active-mode-card {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 16px var(--accent-indigo-glow);
      background: var(--bg-surface-highlight);
    }}

    .lifecycle-card.card-test.active-mode-card {{
      border-color: var(--accent-amber);
      box-shadow: 0 0 16px rgba(245, 158, 11, 0.25);
    }}

    .lifecycle-card.card-production.active-mode-card {{
      border-color: var(--accent-emerald);
      box-shadow: 0 0 16px rgba(16, 185, 129, 0.25);
    }}

    .lifecycle-card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .lifecycle-card-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-primary);
    }}

    .lifecycle-card-title .card-icon {{
      font-size: 1.2rem;
      line-height: 1;
    }}

    .lifecycle-card-title .card-title-hindi {{
      font-size: 0.82rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-left: 4px;
    }}

    .lifecycle-card-badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.74rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 9999px;
      white-space: nowrap;
    }}

    .badge-test-mode {{
      background: rgba(245, 158, 11, 0.14);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }}

    .badge-prod-mode {{
      background: rgba(16, 185, 129, 0.14);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}

    .lifecycle-card-desc {{
      font-size: 0.85rem;
      line-height: 1.55;
      color: var(--text-secondary);
    }}

    .lifecycle-card-desc strong {{
      color: var(--text-primary);
    }}

    .lifecycle-card-features {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 2px;
    }}

    .lifecycle-feature-tag {{
      font-size: 0.74rem;
      font-family: var(--font-mono);
      background: var(--bg-surface);
      padding: 4px 9px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}

    .active-mode-card .lifecycle-feature-tag {{
      color: var(--text-primary);
      border-color: rgba(99, 102, 241, 0.35);
      background: var(--bg-surface-elevated);
    }}

    /* Configuration Tab Mode Lifecycle Callout Block */
    .mode-lifecycle-divider {{
      border: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--border-accent), transparent);
      margin: 18px 0;
    }}

    .mode-lifecycle-callout {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-left: 4px solid var(--accent-indigo);
      border-radius: var(--radius-md);
      padding: 16px 18px;
    }}

    .mode-lifecycle-callout-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.92rem;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 12px;
    }}

    .mode-lifecycle-callout-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .mode-callout-item {{
      background: var(--bg-surface);
      padding: 12px 14px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .mode-callout-item-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .mode-callout-item-title {{
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .mode-callout-item-desc {{
      font-size: 0.81rem;
      line-height: 1.5;
      color: var(--text-secondary);
    }}

    .mode-callout-item-desc strong {{
      color: var(--text-primary);
    }}

    @media (max-width: 768px) {{
      .mode-lifecycle-grid,
      .mode-lifecycle-callout-grid {{
        grid-template-columns: 1fr;
      }}
      .mode-lifecycle-header {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .banner-mode-controls {{
        width: 100%;
        justify-content: space-between;
      }}
      .modes-hero-header {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .modes-hero-actions {{
        width: 100%;
        justify-content: flex-start;
      }}
      .modes-switcher-bar {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .modes-segmented-group {{
        width: 100%;
        display: flex;
        justify-content: stretch;
      }}
      .modes-segmented-group .banner-mode-btn {{
        flex: 1;
        justify-content: center;
      }}
    }}

    /* Mode Switch Dedicated Tab Styles (Dept 04 & 05 Standards) */
    .modes-panel-container {{
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    .modes-hero-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-top: 3px solid var(--accent-indigo);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
      transition: var(--transition);
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}

    .modes-hero-card:hover {{
      border-top-color: #818cf8;
      box-shadow: 0 6px 24px rgba(99, 102, 241, 0.15);
    }}

    .modes-hero-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .modes-title-group {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .modes-hero-icon {{
      font-size: 2rem;
      line-height: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}

    .modes-hero-title {{
      font-size: 1.22rem;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.015em;
      margin: 0;
    }}

    .modes-hero-subtitle {{
      font-size: 0.88rem;
      color: var(--text-secondary);
      margin: 4px 0 0 0;
      line-height: 1.45;
    }}

    .modes-hero-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .modes-process-control-group {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: var(--bg-surface-elevated);
      padding: 6px 12px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    .modes-switcher-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
      background: var(--bg-surface-elevated);
      padding: 12px 18px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    .modes-switcher-label {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.84rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .modes-switcher-label .switcher-dot {{
      color: var(--accent-indigo);
      font-size: 0.9rem;
    }}

    .modes-segmented-group {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-surface);
      padding: 4px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    /* Comparison Card & Table */
    .modes-comparison-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 22px 24px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .modes-comparison-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .modes-comparison-title-wrap {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .comparison-icon {{
      font-size: 1.4rem;
      line-height: 1;
    }}

    .comparison-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0;
    }}

    .comparison-subtitle {{
      font-size: 0.82rem;
      color: var(--text-secondary);
      margin: 3px 0 0 0;
    }}

    .modes-comparison-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
      text-align: left;
    }}

    .modes-comparison-table th {{
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      font-weight: 700;
      padding: 11px 14px;
      border-bottom: 1.5px solid var(--border-subtle);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .modes-comparison-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      line-height: 1.5;
    }}

    .modes-comparison-table tr:hover td {{
      background: var(--bg-surface-highlight);
    }}

    .modes-comparison-table td code {{
      font-family: var(--font-mono);
      font-size: 0.8rem;
      background: var(--bg-surface-elevated);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
    }}

    /* Tab Panels */
    .tab-panel {{
      display: none;
      animation: fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .tab-panel.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{
        opacity: 0;
        transform: translateY(4px);
      }}
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}

    /* 8 High-Level KPIs in Exactly Two Balanced Rows (4 per Row) */
    .metrics-grid-2rows {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }}

    @media (max-width: 992px) {{
      .metrics-grid-2rows {{
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
      }}
    }}

    @media (max-width: 520px) {{
      .metrics-grid-2rows {{
        grid-template-columns: 1fr;
        gap: 10px;
      }}
    }}

    /* Fallback compatibility for single-row wrapper if needed */
    .metrics-row-wrapper {{
      width: 100%;
      margin-bottom: 24px;
    }}

    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }}

    .metric-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
      transition: var(--transition);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      min-height: 110px;
      justify-content: space-between;
    }}

    .metric-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }}

    .metric-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3.5px;
    }}

    /* Card Top Accent Bars */
    .metric-card.card-runs::before {{ background: var(--accent-emerald); }}
    .metric-card.card-questions::before {{ background: var(--accent-indigo); }}
    .metric-card.card-runtime::before {{ background: var(--accent-cyan); }}
    .metric-card.card-chats::before {{ background: var(--accent-purple); }}
    .metric-card.card-latency::before {{ background: var(--accent-amber); }}
    .metric-card.card-density::before {{ background: var(--accent-rose); }}
    .metric-card.card-depth::before {{ background: #3b82f6; }}
    .metric-card.card-speed::before {{ background: #10b981; }}
    .metric-card.card-duration::before {{ background: var(--accent-amber); }}
    .metric-card.card-accuracy::before {{ background: #10b981; }}

    .metric-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
      gap: 8px;
    }}

    /* Anti-Truncation Standard: Never clip, hide, or truncate essential KPI text */
    .metric-title {{
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: normal;
      word-break: normal;
      line-height: 1.3;
    }}

    .metric-icon {{
      font-size: 1.3rem;
      flex-shrink: 0;
      line-height: 1;
    }}

    .metric-value {{
      font-size: 1.65rem;
      font-weight: 700;
      font-family: var(--font-mono);
      letter-spacing: -0.02em;
      line-height: 1.15;
      margin-bottom: 4px;
      white-space: normal;
      color: var(--text-primary);
    }}

    .metric-unit {{
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-left: 2px;
    }}

    .metric-subtitle {{
      font-size: 0.75rem;
      color: var(--text-muted);
      white-space: normal;
      line-height: 1.3;
    }}

    /* Interactive Multi-Dimensional Filter Toolbar */
    .filter-toolbar {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      margin-bottom: 24px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    }}

    .filter-toolbar-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-subtle);
      flex-wrap: wrap;
      gap: 10px;
    }}

    .filter-toolbar-title {{
      font-size: 0.92rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-primary);
    }}

    .filter-header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .filter-stats-badge {{
      font-size: 0.82rem;
      font-family: var(--font-mono);
      color: var(--accent-indigo);
      background: var(--accent-indigo-glow);
      padding: 4px 12px;
      border-radius: 9999px;
      font-weight: 600;
    }}

    /* Filter Toolbar Body & Inverted Rows (Top Row Presets, Bottom Row Inputs) */
    .filter-toolbar-body {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .filter-presets-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      padding: 10px 14px;
      background: var(--bg-surface-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    .presets-label {{
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      display: flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }}

    .filter-presets {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .preset-btn {{
      background: var(--bg-surface);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 5px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition);
      user-select: none;
      white-space: nowrap;
    }}

    .preset-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-highlight);
      border-color: var(--accent-indigo);
    }}

    .preset-btn.active {{
      background: var(--accent-indigo);
      color: #ffffff;
      border-color: var(--accent-indigo);
      box-shadow: 0 2px 8px var(--accent-indigo-glow);
    }}

    .filter-controls-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-end;
    }}

    .filter-control-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 140px;
      flex: 1 1 auto;
    }}

    .filter-date-group {{
      min-width: 280px;
      flex: 2 1 auto;
    }}

    .filter-label {{
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .filter-date-inputs {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .filter-date-sep {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    .filter-input-date,
    .filter-select {{
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
      padding: 8px 12px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-family: var(--font-family);
      outline: none;
      transition: var(--transition);
      width: 100%;
    }}

    .filter-input-date:focus,
    .filter-select:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 0 2px var(--accent-indigo-glow);
    }}

    .btn-reset {{
      background: var(--bg-surface-elevated);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      padding: 8px 14px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: var(--transition);
      white-space: nowrap;
    }}

    .btn-reset:hover {{
      color: var(--accent-rose);
      border-color: var(--accent-rose);
      background: var(--bg-surface-highlight);
    }}

    /* Collapsible Accordion & Interactive Animations (Department 04 & 05 Standards) */
    .collapse-icon {{
      display: inline-block;
      font-size: 0.85rem;
      line-height: 1;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      color: var(--text-secondary);
      user-select: none;
      flex-shrink: 0;
    }}

    .collapsible-header {{
      cursor: pointer;
      user-select: none;
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }}

    .collapsible-header:hover {{
      background-color: var(--bg-surface-highlight) !important;
    }}

    .collapsible-header:focus-visible {{
      outline: 2px solid var(--accent-indigo);
      outline-offset: 2px;
    }}

    .collapse-btn {{
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      border-radius: var(--radius-sm);
      width: 28px;
      height: 28px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: var(--transition);
      flex-shrink: 0;
    }}

    .collapse-btn:hover {{
      background: var(--bg-surface-highlight);
      color: var(--text-primary);
      border-color: var(--accent-indigo);
    }}

    .collapse-toggle-btn {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      border-radius: var(--radius-md);
      padding: 5px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: var(--transition);
      user-select: none;
    }}

    .collapse-toggle-btn:hover {{
      background: var(--bg-surface-highlight);
      color: var(--text-primary);
      border-color: var(--accent-indigo);
    }}

    /* Collapsed state transforms chevron indicator */
    .collapsed .collapse-icon,
    [aria-expanded="false"] .collapse-icon,
    .collapsed > .collapse-icon {{
      transform: rotate(-90deg);
    }}

    .card-collapsible-body,
    .filter-toolbar-body,
    .chat-card-body,
    .run-body,
    .options-list {{
      transition: max-height 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                  opacity 0.25s ease,
                  padding 0.25s ease,
                  margin 0.25s ease;
      overflow: hidden;
    }}

    .card-collapsible-body.collapsed,
    .filter-toolbar-body.collapsed,
    .chat-card-body.collapsed,
    .run-body.collapsed,
    .options-list.collapsed {{
      max-height: 0 !important;
      opacity: 0 !important;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin-top: 0 !important;
      margin-bottom: 0 !important;
      border: none !important;
      pointer-events: none;
    }}

    .card-header.collapsible-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 6px;
      border-radius: var(--radius-sm);
    }}

    .accordion-global-controls {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-shrink: 0;
    }}

    .btn-sm {{
      padding: 6px 12px;
      font-size: 0.8rem;
      border-radius: var(--radius-sm);
    }}

    /* Architecture Diagram Card */
    .architecture-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
      overflow-x: auto;
    }}

    .card-title {{
      font-size: 1.02rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* Interactive Pure SVG Charts Grid */
    .charts-grid-two {{
      display: grid;
      grid-template-columns: 1.35fr 1fr;
      gap: 18px;
      margin-bottom: 20px;
    }}

    @media (max-width: 900px) {{
      .charts-grid-two {{
        grid-template-columns: 1fr;
      }}
    }}

    .chart-card-wide {{
      margin-bottom: 24px;
    }}

    .charts-grid {{
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 18px;
      margin-bottom: 24px;
    }}

    @media (max-width: 900px) {{
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .chart-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
    }}

    .chart-card svg {{
      width: 100%;
      height: auto;
    }}

    /* Chat Stats Strip */
    .stats-strip {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}

    .stat-pill {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 8px 16px;
      font-size: 0.82rem;
      color: var(--text-secondary);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}

    .stat-num {{
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--accent-indigo);
      font-size: 0.95rem;
    }}

    /* Controls Bar */
    .controls-bar {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      align-items: center;
      flex-wrap: wrap;
    }}

    .search-input {{
      flex: 1;
      min-width: 260px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      padding: 10px 16px;
      border-radius: var(--radius-md);
      font-size: 0.9rem;
      outline: none;
      transition: var(--transition);
    }}

    .search-input:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 0 2px var(--accent-indigo-glow);
    }}

    /* Section Headers */
    .section-title {{
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* Chat Breakdown Table */
    .table-container {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      overflow-x: auto;
      margin-bottom: 32px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }}

    th {{
      background: var(--bg-surface-elevated);
      color: var(--text-secondary);
      font-weight: 600;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-subtle);
      vertical-align: middle;
    }}

    tr:last-child td {{
      border-bottom: none;
    }}

    tr:hover td {{
      background: var(--bg-surface-elevated);
    }}

    .chat-id-tag {{
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: var(--accent-indigo);
      background: var(--accent-indigo-glow);
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      display: inline-block;
    }}

    .badge-count {{
      background: var(--bg-surface-highlight);
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 700;
      font-family: var(--font-mono);
      font-size: 0.82rem;
    }}

    /* Question & Option Cards (Deep Collapsible Hierarchy) */
    .chat-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      margin-bottom: 24px;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }}

    .chat-card-header.collapsible-header {{
      background: var(--bg-surface-elevated);
      padding: 14px 20px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .chat-card-title {{
      font-size: 0.95rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .chat-card-meta {{
      display: flex;
      gap: 8px;
      align-items: center;
      font-size: 0.8rem;
      color: var(--text-secondary);
    }}

    .run-block {{
      padding: 16px 20px;
      border-bottom: 1px dashed var(--border-subtle);
    }}

    .run-block:last-child {{
      border-bottom: none;
    }}

    .run-header.collapsible-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: var(--bg-surface-elevated);
      border-radius: var(--radius-md);
      font-size: 0.82rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
      margin-bottom: 12px;
      border: 1px solid var(--border-subtle);
    }}

    .run-body {{
      padding-top: 4px;
    }}

    .question-card {{
      background: var(--bg-primary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px;
      margin-bottom: 12px;
    }}

    .question-card:last-child {{
      margin-bottom: 0;
    }}

    .question-prompt.collapsible-header {{
      font-weight: 600;
      font-size: 0.92rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 6px 10px;
      border-radius: var(--radius-sm);
      margin-bottom: 10px;
    }}

    .question-prompt-left {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
    }}

    .question-prompt-right {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .question-num {{
      background: var(--accent-indigo);
      color: #fff;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      font-family: var(--font-mono);
      margin-top: 2px;
      flex-shrink: 0;
    }}

    .options-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .option-item {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      font-size: 0.88rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      transition: var(--transition);
    }}

    .option-item.selected {{
      background: var(--accent-emerald-bg);
      border: 1px solid var(--accent-emerald);
      border-left: 4px solid var(--accent-emerald);
      font-weight: 600;
      color: var(--text-primary);
    }}

    .option-badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: var(--accent-emerald);
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 9999px;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    .empty-state {{
      text-align: center;
      padding: 48px 20px;
      color: var(--text-muted);
      background: var(--bg-surface);
      border: 1px dashed var(--border-subtle);
      border-radius: var(--radius-lg);
    }}

    footer {{
      margin-top: 40px;
      text-align: center;
      font-size: 0.78rem;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    /* Configuration Modal Backdrop & Overlay */
    .modal-backdrop {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.25s ease, visibility 0.25s ease;
      padding: 16px;
    }}

    .modal-backdrop.active {{
      opacity: 1;
      visibility: visible;
    }}

    .modal-content {{
      background: var(--bg-surface);
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-lg);
      max-width: 620px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), 0 0 24px var(--accent-indigo-glow);
      transform: scale(0.96);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      overflow: hidden;
    }}

    .modal-backdrop.active .modal-content {{
      transform: scale(1);
    }}

    .modal-header {{
      padding: 18px 24px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface-elevated);
    }}

    .modal-title-wrap {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .modal-icon {{
      font-size: 1.5rem;
      line-height: 1;
    }}

    .modal-title {{
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-primary);
    }}

    .modal-subtitle {{
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-top: 2px;
    }}

    .modal-close-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.6rem;
      cursor: pointer;
      line-height: 1;
      padding: 4px 8px;
      border-radius: var(--radius-sm);
      transition: var(--transition);
    }}

    .modal-close-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-highlight);
    }}

    .modal-body {{
      padding: 20px 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .config-group {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding: 12px 14px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      transition: var(--transition);
    }}

    .config-group:hover {{
      border-color: var(--border-accent);
    }}

    .config-group.config-actions-group {{
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }}

    .config-label-wrap {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
    }}

    .config-label {{
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-primary);
    }}

    .config-hint {{
      font-size: 0.78rem;
      color: var(--text-muted);
      line-height: 1.3;
    }}

    .config-select {{
      background: var(--bg-surface);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
      padding: 8px 12px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-family: var(--font-family);
      outline: none;
      min-width: 190px;
      transition: var(--transition);
    }}

    .config-select:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 0 2px var(--accent-indigo-glow);
    }}

    .config-data-btns {{
      display: flex;
      gap: 10px;
      width: 100%;
      flex-wrap: wrap;
    }}

    .btn-export {{
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border: 1px solid #10b981;
      flex: 1;
      justify-content: center;
    }}

    .btn-export:hover {{
      background: rgba(16, 185, 129, 0.25);
    }}

    .btn-reset-cfg {{
      background: var(--bg-surface);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      flex: 1;
      justify-content: center;
    }}

    .btn-reset-cfg:hover {{
      color: var(--accent-rose);
      border-color: var(--accent-rose);
    }}

    .modal-footer {{
      padding: 16px 24px;
      background: var(--bg-surface-elevated);
      border-top: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .modal-footer-left {{
      display: flex;
      align-items: center;
    }}

    .config-status-badge {{
      font-size: 0.75rem;
      font-family: var(--font-mono);
      color: var(--text-muted);
    }}

    .modal-footer-right {{
      display: flex;
      gap: 10px;
    }}

    .btn-primary {{
      background: var(--accent-indigo);
      color: #ffffff;
      border: 1px solid var(--accent-indigo);
      box-shadow: 0 2px 10px var(--accent-indigo-glow);
    }}

    .btn-primary:hover {{
      background: #4f46e5;
      border-color: #4f46e5;
    }}

    /* Animated Toast Notification */
    .toast-notification {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--accent-emerald-border);
      border-left: 4px solid var(--accent-emerald);
      padding: 12px 20px;
      border-radius: var(--radius-md);
      font-size: 0.88rem;
      font-weight: 600;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      z-index: 10000;
      opacity: 0;
      transform: translateY(16px);
      pointer-events: none;
      transition: opacity 0.25s ease, transform 0.25s ease;
    }}

    .toast-notification.active {{
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }}

    .toast-notification.info {{
      border-color: var(--accent-indigo);
      border-left-color: var(--accent-indigo);
    }}

    .toast-notification.error {{
      border-color: var(--accent-rose);
      border-left-color: var(--accent-rose);
    }}

    /* Refresh & Combined Auto-Refresh Tag in Header */
    .btn-refresh {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }}

    .btn-refresh.is-polling {{
      border-color: rgba(6, 182, 212, 0.45);
      background: rgba(6, 182, 212, 0.08);
    }}

    .auto-refresh-tag,
    .auto-refresh-badge {{
      display: inline-flex;
      align-items: center;
      color: var(--accent-cyan, #06b6d4);
      font-size: 0.78rem;
      font-family: var(--font-mono);
      font-weight: 600;
      margin-left: 2px;
    }}

    .spin-icon {{
      display: inline-block;
      transition: transform 0.3s ease;
    }}

    .btn-refresh:hover .spin-icon,
    .btn-refresh.is-polling .spin-icon {{
      animation: spin 2.5s linear infinite;
    }}

    @keyframes spin {{
      100% {{ transform: rotate(360deg); }}
    }}

    /* Tab 4: Config Panel Layout (Department 04 & 05 Standard) */
    .config-panel-container {{
      display: flex;
      flex-direction: column;
      gap: 24px;
      margin-bottom: 32px;
    }}

    /* Global Expand / Collapse All Toolbar */
    .config-global-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 18px;
      margin-bottom: 8px;
      gap: 12px;
      flex-wrap: wrap;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }}

    .toolbar-title-wrap {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .toolbar-icon {{
      font-size: 1.25rem;
      line-height: 1;
    }}

    .toolbar-label {{
      font-size: 0.94rem;
      font-weight: 700;
      color: var(--text-primary);
    }}

    .toolbar-badge {{
      font-size: 0.72rem;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--accent-indigo);
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 2px 8px;
      border-radius: var(--radius-sm);
    }}

    .toolbar-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .btn-collapse-control {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      font-size: 0.82rem;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: var(--transition);
      outline: none;
    }}

    .btn-collapse-control:hover {{
      background: var(--bg-surface-highlight);
      border-color: var(--border-accent);
      color: var(--text-primary);
    }}

    .btn-collapse-control:focus-visible {{
      ring: 2px solid var(--accent-indigo);
      outline: 2px solid var(--accent-indigo);
    }}

    /* Collapsible Card Headers & Chevron Indicators */
    .collapsible-card-header {{
      cursor: pointer;
      user-select: none;
      transition: background 0.2s ease;
      border-radius: var(--radius-md);
      padding: 4px 6px;
      margin: -4px -6px 18px -6px;
    }}

    .collapsible-card-header:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .collapsible-card-header[aria-expanded="false"] {{
      margin-bottom: 0;
    }}

    .collapsible-card-header:focus-visible,
    .config-subgroup-header:focus-visible {{
      outline: 2px solid var(--accent-indigo);
      outline-offset: 2px;
    }}

    .accordion-chevron,
    .subaccordion-chevron {{
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-muted);
      transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s ease, border-color 0.2s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      line-height: 1;
    }}

    .collapsible-card-header:hover .accordion-chevron,
    .config-subgroup-header:hover .subaccordion-chevron {{
      color: var(--text-primary);
      border-color: var(--border-accent);
      background: var(--bg-surface-highlight);
    }}

    .collapsible-card-header[aria-expanded="false"] .accordion-chevron,
    .config-subgroup-header[aria-expanded="false"] .subaccordion-chevron {{
      transform: rotate(-90deg);
    }}

    .collapsible-card-body {{
      transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
      overflow: hidden;
    }}

    .collapsible-card-body.collapsed {{
      max-height: 0 !important;
      opacity: 0;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin-top: 0 !important;
      margin-bottom: 0 !important;
      pointer-events: none;
    }}

    /* Sub-Accordions inside Cards */
    .accordion-group {{
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      background: var(--bg-surface-elevated);
      overflow: hidden;
      transition: var(--transition);
      padding: 0;
    }}

    .accordion-group:hover {{
      border-color: var(--border-accent);
    }}

    .config-subgroup-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 18px;
      cursor: pointer;
      user-select: none;
      background: var(--bg-surface-elevated);
      transition: background 0.2s ease;
      border-bottom: 1px solid transparent;
    }}

    .config-subgroup-header:hover {{
      background: var(--bg-surface-highlight);
    }}

    .config-subgroup-header[aria-expanded="true"] {{
      border-bottom-color: var(--border-subtle);
    }}

    .config-subgroup-body {{
      padding: 16px 18px;
      transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease, padding 0.3s ease;
      overflow: hidden;
    }}

    .config-subgroup-body.collapsed {{
      max-height: 0 !important;
      opacity: 0;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin-top: 0 !important;
      margin-bottom: 0 !important;
      pointer-events: none;
    }}

    .config-section-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
      position: relative;
      overflow: hidden;
    }}

    .config-section-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3.5px;
    }}

    #runtime-config-section::before {{
      background: linear-gradient(90deg, var(--accent-indigo), var(--accent-cyan));
    }}

    #dashboard-config-section::before {{
      background: linear-gradient(90deg, var(--accent-emerald), var(--accent-purple));
    }}

    .config-section-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 22px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-subtle);
      flex-wrap: wrap;
      gap: 12px;
    }}

    .config-section-title-wrap {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
    }}

    .config-section-icon {{
      font-size: 1.8rem;
      line-height: 1;
      padding: 8px;
      background: var(--bg-surface-elevated);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }}

    .config-section-title-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .config-section-title {{
      font-size: 1.22rem;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }}

    .config-badge-live {{
      background: rgba(99, 102, 241, 0.15);
      color: var(--accent-indigo);
      border: 1px solid rgba(99, 102, 241, 0.35);
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
    }}

    .config-badge-browser {{
      background: rgba(16, 185, 129, 0.15);
      color: var(--accent-emerald);
      border: 1px solid rgba(16, 185, 129, 0.35);
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
    }}

    .config-section-desc {{
      font-size: 0.84rem;
      color: var(--text-secondary);
      margin-top: 4px;
      line-height: 1.4;
    }}

    .status-indicator-live {{
      font-size: 0.78rem;
      font-weight: 700;
      font-family: var(--font-mono);
      color: #10b981;
      background: rgba(16, 185, 129, 0.12);
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid rgba(16, 185, 129, 0.25);
    }}

    .status-indicator-client {{
      font-size: 0.78rem;
      font-weight: 700;
      font-family: var(--font-mono);
      color: #06b6d4;
      background: rgba(6, 182, 212, 0.12);
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid rgba(6, 182, 212, 0.25);
    }}

    .config-section-body {{
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}

    .config-card-subgroup {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px 20px;
      transition: var(--transition);
    }}

    .config-card-subgroup:hover {{
      border-color: var(--border-accent);
    }}

    .config-subgroup-title {{
      font-size: 0.96rem;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }}

    .config-subgroup-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 14px;
      line-height: 1.35;
    }}

    /* Execution Mode Pill Selector */
    .mode-pill-selector {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    .mode-pill {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-radius: var(--radius-md);
      background: var(--bg-surface);
      border: 1.5px solid var(--border-subtle);
      color: var(--text-secondary);
      cursor: pointer;
      transition: var(--transition);
      text-align: left;
      outline: none;
    }}

    .mode-pill:hover {{
      border-color: var(--border-accent);
      color: var(--text-primary);
      background: var(--bg-surface-highlight);
    }}

    .mode-pill.active {{
      border-color: var(--accent-indigo);
      background: rgba(99, 102, 241, 0.1);
      color: var(--text-primary);
      box-shadow: 0 0 16px var(--accent-indigo-glow);
    }}

    .mode-pill[data-mode="production"].active {{
      border-color: #10b981;
      background: rgba(16, 185, 129, 0.1);
      box-shadow: 0 0 16px rgba(16, 185, 129, 0.2);
    }}

    .mode-pill-content {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .mode-pill-icon {{
      font-size: 1.4rem;
      line-height: 1;
    }}

    .mode-pill-text strong {{
      display: block;
      font-size: 0.92rem;
      color: var(--text-primary);
    }}

    .mode-pill-text small {{
      display: block;
      font-size: 0.75rem;
      color: var(--text-secondary);
      margin-top: 2px;
    }}

    .mode-pill-check {{
      font-weight: 700;
      color: #10b981;
      opacity: 0;
      font-size: 1.1rem;
      transition: var(--transition);
    }}

    .mode-pill.active .mode-pill-check {{
      opacity: 1;
    }}

    /* Pipeline Steps Toggles Grid */
    .steps-toggle-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .step-toggle-card {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      gap: 14px;
      transition: var(--transition);
    }}

    .step-toggle-card:hover {{
      border-color: var(--border-accent);
    }}

    .step-toggle-info {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .step-toggle-title-row {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .step-tag-pill {{
      font-size: 0.72rem;
      font-family: var(--font-mono);
      font-weight: 700;
      background: var(--accent-indigo-glow);
      color: var(--accent-indigo);
      padding: 2px 6px;
      border-radius: 4px;
    }}

    .step-toggle-desc {{
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.3;
    }}

    /* Switch Toggle Slider Standard */
    .switch-toggle {{
      position: relative;
      display: inline-block;
      width: 46px;
      height: 26px;
      flex-shrink: 0;
      cursor: pointer;
    }}

    .switch-toggle input {{
      opacity: 0;
      width: 0;
      height: 0;
    }}

    .slider-round {{
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: var(--bg-surface-highlight);
      transition: 0.25s;
      border-radius: 34px;
      border: 1px solid var(--border-subtle);
    }}

    .slider-round:before {{
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background-color: #ffffff;
      transition: 0.25s;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }}

    .switch-toggle input:checked + .slider-round {{
      background-color: var(--accent-emerald);
      border-color: var(--accent-emerald);
    }}

    .switch-toggle input:focus-visible + .slider-round {{
      box-shadow: 0 0 0 2px var(--accent-indigo);
    }}

    .switch-toggle input:checked + .slider-round:before {{
      transform: translateX(20px);
    }}

    /* Timing Inputs Grid */
    .timing-inputs-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
    }}

    .input-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .input-card-label {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-primary);
    }}

    .unit-tag {{
      font-size: 0.72rem;
      font-family: var(--font-mono);
      font-weight: 600;
      color: var(--accent-indigo);
      background: var(--accent-indigo-glow);
      padding: 2px 6px;
      border-radius: 4px;
    }}

    .cfg-num-input,
    .cfg-text-input {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 0.95rem;
      font-weight: 600;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      outline: none;
      transition: var(--transition);
      width: 100%;
    }}

    .cfg-num-input:focus,
    .cfg-text-input:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 0 2px var(--accent-indigo-glow);
    }}

    .input-card-help {{
      font-size: 0.74rem;
      color: var(--text-muted);
      line-height: 1.25;
    }}

    /* Governance Grid & Logging Grid */
    .governance-grid,
    .logging-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    .governance-card,
    .logging-card {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      gap: 12px;
    }}

    .input-with-suffix {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      width: 140px;
    }}

    .suffix-badge {{
      font-size: 0.75rem;
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--text-secondary);
    }}

    /* Action Controls & CLI Command Generator */
    .runtime-action-buttons {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }}

    .btn-cli {{
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border: 1px solid #6366f1;
    }}

    .btn-cli:hover {{
      background: rgba(99, 102, 241, 0.25);
    }}

    .btn-download {{
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
      border: 1px solid #06b6d4;
    }}

    .btn-download:hover {{
      background: rgba(6, 182, 212, 0.25);
    }}

    /* JSON Preview Drawer */
    .json-preview-drawer {{
      margin-top: 14px;
      background: #0b0f17;
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-md);
      overflow: hidden;
      animation: fadeIn 0.2s ease;
    }}

    .drawer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 14px;
      background: rgba(255, 255, 255, 0.04);
      border-bottom: 1px solid var(--border-subtle);
      font-size: 0.78rem;
      font-family: var(--font-mono);
      color: var(--text-secondary);
    }}

    .drawer-badge {{
      background: rgba(99, 102, 241, 0.2);
      color: var(--accent-indigo);
      font-size: 0.7rem;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
    }}

    .json-preview-code {{
      margin: 0;
      padding: 14px;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: #38bdf8;
      overflow-x: auto;
      max-height: 280px;
      line-height: 1.4;
    }}

    /* Section 2: Dashboard UI Configuration Grid */
    .dashboard-config-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      margin-bottom: 16px;
    }}

    .dash-cfg-card {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      gap: 14px;
      transition: var(--transition);
    }}

    .dash-cfg-card:hover {{
      border-color: var(--border-accent);
    }}

    .dash-cfg-label-wrap {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
    }}

    .dash-cfg-sound-row {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-chime {{
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
      padding: 6px 10px;
      font-size: 0.8rem;
      white-space: nowrap;
    }}

    .btn-chime:hover {{
      background: rgba(245, 158, 11, 0.25);
    }}

    .dash-cfg-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 14px;
      border-top: 1px solid var(--border-subtle);
      flex-wrap: wrap;
      gap: 12px;
    }}

    .dash-cfg-footer-left,
    .dash-cfg-footer-right {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    @media (max-width: 860px) {{
      .mode-pill-selector,
      .steps-toggle-grid,
      .timing-inputs-grid,
      .governance-grid,
      .logging-grid,
      .dashboard-config-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    /* Reduced Motion accessibility standard */
    html.reduced-motion *,
    html.reduced-motion ::before,
    html.reduced-motion ::after {{
      animation: none !important;
      transition: none !important;
    }}
    /* ========================================================================
       Slide-Up Live Console Logs Drawer (Classic Parity)
       ======================================================================== */
    .log-unread-badge {{
      background: var(--accent-indigo);
      color: #ffffff;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 9999px;
      margin-left: 4px;
    }}

    #logs-drawer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 380px;
      background: #0b0f17;
      border-top: 2px solid var(--accent-indigo);
      box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.6);
      z-index: 800;
      transform: translateY(100%);
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
    }}

    #logs-drawer.open {{
      transform: translateY(0);
    }}

    .logs-drawer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 18px;
      background: #131926;
      border-bottom: 1px solid var(--border-subtle);
      color: #f8fafc;
      font-size: 0.82rem;
      font-weight: 600;
    }}

    .logs-terminal-body {{
      flex: 1;
      padding: 12px 18px;
      overflow-y: auto;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      line-height: 1.6;
      color: #94a3b8;
      background: #0b0f17;
      white-space: pre-wrap;
      word-break: break-all;
    }}

    .log-line-info {{ color: #38bdf8; }}
    .log-line-warn {{ color: #f59e0b; }}
    .log-line-err  {{ color: #f43f5e; font-weight: 600; }}
    .log-line-step {{ color: #c084fc; font-weight: 600; }}
    .log-line-ok   {{ color: #34d399; font-weight: 600; }}

    #btn-floating-logs {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 700;
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--border-accent);
      padding: 8px 14px;
      border-radius: 9999px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      font-size: 0.82rem;
      font-weight: 600;
      transition: var(--transition);
    }}

    #btn-floating-logs:hover {{
      background: var(--bg-surface-highlight);
      border-color: var(--accent-indigo);
      box-shadow: 0 6px 20px var(--accent-indigo-glow);
      transform: translateY(-2px);
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="header-left">
        <div class="logo-badge">⚡</div>
        <div class="header-titles">
          <h1>AutoSelect Antigravity Dashboard</h1>
          <p>Real-Time Step 1-3 Execution Ledger & Grill-Me Option Reporting</p>
        </div>
      </div>
      <div class="header-actions">
        <span class="status-pill status-bridge-online" id="server-bridge-pill" title="Control Server active on port 8501">🟢 Server Online</span>
        <span class="status-pill status-idle" id="dashboard-status-pill">⚪ Inactive</span>
        <span class="status-pill status-mode-badge" id="header-mode-badge" role="button" tabindex="0" title="{header_badge_title}" style="background: {header_badge_bg}; color: {header_badge_color}; border: 1px solid {header_badge_border}; cursor: pointer; font-weight: 700; user-select: none;">
          {header_badge_icon} {header_badge_text}
        </span>
        <button class="btn btn-automation-toggle state-stopped" id="automation-toggle-btn" title="Toggle AutoSelect Antigravity Automation">
          <span class="control-icon" id="control-icon">▶️</span>
          <span class="control-label" id="control-label">Start</span>
        </button>
        <button class="btn" id="theme-toggle" title="Toggle Light/Dark Theme">🌓 Theme</button>
        <button class="btn btn-refresh" id="btn-header-refresh" onclick="location.reload()" title="Refresh Ledger / Auto-refresh">
          <span class="spin-icon">🔄</span>
          <span>Refresh</span>
          <span class="auto-refresh-tag" id="auto-refresh-tag" style="display: none;">(<span id="refresh-countdown">10s</span>)</span>
        </button>
        <button class="btn btn-modern-switch" id="btn-switch-modern" onclick="window.location.href = window.location.protocol.startsWith('http') ? '/' : '../Modern and Interactive Dashboard/dashboard.html'" title="Switch to Modern & Interactive Dashboard">
          <span>✨</span>
          <span>Modern</span>
        </button>
        <button class="btn" id="btn-toggle-logs" title="Toggle Live Console Logs Stream (L)">
          <span>📟</span>
          <span>Logs</span>
          <span class="log-unread-badge" id="log-count-badge">0</span>
        </button>
      </div>
    </header>

    <!-- Horizontal Tab Navigation Bar (Single-word intuitive names: Overview, Chats, Questions, Config) -->
    <nav class="tab-nav" role="tablist" aria-label="Dashboard Tabs">
      <button class="tab-btn active" id="tab-btn-overview" role="tab" aria-selected="true" aria-controls="tab-overview" data-tab="overview">
        <span class="tab-icon">📊</span>
        <span class="tab-label">Overview</span>
      </button>
      <button class="tab-btn" id="tab-btn-chats" role="tab" aria-selected="false" aria-controls="tab-chats" data-tab="chats">
        <span class="tab-icon">📂</span>
        <span class="tab-label">Chats</span>
        <span class="tab-badge" id="tab-chats-badge">{total_chats}</span>
      </button>
      <button class="tab-btn" id="tab-btn-questions" role="tab" aria-selected="false" aria-controls="tab-questions" data-tab="questions">
        <span class="tab-icon">💬</span>
        <span class="tab-label">Questions</span>
        <span class="tab-badge" id="tab-questions-badge">{total_questions}</span>
      </button>
      <button class="tab-btn" id="tab-btn-modes" role="tab" aria-selected="false" aria-controls="tab-modes" data-tab="modes">
        <span class="tab-icon">🎛️</span>
        <span class="tab-label">Mode Switch</span>
        <span class="tab-badge {tab_modes_badge_class}" id="tab-modes-badge">{tab_modes_badge_text}</span>
      </button>
      <button class="tab-btn" id="tab-btn-config" role="tab" aria-selected="false" aria-controls="tab-config" data-tab="config">
        <span class="tab-icon">⚙️</span>
        <span class="tab-label">Config</span>
      </button>
    </nav>

    <!-- Legacy Search Box Compatibility Hook (Hidden) -->
    <input type="hidden" id="search-box" value="">
    <input type="hidden" id="search-overview" value="">

    <!-- Interactive Multi-Dimensional Filter Toolbar (Inverted Rows & Rich Presets) -->
    <section class="filter-toolbar" aria-label="Filters Toolbar">
      <div class="filter-toolbar-header">
        <div class="filter-toolbar-title">
          <span>🔍</span>
          <span>Interactive Filter Toolbar</span>
        </div>
        <div class="filter-header-actions">
          <div class="filter-stats-badge" id="filter-stats-badge">
            Showing <span id="filter-count">{total_runs}</span> of <span id="filter-total">{total_runs}</span> runs
          </div>
          <button type="button" class="collapse-toggle-btn" id="filter-collapse-btn" aria-expanded="true" aria-controls="filter-toolbar-body" title="Collapse/Expand Filters">
            <span class="collapse-icon">▾</span>
            <span class="collapse-label">Collapse</span>
          </button>
        </div>
      </div>

      <div class="filter-toolbar-body" id="filter-toolbar-body">
        <!-- Row 1 (Top): Quick Presets Bar (Up वाला Down, Down वाला Up) -->
        <div class="filter-presets-row">
          <span class="presets-label">⚡ Quick Presets:</span>
          <div class="filter-presets">
            <button type="button" class="preset-btn active" data-preset="all">All Time</button>
            <button type="button" class="preset-btn" data-preset="today">Today</button>
            <button type="button" class="preset-btn" data-preset="yesterday">Yesterday</button>
            <button type="button" class="preset-btn" data-preset="7d">Last 7 Days</button>
            <button type="button" class="preset-btn" data-preset="30d">Last 30 Days</button>
            <button type="button" class="preset-btn" data-preset="week">This Week</button>
            <button type="button" class="preset-btn" data-preset="month">This Month</button>
          </div>
        </div>

        <!-- Row 2 (Bottom): Granular Custom Controls -->
        <div class="filter-controls-row">
          <!-- Date Range Filter -->
          <div class="filter-control-group filter-date-group">
            <label class="filter-label" for="filter-date-from">Date Range</label>
            <div class="filter-date-inputs">
              <input type="date" id="filter-date-from" class="filter-input-date" title="Filter From Date">
              <span class="filter-date-sep">to</span>
              <input type="date" id="filter-date-to" class="filter-input-date" title="Filter To Date">
            </div>
          </div>

          <!-- Chat Filter Dropdown -->
          <div class="filter-control-group">
            <label class="filter-label" for="filter-chat">Conversation</label>
            <select id="filter-chat" class="filter-select">
              <option value="all">All Conversations ({total_chats})</option>
              {chat_options_html}
            </select>
          </div>

          <!-- Complexity Filter Dropdown -->
          <div class="filter-control-group">
            <label class="filter-label" for="filter-complexity">Complexity</label>
            <select id="filter-complexity" class="filter-select">
              <option value="all">All Runs</option>
              <option value="single">Single-Question (1)</option>
              <option value="multi">Multi-Question (2+)</option>
            </select>
          </div>

          <!-- Speed Filter Dropdown -->
          <div class="filter-control-group">
            <label class="filter-label" for="filter-speed">Speed / Latency</label>
            <select id="filter-speed" class="filter-select">
              <option value="all">All Durations</option>
              <option value="fast">Fast (&lt; 3s)</option>
              <option value="moderate">Moderate (3s - 8s)</option>
              <option value="heavy">Heavy (&gt; 8s)</option>
            </select>
          </div>

          <!-- Reset Button -->
          <div class="filter-control-group filter-actions-group">
            <label class="filter-label">&nbsp;</label>
            <button type="button" class="btn btn-reset" id="filter-reset-btn" title="Reset all filters">
              <span>🔄</span>
              <span>Reset Filters</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Tab 1: Overview Panel (8 Two-Row KPIs + SVG Architecture + Dynamic SVG Charts) -->
    <main id="tab-overview" class="tab-panel active" role="tabpanel" aria-labelledby="tab-btn-overview">
      <!-- 8 High-Level KPIs in Exactly Two Balanced Rows (4 in Row 1, 4 in Row 2) -->
      <div class="metrics-grid-2rows">
        <!-- Row 1: Primary Activity & Scale -->
        <!-- 1. Total Runs -->
        <div class="metric-card card-runs">
          <div class="metric-header">
            <span class="metric-title">Total Pipeline Runs</span>
            <span class="metric-icon">🚀</span>
          </div>
          <div class="metric-value">{total_runs}</div>
          <div class="metric-subtitle">Completed Runs</div>
        </div>

        <!-- 2. Questions Answered -->
        <div class="metric-card card-questions">
          <div class="metric-header">
            <span class="metric-title">Questions Answered</span>
            <span class="metric-icon">💬</span>
          </div>
          <div class="metric-value">{total_questions}</div>
          <div class="metric-subtitle">Grill-Me Resolved</div>
        </div>

        <!-- 3. Cumulative Runtime -->
        <div class="metric-card card-runtime">
          <div class="metric-header">
            <span class="metric-title">Cumulative Runtime</span>
            <span class="metric-icon">⏱️</span>
          </div>
          <div class="metric-value">{runtime_fmt}</div>
          <div class="metric-subtitle">{total_seconds:.1f}s Total Active</div>
        </div>

        <!-- 4. Unique Chats Automated -->
        <div class="metric-card card-chats">
          <div class="metric-header">
            <span class="metric-title">Unique Chats Automated</span>
            <span class="metric-icon">📂</span>
          </div>
          <div class="metric-value">{total_chats}</div>
          <div class="metric-subtitle">Distinct Conversations</div>
        </div>

        <!-- Row 2: Performance, Density & Speed -->
        <!-- 5. Mean Run Latency -->
        <div class="metric-card card-latency card-duration">
          <div class="metric-header">
            <span class="metric-title">Mean Run Latency</span>
            <span class="metric-icon">⚡</span>
          </div>
          <div class="metric-value">{avg_duration_fmt}</div>
          <div class="metric-subtitle">Avg Seconds / Run</div>
        </div>

        <!-- 6. Questions per Run Density -->
        <div class="metric-card card-density">
          <div class="metric-header">
            <span class="metric-title">Questions per Run</span>
            <span class="metric-icon">📊</span>
          </div>
          <div class="metric-value">{qs_density_fmt} <span class="metric-unit">Qs/run</span></div>
          <div class="metric-subtitle">Avg Question Density</div>
        </div>

        <!-- 7. Questions per Chat Depth -->
        <div class="metric-card card-depth">
          <div class="metric-header">
            <span class="metric-title">Questions per Chat</span>
            <span class="metric-icon">📑</span>
          </div>
          <div class="metric-value">{avg_qs_per_chat_fmt} <span class="metric-unit">Qs/chat</span></div>
          <div class="metric-subtitle">Avg Questions / Chat</div>
        </div>

        <!-- 8. Execution Speed -->
        <div class="metric-card card-speed">
          <div class="metric-header">
            <span class="metric-title">Execution Speed</span>
            <span class="metric-icon">🏎️</span>
          </div>
          <div class="metric-value">{sec_per_question_fmt} <span class="metric-unit">s/Q</span></div>
          <div class="metric-subtitle">Sec / Question Resolved</div>
        </div>
      </div>

      <!-- Pipeline Execution & System Topology Diagram (Pure Vector SVG & Collapsible) -->
      <div class="architecture-card" id="card-architecture">
        <div class="card-header collapsible-header" data-target="architecture-body" role="button" tabindex="0" aria-expanded="true" title="Toggle Architecture Diagram">
          <div class="card-title" style="margin-bottom: 0;">
            <span class="collapse-icon">▾</span>
            <span>🚀 System Component Topology & Health Architecture (Step 0 → Step 4)</span>
          </div>
          <button type="button" class="collapse-btn" aria-label="Toggle Architecture Diagram">
            <span class="collapse-icon">▾</span>
          </button>
        </div>
        <div class="card-collapsible-body" id="architecture-body" style="margin-top: 16px;">
          {topology_svg}
        </div>
      </div>

      <!-- Row 1 of Charts: Dual-Axis Velocity Timeline & Productivity Gauge -->
      <div class="charts-grid-two">
        <div class="chart-card" id="chart-card-velocity">
          <div class="card-header collapsible-header" data-target="chart-body-velocity" role="button" tabindex="0" aria-expanded="true" title="Toggle Velocity Timeline Chart">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>⚡ Dual-Axis Execution & Question Velocity Timeline</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Velocity Timeline Chart">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-velocity" style="margin-top: 16px;">
            {velocity_svg}
          </div>
        </div>

        <div class="chart-card" id="chart-card-productivity">
          <div class="card-header collapsible-header" data-target="chart-body-productivity" role="button" tabindex="0" aria-expanded="true" title="Toggle Productivity Gauge">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>🏎️ Developer Productivity & Time Saved Gauge</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Productivity Gauge">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-productivity" style="margin-top: 16px;">
            {productivity_svg}
          </div>
        </div>
      </div>

      <!-- Row 2 of Charts: Hourly Heatmap & Option Selection Breakdown -->
      <div class="charts-grid-two">
        <div class="chart-card" id="chart-card-heatmap">
          <div class="card-header collapsible-header" data-target="chart-body-heatmap" role="button" tabindex="0" aria-expanded="true" title="Toggle Activity Heatmap">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>🕒 Hourly Activity & Time-of-Day Heatmap</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Activity Heatmap">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-heatmap" style="margin-top: 16px;">
            {heatmap_svg}
          </div>
        </div>

        <div class="chart-card" id="chart-card-option-breakdown">
          <div class="card-header collapsible-header" data-target="chart-body-option-breakdown" role="button" tabindex="0" aria-expanded="true" title="Toggle Option Selection Breakdown">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>🎯 Option Selection Distribution & Recommendation Adherence</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Option Selection Breakdown">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-option-breakdown" style="margin-top: 16px;">
            {option_breakdown_svg}
          </div>
        </div>
      </div>

      <!-- Row 3 of Charts: Chat Distribution & Topic Share -->
      <div class="charts-grid-two">
        <div class="chart-card" id="chart-card-distribution">
          <div class="card-header collapsible-header" data-target="chart-body-distribution" role="button" tabindex="0" aria-expanded="true" title="Toggle Distribution Chart">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>📊 Chat Automation & Questions Distribution</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Distribution Chart">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-distribution" style="margin-top: 16px;">
            {distribution_svg}
          </div>
        </div>

        <div class="chart-card" id="chart-card-topic">
          <div class="card-header collapsible-header" data-target="chart-body-topic" role="button" tabindex="0" aria-expanded="true" title="Toggle Topic Share Chart">
            <div class="card-title" style="margin-bottom: 0;">
              <span class="collapse-icon">▾</span>
              <span>🥧 Chat Workload & Topic Share</span>
            </div>
            <button type="button" class="collapse-btn" aria-label="Toggle Topic Share Chart">
              <span class="collapse-icon">▾</span>
            </button>
          </div>
          <div class="card-collapsible-body" id="chart-body-topic" style="margin-top: 16px;">
            {topic_share_svg}
          </div>
        </div>
      </div>

      <!-- Row 4: Wide Run Latency & Performance Trend Chart -->
      <div class="chart-card chart-card-wide" id="chart-card-latency">
        <div class="card-header collapsible-header" data-target="chart-body-latency" role="button" tabindex="0" aria-expanded="true" title="Toggle Latency Trend Chart">
          <div class="card-title" style="margin-bottom: 0;">
            <span class="collapse-icon">▾</span>
            <span>⚡ Run Latency & Performance Trend</span>
          </div>
          <button type="button" class="collapse-btn" aria-label="Toggle Latency Trend Chart">
            <span class="collapse-icon">▾</span>
          </button>
        </div>
        <div class="card-collapsible-body" id="chart-body-latency" style="margin-top: 16px;">
          {latency_trend_svg}
        </div>
      </div>
    </main>

    <!-- Tab 2: Chats Panel (Chat-wise Breakdown Table & Dedicated Search) -->
    <main id="tab-chats" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-chats">
      <!-- Chat Summary Stats Strip -->
      <div class="stats-strip">
        <div class="stat-pill">
          <span class="stat-num">{total_chats}</span>
          <span>Total Unique Chats</span>
        </div>
        <div class="stat-pill">
          <span class="stat-num">{total_runs}</span>
          <span>Lifetime Pipeline Runs</span>
        </div>
        <div class="stat-pill">
          <span class="stat-num">{avg_runs_per_chat:.1f}</span>
          <span>Avg Runs / Chat</span>
        </div>
      </div>

      <!-- Dedicated Search Controls for Chats -->
      <div class="controls-bar">
        <input type="text" id="search-chats" class="search-input" placeholder="🔍 Search chats by Conversation ID or topic summary...">
      </div>

      <!-- Chat-wise Automation Summary Table (Collapsible) -->
      <div class="section-collapsible" id="chats-breakdown-section">
        <div class="section-header collapsible-header" data-target="chats-table-container" role="button" tabindex="0" aria-expanded="false" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 6px 10px; border-radius: var(--radius-sm);" title="Toggle Chat Breakdown Table">
          <div class="section-title" style="margin-bottom: 0;">
            <span class="collapse-icon">▾</span>
            <span>📊 Chat-wise Automation Breakdown</span>
          </div>
          <button type="button" class="collapse-btn" aria-label="Toggle Chat Breakdown Table">
            <span class="collapse-icon">▾</span>
          </button>
        </div>
        <div class="card-collapsible-body collapsed" id="chats-table-container">
          <div class="table-container">
            <table id="summary-table">
              <thead>
                <tr>
                  <th>Conversation ID</th>
                  <th>Topic Summary</th>
                  <th>Runs Count</th>
                  <th>Questions Answered</th>
                  <th>Last Automated</th>
                </tr>
              </thead>
              <tbody id="summary-tbody">
                <!-- Dynamically populated by client JS -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Tab 3: Questions Panel (All Questions & Answers Ledger & Dedicated Search) -->
    <main id="tab-questions" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-questions">
      <!-- Dedicated Search Controls & Global Accordion Buttons -->
      <div class="controls-bar">
        <input type="text" id="search-questions" class="search-input" placeholder="🔍 Search questions, options, topics, or conversation IDs...">
        <div class="accordion-global-controls">
          <button type="button" class="btn btn-sm" id="btn-expand-all-questions" title="Expand all chats, runs, and questions">📂 Expand All</button>
          <button type="button" class="btn btn-sm" id="btn-collapse-all-questions" title="Collapse all chats, runs, and questions">📁 Collapse All</button>
        </div>
      </div>

      <!-- Detailed Questions & Answers Ledger -->
      <div class="section-title">📝 Questions & Answers Ledger</div>
      <div id="details-container">
        <!-- Dynamically populated by client JS -->
      </div>
    </main>

    <!-- Tab 4: Mode Switch Panel (Dedicated Execution Mode Control & Lifecycle Standard) -->
    <main id="tab-modes" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-modes">
      <div class="modes-panel-container">
        <!-- Header & Mode Switch Control Section -->
        <div class="modes-hero-card">
          <div class="modes-hero-header">
            <div class="modes-title-group">
              <span class="modes-hero-icon">🎛️</span>
              <div>
                <h2 class="modes-hero-title">Execution Mode Control &amp; Lifecycle Standard</h2>
                <p class="modes-hero-subtitle">मोड स्विच एवं कार्यप्रणाली • Select between Test Mode (single-run auto-stop) and Production Mode (continuous autonomous loop).</p>
              </div>
            </div>
            <div class="modes-hero-actions">
              <div class="modes-process-control-group">
                <span class="status-pill status-idle" id="modes-status-pill">⚪ Automation Inactive</span>
                <button type="button" class="btn btn-automation-toggle state-stopped" id="modes-automation-toggle-btn" title="Toggle AutoSelect Antigravity Automation directly from Mode Switch">
                  <span class="control-icon" id="modes-control-icon">▶️</span>
                  <span class="control-label" id="modes-control-label">Start</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Segmented Mode Switcher -->
          <div class="modes-switcher-bar">
            <div class="modes-switcher-label">
              <span class="switcher-dot">●</span>
              <span>Active Operating Mode:</span>
            </div>
            <div class="banner-mode-switcher modes-segmented-group" role="radiogroup" aria-label="Active Execution Mode Switcher">
              <button type="button" class="banner-mode-btn {banner_test_active_class}" id="banner-mode-test-btn" data-mode="test" title="Switch to Test Mode (Single-Run Auto-Stop)">
                <span>🧪 Test Mode</span>
                <span class="banner-mode-indicator">Auto-Stop</span>
              </button>
              <button type="button" class="banner-mode-btn {banner_prod_active_class}" id="banner-mode-prod-btn" data-mode="production" title="Switch to Production Mode (Continuous Autonomous Loop)">
                <span>🛡️ Production</span>
                <span class="banner-mode-indicator">Continuous Loop</span>
              </button>
            </div>
          </div>

          <!-- Two Rich Interactive Mode Cards -->
          <div class="mode-lifecycle-grid">
            <!-- 1. Test Mode Card -->
            <div class="lifecycle-card card-test {card_test_active_class}" id="banner-card-test" role="button" tabindex="0" title="Click to select Test Mode">
              <div class="lifecycle-card-top">
                <div class="lifecycle-card-title">
                  <span class="card-icon">🧪</span>
                  <div class="card-title-text">
                    <strong>Test Mode</strong>
                    <span class="card-title-hindi">(टेस्ट रन - Single-Run &amp; Auto-Stop)</span>
                  </div>
                </div>
                <span class="lifecycle-card-badge badge-test-mode">
                  <span>●</span>
                  <span>Single-Run • Auto-Stops on Task Complete</span>
                </span>
              </div>
              <p class="lifecycle-card-desc">
                जब <strong>Test Run</strong> सिलेक्ट करके स्टार्ट करते हैं, तो यह सिर्फ <strong>1 बार (Single Cycle)</strong> चलेगा और टास्क/पाइपलाइन कम्प्लीट होते ही प्रोसेस अपने आप <strong>Stop</strong> हो जाएगा।
              </p>
              <div class="lifecycle-card-features">
                <span class="lifecycle-feature-tag">⚡ 1 Single Cycle Execution</span>
                <span class="lifecycle-feature-tag">🛑 Auto-Exits on Task Completion</span>
                <span class="lifecycle-feature-tag">🔬 Safe Verification &amp; Dry-Runs</span>
                <span class="lifecycle-feature-tag">⏱️ Fast 10.0s Poll Cycle</span>
              </div>
            </div>

            <!-- 2. Production Mode Card -->
            <div class="lifecycle-card card-production {card_prod_active_class}" id="banner-card-prod" role="button" tabindex="0" title="Click to select Production Mode">
              <div class="lifecycle-card-top">
                <div class="lifecycle-card-title">
                  <span class="card-icon">🛡️</span>
                  <div class="card-title-text">
                    <strong>Production Mode</strong>
                    <span class="card-title-hindi">(प्रोडक्शन लेवल - Continuous Autonomous Loop)</span>
                  </div>
                </div>
                <span class="lifecycle-card-badge badge-prod-mode">
                  <span>●</span>
                  <span>Continuous Loop • Runs Until Manual Stop</span>
                </span>
              </div>
              <p class="lifecycle-card-desc">
                जब <strong>Production Level</strong> सिलेक्ट करके स्टार्ट करते हैं, तो यह बैकग्राउंड में अनवरत <strong>(Continuous Loop - 300s चक्र)</strong> चलता रहेगा जब तक कि आप मैन्युअली <strong>Stop</strong> बटन न दबाएँ।
              </p>
              <div class="lifecycle-card-features">
                <span class="lifecycle-feature-tag">🔄 Continuous 300s Polling Loop</span>
                <span class="lifecycle-feature-tag">♾️ Runs Indefinitely in Background</span>
                <span class="lifecycle-feature-tag">👤 Manual User Stop Required</span>
                <span class="lifecycle-feature-tag">🚀 Full Autonomous Multi-Step Pipeline</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Lifecycle Comparison Table Card -->
        <div class="modes-comparison-card">
          <div class="modes-comparison-header">
            <div class="modes-comparison-title-wrap">
              <span class="comparison-icon">⚖️</span>
              <div>
                <h3 class="comparison-title">Operational Lifecycle &amp; Parameters Comparison</h3>
                <p class="comparison-subtitle">विस्तृत कार्यप्रणाली तुलना • Comprehensive breakdown of runtime parameters, stop conditions, and resource allocation</p>
              </div>
            </div>
          </div>
          <div class="table-container">
            <table class="modes-comparison-table">
              <thead>
                <tr>
                  <th style="min-width: 180px;">Operational Parameter / आयाम</th>
                  <th>🧪 Test Mode (टेस्ट रन)</th>
                  <th>🛡️ Production Mode (प्रोडक्शन मोड)</th>
                  <th style="min-width: 140px;">Department Standard</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Execution Cycle / निष्पादन आवृत्ति</strong></td>
                  <td><span class="lifecycle-card-badge badge-test-mode">Single Cycle (1 Run Only)</span></td>
                  <td><span class="lifecycle-card-badge badge-prod-mode">Continuous Autonomous Loop</span></td>
                  <td>Dept 06 &amp; Dept 12</td>
                </tr>
                <tr>
                  <td><strong>Stop Condition / स्टॉप नियम</strong></td>
                  <td><strong>Automatic Auto-Stop</strong> — Chat/Question processing complete होते ही process खुद सुरक्षित exit हो जाता है</td>
                  <td><strong>Manual Stop Only</strong> — User जब तक Stop बटन नहीं दबाता, तब तक 300s loop अनवरत चलता रहता है</td>
                  <td>Rule 26 Zero-Hang</td>
                </tr>
                <tr>
                  <td><strong>Step 0 Polling Interval / पोलिंग अंतराल</strong></td>
                  <td><code>10.0s</code> (त्वरित परीक्षण एवं डिबग चक्र)</td>
                  <td><code>300.0s</code> (5 मिनट का स्थिर प्रोडक्शन अंतराल)</td>
                  <td>Dept 14 Telemetry</td>
                </tr>
                <tr>
                  <td><strong>Target Scope / लक्षित उपयोग</strong></td>
                  <td>Local verification, step testing, single question verification</td>
                  <td>24/7 autonomous monitoring &amp; unattended execution</td>
                  <td>Dept 08 QA Gates</td>
                </tr>
                <tr>
                  <td><strong>Config Persistence / डेटा सिंक</strong></td>
                  <td>Direct persistence to <code>step_9_complete_automation/config.json</code></td>
                  <td>Direct persistence to <code>step_9_complete_automation/config.json</code></td>
                  <td>Universal Rule 15 &amp; 23</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Tab 5: Config Panel (Always the Last Tab - System Runtime & Dashboard Configuration) -->
    <main id="tab-config" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-config">
      <div class="config-panel-container">
        <!-- Global Expand / Collapse All Controls -->
        <div class="config-global-toolbar">
          <div class="toolbar-title-wrap">
            <span class="toolbar-icon">⚙️</span>
            <div>
              <span class="toolbar-label">Unified Configuration Control Center</span>
              <span class="toolbar-badge">Cross-Step Synchronized</span>
            </div>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="btn-collapse-control" id="btn-expand-all-config" title="Expand all configuration cards and sections">
              <span>📂</span>
              <span>Expand All Sections</span>
            </button>
            <button type="button" class="btn-collapse-control" id="btn-collapse-all-config" title="Collapse all configuration cards and sections">
              <span>📁</span>
              <span>Collapse All Sections</span>
            </button>
          </div>
        </div>

        <!-- Section 1: System Runtime Configuration (step_9_complete_automation/config.json) -->
        <div class="config-section-card collapsible-card" id="runtime-config-section">
          <div class="config-section-header collapsible-card-header" id="header-runtime-config" role="button" tabindex="0" aria-expanded="false" aria-controls="body-runtime-config">
            <div class="config-section-title-wrap">
              <span class="config-section-icon">⚡</span>
              <div>
                <div class="config-section-title-row">
                  <h2 class="config-section-title">System Runtime Configuration</h2>
                  <span class="config-badge-live">step_9_complete_automation/config.json</span>
                </div>
                <p class="config-section-desc">Governs Step 0 Detector, Step 1 Identifier, Step 2 Window Focus, Step 3 Keyboard Automation &amp; Step 4 Reporting daemon engine</p>
              </div>
            </div>
            <div class="config-section-meta">
              <span class="status-indicator-live">● Live Engine Seam</span>
              <span class="accordion-chevron" aria-hidden="true">▾</span>
            </div>
          </div>

          <div class="config-section-body collapsible-card-body collapsed" id="body-runtime-config">
            <!-- 1. Execution Mode & Environment -->
            <div class="config-card-subgroup accordion-group" id="acc-runtime-mode">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-mode">
                <div class="config-subgroup-title">
                  <span>🛡️</span>
                  <span>Execution Mode &amp; Environment</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-mode">
                <p class="config-subgroup-desc">Select whether the automation pipeline runs in full autonomous Production mode (continuous loop until manually stopped) or fast Test mode (single-run auto-stop).</p>
                
                <div class="mode-pill-selector" role="radiogroup" aria-label="Operating Mode">
                  <button type="button" class="mode-pill {mode_prod_active_class}" id="cfg-mode-prod-btn" data-mode="production">
                    <div class="mode-pill-content">
                      <span class="mode-pill-icon">🛡️</span>
                      <div class="mode-pill-text">
                        <strong>Production Mode (Continuous Loop)</strong>
                        <small>Runs continuously in background until manually stopped by user (300.0s cycle)</small>
                      </div>
                    </div>
                    <span class="mode-pill-check">✓</span>
                  </button>
                  <button type="button" class="mode-pill {mode_test_active_class}" id="cfg-mode-test-btn" data-mode="test">
                    <div class="mode-pill-content">
                      <span class="mode-pill-icon">🧪</span>
                      <div class="mode-pill-text">
                        <strong>Test Mode (Single-Run Auto-Stop)</strong>
                        <small>Runs once and automatically stops as soon as the task completes (10.0s interval)</small>
                      </div>
                    </div>
                    <span class="mode-pill-check">✓</span>
                  </button>
                </div>
                <input type="hidden" id="cfg-runtime-mode" value="{cfg_mode_val}">

                <!-- Dedicated Horizontal Divider & Mode Lifecycle Callout Block -->
                <hr class="mode-lifecycle-divider">
                <div class="mode-lifecycle-callout">
                  <div class="mode-lifecycle-callout-header">
                    <span class="callout-header-icon">ℹ️</span>
                    <span>Execution Mode Lifecycle Rules / रन मोड कार्यप्रणाली एवं स्टॉप नियम</span>
                  </div>
                  <div class="mode-lifecycle-callout-grid">
                    <div class="mode-callout-item callout-test">
                      <div class="mode-callout-item-header">
                        <span class="mode-callout-item-title">🧪 <strong>Test Mode (टेस्ट रन)</strong></span>
                        <span class="lifecycle-card-badge badge-test-mode">Single-Run Auto-Stop</span>
                      </div>
                      <p class="mode-callout-item-desc">
                        जब आप <strong>Test Run</strong> चुनते हैं, तो ऑटोमेशन केवल <strong>1 बार (Single Cycle)</strong> निष्पादित होता है। जैसे ही टास्क या चैट प्रोसेसिंग पूर्ण होती है, प्रोसेस अपने आप (Automatically) सुरक्षित रूप से <strong>Stop</strong> हो जाता है। यह टेस्टिंग और सत्यापन के लिए आदर्श है।
                      </p>
                    </div>
                    <div class="mode-callout-item callout-prod">
                      <div class="mode-callout-item-header">
                        <span class="mode-callout-item-title">🛡️ <strong>Production Mode (प्रोडक्शन लेवल)</strong></span>
                        <span class="lifecycle-card-badge badge-prod-mode">Continuous Loop</span>
                      </div>
                      <p class="mode-callout-item-desc">
                        जब आप <strong>Production Level</strong> चुनते हैं, तो ऑटोमेशन बैकग्राउंड में अनवरत <strong>(Continuous Loop - 300s अंतराल)</strong> चलता रहता है। यह तब तक लगातार निगरानी और निष्पादन करता रहेगा जब तक कि आप स्वयं मैन्युअली <strong>Stop</strong> बटन न दबाएँ।
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Pipeline Steps Toggles (Enabled Steps) -->
            <div class="config-card-subgroup accordion-group" id="acc-runtime-steps">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-steps">
                <div class="config-subgroup-title">
                  <span>🔄</span>
                  <span>Pipeline Steps Toggles</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-steps">
                <p class="config-subgroup-desc">Toggle individual execution steps. Disabled steps are cleanly bypassed during execution with zero side-effects.</p>

                <div class="steps-toggle-grid">
                  <!-- Step 1 -->
                  <div class="step-toggle-card">
                    <div class="step-toggle-info">
                      <div class="step-toggle-title-row">
                        <span class="step-tag-pill">Step 1</span>
                        <strong>Find &amp; Focus Target Window</strong>
                      </div>
                      <span class="step-toggle-desc">Win32 process targeting, window activation &amp; focus</span>
                    </div>
                    <label class="switch-toggle" for="cfg-step1-enabled">
                      <input type="checkbox" id="cfg-step1-enabled" {step1_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>

                  <!-- Step 2 -->
                  <div class="step-toggle-card">
                    <div class="step-toggle-info">
                      <div class="step-toggle-title-row">
                        <span class="step-tag-pill">Step 2</span>
                        <strong>GUI Chat Select &amp; Focus</strong>
                      </div>
                      <span class="step-toggle-desc">Locates active pending conversation with Grill-Me options</span>
                    </div>
                    <label class="switch-toggle" for="cfg-step2-enabled">
                      <input type="checkbox" id="cfg-step2-enabled" {step2_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>

                  <!-- Step 3 -->
                  <div class="step-toggle-card">
                    <div class="step-toggle-info">
                      <div class="step-toggle-title-row">
                        <span class="step-tag-pill">Step 3</span>
                        <strong>Keyboard Recommendation Selector</strong>
                      </div>
                      <span class="step-toggle-desc">Autonomous Option 1 keypress navigation &amp; Enter selection</span>
                    </div>
                    <label class="switch-toggle" for="cfg-step3-enabled">
                      <input type="checkbox" id="cfg-step3-enabled" {step3_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>

                  <!-- Step 4 -->
                  <div class="step-toggle-card">
                    <div class="step-toggle-info">
                      <div class="step-toggle-title-row">
                        <span class="step-tag-pill">Step 4</span>
                        <strong>Visual Reporting &amp; Telemetry</strong>
                      </div>
                      <span class="step-toggle-desc">Telemetry recording, dynamic charts &amp; user inactivity HUD</span>
                    </div>
                    <label class="switch-toggle" for="cfg-step4-enabled">
                      <input type="checkbox" id="cfg-step4-enabled" {step4_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Timing & Delays Engine -->
            <div class="config-card-subgroup accordion-group" id="acc-runtime-timing">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-timing">
                <div class="config-subgroup-title">
                  <span>⏱️</span>
                  <span>Timing &amp; Delays Engine</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-timing">
                <p class="config-subgroup-desc">Configure sleep intervals, inter-step settle buffers, and user activity detection pauses.</p>

                <div class="timing-inputs-grid">
                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-prod-poll">
                      <span>Step 0 Polling Interval (Prod)</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-prod-poll" class="cfg-num-input" value="{step0_poll_prod}" step="5" min="1" max="3600">
                    <span class="input-card-help">Main idle polling cycle interval in production mode</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-test-poll">
                      <span>Step 0 Polling Interval (Test)</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-test-poll" class="cfg-num-input" value="{step0_poll_test}" step="1" min="1" max="300">
                    <span class="input-card-help">Accelerated validation cycle for testing</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-settle">
                      <span>Settle Delay Between Steps</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-settle" class="cfg-num-input" value="{settle_delay}" step="0.1" min="0" max="10">
                    <span class="input-card-help">Pause between step transitions for UI stability</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-activity-delay">
                      <span>Step 4 User Inactivity Delay</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-activity-delay" class="cfg-num-input" value="{step4_delay}" step="0.5" min="0" max="120">
                    <span class="input-card-help">Wait time after mouse/key detection before opening report</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step4-poll">
                      <span>Step 4 Activity Polling Interval</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-step4-poll" class="cfg-num-input" value="{step4_poll}" step="0.05" min="0.01" max="5">
                    <span class="input-card-help">Polling interval for user mouse and keystroke detection</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step1-focus">
                      <span>Step 1 Window Focus Delay</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-step1-focus" class="cfg-num-input" value="{step1_focus}" step="0.05" min="0" max="5">
                    <span class="input-card-help">Settle buffer after bringing Antigravity window to foreground</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step2-dom-settle">
                      <span>Step 2 DOM Click Settle Delay</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-step2-dom-settle" class="cfg-num-input" value="{step2_dom_settle}" step="0.05" min="0" max="5">
                    <span class="input-card-help">Settle pause after simulated click on chat row in GUI</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step3-countdown">
                      <span>Step 3 Countdown Delay</span>
                      <span class="unit-tag">sec</span>
                    </label>
                    <input type="number" id="cfg-timing-step3-countdown" class="cfg-num-input" value="{step3_countdown}" step="0.5" min="0" max="30">
                    <span class="input-card-help">Pre-execution countdown before keystrokes are transmitted</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step3-hold-ms">
                      <span>Step 3 Key Hold Duration</span>
                      <span class="unit-tag">ms</span>
                    </label>
                    <input type="number" id="cfg-timing-step3-hold-ms" class="cfg-num-input" value="{step3_hold_ms}" step="10" min="5" max="1000">
                    <span class="input-card-help">Hardware scan code hold duration during keyboard press</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step3-post-ms">
                      <span>Step 3 Post-Keypress Pause</span>
                      <span class="unit-tag">ms</span>
                    </label>
                    <input type="number" id="cfg-timing-step3-post-ms" class="cfg-num-input" value="{step3_post_ms}" step="25" min="10" max="5000">
                    <span class="input-card-help">Pause after each individual key stroke (बटन दबने के बाद का पॉज़)</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step3-inter-q-ms">
                      <span>Step 3 Inter-Question Delay</span>
                      <span class="unit-tag">ms</span>
                    </label>
                    <input type="number" id="cfg-timing-step3-inter-q-ms" class="cfg-num-input" value="{step3_inter_q_ms}" step="50" min="50" max="10000">
                    <span class="input-card-help">Pause between answering consecutive questionnaire prompts</span>
                  </div>

                  <div class="input-card">
                    <label class="input-card-label" for="cfg-timing-step3-round-ms">
                      <span>Step 3 Round Completion Pause</span>
                      <span class="unit-tag">ms</span>
                    </label>
                    <input type="number" id="cfg-timing-step3-round-ms" class="cfg-num-input" value="{step3_round_ms}" step="100" min="100" max="30000">
                    <span class="input-card-help">Cooldown pause after completing an entire questionnaire round</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 4. AntiGravity Governance Rules -->
            <div class="config-card-subgroup accordion-group" id="acc-runtime-governance">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-governance">
                <div class="config-subgroup-title">
                  <span>🛡️</span>
                  <span>AntiGravity Governance Rules</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-governance">
                <p class="config-subgroup-desc">Define targeting policies and threshold safety parameters.</p>

                <div class="governance-grid">
                  <div class="governance-card">
                    <div class="governance-info">
                      <label class="config-label" for="cfg-antigravity-require-grillme">Require Grill-Me Detection</label>
                      <span class="config-hint">Only act on Antigravity windows with active interactive questionnaire</span>
                    </div>
                    <label class="switch-toggle" for="cfg-antigravity-require-grillme">
                      <input type="checkbox" id="cfg-antigravity-require-grillme" {require_grill_me_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>

                  <div class="governance-card">
                    <div class="governance-info">
                      <label class="config-label" for="cfg-antigravity-active-hours">Active Window Max Age</label>
                      <span class="config-hint">Maximum window age before skipping stale conversation sessions</span>
                    </div>
                    <div class="input-with-suffix">
                      <input type="number" id="cfg-antigravity-active-hours" class="cfg-num-input" value="{active_hours}" step="0.5" min="0.5" max="168">
                      <span class="suffix-badge">hrs</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 5. Logging & Telemetry Engine -->
            <div class="config-card-subgroup accordion-group" id="acc-runtime-logging">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-logging">
                <div class="config-subgroup-title">
                  <span>📝</span>
                  <span>Logging &amp; Telemetry Engine</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-logging">
                <p class="config-subgroup-desc">Configure daemon logging output file and console verbosity standard.</p>

                <div class="logging-grid">
                  <div class="logging-card">
                    <div class="logging-info">
                      <label class="config-label" for="cfg-logging-verbose">Verbose Logging</label>
                      <span class="config-hint">Emit comprehensive step details and timestamps in logs</span>
                    </div>
                    <label class="switch-toggle" for="cfg-logging-verbose">
                      <input type="checkbox" id="cfg-logging-verbose" {verbose_checked}>
                      <span class="slider-round"></span>
                    </label>
                  </div>

                  <div class="logging-card">
                    <div class="logging-info">
                      <label class="config-label" for="cfg-logging-file">Log File Name</label>
                      <span class="config-hint">Target output file relative to step_9_complete_automation/</span>
                    </div>
                    <input type="text" id="cfg-logging-file" class="cfg-text-input" value="{log_file_val}">
                  </div>
                </div>
              </div>
            </div>

            <!-- 6. Action Controls & 1-Click CLI Apply -->
            <div class="config-card-subgroup actions-subgroup accordion-group" id="acc-runtime-actions">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-runtime-actions">
                <div class="config-subgroup-title">
                  <span>⚡</span>
                  <span>Action Controls &amp; 1-Click CLI Apply</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-runtime-actions">
                <p class="config-subgroup-desc">Apply settings, copy the 1-click PowerShell/Python CLI command to update config.json directly, or download the configuration.</p>

                <div class="runtime-action-buttons">
                  <button type="button" class="btn btn-primary" id="btn-save-runtime-cfg" title="Save runtime configuration in browser cache">
                    <span>💾</span>
                    <span>Save Runtime Config</span>
                  </button>
                  <button type="button" class="btn btn-cli" id="btn-copy-cli-cmd" title="Copy 1-click Python/PowerShell CLI command to persist into config.json directly">
                    <span>📋</span>
                    <span>Copy CLI Command / Apply</span>
                  </button>
                  <button type="button" class="btn btn-download" id="btn-download-runtime-cfg" title="Download updated config.json">
                    <span>📥</span>
                    <span>Download config.json</span>
                  </button>
                  <button type="button" class="btn" id="btn-toggle-json-preview" title="Show formatted JSON representation">
                    <span>👁️</span>
                    <span>Preview config.json</span>
                  </button>
                  <button type="button" class="btn btn-reset" id="btn-reset-runtime-cfg" title="Reset fields to original disk config">
                    <span>🔄</span>
                    <span>Reset to Defaults</span>
                  </button>
                </div>

                <!-- Collapsible Formatted JSON Preview Drawer -->
                <div class="json-preview-drawer" id="runtime-json-drawer" style="display: none;">
                  <div class="drawer-header">
                    <span class="drawer-title">📄 Preview: step_9_complete_automation/config.json</span>
                    <span class="drawer-badge">Live Formatted JSON</span>
                  </div>
                  <pre class="json-preview-code"><code id="runtime-json-preview">{runtime_config_json_str}</code></pre>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Section 2: Dashboard UI Configuration -->
        <div class="config-section-card collapsible-card" id="dashboard-config-section">
          <div class="config-section-header collapsible-card-header" id="header-dashboard-config" role="button" tabindex="0" aria-expanded="false" aria-controls="body-dashboard-config">
            <div class="config-section-title-wrap">
              <span class="config-section-icon">🎨</span>
              <div>
                <div class="config-section-title-row">
                  <h2 class="config-section-title">Dashboard UI Configuration</h2>
                  <span class="config-badge-browser">Browser LocalStorage • Visual Preferences</span>
                </div>
                <p class="config-section-desc">Customize live refresh cadence, display themes, motion preferences, synthesized chimes &amp; navigation defaults</p>
              </div>
            </div>
            <div class="config-section-meta">
              <span class="status-indicator-client">● Browser State</span>
              <span class="accordion-chevron" aria-hidden="true">▾</span>
            </div>
          </div>

          <div class="config-section-body collapsible-card-body collapsed" id="body-dashboard-config">
            <!-- 1. Auto-Refresh & Inactivity Timers -->
            <div class="config-card-subgroup accordion-group" id="acc-dash-timers">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-dash-timers">
                <div class="config-subgroup-title">
                  <span>⏱️</span>
                  <span>Auto-Refresh &amp; Inactivity Timers</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-dash-timers">
                <p class="config-subgroup-desc">Configure client-side polling intervals and auto-launch countdown timers.</p>

                <div class="dashboard-config-grid">
                  <!-- Setting 1: Auto-Refresh Interval -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-auto-refresh">Auto-Refresh Interval</label>
                      <span class="config-hint">Automatically reload live telemetry without manual page refresh</span>
                    </div>
                    <select id="cfg-auto-refresh" class="config-select">
                      <option value="0">Off (Manual Refresh Only)</option>
                      <option value="5">Every 5 Seconds</option>
                      <option value="10">Every 10 Seconds</option>
                      <option value="30">Every 30 Seconds</option>
                      <option value="60">Every 60 Seconds</option>
                    </select>
                  </div>

                  <!-- Setting 2: User Inactivity Delay -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-activity-delay">User Inactivity Delay</label>
                      <span class="config-hint">Time to wait after detecting user input before launching dashboard</span>
                    </div>
                    <select id="cfg-activity-delay" class="config-select">
                      <option value="5">5 Seconds (Ultra Responsive)</option>
                      <option value="10" selected>10 Seconds (Standard Default)</option>
                      <option value="15">15 Seconds (Relaxed Buffer)</option>
                      <option value="30">30 Seconds (Extended Idle)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Visual Theme & Motion Modes -->
            <div class="config-card-subgroup accordion-group" id="acc-dash-visual">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-dash-visual">
                <div class="config-subgroup-title">
                  <span>🎭</span>
                  <span>Visual Theme &amp; Motion Modes</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-dash-visual">
                <p class="config-subgroup-desc">Tune animation speeds, hardware-accelerated SVG motion, and question choice selection behaviors.</p>

                <div class="dashboard-config-grid">
                  <!-- Setting 4: Recommendation Selection Policy -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-selection-policy">Recommendation Selection Policy</label>
                      <span class="config-hint">Execution behavior for grill-me multi-choice questions</span>
                    </div>
                    <select id="cfg-selection-policy" class="config-select">
                      <option value="option1_auto">Option 1 (Recommended - Autonomous)</option>
                      <option value="prompt_manual">Prompt / Manual Review Required</option>
                      <option value="first_available">First Available Option</option>
                    </select>
                  </div>

                  <!-- Setting 5: Animation & Visual Effects -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-visual-effects">Animation &amp; Visual Effects</label>
                      <span class="config-hint">Hardware-accelerated SVG animations and card transitions</span>
                    </div>
                    <select id="cfg-visual-effects" class="config-select">
                      <option value="high">High (Smooth SVGs &amp; Animated Pulse Bus)</option>
                      <option value="reduced">Reduced Motion / Static (WCAG 2.1 Compliant)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Audio Alerts & Synthesizer Chime -->
            <div class="config-card-subgroup accordion-group" id="acc-dash-audio">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-dash-audio">
                <div class="config-subgroup-title">
                  <span>🔔</span>
                  <span>Audio Alerts &amp; Synthesizer Chime</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-dash-audio">
                <p class="config-subgroup-desc">Web Audio harmonic chime cues and run completion acoustic alerts.</p>

                <div class="dashboard-config-grid">
                  <!-- Setting 6: Sound Notifications -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-sound-notify">Audio Chime Notifications</label>
                      <span class="config-hint">Synthesized Web Audio chime when a new automation run is ingested</span>
                    </div>
                    <div class="dash-cfg-sound-row">
                      <select id="cfg-sound-notify" class="config-select">
                        <option value="enabled">Enabled (Subtle Web Audio Chime)</option>
                        <option value="disabled" selected>Disabled (Silent Operation)</option>
                      </select>
                      <button type="button" class="btn btn-sm btn-chime" id="btn-test-chime" title="Test synthesized Web Audio chime">
                        <span>🔔</span>
                        <span>Test Chime</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 4. Default Tab & Data Backups -->
            <div class="config-card-subgroup accordion-group" id="acc-dash-data">
              <div class="config-subgroup-header" role="button" tabindex="0" aria-expanded="false" aria-controls="subbody-dash-data">
                <div class="config-subgroup-title">
                  <span>💾</span>
                  <span>Default Tab &amp; Data Backups</span>
                </div>
                <span class="subaccordion-chevron" aria-hidden="true">▾</span>
              </div>
              <div class="config-subgroup-body collapsed" id="subbody-dash-data">
                <p class="config-subgroup-desc">Select initial view and manage export/reset operations for local telemetry storage.</p>

                <div class="dashboard-config-grid">
                  <!-- Setting 3: Default Landing Tab -->
                  <div class="dash-cfg-card">
                    <div class="dash-cfg-label-wrap">
                      <label class="config-label" for="cfg-default-tab">Default Landing Tab</label>
                      <span class="config-hint">Initial view displayed whenever the dashboard is opened</span>
                    </div>
                    <select id="cfg-default-tab" class="config-select">
                      <option value="overview">Overview (KPIs &amp; Visual Charts)</option>
                      <option value="chats">Chats (Conversations Breakdown)</option>
                      <option value="questions">Questions (Detailed Q&amp;A Ledger)</option>
                      <option value="modes">Mode Switch (Execution Mode &amp; Lifecycle)</option>
                      <option value="config">Config (Master System &amp; Dashboard Settings)</option>
                    </select>
                  </div>
                </div>

                <!-- Data Management & Save Row -->
                <div class="dash-cfg-footer">
                  <div class="dash-cfg-footer-left">
                    <button type="button" class="btn btn-export" id="cfg-export-btn" title="Download automation_history.json">
                      <span>📥</span>
                      <span>Export History JSON</span>
                    </button>
                    <button type="button" class="btn btn-reset-cfg" id="cfg-reset-btn" title="Reset all dashboard settings to defaults">
                      <span>🔄</span>
                      <span>Reset Dashboard Defaults</span>
                    </button>
                  </div>
                  <div class="dash-cfg-footer-right">
                    <span class="config-status-badge" id="cfg-status-badge">Active Settings Synced</span>
                    <button type="button" class="btn btn-primary" id="config-save-btn">
                      <span>💾</span>
                      <span>Save Dashboard Config</span>
                    </button>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </div>
      </div>
    </main>

    <!-- Configuration Modal Compatibility Wrapper (Department 04 & 05 Standard) -->
    <div class="modal-backdrop" id="config-modal" role="dialog" aria-modal="true" aria-labelledby="config-modal-title" style="display: none;">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-title-wrap">
            <span class="modal-icon">⚙️</span>
            <div>
              <h2 id="config-modal-title" class="modal-title">Dashboard & Automation Settings</h2>
              <p class="modal-subtitle">Full Master Configuration is now in the dedicated Config tab</p>
            </div>
          </div>
          <button type="button" class="modal-close-btn" id="config-close-btn" aria-label="Close Settings">&times;</button>
        </div>
        <div class="modal-body">
          <p style="margin-bottom: 14px; font-size: 0.9rem; color: var(--text-secondary);">
            Both <strong>⚡ System Runtime Configuration</strong> and <strong>🎨 Dashboard UI Configuration</strong> have been elevated into a dedicated, permanent tab:
          </p>
          <button type="button" class="btn btn-primary" style="width: 100%; justify-content: center; padding: 12px;" onclick="switchTab('config'); closeConfigModal();">
            <span>⚙️ Open Config Tab</span>
          </button>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" id="config-cancel-btn">Close</button>
        </div>
      </div>
    </div>

    <!-- Automation 1-Click Execution & Monitor Modal (Dept 04 & 06 Standard) -->
    <div class="modal-backdrop" id="automation-modal" style="display: none;" role="dialog" aria-modal="true" aria-labelledby="automation-modal-title">
      <div class="modal-content" style="max-width: 620px;">
        <div class="modal-header">
          <div class="modal-title-wrap">
            <span class="modal-icon">🚀</span>
            <div>
              <h2 class="modal-title" id="automation-modal-title">AutoSelect Antigravity Automation</h2>
              <p class="modal-subtitle">Autonomous Two-Factor Background Monitoring &amp; Execution</p>
            </div>
          </div>
          <button type="button" class="modal-close-btn" id="btn-close-automation-modal" aria-label="Close Automation Dialog">&times;</button>
        </div>
        <div class="modal-body">
          <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-md); padding: 14px 16px; margin-bottom: 18px;">
            <div style="display: flex; align-items: center; gap: 10px; font-weight: 600; color: var(--accent-emerald); margin-bottom: 6px;">
              <span>🟢</span>
              <span>Active Background Monitoring Engaged</span>
            </div>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0; line-height: 1.5;">
              AutoSelect Antigravity is actively scanning Antigravity chat transcripts. When a pending Grill-Me question appears, it will automatically focus the chat window and select the recommended option.
            </p>
          </div>

          <div style="margin-bottom: 16px;">
            <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 8px;">
              1-Click Server &amp; Terminal Execution Commands:
            </label>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <code style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--accent-emerald);">wscript start_dashboard_background.vbs</code>
                <button type="button" class="btn btn-sm" id="btn-copy-automation-vbs" style="padding: 4px 10px; font-size: 0.78rem;">📋 Copy</button>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <code style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--accent-emerald);">.\\run_dashboard.bat</code>
                <button type="button" class="btn btn-sm" id="btn-copy-automation-run-bat" style="padding: 4px 10px; font-size: 0.78rem;">📋 Copy</button>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <code style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--accent-indigo);">python step_9_complete_automation/complete_automation.py</code>
                <button type="button" class="btn btn-sm" id="btn-copy-automation-cmd" style="padding: 4px 10px; font-size: 0.78rem;">📋 Copy</button>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <code style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--accent-indigo);">.\\complete_automation.bat</code>
                <button type="button" class="btn btn-sm" id="btn-copy-automation-bat" style="padding: 4px 10px; font-size: 0.78rem;">📋 Copy</button>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 10px 14px;">
                <code style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--accent-indigo);">python step_9_complete_automation/complete_automation.py --dry-run</code>
                <button type="button" class="btn btn-sm" id="btn-copy-automation-dry-run" style="padding: 4px 10px; font-size: 0.78rem;">📋 Copy</button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" id="btn-close-automation-modal-footer">Close</button>
        </div>
      </div>
    </div>

    <!-- Animated Toast Notification Container -->
    <div class="toast-notification" id="toast-notify" role="alert" aria-live="polite"></div>

    <!-- Footer -->
    <footer>
      <div>Generated by AutoSelect Antigravity (Step 4 Reporting Subsystem)</div>
      <div>Department 06 (Backend & API) & Department 04 (UI/UX Design System) Standard</div>
      <div>Last Synchronized: <span style="font-family: var(--font-mono);">{last_updated_display}</span></div>
    </footer>
  </div>

  <!-- Raw History JSON Store for Zero-Dependency Dynamic Client Render -->
  <script id="history-data" type="application/json">
{history_json_str}
  </script>

  <!-- Raw System Runtime Configuration JSON Store -->
  <script id="runtime-config-data" type="application/json">
{runtime_config_json_str}
  </script>

  <script>
    (function() {{
      const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:')
        ? window.location.origin
        : 'http://127.0.0.1:8501';

      let statusPollTimer = null;
      let isAutomationActive = false;

      const rawData = JSON.parse(document.getElementById('history-data').textContent);
      const chats = rawData.chats || {{}};
      const searchChats = document.getElementById('search-chats');
      const searchQuestions = document.getElementById('search-questions');
      const searchOverview = document.getElementById('search-overview');
      const searchBoxFallback = document.getElementById('search-box');
      const summaryTbody = document.getElementById('summary-tbody');
      const detailsContainer = document.getElementById('details-container');
      const themeToggle = document.getElementById('theme-toggle');

      // Filter Toolbar elements
      const filterDateFrom = document.getElementById('filter-date-from');
      const filterDateTo = document.getElementById('filter-date-to');
      const filterChat = document.getElementById('filter-chat');
      const filterComplexity = document.getElementById('filter-complexity');
      const filterSpeed = document.getElementById('filter-speed');
      const filterResetBtn = document.getElementById('filter-reset-btn');
      const presetBtns = document.querySelectorAll('.preset-btn');
      const filterCountEl = document.getElementById('filter-count');
      const filterTotalEl = document.getElementById('filter-total');

      // Configuration Management & In-Dashboard Settings Engine
      const configModal = document.getElementById('config-modal');
      const configCloseBtn = document.getElementById('config-close-btn');
      const configCancelBtn = document.getElementById('config-cancel-btn');
      const configSaveBtn = document.getElementById('config-save-btn');
      const configResetBtn = document.getElementById('cfg-reset-btn');
      const configExportBtn = document.getElementById('cfg-export-btn');
      const toastNotify = document.getElementById('toast-notify');
      const cfgStatusBadge = document.getElementById('cfg-status-badge');
      const autoRefreshTag = document.getElementById('auto-refresh-tag');
      const autoRefreshBadge = document.getElementById('auto-refresh-badge') || autoRefreshTag;
      const refreshCountdownEl = document.getElementById('refresh-countdown');
      const btnHeaderRefresh = document.getElementById('btn-header-refresh');

      const cfgAutoRefresh = document.getElementById('cfg-auto-refresh');
      const cfgActivityDelay = document.getElementById('cfg-activity-delay');
      const cfgDefaultTab = document.getElementById('cfg-default-tab');
      const cfgSelectionPolicy = document.getElementById('cfg-selection-policy');
      const cfgVisualEffects = document.getElementById('cfg-visual-effects');
      const cfgSoundNotify = document.getElementById('cfg-sound-notify');

      // Runtime Automation Config Elements
      const rawRuntimeConfigScript = document.getElementById('runtime-config-data');
      let baseRuntimeConfig = {{}};
      try {{
        if (rawRuntimeConfigScript) {{
          baseRuntimeConfig = JSON.parse(rawRuntimeConfigScript.textContent);
        }}
      }} catch (e) {{}}

      const cfgModeProdBtn = document.getElementById('cfg-mode-prod-btn');
      const cfgModeTestBtn = document.getElementById('cfg-mode-test-btn');
      const cfgRuntimeMode = document.getElementById('cfg-runtime-mode');

      const cfgStep1Enabled = document.getElementById('cfg-step1-enabled');
      const cfgStep2Enabled = document.getElementById('cfg-step2-enabled');
      const cfgStep3Enabled = document.getElementById('cfg-step3-enabled');
      const cfgStep4Enabled = document.getElementById('cfg-step4-enabled');

      const cfgTimingProdPoll = document.getElementById('cfg-timing-prod-poll');
      const cfgTimingTestPoll = document.getElementById('cfg-timing-test-poll');
      const cfgTimingSettle = document.getElementById('cfg-timing-settle');
      const cfgTimingActivityDelay = document.getElementById('cfg-timing-activity-delay');
      const cfgTimingStep4Poll = document.getElementById('cfg-timing-step4-poll');
      const cfgTimingStep1Focus = document.getElementById('cfg-timing-step1-focus');
      const cfgTimingStep2DomSettle = document.getElementById('cfg-timing-step2-dom-settle');
      const cfgTimingStep3Countdown = document.getElementById('cfg-timing-step3-countdown');
      const cfgTimingStep3HoldMs = document.getElementById('cfg-timing-step3-hold-ms');
      const cfgTimingStep3PostMs = document.getElementById('cfg-timing-step3-post-ms');
      const cfgTimingStep3InterQMs = document.getElementById('cfg-timing-step3-inter-q-ms');
      const cfgTimingStep3RoundMs = document.getElementById('cfg-timing-step3-round-ms');

      const cfgAntigravityRequireGrillme = document.getElementById('cfg-antigravity-require-grillme');
      const cfgAntigravityActiveHours = document.getElementById('cfg-antigravity-active-hours');

      const cfgLoggingVerbose = document.getElementById('cfg-logging-verbose');
      const cfgLoggingFile = document.getElementById('cfg-logging-file');

      const btnSaveRuntimeCfg = document.getElementById('btn-save-runtime-cfg');
      const btnCopyCliCmd = document.getElementById('btn-copy-cli-cmd');
      const btnDownloadRuntimeCfg = document.getElementById('btn-download-runtime-cfg');
      const btnToggleJsonPreview = document.getElementById('btn-toggle-json-preview');
      const btnResetRuntimeCfg = document.getElementById('btn-reset-runtime-cfg');
      const runtimeJsonDrawer = document.getElementById('runtime-json-drawer');
      const runtimeJsonPreview = document.getElementById('runtime-json-preview');

      const btnTestChime = document.getElementById('btn-test-chime');

      function buildRuntimeConfigFromForm() {{
        const modeVal = (cfgRuntimeMode && cfgRuntimeMode.value) ? cfgRuntimeMode.value : 'production';
        const s1 = cfgStep1Enabled ? cfgStep1Enabled.checked : true;
        const s2 = cfgStep2Enabled ? cfgStep2Enabled.checked : true;
        const s3 = cfgStep3Enabled ? cfgStep3Enabled.checked : true;
        const s4 = cfgStep4Enabled ? cfgStep4Enabled.checked : true;

        const pPoll = cfgTimingProdPoll ? parseFloat(cfgTimingProdPoll.value) || 300.0 : 300.0;
        const tPoll = cfgTimingTestPoll ? parseFloat(cfgTimingTestPoll.value) || 10.0 : 10.0;
        const setl = cfgTimingSettle ? parseFloat(cfgTimingSettle.value) || 0.8 : 0.8;
        const actDel = cfgTimingActivityDelay ? parseFloat(cfgTimingActivityDelay.value) || 10.0 : 10.0;
        const s4Poll = cfgTimingStep4Poll ? parseFloat(cfgTimingStep4Poll.value) || 0.1 : 0.1;
        const s1Focus = cfgTimingStep1Focus ? parseFloat(cfgTimingStep1Focus.value) || 0.2 : 0.2;
        const s2DomSettle = cfgTimingStep2DomSettle ? parseFloat(cfgTimingStep2DomSettle.value) || 0.3 : 0.3;
        const s3Countdown = cfgTimingStep3Countdown ? parseFloat(cfgTimingStep3Countdown.value) || 3.0 : 3.0;
        const s3HoldMs = cfgTimingStep3HoldMs ? parseFloat(cfgTimingStep3HoldMs.value) || 50.0 : 50.0;
        const s3PostMs = cfgTimingStep3PostMs ? parseFloat(cfgTimingStep3PostMs.value) || 250.0 : 250.0;
        const s3InterQMs = cfgTimingStep3InterQMs ? parseFloat(cfgTimingStep3InterQMs.value) || 500.0 : 500.0;
        const s3RoundMs = cfgTimingStep3RoundMs ? parseFloat(cfgTimingStep3RoundMs.value) || 1000.0 : 1000.0;

        const reqGm = cfgAntigravityRequireGrillme ? cfgAntigravityRequireGrillme.checked : true;
        const actHrs = cfgAntigravityActiveHours ? parseFloat(cfgAntigravityActiveHours.value) || 12.0 : 12.0;

        const verb = cfgLoggingVerbose ? cfgLoggingVerbose.checked : true;
        const logF = (cfgLoggingFile && cfgLoggingFile.value.trim()) ? cfgLoggingFile.value.trim() : 'complete_automation.log';

        return {{
          _comment: "Step 9: Complete Automation Configuration - AutoSelect Antigravity Master Configuration",
          mode: modeVal,
          timing: {{
            step0_poll_interval_prod_seconds: pPoll,
            step0_poll_interval_test_seconds: tPoll,
            settle_delay_between_steps_seconds: setl,
            step4_user_activity_delay_seconds: actDel,
            step4_poll_interval_seconds: s4Poll,
            step1_window_focus_delay_seconds: s1Focus,
            step2_dom_click_settle_delay_seconds: s2DomSettle,
            step3_countdown_seconds: s3Countdown,
            step3_key_hold_delay_ms: s3HoldMs,
            step3_post_keypress_delay_ms: s3PostMs,
            step3_inter_question_delay_ms: s3InterQMs,
            step3_round_completion_pause_ms: s3RoundMs
          }},
          enabled_steps: {{
            step1_find_and_focus: s1,
            step2_gui_chat_select: s2,
            step3_keyboard_automation: s3,
            step4_reporting: s4
          }},
          antigravity: {{
            require_grill_me: reqGm,
            active_hours: actHrs
          }},
          logging: {{
            log_file: logF,
            verbose: verb
          }}
        }};
      }}

      function updateRuntimeJsonPreview() {{
        if (!runtimeJsonPreview) return;
        const cfgObj = buildRuntimeConfigFromForm();
        runtimeJsonPreview.textContent = JSON.stringify(cfgObj, null, 2);
      }}

      let lastUserModeChangeTime = 0;

      // Mode selection synchronization across Banner, Header & Config Tab (Dept 05 Standard)
      function setExecutionMode(mode, updateConfig = true) {{
        const targetMode = (mode === 'test') ? 'test' : 'production';
        const isTest = (targetMode === 'test');
        lastUserModeChangeTime = Date.now();

        // 0. Update Header Mode Badge (Instantly Reflect State)
        const headerModeBadge = document.getElementById('header-mode-badge');
        if (headerModeBadge) {{
          headerModeBadge.innerHTML = isTest ? '🧪 TEST' : '⚡ LIVE';
          headerModeBadge.style.background = isTest ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)';
          headerModeBadge.style.color = isTest ? '#fbbf24' : '#34d399';
          headerModeBadge.style.borderColor = isTest ? 'rgba(245, 158, 11, 0.35)' : 'rgba(16, 185, 129, 0.35)';
          headerModeBadge.title = isTest ? 'Operating in Single-Run Test Mode (Auto-Stop on Completion) • Click to toggle to LIVE' : 'Operating in Continuous Live Mode (Continuous Loop) • Click to toggle to TEST';
        }}

        // 1. Update hidden form input
        if (cfgRuntimeMode) cfgRuntimeMode.value = targetMode;

        // 2. Update Banner Mode Buttons
        const bannerTestBtn = document.getElementById('banner-mode-test-btn');
        const bannerProdBtn = document.getElementById('banner-mode-prod-btn');
        if (bannerTestBtn) bannerTestBtn.classList.toggle('active', isTest);
        if (bannerProdBtn) bannerProdBtn.classList.toggle('active', !isTest);

        // 3. Update Banner Lifecycle Cards Active Highlight
        const bannerTestCard = document.getElementById('banner-card-test');
        const bannerProdCard = document.getElementById('banner-card-prod');
        if (bannerTestCard) bannerTestCard.classList.toggle('active-mode-card', isTest);
        if (bannerProdCard) bannerProdCard.classList.toggle('active-mode-card', !isTest);

        // 4. Update Config Tab Mode Pills
        if (cfgModeTestBtn) cfgModeTestBtn.classList.toggle('active', isTest);
        if (cfgModeProdBtn) cfgModeProdBtn.classList.toggle('active', !isTest);

        // 5. Update Tab Badge for Mode Switch tab
        const tabModesBadge = document.getElementById('tab-modes-badge');
        if (tabModesBadge) {{
          tabModesBadge.textContent = isTest ? 'Test' : 'Prod';
          tabModesBadge.classList.toggle('tab-badge-test', isTest);
          tabModesBadge.classList.toggle('tab-badge-prod', !isTest);
        }}

        // 6. Update Current Config Object and Live JSON Preview
        if (typeof currentConfig !== 'undefined' && currentConfig) currentConfig.mode = targetMode;
        if (updateConfig && typeof updateRuntimeJsonPreview === 'function') {{
          updateRuntimeJsonPreview();
        }}

        // 7. Persist to LocalStorage and Server API immediately
        localStorage.setItem('asc_execution_mode', targetMode);
        localStorage.setItem('asc_automation_last_mode', targetMode);

        fetch(API_BASE + '/api/config/save', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ mode: targetMode }})
        }}).catch(() => {{}});
      }}

      // Banner Mode Buttons & Card Clicks
      const bannerModeTestBtn = document.getElementById('banner-mode-test-btn');
      const bannerModeProdBtn = document.getElementById('banner-mode-prod-btn');
      const bannerCardTest = document.getElementById('banner-card-test');
      const bannerCardProd = document.getElementById('banner-card-prod');

      if (bannerModeTestBtn) {{
        bannerModeTestBtn.addEventListener('click', () => setExecutionMode('test'));
      }}
      if (bannerModeProdBtn) {{
        bannerModeProdBtn.addEventListener('click', () => setExecutionMode('production'));
      }}
      if (bannerCardTest) {{
        bannerCardTest.addEventListener('click', () => setExecutionMode('test'));
      }}
      if (bannerCardProd) {{
        bannerCardProd.addEventListener('click', () => setExecutionMode('production'));
      }}

      // Header Mode Badge Click & Keydown to toggle mode
      const headerModeBadgeEl = document.getElementById('header-mode-badge');
      if (headerModeBadgeEl) {{
        headerModeBadgeEl.addEventListener('click', () => {{
          const currentMode = (typeof currentConfig !== 'undefined' && currentConfig && currentConfig.mode) ||
                              localStorage.getItem('asc_execution_mode') || 'production';
          const nextMode = (currentMode === 'test') ? 'production' : 'test';
          setExecutionMode(nextMode);
          showToast(`Switched mode to ${{nextMode === 'test' ? 'TEST' : 'LIVE'}}!`, 'info');
        }});
        headerModeBadgeEl.addEventListener('keydown', (e) => {{
          if (e.key === 'Enter' || e.key === ' ') {{
            e.preventDefault();
            headerModeBadgeEl.click();
          }}
        }});
      }}

      // Keyboard accessibility for interactive banner cards
      [bannerCardTest, bannerCardProd].forEach(card => {{
        if (card) {{
          card.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter' || e.key === ' ') {{
              e.preventDefault();
              card.click();
            }}
          }});
        }}
      }});

      // Config Tab Mode Pills
      if (cfgModeProdBtn && cfgModeTestBtn) {{
        cfgModeProdBtn.addEventListener('click', () => setExecutionMode('production'));
        cfgModeTestBtn.addEventListener('click', () => setExecutionMode('test'));
      }}

      // Form change listeners
      const runtimeInputs = [
        cfgStep1Enabled, cfgStep2Enabled, cfgStep3Enabled, cfgStep4Enabled,
        cfgTimingProdPoll, cfgTimingTestPoll, cfgTimingSettle, cfgTimingActivityDelay,
        cfgTimingStep4Poll, cfgTimingStep1Focus, cfgTimingStep2DomSettle,
        cfgTimingStep3Countdown, cfgTimingStep3HoldMs, cfgTimingStep3PostMs,
        cfgTimingStep3InterQMs, cfgTimingStep3RoundMs,
        cfgAntigravityRequireGrillme, cfgAntigravityActiveHours,
        cfgLoggingVerbose, cfgLoggingFile
      ];
      runtimeInputs.forEach(el => {{
        if (el) {{
          el.addEventListener('change', updateRuntimeJsonPreview);
          el.addEventListener('input', updateRuntimeJsonPreview);
        }}
      }});

      if (btnToggleJsonPreview && runtimeJsonDrawer) {{
        btnToggleJsonPreview.addEventListener('click', () => {{
          const isHidden = runtimeJsonDrawer.style.display === 'none';
          runtimeJsonDrawer.style.display = isHidden ? 'block' : 'none';
          btnToggleJsonPreview.innerHTML = isHidden ? '<span>👁️</span><span>Hide JSON Preview</span>' : '<span>👁️</span><span>Preview config.json</span>';
        }});
      }}

      if (btnSaveRuntimeCfg) {{
        btnSaveRuntimeCfg.addEventListener('click', async () => {{
          const cfgObj = buildRuntimeConfigFromForm();
          localStorage.setItem('asc_runtime_config', JSON.stringify(cfgObj));
          updateRuntimeJsonPreview();

          try {{
            const controller = new AbortController();
            const tid = setTimeout(() => controller.abort(), 3000);
            const resp = await fetch(API_BASE + '/api/config/save', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify(cfgObj),
              signal: controller.signal
            }});
            clearTimeout(tid);

            if (resp.ok) {{
              const res = await resp.json();
              if (res.success) {{
                showToast('💾 Runtime configuration saved directly to config.json on disk!', 'success');
                return;
              }}
            }}
          }} catch (e) {{
            // Server offline
          }}
          showToast('✓ Runtime config staged! Use [Copy CLI Command] or start dashboard server to persist to config.json', 'success');
        }});
      }}

      function copyTextToClipboard(text, successMsg) {{
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text).then(() => {{
            showToast(successMsg, 'success');
          }}).catch(() => {{
            fallbackClipboardCopy(text, successMsg);
          }});
        }} else {{
          fallbackClipboardCopy(text, successMsg);
        }}
      }}

      function fallbackClipboardCopy(text, successMsg) {{
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try {{
          document.execCommand('copy');
          showToast(successMsg, 'success');
        }} catch (e) {{
          showToast('❌ Copy to clipboard failed: ' + e.message, 'error');
        }}
        document.body.removeChild(ta);
      }}

      if (btnCopyCliCmd) {{
        btnCopyCliCmd.addEventListener('click', () => {{
          const cfgObj = buildRuntimeConfigFromForm();
          const jsonStr = JSON.stringify(cfgObj).replace(/"/g, '\"');
          const pyCmd = `python -c "import json, pathlib; p=pathlib.Path('step_9_complete_automation/config.json'); p.write_text(json.dumps(json.loads('${{jsonStr}}'), indent=2), encoding='utf-8'); print('[SUCCESS] config.json updated successfully!')"`;
          copyTextToClipboard(pyCmd, '📋 1-Click CLI Command copied! Paste into PowerShell to apply directly to config.json.');
        }});
      }}

      if (btnDownloadRuntimeCfg) {{
        btnDownloadRuntimeCfg.addEventListener('click', () => {{
          try {{
            const cfgObj = buildRuntimeConfigFromForm();
            const blob = new Blob([JSON.stringify(cfgObj, null, 2)], {{ type: 'application/json;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'config.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('📥 config.json downloaded successfully!', 'success');
          }} catch (err) {{
            showToast('❌ Download failed: ' + err.message, 'error');
          }}
        }});
      }}

      if (btnResetRuntimeCfg) {{
        btnResetRuntimeCfg.addEventListener('click', () => {{
          if (!baseRuntimeConfig || Object.keys(baseRuntimeConfig).length === 0) return;
          const modeVal = baseRuntimeConfig.mode || 'production';
          if (cfgRuntimeMode) cfgRuntimeMode.value = modeVal;
          if (modeVal === 'production') {{
            if (cfgModeProdBtn) cfgModeProdBtn.classList.add('active');
            if (cfgModeTestBtn) cfgModeTestBtn.classList.remove('active');
          }} else {{
            if (cfgModeTestBtn) cfgModeTestBtn.classList.add('active');
            if (cfgModeProdBtn) cfgModeProdBtn.classList.remove('active');
          }}

          const steps = baseRuntimeConfig.enabled_steps || {{}};
          if (cfgStep1Enabled) cfgStep1Enabled.checked = steps.step1_find_and_focus !== false;
          if (cfgStep2Enabled) cfgStep2Enabled.checked = steps.step2_gui_chat_select !== false;
          if (cfgStep3Enabled) cfgStep3Enabled.checked = steps.step3_keyboard_automation !== false;
          if (cfgStep4Enabled) cfgStep4Enabled.checked = steps.step4_reporting !== false;

          const tm = baseRuntimeConfig.timing || {{}};
          if (cfgTimingProdPoll) cfgTimingProdPoll.value = tm.step0_poll_interval_prod_seconds ?? 300.0;
          if (cfgTimingTestPoll) cfgTimingTestPoll.value = tm.step0_poll_interval_test_seconds ?? 10.0;
          if (cfgTimingSettle) cfgTimingSettle.value = tm.settle_delay_between_steps_seconds ?? 0.8;
          if (cfgTimingActivityDelay) cfgTimingActivityDelay.value = tm.step4_user_activity_delay_seconds ?? 10.0;
          if (cfgTimingStep4Poll) cfgTimingStep4Poll.value = tm.step4_poll_interval_seconds ?? 0.1;
          if (cfgTimingStep1Focus) cfgTimingStep1Focus.value = tm.step1_window_focus_delay_seconds ?? 0.2;
          if (cfgTimingStep2DomSettle) cfgTimingStep2DomSettle.value = tm.step2_dom_click_settle_delay_seconds ?? 0.3;
          if (cfgTimingStep3Countdown) cfgTimingStep3Countdown.value = tm.step3_countdown_seconds ?? 3.0;
          if (cfgTimingStep3HoldMs) cfgTimingStep3HoldMs.value = tm.step3_key_hold_delay_ms ?? 50.0;
          if (cfgTimingStep3PostMs) cfgTimingStep3PostMs.value = tm.step3_post_keypress_delay_ms ?? 250.0;
          if (cfgTimingStep3InterQMs) cfgTimingStep3InterQMs.value = tm.step3_inter_question_delay_ms ?? 500.0;
          if (cfgTimingStep3RoundMs) cfgTimingStep3RoundMs.value = tm.step3_round_completion_pause_ms ?? 1000.0;

          const ag = baseRuntimeConfig.antigravity || {{}};
          if (cfgAntigravityRequireGrillme) cfgAntigravityRequireGrillme.checked = ag.require_grill_me !== false;
          if (cfgAntigravityActiveHours) cfgAntigravityActiveHours.value = ag.active_hours || 12.0;

          const lg = baseRuntimeConfig.logging || {{}};
          if (cfgLoggingVerbose) cfgLoggingVerbose.checked = lg.verbose !== false;
          if (cfgLoggingFile) cfgLoggingFile.value = lg.log_file || 'complete_automation.log';

          updateRuntimeJsonPreview();
          showToast('🔄 Runtime configuration reset to disk defaults!', 'info');
        }});
      }}

      if (btnTestChime) {{
        btnTestChime.addEventListener('click', () => {{
          playSoundChime();
          showToast('🔔 Synthesized Web Audio chime played!', 'info');
        }});
      }}

      const DEFAULT_CONFIG = {{
        autoRefresh: 0,
        activityDelay: 10,
        defaultTab: 'overview',
        selectionPolicy: 'option1_auto',
        visualEffects: 'high',
        soundNotify: 'disabled'
      }};

      function loadConfig() {{
        try {{
          const raw = localStorage.getItem('asc_dashboard_config');
          if (raw) return {{ ...DEFAULT_CONFIG, ...JSON.parse(raw) }};
        }} catch (e) {{}}
        return {{ ...DEFAULT_CONFIG }};
      }}

      let currentConfig = loadConfig();

      function showToast(msg, type = 'success') {{
        if (!toastNotify) return;
        toastNotify.textContent = msg;
        toastNotify.className = 'toast-notification active ' + type;
        setTimeout(() => {{
          toastNotify.classList.remove('active');
        }}, 3500);
      }}

      function playSoundChime() {{
        try {{
          const AudioContext = window.AudioContext || window.webkitAudioContext;
          if (!AudioContext) return;
          const ctx = new AudioContext();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(587.33, ctx.currentTime);
          osc.frequency.exponentialRampToValueAtTime(880.0, ctx.currentTime + 0.15);
          gain.gain.setValueAtTime(0.12, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          osc.stop(ctx.currentTime + 0.35);
        }} catch (e) {{}}
      }}

      function syncFormWithConfig(cfg) {{
        if (cfgAutoRefresh) cfgAutoRefresh.value = String(cfg.autoRefresh);
        if (cfgActivityDelay) cfgActivityDelay.value = String(cfg.activityDelay);
        if (cfgDefaultTab) cfgDefaultTab.value = cfg.defaultTab;
        if (cfgSelectionPolicy) cfgSelectionPolicy.value = cfg.selectionPolicy;
        if (cfgVisualEffects) cfgVisualEffects.value = cfg.visualEffects;
        if (cfgSoundNotify) cfgSoundNotify.value = cfg.soundNotify;
        if (cfgStatusBadge) cfgStatusBadge.textContent = 'Active Settings Synced';
      }}

      let refreshTimer = null;
      let countdownSeconds = 0;

      function startLivePolling(intervalSeconds) {{
        if (refreshTimer) {{
          clearInterval(refreshTimer);
          refreshTimer = null;
        }}
        countdownSeconds = intervalSeconds;
        if (autoRefreshTag) autoRefreshTag.style.display = 'inline';
        if (autoRefreshBadge && autoRefreshBadge !== autoRefreshTag) autoRefreshBadge.style.display = 'inline-flex';
        if (refreshCountdownEl) refreshCountdownEl.textContent = countdownSeconds + 's';
        if (btnHeaderRefresh) btnHeaderRefresh.classList.add('is-polling');

        refreshTimer = setInterval(() => {{
          countdownSeconds -= 1;
          if (refreshCountdownEl) refreshCountdownEl.textContent = countdownSeconds + 's';
          if (countdownSeconds <= 0) {{
            clearInterval(refreshTimer);
            try {{
              sessionStorage.setItem('asc_scroll_y', String(window.scrollY));
            }} catch (e) {{}}
            location.reload();
          }}
        }}, 1000);
      }}

      function stopLivePolling() {{
        if (refreshTimer) {{
          clearInterval(refreshTimer);
          refreshTimer = null;
        }}
        if (autoRefreshTag) autoRefreshTag.style.display = 'none';
        if (autoRefreshBadge && autoRefreshBadge !== autoRefreshTag) autoRefreshBadge.style.display = 'none';
        if (btnHeaderRefresh) btnHeaderRefresh.classList.remove('is-polling');
      }}

      function applyDynamicSettings(cfg) {{
        if (cfg.visualEffects === 'reduced') {{
          document.documentElement.classList.add('reduced-motion');
        }} else {{
          document.documentElement.classList.remove('reduced-motion');
        }}

        // Full page reload timer ONLY if explicitly enabled by user (> 0)
        const configuredRefresh = parseInt(cfg.autoRefresh, 10);
        if (configuredRefresh > 0) {{
          startLivePolling(configuredRefresh);
        }} else {{
          stopLivePolling();
        }}
      }}

      // ======================================================================
      // Dynamic Automation Start/Stop Control (AutoSelect Antigravity Engine)
      // ======================================================================
      const automationToggleBtn = document.getElementById('automation-toggle-btn');
      const controlIconEl = document.getElementById('control-icon');
      const controlLabelEl = document.getElementById('control-label');
      const dashboardStatusPill = document.getElementById('dashboard-status-pill');
      const automationModal = document.getElementById('automation-modal');
      const btnCloseAutomationModal = document.getElementById('btn-close-automation-modal');
      const btnCloseAutomationModalFooter = document.getElementById('btn-close-automation-modal-footer');
      const btnCopyAutomationCmd = document.getElementById('btn-copy-automation-cmd');
      const btnCopyAutomationBat = document.getElementById('btn-copy-automation-bat');
      const btnCopyAutomationDryRun = document.getElementById('btn-copy-automation-dry-run');

      function getAutomationRunning() {{
        return localStorage.getItem('asc_automation_running') === 'true';
      }}

      let userInitiatedStop = false;
      let isServerBridgeOnline = false;
      let serverHealthPollTimer = null;
      let isCheckingStatus = false;

      function updateServerBridgeUI(isOnline) {{
        const bridgePill = document.getElementById('server-bridge-pill');
        if (!bridgePill) return;
        if (isOnline) {{
          bridgePill.className = 'status-pill status-bridge-online';
          bridgePill.innerHTML = '🟢 Server Online';
          bridgePill.setAttribute('title', 'Server Bridge connected: Control daemon is active on port 8501');
        }} else {{
          bridgePill.className = 'status-pill status-bridge-offline';
          bridgePill.innerHTML = '🔴 Server Offline';
          bridgePill.setAttribute('title', 'Server Bridge offline on port 8501. Run start_dashboard_background.vbs or run_dashboard.bat to connect.');
        }}
      }}

      function updateProcessStatusUI(status) {{
        const dashboardStatusPill = document.getElementById('dashboard-status-pill');
        const modesStatusPill = document.getElementById('modes-status-pill');

        let pillClass = 'status-pill status-idle';
        let pillHtml = '⚪ Inactive';
        let modesHtml = '⚪ Automation Inactive';
        let pillTitle = 'Automation is not running';

        if (status && status.running) {{
          if (status.is_paused) {{
            pillClass = 'status-pill status-paused';
            pillHtml = '⏸️ Paused (User Active)';
            modesHtml = '⏸️ Paused (User Active)';
            pillTitle = 'Automation paused: user activity detected (idle < 60s)';
          }} else {{
            pillClass = 'status-pill status-active';
            pillHtml = '🟢 Active';
            modesHtml = '🟢 Active';
            pillTitle = 'Automation active: background monitoring enabled';
          }}
        }}

        if (dashboardStatusPill) {{
          dashboardStatusPill.className = pillClass;
          dashboardStatusPill.innerHTML = pillHtml;
          dashboardStatusPill.setAttribute('title', pillTitle);
        }}

        if (modesStatusPill) {{
          modesStatusPill.className = pillClass;
          modesStatusPill.innerHTML = modesHtml;
          modesStatusPill.setAttribute('title', pillTitle);
        }}
      }}

      async function checkProcessStatus() {{
        if (isCheckingStatus) return isAutomationActive;
        isCheckingStatus = true;
        try {{
          const controller = new AbortController();
          const tid = setTimeout(() => controller.abort(), 2000);
          const resp = await fetch(API_BASE + '/api/automation/status', {{
            method: 'GET',
            signal: controller.signal
          }});
          clearTimeout(tid);
          if (resp.ok) {{
            const res = await resp.json();
            if (res.success && res.data) {{
              const wasOffline = !isServerBridgeOnline;
              isServerBridgeOnline = true;
              updateServerBridgeUI(true);

              if (wasOffline) {{
                showToast('🟢 Server Reconnected! Control daemon is active on port 8501.', 'success');
              }}

              const running = !!res.data.running;
              const wasRunning = isAutomationActive || getAutomationRunning();
              const recordedMode = localStorage.getItem('asc_automation_last_mode') || res.data.mode || (cfgRuntimeMode ? cfgRuntimeMode.value : 'production');

              if (res.data.mode && typeof res.data.mode === 'string') {{
                const serverMode = res.data.mode.trim().toLowerCase();
                if (Date.now() - lastUserModeChangeTime > 4000) {{
                  const localMode = (cfgRuntimeMode ? cfgRuntimeMode.value : (currentConfig ? currentConfig.mode : '')) || 'production';
                  if (serverMode !== localMode.toLowerCase()) {{
                    setExecutionMode(serverMode, false);
                  }}
                }}
              }}
              if (running) {{
                if (res.data.mode) {{
                  localStorage.setItem('asc_automation_last_mode', res.data.mode);
                }}
              }} else if (wasRunning && !userInitiatedStop) {{
                // Automation finished and exited automatically
                if (recordedMode === 'test') {{
                  showToast('✅ Test Mode task completed! Automation stopped automatically.', 'success');
                }} else {{
                  showToast('⏹️ Automation process completed or stopped.', 'info');
                }}
              }}

              userInitiatedStop = false;
              isAutomationActive = running;
              localStorage.setItem('asc_automation_running', String(running));
              updateAutomationUI(running, false, res.data);
              updateProcessStatusUI(res.data);
              return running;
            }}
          }}
        }} catch (e) {{
          // Server offline / not reachable
          isServerBridgeOnline = false;
          updateServerBridgeUI(false);
          updateProcessStatusUI({{ running: false, is_paused: false }});
          isAutomationActive = false;
          localStorage.setItem('asc_automation_running', 'false');
          updateAutomationUI(false, false);
        }} finally {{
          isCheckingStatus = false;
        }}
        return false;
      }}

      function startServerHealthPolling(intervalMs = 3000) {{
        if (serverHealthPollTimer) clearInterval(serverHealthPollTimer);
        checkProcessStatus();
        serverHealthPollTimer = setInterval(checkProcessStatus, intervalMs);
      }}

      function startProcessStatusPolling(intervalMs = 2000) {{
        startServerHealthPolling(intervalMs);
      }}

      function stopProcessStatusPolling() {{
        startServerHealthPolling(3000);
      }}

      function updateAutomationUI(isRunning, triggerToast = false, statusData = null) {{
        const modesAutomationToggleBtn = document.getElementById('modes-automation-toggle-btn');
        const modesControlIconEl = document.getElementById('modes-control-icon');
        const modesControlLabelEl = document.getElementById('modes-control-label');

        if (isRunning) {{
          if (automationToggleBtn) {{
            automationToggleBtn.classList.remove('state-stopped');
            automationToggleBtn.classList.add('state-running');
            if (controlIconEl) controlIconEl.textContent = '⏹️';
            if (controlLabelEl) controlLabelEl.textContent = 'Stop';
            automationToggleBtn.setAttribute('title', 'Click to Stop AutoSelect Antigravity Automation');
          }}

          if (modesAutomationToggleBtn) {{
            modesAutomationToggleBtn.classList.remove('state-stopped');
            modesAutomationToggleBtn.classList.add('state-running');
            if (modesControlIconEl) modesControlIconEl.textContent = '⏹️';
            if (modesControlLabelEl) modesControlLabelEl.textContent = 'Stop';
            modesAutomationToggleBtn.setAttribute('title', 'Click to Stop AutoSelect Antigravity Automation');
          }}

          updateProcessStatusUI(statusData || {{ running: true, is_paused: false }});
          startProcessStatusPolling(2000);

          if (triggerToast) {{
            showToast('🚀 Automation Started! AutoSelect Antigravity is actively monitoring chats.', 'success');
          }}
        }} else {{
          if (automationToggleBtn) {{
            automationToggleBtn.classList.remove('state-running');
            automationToggleBtn.classList.add('state-stopped');
            if (controlIconEl) controlIconEl.textContent = '▶️';
            if (controlLabelEl) controlLabelEl.textContent = 'Start';
            automationToggleBtn.setAttribute('title', 'Click to Start AutoSelect Antigravity Automation');
          }}

          if (modesAutomationToggleBtn) {{
            modesAutomationToggleBtn.classList.remove('state-running');
            modesAutomationToggleBtn.classList.add('state-stopped');
            if (modesControlIconEl) modesControlIconEl.textContent = '▶️';
            if (modesControlLabelEl) modesControlLabelEl.textContent = 'Start';
            modesAutomationToggleBtn.setAttribute('title', 'Click to Start AutoSelect Antigravity Automation');
          }}

          updateProcessStatusUI(statusData || {{ running: false, is_paused: false }});
          stopProcessStatusPolling();

          if (triggerToast) {{
            showToast('⏹️ Automation Stopped.', 'info');
          }}
        }}
      }}

      function openAutomationModal() {{
        if (automationModal) {{
          automationModal.style.display = 'flex';
          setTimeout(() => automationModal.classList.add('active'), 10);
        }}
      }}

      function closeAutomationModal() {{
        if (automationModal) {{
          automationModal.classList.remove('active');
          setTimeout(() => automationModal.style.display = 'none', 250);
        }}
      }}

      const modesAutomationToggleBtn = document.getElementById('modes-automation-toggle-btn');
      if (modesAutomationToggleBtn && automationToggleBtn) {{
        modesAutomationToggleBtn.addEventListener('click', () => {{
          automationToggleBtn.click();
        }});
      }}

      if (automationToggleBtn) {{
        automationToggleBtn.addEventListener('click', async () => {{
          const currentlyRunning = isAutomationActive || getAutomationRunning();

          if (!currentlyRunning && !isServerBridgeOnline) {{
            const isAlive = await checkProcessStatus();
            if (!isAlive) {{
              showToast(
                `⚠️ Local Control Server is offline at ${{API_BASE}}. Run 'wscript start_dashboard_background.vbs' or 'run_dashboard.bat' to launch the server.`,
                'error',
                7000
              );
              openAutomationModal();
              return;
            }}
          }}

          automationToggleBtn.disabled = true;
          if (modesAutomationToggleBtn) modesAutomationToggleBtn.disabled = true;
          if (controlLabelEl) controlLabelEl.textContent = currentlyRunning ? 'Stopping...' : 'Starting...';
          const modesControlLabelEl = document.getElementById('modes-control-label');
          if (modesControlLabelEl) modesControlLabelEl.textContent = currentlyRunning ? 'Stopping...' : 'Starting...';

          if (currentlyRunning) {{
            userInitiatedStop = true;
          }}

          try {{
            const endpoint = API_BASE + (currentlyRunning ? '/api/automation/stop' : '/api/automation/start');
            const selectedMode = (cfgRuntimeMode ? cfgRuntimeMode.value : null) || 'production';
            const payload = currentlyRunning ? {{}} : {{ mode: selectedMode }};

            if (!currentlyRunning) {{
              localStorage.setItem('asc_automation_last_mode', selectedMode);
              userInitiatedStop = false;
            }}

            const controller = new AbortController();
            const tid = setTimeout(() => controller.abort(), 6000);

            const resp = await fetch(endpoint, {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify(payload),
              signal: controller.signal
            }});
            clearTimeout(tid);

            if (resp.ok) {{
              const res = await resp.json();
              if (res.success && res.data) {{
                const isNowRunning = !!res.data.running;
                isAutomationActive = isNowRunning;
                localStorage.setItem('asc_automation_running', String(isNowRunning));
                updateAutomationUI(isNowRunning, true);
                return;
              }} else {{
                showToast(`❌ Action failed: ${{res.error?.message || res.message || 'Server error'}}`, 'error');
              }}
            }} else {{
              throw new Error(`HTTP ${{resp.status}}`);
            }}
          }} catch (err) {{
            isServerBridgeOnline = false;
            updateServerBridgeUI(false);
            showToast(
              `⚠️ Local Control Server not reachable at ${{API_BASE}}. Run 'wscript start_dashboard_background.vbs' or 'run_dashboard.bat' to start the server.`,
              'error',
              7000
            );
            openAutomationModal();
            isAutomationActive = false;
            localStorage.setItem('asc_automation_running', 'false');
            updateAutomationUI(false, false);
          }} finally {{
            automationToggleBtn.disabled = false;
            if (modesAutomationToggleBtn) modesAutomationToggleBtn.disabled = false;
          }}
        }});
      }}

      if (btnCloseAutomationModal) {{
        btnCloseAutomationModal.addEventListener('click', closeAutomationModal);
      }}
      if (btnCloseAutomationModalFooter) {{
        btnCloseAutomationModalFooter.addEventListener('click', closeAutomationModal);
      }}
      if (automationModal) {{
        automationModal.addEventListener('click', (e) => {{
          if (e.target === automationModal) closeAutomationModal();
        }});
      }}
      const btnCopyAutomationVbs = document.getElementById('btn-copy-automation-vbs');
      const btnCopyAutomationRunBat = document.getElementById('btn-copy-automation-run-bat');

      if (btnCopyAutomationVbs) {{
        btnCopyAutomationVbs.addEventListener('click', () => {{
          copyTextToClipboard('wscript start_dashboard_background.vbs', '📋 VBS background launcher command copied to clipboard!');
        }});
      }}
      if (btnCopyAutomationRunBat) {{
        btnCopyAutomationRunBat.addEventListener('click', () => {{
          copyTextToClipboard('.\\run_dashboard.bat', '📋 Dashboard launcher batch command copied to clipboard!');
        }});
      }}

      if (btnCopyAutomationCmd) {{
        btnCopyAutomationCmd.addEventListener('click', () => {{
          copyTextToClipboard('python step_9_complete_automation/complete_automation.py', '📋 Execution command copied to clipboard!');
        }});
      }}
      if (btnCopyAutomationBat) {{
        btnCopyAutomationBat.addEventListener('click', () => {{
          copyTextToClipboard('.\\complete_automation.bat', '📋 Batch script command copied to clipboard!');
        }});
      }}
      if (btnCopyAutomationDryRun) {{
        btnCopyAutomationDryRun.addEventListener('click', () => {{
          copyTextToClipboard('python step_9_complete_automation/complete_automation.py --dry-run', '📋 Dry-run test command copied to clipboard!');
        }});
      }}

      // ======================================================================
      // Collapsible Sections & Accordion Controllers (Dept 04 & 05 Standards)
      // ======================================================================
      function setElementCollapsed(header, isCollapsed) {{
        if (!header) return;
        header.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
        const targetId = header.getAttribute('aria-controls');
        const body = targetId ? document.getElementById(targetId) : null;
        const chevron = header.querySelector('.accordion-chevron, .subaccordion-chevron');

        if (body) {{
          if (isCollapsed) {{
            body.classList.add('collapsed');
          }} else {{
            body.classList.remove('collapsed');
          }}
        }}
        if (chevron) {{
          chevron.textContent = isCollapsed ? '▸' : '▾';
        }}
      }}

      function toggleHeader(header) {{
        if (!header) return;
        const isCurrentlyExpanded = header.getAttribute('aria-expanded') === 'true';
        if (isCurrentlyExpanded) {{
          setElementCollapsed(header, true);
        }} else {{
          // Mutual exclusion: collapse any sibling or other open item in same group
          if (header.classList.contains('collapsible-card-header')) {{
            const container = header.closest('.config-panel-container') || document;
            container.querySelectorAll('.collapsible-card-header').forEach(other => {{
              if (other !== header) {{
                setElementCollapsed(other, true);
              }}
            }});
          }} else if (header.classList.contains('config-subgroup-header')) {{
            const parentBody = header.closest('.config-section-body') || header.closest('.collapsible-card') || document;
            parentBody.querySelectorAll('.config-subgroup-header').forEach(other => {{
              if (other !== header) {{
                setElementCollapsed(other, true);
              }}
            }});
          }}
          setElementCollapsed(header, false);
        }}
      }}

      const allCollapsibleHeaders = document.querySelectorAll('.collapsible-card-header, .config-subgroup-header');
      allCollapsibleHeaders.forEach(header => {{
        header.addEventListener('click', (e) => {{
          if (['BUTTON', 'INPUT', 'SELECT', 'A'].includes(e.target.tagName)) return;
          toggleHeader(header);
        }});
        header.addEventListener('keydown', (e) => {{
          if (e.key === 'Enter' || e.key === ' ') {{
            if (['BUTTON', 'INPUT', 'SELECT', 'A'].includes(e.target.tagName)) return;
            e.preventDefault();
            toggleHeader(header);
          }}
        }});
      }});

      const btnExpandAllConfig = document.getElementById('btn-expand-all-config');
      const btnCollapseAllConfig = document.getElementById('btn-collapse-all-config');

      if (btnExpandAllConfig) {{
        btnExpandAllConfig.addEventListener('click', () => {{
          allCollapsibleHeaders.forEach(header => setElementCollapsed(header, false));
          showToast('📂 All configuration sections expanded', 'info');
        }});
      }}

      if (btnCollapseAllConfig) {{
        btnCollapseAllConfig.addEventListener('click', () => {{
          allCollapsibleHeaders.forEach(header => setElementCollapsed(header, true));
          showToast('📁 All configuration sections collapsed', 'info');
        }});
      }}

      function openConfigModal() {{
        switchTab('config');
      }}

      function closeConfigModal() {{
        if (configModal) {{
          configModal.classList.remove('active');
          setTimeout(() => configModal.style.display = 'none', 250);
        }}
      }}

      if (configCloseBtn) configCloseBtn.addEventListener('click', closeConfigModal);
      if (configCancelBtn) configCancelBtn.addEventListener('click', closeConfigModal);

      if (configModal) {{
        configModal.addEventListener('click', (e) => {{
          if (e.target === configModal) closeConfigModal();
        }});
      }}

      document.addEventListener('keydown', (e) => {{
        if (e.key === 'Escape' && configModal && configModal.classList.contains('active')) {{
          closeConfigModal();
        }}
      }});

      if (cfgSoundNotify) {{
        cfgSoundNotify.addEventListener('change', () => {{
          if (cfgSoundNotify.value === 'enabled') {{
            playSoundChime();
          }}
        }});
      }}

      if (configSaveBtn) {{
        configSaveBtn.addEventListener('click', () => {{
          currentConfig = {{
            autoRefresh: parseInt(cfgAutoRefresh ? cfgAutoRefresh.value : 0, 10),
            activityDelay: parseInt(cfgActivityDelay ? cfgActivityDelay.value : 10, 10),
            defaultTab: cfgDefaultTab ? cfgDefaultTab.value : 'overview',
            selectionPolicy: cfgSelectionPolicy ? cfgSelectionPolicy.value : 'option1_auto',
            visualEffects: cfgVisualEffects ? cfgVisualEffects.value : 'high',
            soundNotify: cfgSoundNotify ? cfgSoundNotify.value : 'disabled'
          }};
          localStorage.setItem('asc_dashboard_config', JSON.stringify(currentConfig));
          applyDynamicSettings(currentConfig);
          closeConfigModal();
          showToast('✓ Configuration successfully saved!', 'success');
          if (currentConfig.soundNotify === 'enabled') {{
            playSoundChime();
          }}
        }});
      }}

      if (configResetBtn) {{
        configResetBtn.addEventListener('click', () => {{
          currentConfig = {{ ...DEFAULT_CONFIG }};
          syncFormWithConfig(currentConfig);
          localStorage.setItem('asc_dashboard_config', JSON.stringify(currentConfig));
          applyDynamicSettings(currentConfig);
          showToast('🔄 Configuration reset to defaults!', 'info');
        }});
      }}

      if (configExportBtn) {{
        configExportBtn.addEventListener('click', () => {{
          try {{
            const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(rawData, null, 2));
            const dlAnchor = document.createElement('a');
            dlAnchor.setAttribute('href', dataStr);
            dlAnchor.setAttribute('download', 'automation_history.json');
            document.body.appendChild(dlAnchor);
            dlAnchor.click();
            dlAnchor.remove();
            showToast('📥 automation_history.json exported successfully!', 'success');
          }} catch (err) {{
            showToast('❌ Export failed: ' + err.message, 'error');
          }}
        }});
      }}

      // Initialize dynamic automation control state
      updateAutomationUI(getAutomationRunning(), false);
      applyDynamicSettings(currentConfig);
      checkProcessStatus();

      // Seamlessly restore scroll position if reloaded
      try {{
        const savedScroll = sessionStorage.getItem('asc_scroll_y');
        if (savedScroll) {{
          window.scrollTo({{ top: parseInt(savedScroll, 10), behavior: 'instant' }});
          sessionStorage.removeItem('asc_scroll_y');
        }}
      }} catch (e) {{}}

      // Theme toggle persistence
      const savedTheme = localStorage.getItem('asc_dashboard_theme') || 'dark';
      document.documentElement.setAttribute('data-theme', savedTheme);

      if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
          const current = document.documentElement.getAttribute('data-theme');
          const next = current === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', next);
          localStorage.setItem('asc_dashboard_theme', next);
        }});
      }}

      // Horizontal Tab switching logic with localStorage persistence
      const tabBtns = document.querySelectorAll('.tab-btn');
      const tabPanels = document.querySelectorAll('.tab-panel');
      const validTabs = ['overview', 'chats', 'questions', 'modes', 'config'];
      const savedTab = localStorage.getItem('asc_dashboard_tab') || currentConfig.defaultTab || 'overview';

      function switchTab(tabId) {{
        const targetTab = validTabs.includes(tabId) ? tabId : 'overview';

        tabBtns.forEach(btn => {{
          const isActive = btn.getAttribute('data-tab') === targetTab;
          btn.classList.toggle('active', isActive);
          btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
        }});
        tabPanels.forEach(panel => {{
          panel.classList.toggle('active', panel.id === `tab-${{targetTab}}`);
        }});
        localStorage.setItem('asc_dashboard_tab', targetTab);
      }}

      tabBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
          const tabId = btn.getAttribute('data-tab');
          if (tabId) switchTab(tabId);
        }});
      }});

      // Restore active tab
      switchTab(savedTab);

      // Multi-dimensional run filter evaluator
      function runMatchesFilters(cid, chat, run) {{
        const fromVal = filterDateFrom ? filterDateFrom.value : '';
        const toVal = filterDateTo ? filterDateTo.value : '';
        const selChat = filterChat ? filterChat.value : 'all';
        const selComplexity = filterComplexity ? filterComplexity.value : 'all';
        const selSpeed = filterSpeed ? filterSpeed.value : 'all';

        // 1. Conversation filter
        if (selChat !== 'all' && cid !== selChat) {{
          return false;
        }}

        // 2. Date range filter
        if (run && run.timestamp) {{
          const runDateStr = run.timestamp.split('T')[0];
          if (fromVal && runDateStr < fromVal) return false;
          if (toVal && runDateStr > toVal) return false;
        }}

        // 3. Complexity filter
        if (run) {{
          const qCount = run.questions_count !== undefined ? run.questions_count : (run.questions ? run.questions.length : 0);
          if (selComplexity === 'single' && qCount !== 1) return false;
          if (selComplexity === 'multi' && qCount < 2) return false;
        }}

        // 4. Latency / Speed filter
        if (run) {{
          const dur = typeof run.duration_seconds === 'number' ? run.duration_seconds : 0.0;
          if (selSpeed === 'fast' && dur >= 3.0) return false;
          if (selSpeed === 'moderate' && (dur < 3.0 || dur > 8.0)) return false;
          if (selSpeed === 'heavy' && dur <= 8.0) return false;
        }}

        return true;
      }}

      // Render Tab 2: Chats Breakdown Table
      function renderChats() {{
        if (!summaryTbody) return;
        const searchVal = (searchChats ? searchChats.value : (searchBoxFallback ? searchBoxFallback.value : '')).toLowerCase().trim();
        const chatEntries = Object.entries(chats);
        summaryTbody.innerHTML = '';
        let tableRows = 0;

        for (const [cid, chat] of chatEntries) {{
          const topic = chat.topic_summary || 'Untitled Conversation';
          const prompt = chat.last_user_prompt || '';
          const runs = chat.runs || [];

          // Text match
          const textMatch = !searchVal ||
            cid.toLowerCase().includes(searchVal) ||
            topic.toLowerCase().includes(searchVal) ||
            prompt.toLowerCase().includes(searchVal);

          if (!textMatch) continue;

          // Check if any run matches active multidimensional filters
          const matchingRuns = runs.filter(run => runMatchesFilters(cid, chat, run));
          const chatFilterMatch = runs.length > 0 ? (matchingRuns.length > 0) : (filterChat ? filterChat.value === 'all' || filterChat.value === cid : true);

          if (chatFilterMatch) {{
            tableRows++;
            const displayRunCount = runs.length > 0 ? matchingRuns.length : (chat.run_count || 0);
            const displayQsCount = runs.length > 0 ? matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0) : (chat.total_questions || 0);

            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><span class="chat-id-tag">${{escapeHtml(cid)}}</span></td>
              <td><strong>${{escapeHtml(topic)}}</strong></td>
              <td><span class="badge-count">${{displayRunCount}}</span></td>
              <td><span class="badge-count">${{displayQsCount}}</span></td>
              <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">${{chat.last_run_timestamp ? new Date(chat.last_run_timestamp).toLocaleString() : 'N/A'}}</td>
            `;
            summaryTbody.appendChild(tr);
          }}
        }}

        if (tableRows === 0) {{
          summaryTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching chat records found.</td></tr>`;
        }}
      }}

      // Date formatting helper (local time)
      function formatDate(d) {{
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${{year}}-${{month}}-${{day}}`;
      }}

      // Render Tab 3: Detailed Questions & Answers
      function renderQuestions() {{
        if (!detailsContainer) return;
        const searchVal = (searchQuestions ? searchQuestions.value : (searchBoxFallback ? searchBoxFallback.value : '')).toLowerCase().trim();
        const chatEntries = Object.entries(chats);
        detailsContainer.innerHTML = '';
        let cardsCount = 0;

        for (const [cid, chat] of chatEntries) {{
          const topic = chat.topic_summary || 'Untitled Conversation';
          const runs = chat.runs || [];

          // Filter inside questions and runs
          const matchingRuns = runs.filter(run => {{
            if (!runMatchesFilters(cid, chat, run)) return false;

            if (!searchVal) return true;
            if (cid.toLowerCase().includes(searchVal) || topic.toLowerCase().includes(searchVal)) return true;
            return (run.questions || []).some(q =>
              (q.question || '').toLowerCase().includes(searchVal) ||
              (q.options || []).some(opt => opt.toLowerCase().includes(searchVal))
            );
          }});

          if (matchingRuns.length > 0) {{
            cardsCount++;
            const card = document.createElement('div');
            card.className = 'chat-card';

            let runsHtml = '';
            matchingRuns.forEach((run, rIdx) => {{
              const runDate = run.timestamp ? new Date(run.timestamp).toLocaleString() : 'N/A';
              const dur = run.duration_seconds ? run.duration_seconds.toFixed(1) + 's' : 'N/A';
              const questions = run.questions || [];

              let qHtml = '';
              questions.forEach((q, qIdx) => {{
                let optionsHtml = '';
                (q.options || []).forEach((opt, optIdx) => {{
                  const isSelected = (optIdx + 1 === q.selected_option_index) ||
                                     (q.selected_option_text && opt.trim() === q.selected_option_text.trim());
                  optionsHtml += `
                    <div class="option-item ${{isSelected ? 'selected' : ''}}">
                      <span><strong>${{optIdx + 1}}.</strong> ${{escapeHtml(opt)}}</span>
                      ${{isSelected ? '<span class="option-badge">✓ Selected (Recommended)</span>' : ''}}
                    </div>
                  `;
                }});

                qHtml += `
                  <div class="question-card" data-question-num="${{q.question_index || (qIdx + 1)}}">
                    <div class="question-prompt collapsible-header" role="button" tabindex="0" aria-expanded="false" title="Click to collapse/expand options">
                      <div class="question-prompt-left">
                        <span class="collapse-icon">▾</span>
                        <span class="question-num">Q${{q.question_index || (qIdx + 1)}}</span>
                        <span>${{escapeHtml(q.question)}}</span>
                      </div>
                      <div class="question-prompt-right">
                        <span class="badge-count" style="font-size: 0.72rem;">${{(q.options || []).length}} options</span>
                      </div>
                    </div>
                    <div class="options-list collapsed">
                      ${{optionsHtml}}
                    </div>
                  </div>
                `;
              }});

              runsHtml += `
                <div class="run-block" data-run-id="${{escapeHtml(run.run_id || '')}}">
                  <div class="run-header collapsible-header" role="button" tabindex="0" aria-expanded="false" title="Click to collapse/expand run questions">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="collapse-icon">▾</span>
                      <span style="font-weight: 700; color: var(--text-primary);">⚡ Run #${{rIdx + 1}} (${{escapeHtml(run.run_id || 'N/A')}})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                      <span>Duration: ${{dur}} | ${{runDate}}</span>
                      <button type="button" class="collapse-btn" aria-label="Toggle Run">
                        <span class="collapse-icon">▾</span>
                      </button>
                    </div>
                  </div>
                  <div class="run-body collapsed">
                    ${{qHtml}}
                  </div>
                </div>
              `;
            }});

            const totalFilteredQs = matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0);

            card.innerHTML = `
              <div class="chat-card-header collapsible-header" role="button" tabindex="0" aria-expanded="false" title="Click to collapse/expand conversation runs">
                <div class="chat-card-title">
                  <span class="collapse-icon">▾</span>
                  <span class="chat-id-tag">${{escapeHtml(cid)}}</span>
                  <span>${{escapeHtml(topic)}}</span>
                </div>
                <div class="chat-card-meta">
                  <span class="badge-count">${{matchingRuns.length}} run(s)</span>
                  <span class="badge-count">${{totalFilteredQs}} question(s)</span>
                  <button type="button" class="collapse-btn" aria-label="Toggle Chat">
                    <span class="collapse-icon">▾</span>
                  </button>
                </div>
              </div>
              <div class="chat-card-body collapsed">
                ${{runsHtml}}
              </div>
            `;
            detailsContainer.appendChild(card);
          }}
        }}

        if (cardsCount === 0) {{
          detailsContainer.innerHTML = `
            <div class="empty-state">
              <div style="font-size: 2rem; margin-bottom: 8px;">📭</div>
              <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 4px;">No Questions Found</div>
              <div>No questions match your filter criteria or search query.</div>
            </div>
          `;
        }}
      }}

      function applyFilters() {{
        let totalRunsCount = 0;
        let matchingRunsCount = 0;

        for (const [cid, chat] of Object.entries(chats)) {{
          const runs = chat.runs || [];
          totalRunsCount += runs.length;
          runs.forEach(run => {{
            if (runMatchesFilters(cid, chat, run)) {{
              matchingRunsCount++;
            }}
          }});
        }}

        if (filterCountEl) filterCountEl.textContent = matchingRunsCount;
        if (filterTotalEl) filterTotalEl.textContent = totalRunsCount;

        renderChats();
        renderQuestions();
      }}

      function escapeHtml(str) {{
        if (!str) return '';
        return String(str)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#039;');
      }}

      // Preset button handlers (7 options: all, today, yesterday, 7d, 30d, week, month)
      presetBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
          presetBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const preset = btn.getAttribute('data-preset');
          const now = new Date();

          if (preset === 'all') {{
            if (filterDateFrom) filterDateFrom.value = '';
            if (filterDateTo) filterDateTo.value = '';
          }} else if (preset === 'today') {{
            const todayStr = formatDate(now);
            if (filterDateFrom) filterDateFrom.value = todayStr;
            if (filterDateTo) filterDateTo.value = todayStr;
          }} else if (preset === 'yesterday') {{
            const y = new Date(now);
            y.setDate(y.getDate() - 1);
            const yStr = formatDate(y);
            if (filterDateFrom) filterDateFrom.value = yStr;
            if (filterDateTo) filterDateTo.value = yStr;
          }} else if (preset === '7d') {{
            const past = new Date(now);
            past.setDate(past.getDate() - 6);
            if (filterDateFrom) filterDateFrom.value = formatDate(past);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === '30d') {{
            const past = new Date(now);
            past.setDate(past.getDate() - 29);
            if (filterDateFrom) filterDateFrom.value = formatDate(past);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === 'week') {{
            const day = now.getDay();
            const diffToMonday = (day === 0 ? -6 : 1) - day;
            const monday = new Date(now);
            monday.setDate(now.getDate() + diffToMonday);
            if (filterDateFrom) filterDateFrom.value = formatDate(monday);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === 'month') {{
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            if (filterDateFrom) filterDateFrom.value = formatDate(firstDay);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }}

          applyFilters();
        }});
      }});

      // Filter change listeners
      if (filterDateFrom) {{
        filterDateFrom.addEventListener('change', () => {{
          presetBtns.forEach(b => b.classList.remove('active'));
          applyFilters();
        }});
      }}
      if (filterDateTo) {{
        filterDateTo.addEventListener('change', () => {{
          presetBtns.forEach(b => b.classList.remove('active'));
          applyFilters();
        }});
      }}
      if (filterChat) filterChat.addEventListener('change', applyFilters);
      if (filterComplexity) filterComplexity.addEventListener('change', applyFilters);
      if (filterSpeed) filterSpeed.addEventListener('change', applyFilters);

      // Reset button listener
      if (filterResetBtn) {{
        filterResetBtn.addEventListener('click', () => {{
          if (filterDateFrom) filterDateFrom.value = '';
          if (filterDateTo) filterDateTo.value = '';
          if (filterChat) filterChat.value = 'all';
          if (filterComplexity) filterComplexity.value = 'all';
          if (filterSpeed) filterSpeed.value = 'all';
          if (searchChats) searchChats.value = '';
          if (searchQuestions) searchQuestions.value = '';
          if (searchOverview) searchOverview.value = '';
          if (searchBoxFallback) searchBoxFallback.value = '';
          presetBtns.forEach(b => b.classList.toggle('active', b.getAttribute('data-preset') === 'all'));
          applyFilters();
        }});
      }}

      // Search listeners
      if (searchChats) {{
        searchChats.addEventListener('input', () => renderChats());
      }}
      if (searchQuestions) {{
        searchQuestions.addEventListener('input', () => renderQuestions());
      }}
      if (searchOverview) {{
        searchOverview.addEventListener('input', () => renderChats());
      }}
      if (searchBoxFallback) {{
        searchBoxFallback.addEventListener('input', () => {{
          renderChats();
          renderQuestions();
        }});
      }}

      // Filter Toolbar Collapse / Expand Button
      const filterCollapseBtn = document.getElementById('filter-collapse-btn');
      const filterToolbarBody = document.getElementById('filter-toolbar-body');
      if (filterCollapseBtn && filterToolbarBody) {{
        filterCollapseBtn.addEventListener('click', () => {{
          const isCollapsed = filterToolbarBody.classList.toggle('collapsed');
          filterCollapseBtn.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
          const icon = filterCollapseBtn.querySelector('.collapse-icon');
          const label = filterCollapseBtn.querySelector('.collapse-label');
          if (icon) icon.textContent = isCollapsed ? '▸' : '▾';
          if (label) label.textContent = isCollapsed ? 'Expand' : 'Collapse';
        }});
      }}

      // Collapsible Card Headers with data-target (Architecture Diagram, Charts, Chats Table)
      document.querySelectorAll('.collapsible-header[data-target]').forEach(header => {{
        const targetId = header.getAttribute('data-target');
        const body = document.getElementById(targetId);
        if (body) {{
          const toggle = (e) => {{
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION') return;
            const willExpand = body.classList.contains('collapsed');
            if (willExpand) {{
              // Mutual exclusion: collapse any other open collapsible card in the same tab panel (disabled for overview tab)
              const isOverview = !!header.closest('#tab-overview');
              if (!isOverview) {{
                const container = header.closest('.tab-panel') || document;
                container.querySelectorAll('.collapsible-header[data-target]').forEach(otherHeader => {{
                  if (otherHeader !== header) {{
                    const otherTargetId = otherHeader.getAttribute('data-target');
                    const otherBody = document.getElementById(otherTargetId);
                    if (otherBody) {{
                      otherBody.classList.add('collapsed');
                      otherHeader.setAttribute('aria-expanded', 'false');
                      otherHeader.querySelectorAll('.collapse-icon').forEach(ic => ic.textContent = '▾');
                    }}
                  }}
                }});
              }}
              body.classList.remove('collapsed');
              header.setAttribute('aria-expanded', 'true');
              header.querySelectorAll('.collapse-icon').forEach(ic => ic.textContent = '▾');
            }} else {{
              body.classList.add('collapsed');
              header.setAttribute('aria-expanded', 'false');
              header.querySelectorAll('.collapse-icon').forEach(ic => ic.textContent = '▾');
            }}
          }};
          header.addEventListener('click', toggle);
          header.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter' || e.key === ' ') {{
              e.preventDefault();
              toggle(e);
            }}
          }});
        }}
      }});

      // Questions Tab - Deep Collapsible Accordion Delegated Handler
      if (detailsContainer) {{
        detailsContainer.addEventListener('click', (e) => {{
          // 1. Question Card prompt click
          const qHeader = e.target.closest('.question-prompt.collapsible-header');
          if (qHeader) {{
            const qCard = qHeader.closest('.question-card');
            const optList = qCard ? qCard.querySelector('.options-list') : null;
            if (optList) {{
              const willExpand = optList.classList.contains('collapsed');
              if (willExpand) {{
                // Mutual exclusion: collapse sibling question cards inside the same run-body
                const parentRun = qCard.closest('.run-body') || detailsContainer;
                parentRun.querySelectorAll('.question-card').forEach(otherCard => {{
                  if (otherCard !== qCard) {{
                    const otherOpt = otherCard.querySelector('.options-list');
                    const otherHdr = otherCard.querySelector('.question-prompt.collapsible-header');
                    if (otherOpt) otherOpt.classList.add('collapsed');
                    if (otherHdr) {{
                      otherHdr.setAttribute('aria-expanded', 'false');
                    }}
                  }}
                }});
                optList.classList.remove('collapsed');
                qHeader.setAttribute('aria-expanded', 'true');
              }} else {{
                optList.classList.add('collapsed');
                qHeader.setAttribute('aria-expanded', 'false');
              }}
            }}
            return;
          }}

          // 2. Run Header click
          const runHeader = e.target.closest('.run-header.collapsible-header');
          if (runHeader) {{
            const runBlock = runHeader.closest('.run-block');
            const runBody = runBlock ? runBlock.querySelector('.run-body') : null;
            if (runBody) {{
              const willExpand = runBody.classList.contains('collapsed');
              if (willExpand) {{
                // Mutual exclusion: collapse sibling run blocks inside the same chat-card-body
                const parentChat = runBlock.closest('.chat-card-body') || detailsContainer;
                parentChat.querySelectorAll('.run-block').forEach(otherRun => {{
                  if (otherRun !== runBlock) {{
                    const otherRunBody = otherRun.querySelector('.run-body');
                    const otherRunHdr = otherRun.querySelector('.run-header.collapsible-header');
                    if (otherRunBody) otherRunBody.classList.add('collapsed');
                    if (otherRunHdr) {{
                      otherRunHdr.setAttribute('aria-expanded', 'false');
                    }}
                  }}
                }});
                runBody.classList.remove('collapsed');
                runHeader.setAttribute('aria-expanded', 'true');
              }} else {{
                runBody.classList.add('collapsed');
                runHeader.setAttribute('aria-expanded', 'false');
              }}
            }}
            return;
          }}

          // 3. Chat Card Header click
          const chatHeader = e.target.closest('.chat-card-header.collapsible-header');
          if (chatHeader) {{
            const chatCard = chatHeader.closest('.chat-card');
            const chatBody = chatCard ? chatCard.querySelector('.chat-card-body') : null;
            if (chatBody) {{
              const willExpand = chatBody.classList.contains('collapsed');
              if (willExpand) {{
                // Mutual exclusion: collapse sibling chat cards inside details container
                detailsContainer.querySelectorAll('.chat-card').forEach(otherChat => {{
                  if (otherChat !== chatCard) {{
                    const otherChatBody = otherChat.querySelector('.chat-card-body');
                    const otherChatHdr = otherChat.querySelector('.chat-card-header.collapsible-header');
                    if (otherChatBody) otherChatBody.classList.add('collapsed');
                    if (otherChatHdr) {{
                      otherChatHdr.setAttribute('aria-expanded', 'false');
                    }}
                  }}
                }});
                chatBody.classList.remove('collapsed');
                chatHeader.setAttribute('aria-expanded', 'true');
              }} else {{
                chatBody.classList.add('collapsed');
                chatHeader.setAttribute('aria-expanded', 'false');
              }}
            }}
            return;
          }}
        }});

        // Keyboard navigation for questions accordion
        detailsContainer.addEventListener('keydown', (e) => {{
          if (e.key === 'Enter' || e.key === ' ') {{
            const header = e.target.closest('.collapsible-header');
            if (header) {{
              e.preventDefault();
              header.click();
            }}
          }}
        }});
      }}

      // Questions Global Expand All / Collapse All
      const btnExpandAll = document.getElementById('btn-expand-all-questions');
      const btnCollapseAll = document.getElementById('btn-collapse-all-questions');

      if (btnExpandAll) {{
        btnExpandAll.addEventListener('click', () => {{
          if (!detailsContainer) return;
          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {{
            el.classList.remove('collapsed');
          }});
          detailsContainer.querySelectorAll('.collapsible-header').forEach(hdr => {{
            hdr.setAttribute('aria-expanded', 'true');
            hdr.querySelectorAll('.collapse-icon').forEach(ic => ic.textContent = '▾');
          }});
        }});
      }}

      if (btnCollapseAll) {{
        btnCollapseAll.addEventListener('click', () => {{
          if (!detailsContainer) return;
          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {{
            el.classList.add('collapsed');
          }});
          detailsContainer.querySelectorAll('.collapsible-header').forEach(hdr => {{
            hdr.setAttribute('aria-expanded', 'false');
            hdr.querySelectorAll('.collapse-icon').forEach(ic => ic.textContent = '▸');
          }});
        }});
      }}

      // Initialize Server Bridge Health & Process Status Polling
      startServerHealthPolling(3000);

      // Live Logs Drawer
      const logsDrawer = document.getElementById('logs-drawer');
      const btnToggleLogs = document.getElementById('btn-toggle-logs');
      const btnFloatingLogs = document.getElementById('btn-floating-logs');
      const btnCloseLogs = document.getElementById('btn-close-logs');
      const logsTerminal = document.getElementById('logs-terminal');
      const logBadge = document.getElementById('log-count-badge');
      const floatingLogBadge = document.getElementById('floating-log-count-badge');
      let logsOpen = false;
      let logsInterval = null;
      let autoScrollLogs = true;

      function startLogsPolling() {{
        if (logsInterval) clearInterval(logsInterval);
        fetchLogs();
        logsInterval = setInterval(fetchLogs, 1500);
      }}

      function stopLogsPolling() {{
        if (logsInterval) {{
          clearInterval(logsInterval);
          logsInterval = null;
        }}
      }}

      function toggleLogs(forceState) {{
        logsOpen = (forceState !== undefined) ? forceState : !logsOpen;
        if (logsDrawer) logsDrawer.classList.toggle('open', logsOpen);
        if (logsOpen) {{
          startLogsPolling();
        }} else {{
          stopLogsPolling();
        }}
      }}

      if (btnToggleLogs) btnToggleLogs.addEventListener('click', () => toggleLogs());
      if (btnFloatingLogs) btnFloatingLogs.addEventListener('click', () => toggleLogs());
      if (btnCloseLogs) btnCloseLogs.addEventListener('click', () => toggleLogs(false));

      function fetchLogs() {{
        if (!logsOpen) return;
        fetch(API_BASE + '/api/logs/tail?lines=150')
          .then(res => res.json())
          .then(data => {{
            let lines = [];
            if (data && data.data) {{
              if (Array.isArray(data.data.logs)) {{
                lines = data.data.logs;
              }} else if (typeof data.data.logs === 'string') {{
                lines = data.data.logs.split('\n').map(l => l.trim()).filter(l => l.length > 0);
              }} else if (typeof data.data.raw === 'string') {{
                lines = data.data.raw.split('\n').map(l => l.trim()).filter(l => l.length > 0);
              }}
            }}
            const count = lines.length;
            if (logBadge) logBadge.textContent = count;
            if (floatingLogBadge) floatingLogBadge.textContent = count;
            let colored = '';
            lines.forEach(l => {{
              let cls = '';
              const upper = l.toUpperCase();
              if (upper.includes('[ERROR]') || upper.includes('ERROR:')) cls = 'log-line-err';
              else if (upper.includes('[WARNING]') || upper.includes('[WARN]')) cls = 'log-line-warn';
              else if (upper.includes('[SUCCESS]') || upper.includes('PASSED') || upper.includes('SUCCESS:')) cls = 'log-line-ok';
              else if (upper.includes('[STEP') || upper.includes('STEP 0') || upper.includes('STEP 1') || upper.includes('STEP 2') || upper.includes('STEP 3') || upper.includes('STEP 4') || upper.includes('STEP 9')) cls = 'log-line-step';
              else if (upper.includes('[INFO]')) cls = 'log-line-info';
              const escaped = l.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
              colored += `<div class="${{cls}}">${{escaped}}</div>`;
            }});
            if (logsTerminal) {{
              const wasAtBottom = (logsTerminal.scrollHeight - logsTerminal.scrollTop - logsTerminal.clientHeight) <= 40;
              logsTerminal.innerHTML = colored || '<div style="color: #64748b; padding: 6px;">Log file empty. Waiting for automation output...</div>';
              if (autoScrollLogs && wasAtBottom) {{
                logsTerminal.scrollTop = logsTerminal.scrollHeight;
              }}
            }}
          }})
          .catch(() => {{}});
      }}

      // Auto-Scroll Toggle
      const btnAutoScroll = document.getElementById('btn-toggle-autoscroll');
      if (btnAutoScroll) {{
        btnAutoScroll.addEventListener('click', () => {{
          autoScrollLogs = !autoScrollLogs;
          btnAutoScroll.textContent = 'Auto-Scroll: ' + (autoScrollLogs ? 'ON' : 'OFF');
          if (autoScrollLogs && logsTerminal) {{
            logsTerminal.scrollTop = logsTerminal.scrollHeight;
          }}
        }});
      }}

      const btnClearLogs = document.getElementById('btn-clear-logs');
      if (btnClearLogs) {{
        btnClearLogs.addEventListener('click', () => {{
          if (logsTerminal) logsTerminal.innerHTML = '<div style="color: #64748b; padding: 6px;">Console cleared. Waiting for next stream tick...</div>';
        }});
      }}

      // Keyboard shortcuts
      document.addEventListener('keydown', (e) => {{
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
        if (e.key.toLowerCase() === 'l') {{
          e.preventDefault();
          toggleLogs();
        }} else if (e.key === 'Escape') {{
          if (logsOpen) toggleLogs(false);
        }}
      }});

      // Initial Render & Filter Count Initialization
      applyFilters();
    }})();
  </script>
  <!-- Floating Logs Button (Bottom Right) -->
  <button id="btn-floating-logs" title="Toggle Live Console Logs (L)">
    <span>📟</span>
    <span>Live Logs</span>
    <span class="log-unread-badge" id="floating-log-count-badge">0</span>
  </button>

  <!-- Slide-Up Live Console Logs Drawer -->
  <div id="logs-drawer">
    <div class="logs-drawer-header">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span>📟</span>
        <span>Live Console Logs (complete_automation.log)</span>
        <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 9999px; background: rgba(16,185,129,0.2); color: #34d399;">STREAMING</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <button class="btn" id="btn-toggle-autoscroll" style="padding: 3px 8px; font-size: 0.72rem;">Auto-Scroll: ON</button>
        <button class="btn" id="btn-clear-logs" style="padding: 3px 8px; font-size: 0.72rem;">Clear</button>
        <button class="btn" id="btn-close-logs" style="padding: 3px 8px; font-size: 0.72rem;">✕ Close (Esc)</button>
      </div>
    </div>
    <div class="logs-terminal-body" id="logs-terminal">
      Connecting to local daemon log tail on port 8501...
    </div>
  </div>
</body>
</html>
"""

        try:
            logger.info("[STEP 4.20] [DASHBOARD_FILE_WRITE] Wrote dashboard HTML file to disk: %s", self.dashboard_file)
            with open(self.dashboard_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            with open(self.reports_dir / "classic_dashboard.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            simple_f = self.reports_dir.parent / "Simple and Classic Dashboard" / "dashboard.html"
            if simple_f.parent.is_dir():
                with open(simple_f, "w", encoding="utf-8") as f:
                    f.write(html_content)

            # Also ensure Modern and Interactive Dashboard is kept synchronized
            try:
                mod_path = self.reports_dir.parent / "Modern and Interactive Dashboard" / "generate_modern_dashboard.py"
                if mod_path.is_file():
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("modern_dash_gen", str(mod_path))
                    if spec and spec.loader:
                        m_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(m_mod)
                        if hasattr(m_mod, "generate_modern_dashboard"):
                            m_mod.generate_modern_dashboard(workspace_dir=self.workspace_dir)
                            logger.info("[STEP 4.19] [MODERN_DASH_UPDATE] Synchronized modern dashboard HTML")
            except Exception:
                pass
        except Exception as e:
            logging.getLogger("Step4Reporting").error("Failed to write dashboard HTML: %s", e)

        return self.dashboard_file

    # ========================================================================
    # Open Dashboard in Browser
    # ========================================================================

    def open_dashboard(self, port: int = 8501, force: bool = False) -> bool:
        """Launch dashboard in web browser. Connects to local server if active, else falls back to file:// URI."""
        if not self.dashboard_file.is_file():
            self.generate_html_dashboard()

        # Session launch lock check (Smart Single-Tab Lifecycle)
        logger.info("[STEP 4.21] [LOCK_CHECK] Inspecting dashboard session lock file: %s", getattr(self, "session_lock_file", ""))
        if not force and hasattr(self, "session_lock_file") and self.session_lock_file.is_file():
            try:
                with open(self.session_lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.load(f)
                launched_at = lock_data.get("launched_at_epoch", 0)
                if (time.time() - launched_at) < 86400:
                    logging.getLogger("Step4Reporting").info(
                        "Dashboard browser tab was already launched in this session. Skipping duplicate launch."
                    )
                    return True
            except Exception:
                pass

        server_running = False
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    server_running = True
        except Exception:
            server_running = False

        try:
            target_f = self.reports_dir.parent / "Modern and Interactive Dashboard" / "dashboard.html"
            if not target_f.is_file():
                target_f = self.reports_dir / "modern_dashboard.html"
            if not target_f.is_file():
                target_f = self.dashboard_file

            url = f"http://127.0.0.1:{port}/" if server_running else target_f.resolve().as_uri()
            logger.info("[STEP 4.26] [BROWSER_OPEN] Launching visual dashboard URL in default browser: %s", url)
            webbrowser.open_new_tab(url)

            # Record session launch lock
            try:
                if hasattr(self, "session_lock_file"):
                    lock_info = {
                        "launched_at": datetime.now(timezone.utc).isoformat(),
                        "launched_at_epoch": time.time(),
                        "pid": os.getpid(),
                        "url": url,
                    }
                    logger.info("[STEP 4.27] [LOCK_WRITE] Written dashboard session lock: %s", self.session_lock_file)
                    with open(self.session_lock_file, "w", encoding="utf-8") as f:
                        json.dump(lock_info, f, indent=2)
            except Exception as le:
                logging.getLogger("Step4Reporting").warning("Failed to write session lock: %s", le)

            return True
        except Exception:
            return False

    # ========================================================================
    # Background Activity Watcher & Delayed Launcher
    # ========================================================================

    def watch_and_launch(
        self,
        delay_seconds: Optional[float] = None,
        timeout: Optional[float] = None,
        poll_interval: Optional[float] = None,
    ) -> bool:
        """
        Two-Way Process:
          1. Wait silently until user moves mouse or strikes a key.
          2. Once user activity is detected, wait exactly delay_seconds (from config or param).
          3. Pop up dashboard.html in the user's browser.
          4. Exit cleanly (Universal Rule 26 hygiene).
        """
        cfg = self.load_runtime_config()
        eff_delay = delay_seconds if delay_seconds is not None else get_user_activity_delay(cfg)
        eff_poll = poll_interval if poll_interval is not None else get_step4_poll_interval(cfg)
        eff_timeout = timeout if timeout is not None else get_step4_timeout(cfg)
        logger.info("[STEP 4.22] [WATCHER_EVAL] Initializing user activity watcher (delay: %.1fs, poll: %.2fs)", eff_delay, eff_poll)
        logger.info("[STEP 4.23] [USER_ACTIVITY_WATCH] Monitoring Windows user input tick via GetLastInputInfo")
        detected = watch_for_user_input(timeout=eff_timeout, poll_interval=eff_poll)
        if detected:
            logger.info("[STEP 4.24] [USER_INPUT_DETECTED] User activity detected! Starting countdown delay: %.1fs", eff_delay)
            if eff_delay > 0:
                time.sleep(eff_delay)
            logger.info("[STEP 4.25] [ACTIVITY_DELAY] Completed %.1fs user activity settle delay before launch", eff_delay)
            self.open_dashboard()
            return True
        return False

    def spawn_background_watcher(
        self,
        delay_seconds: Optional[float] = None,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Spawn a completely detached, windowless background worker process that monitors
        for user input and opens the dashboard after configured delay. Allows the main
        pipeline to complete without blocking and guarantees 100% zero window or terminal appearance.
        """
        # Prefer pythonw.exe on Windows for 100% windowless execution
        python_exe = sys.executable
        if IS_WINDOWS:
            candidates = [
                self.workspace_dir / ".venv" / "Scripts" / "pythonw.exe",
                Path(sys.executable).with_name("pythonw.exe"),
                Path(sys.executable).parent / "pythonw.exe",
            ]
            for c in candidates:
                if c.is_file():
                    python_exe = str(c)
                    break

        script_path = self._this_dir / "step4_reporting.py"
        cfg = self.load_runtime_config()
        eff_delay = delay_seconds if delay_seconds is not None else get_user_activity_delay(cfg)
        eff_poll = poll_interval if poll_interval is not None else get_step4_poll_interval(cfg)
        eff_timeout = timeout if timeout is not None else get_step4_timeout(cfg)

        cmd = [
            str(python_exe),
            str(script_path),
            "--watch-worker",
            "--delay", str(eff_delay),
            "--poll-interval", str(eff_poll),
            "--reports-dir", str(self.reports_dir),
            "--history-file", str(self.history_file),
        ]
        if eff_timeout is not None:
            cmd.extend(["--timeout", str(eff_timeout)])

        creation_flags = 0
        startupinfo = None
        if IS_WINDOWS:
            # CREATE_NO_WINDOW (0x08000000) guarantees no console window or terminal frame is ever shown
            # CREATE_NEW_PROCESS_GROUP (0x00000200) ensures signal isolation
            creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

        try:
            popen_kwargs = {
                "cwd": str(self.workspace_dir),
                "creationflags": creation_flags,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "close_fds": True,
                "shell": False,
            }
            if startupinfo is not None:
                popen_kwargs["startupinfo"] = startupinfo

            logger.info("[STEP 4.28] [SPAWN_WATCHER] Spawning background detached watcher process: %s", " ".join(cmd))
            subprocess.Popen(cmd, **popen_kwargs)
            return True
        except Exception:
            return False


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Step 4 - Reporting & Visual Dashboard Subsystem (AutoSelect Antigravity)"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Path to target_chat.json state file"
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=None,
        help="Directory to store JSON history and HTML dashboard"
    )
    parser.add_argument(
        "--history-file",
        type=str,
        default=None,
        help="Path to automation_history.json"
    )
    parser.add_argument(
        "--show",
        "--manual",
        action="store_true",
        help="Manual Mode: Immediately open visual dashboard in browser"
    )
    parser.add_argument(
        "--no-watch",
        "--record-only",
        action="store_true",
        help="Record history and generate HTML without waiting for user input"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Synchronously watch for user input, sleep 10s, and launch browser"
    )
    parser.add_argument(
        "--watch-worker",
        action="store_true",
        help="Internal worker flag: Run silent input detection loop and launch browser"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay in seconds after user input detection before showing dashboard (default: from config.json)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="Polling interval in seconds between user activity checks (default: from config.json)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds for input detection (None = wait forever)"
    )
    parser.add_argument(
        "--runtime-config",
        "--save-runtime-config",
        type=str,
        default=None,
        help="JSON file path or raw JSON string to update and persist to config.json"
    )
    parser.add_argument(
        "--set-runtime-mode",
        type=str,
        choices=["production", "test"],
        default=None,
        help="Update operating mode in system runtime config.json"
    )

    args, _ = parser.parse_known_args()

    engine = Step4ReportingEngine(
        state_file_path=args.state_file,
        reports_dir=args.reports_dir,
        history_file_path=args.history_file,
    )

    # Runtime configuration CLI handlers
    if args.set_runtime_mode:
        rc = engine.load_runtime_config()
        rc["mode"] = args.set_runtime_mode
        engine.save_runtime_config(rc)
        print(f"[INFO] Operating mode updated to: {args.set_runtime_mode}")

    if args.runtime_config:
        try:
            rc_p = Path(args.runtime_config)
            if rc_p.is_file():
                with open(rc_p, "r", encoding="utf-8") as f:
                    new_rc = json.load(f)
            else:
                new_rc = json.loads(args.runtime_config)
            engine.save_runtime_config(new_rc)
            print("[INFO] System runtime configuration successfully updated.")
        except Exception as e:
            print(f"[ERROR] Failed to apply runtime config: {e}")

    # Manual Mode: Immediately open dashboard
    if args.show:
        engine.generate_html_dashboard()
        engine.open_dashboard(force=True)
        return 0

    # Internal Detached Watcher Worker
    if args.watch_worker:
        engine.watch_and_launch(delay_seconds=args.delay, timeout=args.timeout, poll_interval=args.poll_interval)
        return 0

    # Ingest the latest run from target_chat.json
    ok, msg, _ = engine.ingest_current_run(state_file=args.state_file)

    # If --no-watch or --record-only, exit immediately
    if args.no_watch:
        return 0

    # If --watch, run watcher synchronously
    if args.watch:
        engine.watch_and_launch(delay_seconds=args.delay, timeout=args.timeout, poll_interval=args.poll_interval)
        return 0

    # Default Automated Pipeline Mode:
    # Spawn background watcher so calling pipeline exits cleanly, while watcher waits
    # for physical user input + delay to show dashboard without terminal clutter!
    engine.spawn_background_watcher(
        delay_seconds=args.delay,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )
    logger.info("[STEP 4.40] [STEP4_COMPLETE] Step 4 Reporting & Telemetry execution finished successfully (Exit Code 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
