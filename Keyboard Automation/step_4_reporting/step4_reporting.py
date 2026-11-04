#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 4 - रिपोर्टिंग एवं विजुअल डैशबोर्ड / Step 4 - Reporting & Visual Dashboard
==============================================================================
Part of: AutoSelect-Commander Automation Pipeline
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

class Step4ReportingEngine:
    """
    Core reporting and visual dashboard subsystem for AutoSelect-Commander.
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
            self.state_file = self.workspace_dir / "target_chat.json"

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

        # Ensure history file exists on disk
        if not self.history_file.is_file():
            self.save_history(self.load_history())

    # ========================================================================
    # History Ledger Storage (Load / Save)
    # ========================================================================

    def load_history(self) -> AutomationHistory:
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
            return True
        except Exception:
            return False

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
        if not p_state.is_file():
            return False, f"State file not found at: {p_state}", None

        try:
            with open(p_state, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            return False, f"Failed to parse state file: {e}", None

        data = raw.get("data", {})
        status = data.get("status", "")
        cid = data.get("conversation_id")

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

        self.save_history(history)
        self.generate_html_dashboard(history)

        return True, f"Successfully recorded run {run_id} for chat {cid}.", record

    # ========================================================================
    # SVG Vector Visualizations (Department 04 UI/UX & Zero Dependencies)
    # ========================================================================

    @staticmethod
    def build_pipeline_svg() -> str:
        """
        Generate pure inline vector SVG showing the 5-step execution pipeline
        (Step 0 -> Step 1 -> Step 2 -> Step 3 -> Step 4) with active status badges.
        """
        steps = [
            ("STEP 0", "Step 0: Detector", "AntiGravity Sentinel", "#6366f1", "#818cf8"),
            ("STEP 1", "Step 1: Identifier", "Target Chat Identify", "#06b6d4", "#22d3ee"),
            ("STEP 2", "Step 2: Focus", "Precision Window Focus", "#a855f7", "#c084fc"),
            ("STEP 3", "Step 3: Selector", "Option 1 Auto-Select", "#f59e0b", "#fbbf24"),
            ("STEP 4", "Step 4: Reporter", "Visual Telemetry", "#10b981", "#34d399"),
        ]

        svg_parts = [
            '<svg viewBox="0 0 1000 110" width="100%" height="110" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow:visible;">',
            '  <defs>',
            '    <marker id="pipeline-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#6366f1" />',
            '    </marker>',
            '    <linearGradient id="pipeArrowGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#6366f1" />',
            '      <stop offset="100%" stop-color="#10b981" />',
            '    </linearGradient>',
            '  </defs>',
        ]

        # Draw connecting lines with animated gradient & arrowheads
        for i in range(4):
            x1 = 20 + i * 200 + 160
            x2 = 20 + (i + 1) * 200
            y = 55
            svg_parts.append(
                f'  <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="url(#pipeArrowGrad)" stroke-width="2.5" stroke-dasharray="4 2" marker-end="url(#pipeline-arrow)" />'
            )

        # Draw step node boxes
        for i, (badge, title, subtitle, color, text_color) in enumerate(steps):
            x = 20 + i * 200
            y = 15
            w = 160
            h = 80
            svg_parts.extend([
                f'  <g class="pipeline-step-node" transform="translate({x}, {y})">',
                f'    <rect width="{w}" height="{h}" rx="10" fill="var(--bg-surface-elevated)" stroke="var(--border-subtle)" stroke-width="1.5" />',
                f'    <rect x="10" y="10" width="56" height="18" rx="4" fill="rgba(99, 102, 241, 0.15)" />',
                f'    <text x="38" y="23" font-size="9.5" font-weight="700" font-family="var(--font-mono)" fill="{text_color}" text-anchor="middle">{badge}</text>',
                f'    <circle cx="{w - 18}" cy="19" r="4.5" fill="#10b981" />',
                f'    <text x="10" y="48" font-size="12" font-weight="700" font-family="var(--font-family)" fill="var(--text-primary)">{title}</text>',
                f'    <text x="10" y="66" font-size="10" font-family="var(--font-family)" fill="var(--text-secondary)">{subtitle}</text>',
                f'  </g>',
            ])

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

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

    # ========================================================================
    # Visual Dashboard Generation (Department 04 UI/UX Design System)
    # ========================================================================

    def generate_html_dashboard(self, history: Optional[AutomationHistory] = None) -> Path:
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
        pipeline_svg = self.build_pipeline_svg()
        distribution_svg = self.build_chat_distribution_svg(history)
        latency_trend_svg = self.build_latency_trend_svg(history)
        topic_share_svg = self.build_topic_share_svg(history)
        donut_svg = self.build_donut_gauge_svg(recommendation_rate)

        last_updated_display = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoSelect-Commander • Telemetry & Reporting Dashboard</title>
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
      max-width: 1240px;
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
      gap: 12px;
    }}

    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--accent-emerald-bg);
      color: var(--accent-emerald);
      border: 1px solid var(--accent-emerald-border);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}

    .status-pill::before {{
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.4; }}
    }}

    .btn {{
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
      padding: 8px 14px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition);
      display: inline-flex;
      align-items: center;
      gap: 6px;
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
      gap: 8px;
    }}

    .filter-toolbar-title {{
      font-size: 0.92rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-primary);
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

    .filter-presets {{
      display: flex;
      gap: 6px;
      margin-top: 4px;
    }}

    .preset-btn {{
      background: var(--bg-surface-elevated);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 4px 10px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition);
    }}

    .preset-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-highlight);
    }}

    .preset-btn.active {{
      background: var(--accent-indigo);
      color: #ffffff;
      border-color: var(--accent-indigo);
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

    /* Question & Option Cards */
    .chat-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      margin-bottom: 24px;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }}

    .chat-card-header {{
      background: var(--bg-surface-elevated);
      padding: 16px 20px;
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
      padding: 20px;
      border-bottom: 1px dashed var(--border-subtle);
    }}

    .run-block:last-child {{
      border-bottom: none;
    }}

    .run-header {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 14px;
      font-size: 0.82rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .question-card {{
      background: var(--bg-primary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 14px;
    }}

    .question-card:last-child {{
      margin-bottom: 0;
    }}

    .question-prompt {{
      font-weight: 600;
      font-size: 0.95rem;
      margin-bottom: 12px;
      display: flex;
      gap: 8px;
      align-items: flex-start;
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
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="header-left">
        <div class="logo-badge">⚡</div>
        <div class="header-titles">
          <h1>AutoSelect-Commander • Telemetry Dashboard</h1>
          <p>Real-Time Step 1-3 Execution Ledger & Grill-Me Option Reporting</p>
        </div>
      </div>
      <div class="header-actions">
        <span class="status-pill">Active Ledger</span>
        <button class="btn" id="theme-toggle" title="Toggle Light/Dark Theme">🌓 Theme</button>
        <button class="btn" onclick="location.reload()" title="Refresh Ledger">🔄 Refresh</button>
      </div>
    </header>

    <!-- Horizontal Tab Navigation Bar (Single-word intuitive names: Overview, Chats, Questions) -->
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
    </nav>

    <!-- Legacy Search Box Compatibility Hook (Hidden) -->
    <input type="hidden" id="search-box" value="">
    <input type="hidden" id="search-overview" value="">

    <!-- Interactive Multi-Dimensional Filter Toolbar -->
    <section class="filter-toolbar" aria-label="Filters Toolbar">
      <div class="filter-toolbar-header">
        <div class="filter-toolbar-title">
          <span>🔍</span>
          <span>Interactive Filter Toolbar</span>
        </div>
        <div class="filter-stats-badge" id="filter-stats-badge">
          Showing <span id="filter-count">{total_runs}</span> of <span id="filter-total">{total_runs}</span> runs
        </div>
      </div>

      <div class="filter-controls-row">
        <!-- Date Range Filter -->
        <div class="filter-control-group filter-date-group">
          <label class="filter-label" for="filter-date-from">Date Range</label>
          <div class="filter-date-inputs">
            <input type="date" id="filter-date-from" class="filter-input-date" title="Filter From Date">
            <span class="filter-date-sep">to</span>
            <input type="date" id="filter-date-to" class="filter-input-date" title="Filter To Date">
          </div>
          <div class="filter-presets">
            <button type="button" class="preset-btn active" data-preset="all">All</button>
            <button type="button" class="preset-btn" data-preset="today">Today</button>
            <button type="button" class="preset-btn" data-preset="7d">Last 7 Days</button>
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

      <!-- Pipeline Execution Architecture Diagram (Pure Vector SVG) -->
      <div class="architecture-card">
        <div class="card-title">🚀 Pipeline Execution Architecture (Step 0 → Step 4)</div>
        {pipeline_svg}
      </div>

      <!-- Interactive Dynamic SVG Charts Grid -->
      <div class="charts-grid-two">
        <div class="chart-card">
          <div class="card-title">📊 Chat Automation & Questions Distribution</div>
          {distribution_svg}
        </div>
        <div class="chart-card">
          <div class="card-title">🥧 Chat Workload & Topic Share</div>
          {topic_share_svg}
        </div>
      </div>

      <!-- Wide Run Latency & Performance Trend Chart -->
      <div class="chart-card chart-card-wide">
        <div class="card-title">⚡ Run Latency & Performance Trend</div>
        {latency_trend_svg}
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

      <!-- Chat-wise Automation Summary Table -->
      <div class="section-title">📊 Chat-wise Automation Breakdown</div>
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
    </main>

    <!-- Tab 3: Questions Panel (All Questions & Answers Ledger & Dedicated Search) -->
    <main id="tab-questions" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-questions">
      <!-- Dedicated Search Controls for Questions -->
      <div class="controls-bar">
        <input type="text" id="search-questions" class="search-input" placeholder="🔍 Search questions, options, topics, or conversation IDs...">
      </div>

      <!-- Detailed Questions & Answers Ledger -->
      <div class="section-title">📝 Questions & Answers Ledger</div>
      <div id="details-container">
        <!-- Dynamically populated by client JS -->
      </div>
    </main>

    <!-- Footer -->
    <footer>
      <div>Generated by AutoSelect-Commander (Step 4 Reporting Subsystem)</div>
      <div>Department 06 (Backend & API) & Department 04 (UI/UX Design System) Standard</div>
      <div>Last Synchronized: <span style="font-family: var(--font-mono);">{last_updated_display}</span></div>
    </footer>
  </div>

  <!-- Raw History JSON Store for Zero-Dependency Dynamic Client Render -->
  <script id="history-data" type="application/json">
{history_json_str}
  </script>

  <script>
    (function() {{
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
      const savedTab = localStorage.getItem('asc_dashboard_tab') || 'overview';

      function switchTab(tabId) {{
        const validTabs = ['overview', 'chats', 'questions'];
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
                  <div class="question-card">
                    <div class="question-prompt">
                      <span class="question-num">Q${{q.question_index || (qIdx + 1)}}</span>
                      <span>${{escapeHtml(q.question)}}</span>
                    </div>
                    <div class="options-list">
                      ${{optionsHtml}}
                    </div>
                  </div>
                `;
              }});

              runsHtml += `
                <div class="run-block">
                  <div class="run-header">
                    <span>⚡ Run #${{rIdx + 1}} (${{escapeHtml(run.run_id || 'N/A')}})</span>
                    <span>Duration: ${{dur}} | ${{runDate}}</span>
                  </div>
                  ${{qHtml}}
                </div>
              `;
            }});

            const totalFilteredQs = matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0);

            card.innerHTML = `
              <div class="chat-card-header">
                <div class="chat-card-title">
                  <span class="chat-id-tag">${{escapeHtml(cid)}}</span>
                  <span>${{escapeHtml(topic)}}</span>
                </div>
                <div class="chat-card-meta">
                  <span class="badge-count">${{matchingRuns.length}} run(s)</span>
                  <span class="badge-count">${{totalFilteredQs}} question(s)</span>
                </div>
              </div>
              <div class="chat-card-body">
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

      // Preset button handlers
      presetBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
          presetBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const preset = btn.getAttribute('data-preset');

          if (preset === 'all') {{
            if (filterDateFrom) filterDateFrom.value = '';
            if (filterDateTo) filterDateTo.value = '';
          }} else if (preset === 'today') {{
            const today = new Date().toISOString().split('T')[0];
            if (filterDateFrom) filterDateFrom.value = today;
            if (filterDateTo) filterDateTo.value = today;
          }} else if (preset === '7d') {{
            const now = new Date();
            const past = new Date(now.getTime() - 6 * 24 * 60 * 60 * 1000);
            if (filterDateFrom) filterDateFrom.value = past.toISOString().split('T')[0];
            if (filterDateTo) filterDateTo.value = now.toISOString().split('T')[0];
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

      // Initial Render & Filter Count Initialization
      applyFilters();
    }})();
  </script>
</body>
</html>
"""

        try:
            with open(self.dashboard_file, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            logging.getLogger("Step4Reporting").error("Failed to write dashboard HTML: %s", e)

        return self.dashboard_file

    # ========================================================================
    # Open Dashboard in Browser
    # ========================================================================

    def open_dashboard(self) -> bool:
        """Launch dashboard.html in the default web browser."""
        if not self.dashboard_file.is_file():
            self.generate_html_dashboard()

        try:
            url = self.dashboard_file.resolve().as_uri()
            webbrowser.open_new_tab(url)
            return True
        except Exception:
            return False

    # ========================================================================
    # Background Activity Watcher & Delayed Launcher
    # ========================================================================

    def watch_and_launch(
        self,
        delay_seconds: float = 10.0,
        timeout: Optional[float] = None,
        poll_interval: float = 0.25,
    ) -> bool:
        """
        Two-Way Process:
          1. Wait silently until user moves mouse or strikes a key.
          2. Once user activity is detected, wait exactly delay_seconds (10s).
          3. Pop up dashboard.html in the user's browser.
          4. Exit cleanly (Universal Rule 26 hygiene).
        """
        detected = watch_for_user_input(timeout=timeout, poll_interval=poll_interval)
        if detected:
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            self.open_dashboard()
            return True
        return False

    def spawn_background_watcher(self, delay_seconds: float = 10.0) -> bool:
        """
        Spawn a completely detached background worker process that monitors for user input
        and opens the dashboard 10s after movement. Allows the main pipeline to complete
        without blocking.
        """
        python_exe = sys.executable
        script_path = self._this_dir / "step4_reporting.py"

        cmd = [
            str(python_exe),
            str(script_path),
            "--watch-worker",
            "--delay", str(delay_seconds),
            "--reports-dir", str(self.reports_dir),
            "--history-file", str(self.history_file),
        ]

        creation_flags = 0
        if IS_WINDOWS:
            # DETACHED_PROCESS (0x00000008) + CREATE_NEW_PROCESS_GROUP (0x00000200)
            creation_flags = 0x00000008 | 0x00000200

        try:
            subprocess.Popen(
                cmd,
                cwd=str(self.workspace_dir),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                shell=False,
            )
            return True
        except Exception:
            return False


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Step 4 - Reporting & Visual Dashboard Subsystem (AutoSelect-Commander)"
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
        default=10.0,
        help="Delay in seconds after user input detection before showing dashboard (default: 10.0s)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds for input detection (None = wait forever)"
    )

    args, _ = parser.parse_known_args()

    engine = Step4ReportingEngine(
        state_file_path=args.state_file,
        reports_dir=args.reports_dir,
        history_file_path=args.history_file,
    )

    # Manual Mode: Immediately open dashboard
    if args.show:
        engine.generate_html_dashboard()
        engine.open_dashboard()
        return 0

    # Internal Detached Watcher Worker
    if args.watch_worker:
        engine.watch_and_launch(delay_seconds=args.delay, timeout=args.timeout)
        return 0

    # Ingest the latest run from target_chat.json
    ok, msg, _ = engine.ingest_current_run(state_file=args.state_file)

    # If --no-watch or --record-only, exit immediately
    if args.no_watch:
        return 0

    # If --watch, run watcher synchronously
    if args.watch:
        engine.watch_and_launch(delay_seconds=args.delay, timeout=args.timeout)
        return 0

    # Default Automated Pipeline Mode:
    # Spawn background watcher so calling pipeline exits cleanly, while watcher waits
    # for physical user input + 10s delay to show dashboard without terminal clutter!
    engine.spawn_background_watcher(delay_seconds=args.delay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
