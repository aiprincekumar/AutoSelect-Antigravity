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
      max-width: 1200px;
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

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}

    .metric-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
      transition: var(--transition);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    }}

    .metric-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    }}

    .metric-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
    }}

    .metric-card.card-runs::before {{ background: var(--accent-emerald); }}
    .metric-card.card-questions::before {{ background: var(--accent-indigo); }}
    .metric-card.card-runtime::before {{ background: var(--accent-cyan); }}
    .metric-card.card-chats::before {{ background: var(--accent-purple); }}

    .metric-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .metric-title {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .metric-icon {{
      font-size: 1.25rem;
    }}

    .metric-value {{
      font-size: 2.1rem;
      font-weight: 700;
      font-family: var(--font-mono);
      letter-spacing: -0.03em;
      line-height: 1.1;
      margin-bottom: 6px;
    }}

    .metric-subtitle {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}

    /* Controls Bar */
    .controls-bar {{
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
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

    <!-- Metrics Grid -->
    <div class="metrics-grid">
      <!-- Total Runs -->
      <div class="metric-card card-runs">
        <div class="metric-header">
          <span class="metric-title">Total Automation Runs</span>
          <span class="metric-icon">🚀</span>
        </div>
        <div class="metric-value">{total_runs}</div>
        <div class="metric-subtitle">Steps 1 → 2 → 3 Fully Completed</div>
      </div>

      <!-- Questions Answered -->
      <div class="metric-card card-questions">
        <div class="metric-header">
          <span class="metric-title">Questions Answered</span>
          <span class="metric-icon">💬</span>
        </div>
        <div class="metric-value">{total_questions}</div>
        <div class="metric-subtitle">Grill-Me Questions Resolved</div>
      </div>

      <!-- Script Runtime -->
      <div class="metric-card card-runtime">
        <div class="metric-header">
          <span class="metric-title">Cumulative Runtime</span>
          <span class="metric-icon">⏱️</span>
        </div>
        <div class="metric-value">{runtime_fmt}</div>
        <div class="metric-subtitle">{total_seconds:.2f} Total Seconds Active</div>
      </div>

      <!-- Unique Chats -->
      <div class="metric-card card-chats">
        <div class="metric-header">
          <span class="metric-title">Chats Automated</span>
          <span class="metric-icon">📂</span>
        </div>
        <div class="metric-value">{total_chats}</div>
        <div class="metric-subtitle">Unique Conversations Processed</div>
      </div>
    </div>

    <!-- Controls Bar -->
    <div class="controls-bar">
      <input type="text" id="search-box" class="search-input" placeholder="🔍 Search by Conversation ID, topic, question, or option...">
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

    <!-- Detailed Questions & Options Breakdown -->
    <div class="section-title">📝 Detailed Questions & Options History</div>
    <div id="details-container">
      <!-- Dynamically populated by client JS -->
    </div>

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
      const searchBox = document.getElementById('search-box');
      const summaryTbody = document.getElementById('summary-tbody');
      const detailsContainer = document.getElementById('details-container');
      const themeToggle = document.getElementById('theme-toggle');

      // Theme toggle persistence
      const savedTheme = localStorage.getItem('asc_dashboard_theme') || 'dark';
      document.documentElement.setAttribute('data-theme', savedTheme);

      themeToggle.addEventListener('click', () => {{
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('asc_dashboard_theme', next);
      }});

      function render(filter = '') {{
        const filterLower = filter.toLowerCase().trim();
        const chatEntries = Object.entries(chats);

        // Render Summary Table
        summaryTbody.innerHTML = '';
        let tableRows = 0;

        for (const [cid, chat] of chatEntries) {{
          const topic = chat.topic_summary || 'Untitled Conversation';
          const match = !filterLower ||
            cid.toLowerCase().includes(filterLower) ||
            topic.toLowerCase().includes(filterLower);

          if (match) {{
            tableRows++;
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><span class="chat-id-tag">${{cid}}</span></td>
              <td><strong>${{escapeHtml(topic)}}</strong></td>
              <td><span class="badge-count">${{chat.run_count || 0}}</span></td>
              <td><span class="badge-count">${{chat.total_questions || 0}}</span></td>
              <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">${{chat.last_run_timestamp ? new Date(chat.last_run_timestamp).toLocaleString() : 'N/A'}}</td>
            `;
            summaryTbody.appendChild(tr);
          }}
        }}

        if (tableRows === 0) {{
          summaryTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching chat records found.</td></tr>`;
        }}

        // Render Detailed Cards
        detailsContainer.innerHTML = '';
        let cardsCount = 0;

        for (const [cid, chat] of chatEntries) {{
          const topic = chat.topic_summary || 'Untitled Conversation';
          const runs = chat.runs || [];

          // Filter inside questions
          const matchingRuns = runs.filter(run => {{
            if (!filterLower) return true;
            if (cid.toLowerCase().includes(filterLower) || topic.toLowerCase().includes(filterLower)) return true;
            return (run.questions || []).some(q =>
              (q.question || '').toLowerCase().includes(filterLower) ||
              (q.options || []).some(opt => opt.toLowerCase().includes(filterLower))
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
                    <span>⚡ Run #${{rIdx + 1}} (${{run.run_id || 'N/A'}})</span>
                    <span>Duration: ${{dur}} | ${{runDate}}</span>
                  </div>
                  ${{qHtml}}
                </div>
              `;
            }});

            card.innerHTML = `
              <div class="chat-card-header">
                <div class="chat-card-title">
                  <span class="chat-id-tag">${{cid}}</span>
                  <span>${{escapeHtml(topic)}}</span>
                </div>
                <div class="chat-card-meta">
                  <span class="badge-count">${{chat.run_count || 0}} run(s)</span>
                  <span class="badge-count">${{chat.total_questions || 0}} question(s)</span>
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
              <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 4px;">No Detailed Records Found</div>
              <div>No questions or options have been processed yet or matched your search filter.</div>
            </div>
          `;
        }}
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

      searchBox.addEventListener('input', (e) => render(e.target.value));
      render();
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
