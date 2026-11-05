#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern and Interactive Dashboard Generator (generate_modern_dashboard.py)
========================================================================
Subsystem: Modern and Interactive Dashboard Engine (V2 - Complete Feature Parity + UI/UX Overhaul)
Part of: AutoSelect-Commander Telemetry & Execution Reporting Suite
Department: Department 04 (UI/UX Design System) & Department 05 (Frontend Engineering)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Highlights & Full Feature Set:
  1. Complete Classic Filter Parity:
     - Full Presets: All Time, Today, Yesterday, Last 7 Days, Last 30 Days, This Week, This Month.
     - Date Range pickers (From Date, To Date).
     - Conversation selector dropdown (with dynamic topic & short ID options).
     - Complexity filter dropdown (All, Single Question, Multi-Question).
     - Speed / Latency filter dropdown (All, Fast <3s, Moderate 3-8s, Heavy >8s).
     - Filter Reset button.
     - Active Dismissible Chips for 1-click filter clearing.
  2. Tab-Contextual Keyboard Shortcut [/]:
     - When on 'Chats' tab: pressing [/] focuses #search-chats.
     - When on 'Questions' tab: pressing [/] focuses #search-questions.
     - When on 'Config' tab: pressing [/] focuses #search-config.
     - Auto-selects text on focus.
  3. Chats Tab (Complete Feature Parity):
     - Summary Stats Strip (Unique Chats, Lifetime Runs, Avg Runs/Chat).
     - Dedicated Search Input (#search-chats).
     - Full Chats Breakdown Table with Conversation ID, Topic Summary, Runs Count, Questions Answered, Last Automated.
  4. Questions Tab (Hierarchical & Actionable):
     - Organized by Conversation Card ➔ Run Block ➔ Question Prompt ➔ Option List.
     - 1-Click "Copy Q&A" on every question card with emerald toast notification.
     - Global Expand All / Collapse All buttons.
     - Clear Selected vs Recommended badge differentiation.
  5. Next-Gen Visual Hierarchy:
     - 2 North Star KPI Hero Cards with 2.5rem display font, vibrant gradients, and count-up animations.
     - 6 Secondary Operational Metrics.
     - 5-Step Pipeline Topology vector SVG with animated bus.
     - 7 Analytics SVG Charts with interactive floating tooltips on hover.
  6. Dual Header Clusters:
     - System Health Cluster (Server Bridge Online, Engine State, Mode Badge).
     - Action Control Cluster (Start/Stop, Logs Drawer, Theme, Sound Chimes, Refresh, Classic Switch, Shortcuts).
  7. Slide-Up Live Console Logs Drawer:
     - Real-time stream from /api/logs/tail (2.5s polling).
     - Syntax coloring, auto-scroll toggle, clear, close [Esc] or [L].
  8. Mode Switch & Config Tabs:
     - Side-by-side Production vs Test cards & Parameter Diff Matrix.
     - Live settings search input & floating Unsaved Changes dock.
  9. Web Audio API Synthesizer:
     - Futuristic chimes on Start, Stop, Copy (muteable via [M] or header button).
 10. Bidirectional Switcher:
     - 1-Click toggle between Modern & Interactive and Simple & Classic dashboards.
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Workspace path resolution
_THIS_DIR = Path(__file__).resolve().parent
_STEP4_DIR = _THIS_DIR.parent
_WORKSPACE_DIR = _STEP4_DIR.parent

if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from step_4_reporting.step4_reporting import Step4ReportingEngine, AutomationHistory


def build_modern_dashboard_html(
    history: Optional[AutomationHistory] = None,
    engine: Optional[Step4ReportingEngine] = None,
    workspace_dir: Optional[Path] = None,
) -> str:
    ws = workspace_dir or _WORKSPACE_DIR
    eng = engine or Step4ReportingEngine(workspace_dir=ws)
    hist = history or eng.load_history()

    # Base Metrics
    total_runs = hist.total_pipeline_runs
    total_questions = hist.total_questions_answered
    total_chats = max(hist.total_unique_chats, len(hist.chats))
    total_seconds = hist.total_runtime_seconds

    avg_latency = (total_seconds / total_runs) if total_runs > 0 else 0.0
    avg_density = (total_questions / total_runs) if total_runs > 0 else 0.0
    avg_depth = (total_questions / total_chats) if total_chats > 0 else 0.0
    avg_speed = (total_seconds / total_questions) if total_questions > 0 else 0.0
    avg_runs_per_chat = (total_runs / total_chats) if total_chats > 0 else 0.0

    # Format runtime string
    mins = int(total_seconds // 60)
    secs = int(total_seconds % 60)
    runtime_formatted = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    # Build conversation dropdown options for filter-chat
    chat_options = []
    for cid, chat in hist.chats.items():
        if isinstance(chat, dict):
            topic = chat.get("topic_summary") or "Untitled Conversation"
        else:
            topic = getattr(chat, "topic_summary", "") or "Untitled Conversation"
        trunc_topic = topic[:40] + ".." if len(topic) > 40 else topic
        short_cid = cid[:8] + ".." if len(cid) > 8 else cid
        chat_options.append(f'<option value="{cid}">{trunc_topic} ({short_cid})</option>')
    chat_options_html = "\n              ".join(chat_options)

    # Load runtime config
    cfg_path = ws / "step_9_complete_automation" / "config.json"
    runtime_cfg = {}
    if cfg_path.is_file():
        try:
            runtime_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            runtime_cfg = {}

    current_mode = runtime_cfg.get("mode", "production").lower()
    is_prod = current_mode == "production"

    timing_cfg = runtime_cfg.get("timing", {})
    enabled_steps = runtime_cfg.get("enabled_steps", {})
    poll_prod = timing_cfg.get("production_poll_interval", 1.0)
    poll_test = timing_cfg.get("test_poll_interval", 0.1)
    settle_delay = timing_cfg.get("settle_delay", 1.0)
    activity_delay = timing_cfg.get("user_activity_delay", 10.0)
    step1_enabled = enabled_steps.get("step1_window_focus", True)
    step2_enabled = enabled_steps.get("step2_dom_extraction", True)
    step3_enabled = enabled_steps.get("step3_keyboard_selection", True)
    step4_enabled = enabled_steps.get("step4_reporting", True)

    # Generate pure inline SVG charts
    pipeline_svg = eng.build_pipeline_svg()
    velocity_svg = eng.build_velocity_timeline_svg(hist)
    gauge_svg = eng.build_productivity_gauge_svg(hist)
    heatmap_svg = eng.build_time_heatmap_svg(hist)
    option_breakdown_svg = eng.build_option_breakdown_svg(hist)
    distribution_svg = eng.build_chat_distribution_svg(hist)
    topic_share_svg = eng.build_topic_share_svg(hist)
    latency_trend_svg = eng.build_latency_trend_svg(hist)

    history_json_str = json.dumps(hist.to_dict(), ensure_ascii=False)
    runtime_config_json_str = json.dumps(runtime_cfg, indent=2, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoSelect-Commander • Modern & Interactive Dashboard</title>
  <style>
    :root {{
      --bg-primary: #07090f;
      --bg-surface: #0e1422;
      --bg-surface-elevated: #151d30;
      --bg-surface-highlight: #1e2942;
      --bg-surface-glass: rgba(14, 20, 34, 0.85);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.4);
      --border-hover: rgba(255, 255, 255, 0.18);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-indigo: #6366f1;
      --accent-indigo-glow: rgba(99, 102, 241, 0.35);
      --accent-emerald: #10b981;
      --accent-emerald-bg: rgba(16, 185, 129, 0.12);
      --accent-emerald-border: #059669;
      --accent-emerald-glow: rgba(16, 185, 129, 0.35);
      --accent-cyan: #06b6d4;
      --accent-cyan-glow: rgba(6, 182, 212, 0.35);
      --accent-purple: #a855f7;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --radius-xl: 18px;
      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.25);
      --shadow-md: 0 6px 20px rgba(0, 0, 0, 0.35);
      --shadow-lg: 0 12px 36px rgba(0, 0, 0, 0.5);
      --transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    [data-theme="light"] {{
      --bg-primary: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #f1f5f9;
      --bg-surface-highlight: #e2e8f0;
      --bg-surface-glass: rgba(255, 255, 255, 0.9);
      --border-subtle: rgba(0, 0, 0, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --border-hover: rgba(0, 0, 0, 0.18);
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-muted: #94a3b8;
      --accent-emerald-bg: rgba(16, 185, 129, 0.1);
      --accent-indigo-glow: rgba(99, 102, 241, 0.18);
      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05);
      --shadow-md: 0 6px 20px rgba(0, 0, 0, 0.08);
      --shadow-lg: 0 12px 36px rgba(0, 0, 0, 0.12);
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
      padding: 18px 20px 60px;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.25s ease, color 0.25s ease;
      min-height: 100vh;
    }}

    .container {{
      max-width: 1340px;
      margin: 0 auto;
    }}

    /* ========================================================================
       Header & Modern Dual-Cluster Architecture
       ======================================================================== */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 22px;
      background: var(--bg-surface-glass);
      backdrop-filter: blur(14px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      margin-bottom: 14px;
      box-shadow: var(--shadow-md);
      position: sticky;
      top: 14px;
      z-index: 100;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .header-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .logo-badge {{
      width: 44px;
      height: 44px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 0 18px var(--accent-indigo-glow);
      flex-shrink: 0;
      animation: logoGlow 4s ease-in-out infinite alternate;
    }}

    @keyframes logoGlow {{
      0% {{ box-shadow: 0 0 14px rgba(99, 102, 241, 0.35); }}
      100% {{ box-shadow: 0 0 24px rgba(168, 85, 247, 0.55); }}
    }}

    .header-titles h1 {{
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .header-titles .version-pill {{
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 9999px;
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.4);
      letter-spacing: 0.04em;
    }}

    .header-titles p {{
      font-size: 0.8rem;
      color: var(--text-secondary);
    }}

    .header-right {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .health-cluster {{
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 9999px;
    }}

    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 11px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      white-space: nowrap;
      transition: var(--transition);
    }}

    .pulse-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      display: inline-block;
    }}

    .status-bridge-online {{
      background: var(--accent-emerald-bg);
      color: var(--accent-emerald);
      border: 1px solid var(--accent-emerald-border);
    }}
    .status-bridge-online .pulse-dot {{
      background: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
      animation: pulseAnim 2s infinite;
    }}

    .status-bridge-offline {{
      background: rgba(244, 63, 94, 0.12);
      color: var(--accent-rose);
      border: 1px solid rgba(244, 63, 94, 0.35);
    }}
    .status-bridge-offline .pulse-dot {{
      background: var(--accent-rose);
    }}

    .status-idle {{
      background: rgba(148, 163, 184, 0.12);
      color: var(--text-muted);
      border: 1px solid rgba(148, 163, 184, 0.3);
    }}
    .status-idle .pulse-dot {{
      background: var(--text-muted);
    }}

    .status-active {{
      background: var(--accent-emerald-bg);
      color: var(--accent-emerald);
      border: 1px solid var(--accent-emerald-border);
    }}
    .status-active .pulse-dot {{
      background: var(--accent-emerald);
      box-shadow: 0 0 10px var(--accent-emerald);
      animation: pulseAnim 1.4s infinite;
    }}

    .status-paused {{
      background: rgba(245, 158, 11, 0.12);
      color: var(--accent-amber);
      border: 1px solid rgba(245, 158, 11, 0.4);
    }}
    .status-paused .pulse-dot {{
      background: var(--accent-amber);
      animation: pulseAnim 1.6s infinite;
    }}

    @keyframes pulseAnim {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.4); opacity: 0.6; }}
    }}

    .action-cluster {{
      display: flex;
      align-items: center;
      gap: 7px;
      flex-wrap: wrap;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 13px;
      font-size: 0.8rem;
      font-weight: 600;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      cursor: pointer;
      transition: var(--transition);
      white-space: nowrap;
      user-select: none;
    }}

    .btn:hover {{
      background: var(--bg-surface-highlight);
      border-color: var(--border-hover);
      transform: translateY(-1px);
    }}

    .btn:active {{
      transform: translateY(0);
    }}

    .btn-automation {{
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #ffffff;
      border: 1px solid #059669;
      box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
    }}
    .btn-automation:hover {{
      background: linear-gradient(135deg, #059669 0%, #047857 100%);
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45);
    }}

    .btn-automation.state-running {{
      background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
      border-color: #be123c;
      box-shadow: 0 2px 10px rgba(244, 63, 94, 0.35);
      animation: runningBtnGlow 2s infinite alternate;
    }}
    @keyframes runningBtnGlow {{
      0% {{ box-shadow: 0 0 10px rgba(244, 63, 94, 0.3); }}
      100% {{ box-shadow: 0 0 18px rgba(244, 63, 94, 0.6); }}
    }}

    .btn-classic-switch {{
      background: rgba(99, 102, 241, 0.12);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.3);
    }}
    .btn-classic-switch:hover {{
      background: rgba(99, 102, 241, 0.22);
      border-color: rgba(99, 102, 241, 0.5);
      color: #a5b4fc;
    }}

    .log-unread-badge {{
      background: var(--accent-indigo);
      color: #ffffff;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 9999px;
      margin-left: 2px;
    }}

    /* ========================================================================
       Live Pulse Ticker Strip
       ======================================================================== */
    .live-ticker-strip {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 7px 16px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      margin-bottom: 16px;
      font-size: 0.78rem;
      color: var(--text-secondary);
      box-shadow: var(--shadow-sm);
    }}

    .ticker-left {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .ticker-beacon {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
      color: var(--accent-emerald);
      letter-spacing: 0.03em;
    }}

    .ticker-beacon .beacon-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
      animation: pulseAnim 1.8s infinite;
    }}

    .ticker-msg {{
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 0.76rem;
    }}

    .ticker-clock {{
      font-family: var(--font-mono);
      color: var(--text-muted);
      font-size: 0.76rem;
    }}

    /* ========================================================================
       Horizontal Modern Tab Navigation Bar
       ======================================================================== */
    .tab-nav {{
      display: flex;
      gap: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 5px;
      margin-bottom: 18px;
      box-shadow: var(--shadow-sm);
      overflow-x: auto;
    }}

    .tab-btn {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 9px 18px;
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: var(--transition);
      white-space: nowrap;
    }}

    .tab-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-surface-elevated);
    }}

    .tab-btn.active {{
      background: var(--accent-indigo);
      color: #ffffff;
      box-shadow: 0 2px 12px var(--accent-indigo-glow);
    }}

    .tab-badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 1px 7px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.2);
      color: inherit;
    }}

    .tab-btn:not(.active) .tab-badge {{
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      border: 1px solid var(--border-subtle);
    }}

    /* ========================================================================
       Full Interactive Multi-Dimensional Filter Toolbar (Classic Parity + Modern Chips)
       ======================================================================== */
    .filter-toolbar {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      margin-bottom: 20px;
      box-shadow: var(--shadow-sm);
      transition: var(--transition);
    }}

    .filter-toolbar-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .filter-toolbar-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--text-primary);
    }}

    .filter-stats-badge {{
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-secondary);
      background: var(--bg-surface-elevated);
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid var(--border-subtle);
    }}

    /* Row 1: Quick Presets Bar */
    .filter-presets-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}

    .presets-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
    }}

    .filter-presets {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .preset-btn {{
      padding: 4px 12px;
      font-size: 0.75rem;
      font-weight: 600;
      border-radius: 9999px;
      border: 1px solid var(--border-subtle);
      background: var(--bg-surface-elevated);
      color: var(--text-secondary);
      cursor: pointer;
      transition: var(--transition);
    }}

    .preset-btn:hover {{
      background: var(--bg-surface-highlight);
      color: var(--text-primary);
    }}

    .preset-btn.active {{
      background: var(--accent-indigo);
      color: #ffffff;
      border-color: var(--accent-indigo);
      box-shadow: 0 0 10px var(--accent-indigo-glow);
    }}

    /* Row 2: Granular Controls Row */
    .filter-controls-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      align-items: flex-end;
      margin-bottom: 12px;
    }}

    .filter-control-group {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}

    .filter-label {{
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .filter-select,
    .filter-input-date {{
      width: 100%;
      padding: 8px 12px;
      border-radius: var(--radius-md);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 0.8rem;
      font-family: inherit;
      outline: none;
      transition: var(--transition);
    }}

    .filter-select:focus,
    .filter-input-date:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 10px var(--accent-indigo-glow);
    }}

    .filter-date-inputs {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .filter-date-sep {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    .btn-reset-filter {{
      background: rgba(244, 63, 94, 0.12);
      color: var(--accent-rose);
      border: 1px solid rgba(244, 63, 94, 0.35);
      padding: 8px 14px;
      height: 38px;
    }}
    .btn-reset-filter:hover {{
      background: rgba(244, 63, 94, 0.22);
      border-color: rgba(244, 63, 94, 0.5);
    }}

    /* Active Dismissible Chips Row */
    .active-chips-row {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      padding-top: 10px;
      border-top: 1px dashed var(--border-subtle);
    }}

    .active-chips-label {{
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .filter-chip {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 9px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      background: rgba(99, 102, 241, 0.15);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.35);
    }}

    .filter-chip-remove {{
      cursor: pointer;
      font-weight: 700;
      opacity: 0.7;
    }}
    .filter-chip-remove:hover {{
      opacity: 1;
      color: #ffffff;
    }}

    /* ========================================================================
       Tab Panels & General Containers
       ======================================================================== */
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
      animation: fadeIn 0.22s ease-in-out;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* ========================================================================
       Overview Tab: 8 KPIs with Visual Hierarchy (North Star Hero Cards)
       ======================================================================== */
    .hero-kpis-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin-bottom: 16px;
    }}

    .hero-kpi-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px 24px;
      box-shadow: var(--shadow-md);
      position: relative;
      overflow: hidden;
      transition: var(--transition);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .hero-kpi-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }}

    .hero-kpi-card.card-questions {{
      border-color: rgba(99, 102, 241, 0.4);
      background: linear-gradient(135deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.08) 100%);
    }}
    .hero-kpi-card.card-questions:hover {{
      box-shadow: 0 0 28px rgba(99, 102, 241, 0.25);
    }}

    .hero-kpi-card.card-runs {{
      border-color: rgba(16, 185, 129, 0.4);
      background: linear-gradient(135deg, var(--bg-surface) 0%, rgba(16, 185, 129, 0.08) 100%);
    }}
    .hero-kpi-card.card-runs:hover {{
      box-shadow: 0 0 28px rgba(16, 185, 129, 0.25);
    }}

    .hero-kpi-left .kpi-label {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}

    .hero-kpi-left .kpi-value {{
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.1;
      font-family: var(--font-family);
    }}

    .hero-kpi-left .kpi-subtitle {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 6px;
    }}

    .hero-kpi-badge {{
      font-size: 2.2rem;
      opacity: 0.85;
      padding: 14px;
      border-radius: var(--radius-lg);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
    }}

    .secondary-kpis-grid {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 12px;
      margin-bottom: 24px;
    }}

    @media (max-width: 1100px) {{
      .secondary-kpis-grid {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}

    @media (max-width: 680px) {{
      .hero-kpis-grid,
      .secondary-kpis-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .metric-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      box-shadow: var(--shadow-sm);
      transition: var(--transition);
    }}

    .metric-card:hover {{
      background: var(--bg-surface-elevated);
      border-color: var(--border-hover);
      transform: translateY(-2px);
    }}

    .metric-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .metric-title {{
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .metric-icon {{
      font-size: 1rem;
    }}

    .metric-value {{
      font-size: 1.45rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }}

    .metric-subtitle {{
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    /* ========================================================================
       Charts & Topology Cards
       ======================================================================== */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
      margin-bottom: 24px;
    }}

    .chart-card-wide {{
      grid-column: 1 / -1;
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
      padding: 18px 20px;
      box-shadow: var(--shadow-sm);
      position: relative;
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      user-select: none;
    }}

    .card-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.95rem;
      font-weight: 700;
    }}

    .collapse-icon {{
      transition: transform 0.2s ease;
      font-size: 0.85rem;
      color: var(--text-muted);
    }}

    .collapsed .collapse-icon {{
      transform: rotate(-90deg);
    }}

    .card-collapsible-body {{
      display: grid;
      grid-template-rows: 1fr;
      transition: grid-template-rows 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s;
    }}

    .card-collapsible-body.collapsed {{
      grid-template-rows: 0fr;
      opacity: 0;
      overflow: hidden;
      margin-top: 0 !important;
    }}

    .card-collapsible-body > div,
    .card-collapsible-body > svg {{
      overflow: hidden;
    }}

    /* Floating SVG Tooltip */
    #chart-floating-tooltip {{
      position: fixed;
      pointer-events: none;
      background: rgba(14, 20, 34, 0.95);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #f8fafc;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      font-size: 0.75rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      z-index: 1000;
      display: none;
      line-height: 1.4;
      white-space: nowrap;
    }}

    /* ========================================================================
       Chats Tab (Stats Strip, Dedicated Search, Breakdown Table)
       ======================================================================== */
    .stats-strip {{
      display: flex;
      gap: 14px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}

    .stat-pill {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 18px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      font-size: 0.84rem;
      font-weight: 600;
      color: var(--text-secondary);
      box-shadow: var(--shadow-sm);
    }}

    .stat-num {{
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--accent-indigo);
      font-family: var(--font-mono);
    }}

    .controls-bar {{
      margin-bottom: 16px;
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .search-input-wrap {{
      position: relative;
      flex: 1;
      max-width: 600px;
    }}

    .search-input {{
      width: 100%;
      padding: 10px 14px 10px 38px;
      border-radius: var(--radius-md);
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 0.85rem;
      outline: none;
      transition: var(--transition);
    }}

    .search-input:focus {{
      border-color: var(--accent-indigo);
      box-shadow: 0 0 14px var(--accent-indigo-glow);
    }}

    .search-icon-pos {{
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 0.9rem;
      pointer-events: none;
    }}

    .search-shortcut-hint {{
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 0.72rem;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-family: var(--font-mono);
      pointer-events: none;
    }}

    .table-container {{
      overflow-x: auto;
      border-radius: var(--radius-md);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.84rem;
    }}

    th, td {{
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border-subtle);
    }}

    th {{
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      text-transform: uppercase;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}

    tr:hover td {{
      background: var(--bg-surface-elevated);
    }}

    .chat-id-tag {{
      font-family: var(--font-mono);
      font-size: 0.78rem;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      background: rgba(99, 102, 241, 0.12);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.28);
    }}

    .badge-count {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
    }}

    /* ========================================================================
       Questions Tab (Deep Hierarchical Q&A Tree)
       ======================================================================== */
    .chat-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      margin-bottom: 18px;
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      transition: var(--transition);
    }}

    .chat-card:hover {{
      border-color: var(--border-hover);
    }}

    .chat-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 18px;
      background: var(--bg-surface-elevated);
      cursor: pointer;
      user-select: none;
    }}

    .chat-card-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.92rem;
      font-weight: 700;
    }}

    .chat-card-meta {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .chat-card-body {{
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .chat-card-body.collapsed {{
      display: none;
    }}

    .run-block {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
    }}

    .run-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: var(--bg-surface-highlight);
      cursor: pointer;
      font-size: 0.82rem;
      user-select: none;
    }}

    .run-body {{
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .run-body.collapsed {{
      display: none;
    }}

    .question-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
    }}

    .question-prompt {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      gap: 10px;
      user-select: none;
    }}

    .question-prompt-left {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
    }}

    .question-num {{
      font-size: 0.72rem;
      font-weight: 800;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.15);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
    }}

    .question-prompt-right {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-copy-qa {{
      padding: 3px 8px;
      font-size: 0.72rem;
      border-radius: var(--radius-sm);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      cursor: pointer;
      transition: var(--transition);
    }}
    .btn-copy-qa:hover {{
      background: var(--accent-indigo);
      color: #ffffff;
      border-color: var(--accent-indigo);
    }}

    .options-list {{
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: var(--bg-primary);
      border-top: 1px solid var(--border-subtle);
    }}

    .options-list.collapsed {{
      display: none;
    }}

    .option-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      font-size: 0.82rem;
    }}

    .option-item.selected {{
      background: var(--accent-emerald-bg);
      border-color: var(--accent-emerald-border);
      color: #f8fafc;
    }}

    .option-badge {{
      background: #10b981;
      color: #ffffff;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 9999px;
    }}

    /* ========================================================================
       Mode Switch Tab
       ======================================================================== */
    .mode-cards-container {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
      margin-bottom: 22px;
    }}

    @media (max-width: 800px) {{
      .mode-cards-container {{
        grid-template-columns: 1fr;
      }}
    }}

    .mode-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 22px;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: var(--transition);
      position: relative;
    }}

    .mode-card.active-mode {{
      border-color: var(--accent-emerald);
      box-shadow: 0 0 24px rgba(16, 185, 129, 0.2);
    }}

    .mode-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }}

    .mode-title {{
      font-size: 1.15rem;
      font-weight: 700;
    }}

    .mode-active-pill {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 9999px;
      background: var(--accent-emerald-bg);
      color: var(--accent-emerald);
      border: 1px solid var(--accent-emerald-border);
    }}

    .mode-features-list {{
      list-style: none;
      margin: 14px 0 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 0.82rem;
      color: var(--text-secondary);
    }}

    .mode-features-list li {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .diff-table-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      box-shadow: var(--shadow-sm);
    }}

    /* ========================================================================
       Config Tab
       ======================================================================== */
    .config-group-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      margin-bottom: 16px;
    }}

    .config-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      margin-top: 14px;
    }}

    @media (max-width: 768px) {{
      .config-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .cfg-field {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}

    .cfg-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-secondary);
    }}

    .cfg-input {{
      padding: 8px 12px;
      border-radius: var(--radius-md);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 0.82rem;
      font-family: var(--font-mono);
      outline: none;
    }}

    .cfg-input:focus {{
      border-color: var(--accent-indigo);
    }}

    /* Floating Unsaved Changes Dock */
    #unsaved-changes-dock {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--accent-amber);
      border-radius: 9999px;
      padding: 10px 22px;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
      z-index: 500;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s;
      opacity: 0;
      pointer-events: none;
    }}

    #unsaved-changes-dock.visible {{
      transform: translateX(-50%) translateY(0);
      opacity: 1;
      pointer-events: auto;
    }}

    /* ========================================================================
       Slide-Up Live Console Logs Drawer
       ======================================================================== */
    #logs-drawer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 380px;
      background: #050811;
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
      background: #0a0f1d;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
      background: #050811;
      white-space: pre-wrap;
      word-break: break-all;
    }}

    .log-line-info {{ color: #38bdf8; }}
    .log-line-warn {{ color: #f59e0b; }}
    .log-line-err  {{ color: #f43f5e; }}

    /* Floating Toast */
    #toast-notify {{
      position: fixed;
      top: 24px;
      right: 24px;
      padding: 10px 18px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--accent-emerald-border);
      color: #ffffff;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      font-size: 0.82rem;
      font-weight: 600;
      z-index: 2000;
      display: none;
      animation: toastIn 0.25s ease;
    }}

    @keyframes toastIn {{
      from {{ transform: translateY(-20px); opacity: 0; }}
      to {{ transform: translateY(0); opacity: 1; }}
    }}

    /* Keyboard Shortcuts Modal */
    .modal-backdrop {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(4px);
      z-index: 1500;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}

    .modal-backdrop.open {{
      display: flex;
    }}

    .modal-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      max-width: 520px;
      width: 100%;
      box-shadow: var(--shadow-lg);
    }}

    .shortcut-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 0.82rem;
    }}

    .shortcut-key {{
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      font-family: var(--font-mono);
      font-size: 0.74rem;
      color: var(--accent-indigo);
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Header with Dual Cluster Architecture -->
    <header>
      <div class="header-left">
        <div class="logo-badge">⚡</div>
        <div class="header-titles">
          <h1>AutoSelect-Commander <span class="version-pill">MODERN & INTERACTIVE</span></h1>
          <p>Autonomous Execution Telemetry, Process Control & Grill-Me Decision Ledger</p>
        </div>
      </div>

      <div class="header-right">
        <!-- Cluster 1: System Health Indicators -->
        <div class="health-cluster">
          <span class="status-pill status-bridge-online" id="server-bridge-pill" title="Control Server Port 8501">
            <span class="pulse-dot"></span>
            <span id="bridge-text">Bridge Online</span>
          </span>
          <span class="status-pill status-idle" id="dashboard-status-pill">
            <span class="pulse-dot"></span>
            <span id="status-text">⚪ Inactive</span>
          </span>
          <span class="status-pill" id="header-mode-badge" style="background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.35);">
            ⚡ {current_mode.upper()}
          </span>
        </div>

        <!-- Cluster 2: Action Controls -->
        <div class="action-cluster">
          <button class="btn btn-automation state-stopped" id="automation-toggle-btn" title="Toggle Complete Automation Pipeline">
            <span id="control-icon">▶️</span>
            <span id="control-label">Start Automation</span>
          </button>
          <button class="btn" id="btn-toggle-logs" title="Toggle Live Console Logs Stream (L)">
            <span>📟</span>
            <span>Logs</span>
            <span class="log-unread-badge" id="log-count-badge">0</span>
          </button>
          <button class="btn btn-classic-switch" id="btn-switch-classic" onclick="window.location.href='classic_dashboard.html'" title="Switch to Simple & Classic Dashboard">
            <span>🏛️</span>
            <span>Classic View</span>
          </button>
          <button class="btn" id="btn-audio-toggle" title="Toggle Futuristic Audio Chimes (M)">
            <span id="audio-icon">🔔</span>
          </button>
          <button class="btn" id="theme-toggle" title="Toggle Dark/Light Theme (T)">🌓</button>
          <button class="btn" id="btn-header-refresh" onclick="location.reload()" title="Refresh Telemetry Data">
            <span>🔄</span>
            <span id="refresh-countdown">10s</span>
          </button>
          <button class="btn" id="btn-help-shortcuts" title="Keyboard Shortcuts Help (?)">⌨️</button>
        </div>
      </div>
    </header>

    <!-- Live Pulse Ticker Strip -->
    <div class="live-ticker-strip">
      <div class="ticker-left">
        <span class="ticker-beacon"><span class="beacon-dot"></span> LIVE TELEMETRY</span>
        <span class="ticker-msg" id="ticker-status-msg">Complete Automation Daemon Ready • Last Run: {avg_latency:.1f}s • {total_questions} Questions Resolved</span>
      </div>
      <div class="ticker-clock" id="live-clock">--:--:--</div>
    </div>

    <!-- Horizontal Tab Navigation Bar -->
    <nav class="tab-nav" role="tablist" aria-label="Dashboard Tabs">
      <button class="tab-btn active" id="tab-btn-overview" role="tab" aria-selected="true" aria-controls="tab-overview" data-tab="overview">
        <span>📊</span>
        <span>Overview</span>
      </button>
      <button class="tab-btn" id="tab-btn-chats" role="tab" aria-selected="false" aria-controls="tab-chats" data-tab="chats">
        <span>📂</span>
        <span>Chats</span>
        <span class="tab-badge" id="tab-chats-badge">{total_chats}</span>
      </button>
      <button class="tab-btn" id="tab-btn-questions" role="tab" aria-selected="false" aria-controls="tab-questions" data-tab="questions">
        <span>💬</span>
        <span>Questions</span>
        <span class="tab-badge" id="tab-questions-badge">{total_questions}</span>
      </button>
      <button class="tab-btn" id="tab-btn-modes" role="tab" aria-selected="false" aria-controls="tab-modes" data-tab="modes">
        <span>🎛️</span>
        <span>Mode Switch</span>
        <span class="tab-badge" id="tab-modes-badge" style="background: rgba(16,185,129,0.2); color: #34d399;">Prod</span>
      </button>
      <button class="tab-btn" id="tab-btn-config" role="tab" aria-selected="false" aria-controls="tab-config" data-tab="config">
        <span>⚙️</span>
        <span>Config</span>
      </button>
    </nav>

    <!-- Full Interactive Multi-Dimensional Filter Toolbar (Classic Parity + Modern Dismiss Chips) -->
    <section class="filter-toolbar" id="contextual-filter-toolbar" aria-label="Filters Toolbar">
      <div class="filter-toolbar-header">
        <div class="filter-toolbar-title">
          <span>🔍</span>
          <span>Interactive Multi-Dimensional Filter Toolbar</span>
        </div>
        <div class="filter-stats-badge" id="filter-stats-badge">
          Showing <span id="filter-count" style="font-weight: 700; color: var(--text-primary);">{total_runs}</span> of <span id="filter-total">{total_runs}</span> runs
        </div>
      </div>

      <!-- Row 1: Quick Presets Bar -->
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

      <!-- Row 2: Granular Custom Filter Controls (Classic 100% Parity) -->
      <div class="filter-controls-row">
        <!-- Date Range Filter -->
        <div class="filter-control-group">
          <label class="filter-label" for="filter-date-from">Date Range</label>
          <div class="filter-date-inputs">
            <input type="date" id="filter-date-from" class="filter-input-date" title="Filter From Date">
            <span class="filter-date-sep">to</span>
            <input type="date" id="filter-date-to" class="filter-input-date" title="Filter To Date">
          </div>
        </div>

        <!-- Conversation Selector Dropdown -->
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
            <option value="single">Single Question Runs</option>
            <option value="multi">Multi-Question Runs (&gt;= 2)</option>
          </select>
        </div>

        <!-- Speed / Latency Filter Dropdown -->
        <div class="filter-control-group">
          <label class="filter-label" for="filter-speed">Speed / Latency</label>
          <select id="filter-speed" class="filter-select">
            <option value="all">All Speeds</option>
            <option value="fast">Fast (&lt; 3s)</option>
            <option value="moderate">Moderate (3s - 8s)</option>
            <option value="heavy">Heavy (&gt; 8s)</option>
          </select>
        </div>

        <!-- Reset Button -->
        <div class="filter-control-group">
          <label class="filter-label">&nbsp;</label>
          <button type="button" class="btn btn-reset-filter" id="filter-reset-btn" title="Reset all filters to default">
            <span>✕ Reset</span>
          </button>
        </div>
      </div>

      <!-- Active Dismissible Chips Row -->
      <div class="active-chips-row" id="active-chips-container">
        <span class="active-chips-label">Active:</span>
        <span class="filter-chip" id="chip-preset">Preset: All Time</span>
      </div>
    </section>

    <!-- TAB 1: OVERVIEW -->
    <main id="tab-overview" class="tab-panel active" role="tabpanel" aria-labelledby="tab-btn-overview">
      <!-- Row 1: Two High-Priority North Star Hero Cards -->
      <div class="hero-kpis-grid">
        <div class="hero-kpi-card card-questions">
          <div class="hero-kpi-left">
            <div class="kpi-label">Primary North Star Metric</div>
            <div class="kpi-value counter-value" data-target="{total_questions}">0</div>
            <div class="kpi-subtitle">Total Grill-Me Multi-Choice Questions Resolved</div>
          </div>
          <div class="hero-kpi-badge">💬</div>
        </div>

        <div class="hero-kpi-card card-runs">
          <div class="hero-kpi-left">
            <div class="kpi-label">Pipeline Execution Volume</div>
            <div class="kpi-value counter-value" data-target="{total_runs}">0</div>
            <div class="kpi-subtitle">Completed Autonomous End-to-End Cycles</div>
          </div>
          <div class="hero-kpi-badge">🚀</div>
        </div>
      </div>

      <!-- Row 2: Six Secondary Operational Metrics -->
      <div class="secondary-kpis-grid">
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Active Runtime</span>
            <span class="metric-icon">⏱️</span>
          </div>
          <div class="metric-value">{runtime_formatted}</div>
          <div class="metric-subtitle">{total_seconds:.1f}s cumulative</div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Distinct Chats</span>
            <span class="metric-icon">📂</span>
          </div>
          <div class="metric-value counter-value" data-target="{total_chats}">0</div>
          <div class="metric-subtitle">Active sessions automated</div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Avg Latency</span>
            <span class="metric-icon">⚡</span>
          </div>
          <div class="metric-value">{avg_latency:.1f}s</div>
          <div class="metric-subtitle">Per execution run</div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Question Density</span>
            <span class="metric-icon">📊</span>
          </div>
          <div class="metric-value">{avg_density:.1f}</div>
          <div class="metric-subtitle">Questions / run average</div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Avg Depth</span>
            <span class="metric-icon">🎯</span>
          </div>
          <div class="metric-value">{avg_depth:.1f}</div>
          <div class="metric-subtitle">Questions / chat average</div>
        </div>

        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Resolution Speed</span>
            <span class="metric-icon">⚡</span>
          </div>
          <div class="metric-value">{avg_speed:.1f}s</div>
          <div class="metric-subtitle">Sec / question resolved</div>
        </div>
      </div>

      <!-- Collapsible Architecture Topology Diagram -->
      <div class="chart-card chart-card-wide" style="margin-bottom: 24px;">
        <div class="card-header collapsible-header" data-target="arch-body">
          <div class="card-title">
            <span class="collapse-icon">▾</span>
            <span>⚡ 5-Step Pipeline Topology & Subsystem Bus</span>
          </div>
          <span style="font-size: 0.75rem; color: var(--text-muted);">Step 0 to Step 4 Data Highway</span>
        </div>
        <div class="card-collapsible-body" id="arch-body" style="margin-top: 14px;">
          {pipeline_svg}
        </div>
      </div>

      <!-- 7 Modern Visual Analytics SVG Charts Grid -->
      <div class="charts-grid">
        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-velocity">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>📈 Velocity Timeline & Run Latency</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-velocity" style="margin-top: 14px;">
            {velocity_svg}
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-gauge">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>🎯 Productivity & Efficiency Gauge</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-gauge" style="margin-top: 14px;">
            {gauge_svg}
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-heatmap">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>🗓️ 24-Hour Execution Activity Heatmap</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-heatmap" style="margin-top: 14px;">
            {heatmap_svg}
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-options">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>📊 Option Selection Breakdown</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-options" style="margin-top: 14px;">
            {option_breakdown_svg}
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-dist">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>📶 Chat Distribution & Run Volume</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-dist" style="margin-top: 14px;">
            {distribution_svg}
          </div>
        </div>

        <div class="chart-card">
          <div class="card-header collapsible-header" data-target="chart-topic">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>🍩 Conversation Topic Share</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-topic" style="margin-top: 14px;">
            {topic_share_svg}
          </div>
        </div>

        <div class="chart-card chart-card-wide">
          <div class="card-header collapsible-header" data-target="chart-latency">
            <div class="card-title">
              <span class="collapse-icon">▾</span>
              <span>📉 Run Duration & Latency Trend</span>
            </div>
          </div>
          <div class="card-collapsible-body" id="chart-latency" style="margin-top: 14px;">
            {latency_trend_svg}
          </div>
        </div>
      </div>
    </main>

    <!-- TAB 2: CHATS (Complete Feature Parity & Dedicated Search) -->
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
        <div class="search-input-wrap">
          <span class="search-icon-pos">🔍</span>
          <input type="text" id="search-chats" class="search-input" placeholder="Search chats by Conversation ID or topic summary...">
          <span class="search-shortcut-hint">Press [/]</span>
        </div>
      </div>

      <!-- Chat Breakdown Table -->
      <div class="chart-card chart-card-wide" id="chats-breakdown-section">
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
    </main>

    <!-- TAB 3: QUESTIONS (Hierarchical Tree with Expand/Collapse & Copy) -->
    <main id="tab-questions" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-questions">
      <div class="controls-bar" style="justify-content: space-between; flex-wrap: wrap;">
        <div class="search-input-wrap">
          <span class="search-icon-pos">🔍</span>
          <input type="text" id="search-questions" class="search-input" placeholder="Search questions, options, topics, or conversation IDs...">
          <span class="search-shortcut-hint">Press [/]</span>
        </div>
        <div style="display: flex; gap: 8px;">
          <button type="button" class="btn" id="btn-expand-all-questions">▾ Expand All</button>
          <button type="button" class="btn" id="btn-collapse-all-questions">▸ Collapse All</button>
        </div>
      </div>

      <div id="details-container">
        <!-- Dynamically populated by client JS -->
      </div>
    </main>

    <!-- TAB 4: MODE SWITCH -->
    <main id="tab-modes" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-modes">
      <div class="mode-cards-container">
        <div class="mode-card {'active-mode' if is_prod else ''}" id="mode-card-prod">
          <div>
            <div class="mode-card-header">
              <span class="mode-title">⚡ Production Mode</span>
              {'<span class="mode-active-pill">CURRENT ACTIVE</span>' if is_prod else ''}
            </div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
              Strict human-like execution cadence, safety sentinels, 10-second user inactivity verification, and resilient retry buffers.
            </p>
            <ul class="mode-features-list">
              <li><span>🛡️</span> 10.0s User Inactivity Settle Delay</li>
              <li><span>⏱️</span> 1.0s Process Polling Interval</li>
              <li><span>⌨️</span> Human-mimicking keystroke hold delays</li>
              <li><span>🔒</span> Full Win32 Foreground Focus Verification</li>
            </ul>
          </div>
          <button class="btn btn-automation" id="btn-set-prod" style="width: 100%; justify-content: center;">
            {'✓ Active in Production' if is_prod else 'Switch to Production Mode'}
          </button>
        </div>

        <div class="mode-card {'active-mode' if not is_prod else ''}" id="mode-card-test">
          <div>
            <div class="mode-card-header">
              <span class="mode-title">🧪 Test Mode</span>
              {'<span class="mode-active-pill">CURRENT ACTIVE</span>' if not is_prod else ''}
            </div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
              High-speed development mode with minimal delays, fast 0.1s polling, and rapid execution for automated regression testing.
            </p>
            <ul class="mode-features-list">
              <li><span>⚡</span> 0.5s Fast Settle Delay</li>
              <li><span>⏱️</span> 0.1s High-Frequency Polling</li>
              <li><span>⏩</span> Zero keystroke delay simulation</li>
              <li><span>🧪</span> Lightweight headless test runs</li>
            </ul>
          </div>
          <button class="btn" id="btn-set-test" style="width: 100%; justify-content: center; background: rgba(168,85,247,0.18); color: #c084fc; border-color: rgba(168,85,247,0.4);">
            {'✓ Active in Test Mode' if not is_prod else 'Switch to Test Mode'}
          </button>
        </div>
      </div>

      <!-- Diff Comparison Table -->
      <div class="diff-table-card">
        <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 4px;">Parameter Difference Matrix</h3>
        <p style="font-size: 0.78rem; color: var(--text-muted);">Comparison of execution parameters between Production and Test modes.</p>
        <table class="diff-table">
          <thead>
            <tr>
              <th>Configuration Parameter</th>
              <th>⚡ Production Mode</th>
              <th>🧪 Test Mode</th>
              <th>Safety Impact</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>User Inactivity Delay</td>
              <td><code>10.0s</code> (Strict User32 Check)</td>
              <td><code>0.5s</code> (Instant Execution)</td>
              <td>Prevents accidental input clashes while human is typing</td>
            </tr>
            <tr>
              <td>Engine Polling Interval</td>
              <td><code>1.0s</code> (CPU Efficient)</td>
              <td><code>0.1s</code> (High-Speed Loop)</td>
              <td>Balances background CPU consumption</td>
            </tr>
            <tr>
              <td>DOM Element Settle Delay</td>
              <td><code>1.5s</code> (Reliable Rendering)</td>
              <td><code>0.2s</code> (Fast Simulation)</td>
              <td>Guarantees UIA accessibility tree stabilization</td>
            </tr>
            <tr>
              <td>Step 3 Inter-Key Delay</td>
              <td><code>80ms</code> (Human Cadence)</td>
              <td><code>5ms</code> (Machine Instant)</td>
              <td>Simulates genuine human keyboard entry</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- TAB 5: CONFIG -->
    <main id="tab-config" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-config">
      <div class="controls-bar">
        <div class="search-input-wrap">
          <span class="search-icon-pos">🔍</span>
          <input type="text" class="search-input" id="search-config" placeholder="Filter settings by keyword (timing, delay, poll, step)...">
          <span class="search-shortcut-hint">Press [/]</span>
        </div>
      </div>

      <div class="config-group-card">
        <h3 style="font-size: 0.92rem; font-weight: 700;">⏱️ Execution Timing & Millisecond Delays</h3>
        <div class="config-grid">
          <div class="cfg-field">
            <label class="cfg-label" for="cfg-poll-prod">Production Poll Interval (s)</label>
            <input type="number" step="0.1" class="cfg-input" id="cfg-poll-prod" value="{poll_prod}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label" for="cfg-poll-test">Test Mode Poll Interval (s)</label>
            <input type="number" step="0.05" class="cfg-input" id="cfg-poll-test" value="{poll_test}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label" for="cfg-settle-delay">Window Focus Settle Delay (s)</label>
            <input type="number" step="0.1" class="cfg-input" id="cfg-settle-delay" value="{settle_delay}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label" for="cfg-activity-delay">User Inactivity Delay (s)</label>
            <input type="number" step="0.5" class="cfg-input" id="cfg-activity-delay" value="{activity_delay}">
          </div>
        </div>
      </div>

      <div class="config-group-card">
        <h3 style="font-size: 0.92rem; font-weight: 700;">⚡ Pipeline Step Toggles</h3>
        <div class="config-grid">
          <div class="cfg-field">
            <label class="cfg-label">Step 1: Window Focus & Activation</label>
            <input type="text" class="cfg-input" id="cfg-step1" value="{step1_enabled}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label">Step 2: UIA DOM Element Extraction</label>
            <input type="text" class="cfg-input" id="cfg-step2" value="{step2_enabled}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label">Step 3: Keyboard Grill-Me Selection</label>
            <input type="text" class="cfg-input" id="cfg-step3" value="{step3_enabled}">
          </div>
          <div class="cfg-field">
            <label class="cfg-label">Step 4: Reporting & Visual Dashboard</label>
            <input type="text" class="cfg-input" id="cfg-step4" value="{step4_enabled}">
          </div>
        </div>
      </div>
    </main>

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

    <!-- Floating Unsaved Changes Dock -->
    <div id="unsaved-changes-dock">
      <span style="font-size: 0.8rem; color: var(--accent-amber); font-weight: 600;">⚠️ Unsaved configuration changes detected</span>
      <button class="btn" id="btn-discard-config" style="padding: 4px 10px; font-size: 0.75rem;">Discard</button>
      <button class="btn btn-automation" id="btn-save-config" style="padding: 4px 12px; font-size: 0.75rem;">Save to config.json</button>
    </div>

    <!-- Floating Toast Notification -->
    <div id="toast-notify">Notification</div>

    <!-- Keyboard Shortcuts Help Modal -->
    <div class="modal-backdrop" id="shortcuts-modal">
      <div class="modal-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <h3 style="font-size: 1rem; font-weight: 700;">⌨️ Keyboard Shortcuts</h3>
          <button class="btn" id="btn-close-modal" style="padding: 2px 7px;">✕</button>
        </div>
        <div class="shortcut-row"><span>Switch to Overview</span><span class="shortcut-key">1</span></div>
        <div class="shortcut-row"><span>Switch to Chats</span><span class="shortcut-key">2</span></div>
        <div class="shortcut-row"><span>Switch to Questions</span><span class="shortcut-key">3</span></div>
        <div class="shortcut-row"><span>Switch to Mode Switch</span><span class="shortcut-key">4</span></div>
        <div class="shortcut-row"><span>Switch to Config</span><span class="shortcut-key">5</span></div>
        <div class="shortcut-row"><span>Focus Search Input (Active Tab)</span><span class="shortcut-key">/</span></div>
        <div class="shortcut-row"><span>Toggle Live Logs Drawer</span><span class="shortcut-key">L</span></div>
        <div class="shortcut-row"><span>Toggle Theme (Dark/Light)</span><span class="shortcut-key">T</span></div>
        <div class="shortcut-row"><span>Toggle Sound Chimes</span><span class="shortcut-key">M</span></div>
        <div class="shortcut-row"><span>Close Modal or Drawer</span><span class="shortcut-key">Esc</span></div>
      </div>
    </div>

    <!-- Floating SVG Chart Tooltip -->
    <div id="chart-floating-tooltip"></div>
  </div>

  <!-- Raw Embedded JSON Stores -->
  <script id="history-data" type="application/json">
{history_json_str}
  </script>
  <script id="runtime-config-data" type="application/json">
{runtime_config_json_str}
  </script>

  <!-- Complete Modern & Interactive JavaScript Subsystem -->
  <script>
    (function() {{
      const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:')
        ? window.location.origin
        : 'http://127.0.0.1:8501';

      const rawData = JSON.parse(document.getElementById('history-data').textContent || '{{}}');
      const rawCfg = JSON.parse(document.getElementById('runtime-config-data').textContent || '{{}}');
      const chats = rawData.chats || {{}};

      let isAutomationActive = false;
      let logsOpen = false;
      let logLines = 0;
      let audioMuted = localStorage.getItem('asc_audio_muted') === 'true';
      let autoScrollLogs = true;
      let currentActiveTab = localStorage.getItem('asc_dashboard_tab') || 'overview';

      // Elements
      const summaryTbody = document.getElementById('summary-tbody');
      const detailsContainer = document.getElementById('details-container');
      const searchChats = document.getElementById('search-chats');
      const searchQuestions = document.getElementById('search-questions');
      const searchConfig = document.getElementById('search-config');

      // Filter Toolbar Elements
      const filterDateFrom = document.getElementById('filter-date-from');
      const filterDateTo = document.getElementById('filter-date-to');
      const filterChat = document.getElementById('filter-chat');
      const filterComplexity = document.getElementById('filter-complexity');
      const filterSpeed = document.getElementById('filter-speed');
      const filterResetBtn = document.getElementById('filter-reset-btn');
      const filterCountEl = document.getElementById('filter-count');
      const filterTotalEl = document.getElementById('filter-total');
      const activeChipsContainer = document.getElementById('active-chips-container');
      const presetBtns = document.querySelectorAll('.preset-btn');

      function escapeHtml(str) {{
        if (!str) return '';
        return String(str)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#039;');
      }}

      // Toast notification helper
      function showToast(msg) {{
        const t = document.getElementById('toast-notify');
        if (!t) return;
        t.textContent = msg;
        t.style.display = 'block';
        setTimeout(() => {{ t.style.display = 'none'; }}, 2800);
      }}

      // Web Audio API Synthesizer (0 external files)
      function playChime(type) {{
        if (audioMuted) return;
        try {{
          const ctx = new (window.AudioContext || window.webkitAudioContext)();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain);
          gain.connect(ctx.destination);
          const now = ctx.currentTime;

          if (type === 'start') {{
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc.start(now);
            osc.stop(now + 0.25);
          }} else if (type === 'stop') {{
            osc.frequency.setValueAtTime(660, now);
            osc.frequency.exponentialRampToValueAtTime(330, now + 0.22);
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
            osc.start(now);
            osc.stop(now + 0.28);
          }} else if (type === 'copy') {{
            osc.frequency.setValueAtTime(987, now);
            gain.gain.setValueAtTime(0.06, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
            osc.start(now);
            osc.stop(now + 0.12);
          }}
        }} catch(e) {{}}
      }}

      // Digital Clock
      function updateClock() {{
        const el = document.getElementById('live-clock');
        if (el) {{
          const d = new Date();
          el.textContent = d.toTimeString().split(' ')[0];
        }}
      }}
      setInterval(updateClock, 1000);
      updateClock();

      // Number Count-Up Animation for KPIs
      function runCounters() {{
        document.querySelectorAll('.counter-value').forEach(el => {{
          const target = parseFloat(el.getAttribute('data-target') || '0');
          if (isNaN(target) || target <= 0) return;
          const duration = 650;
          const start = performance.now();
          function step(now) {{
            const progress = Math.min((now - start) / duration, 1);
            const current = Math.floor(progress * target);
            el.textContent = current;
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target;
          }}
          requestAnimationFrame(step);
        }});
      }}
      runCounters();

      // Horizontal Tabs & Contextual Filter Toolbar visibility
      const tabs = document.querySelectorAll('.tab-btn');
      const panels = document.querySelectorAll('.tab-panel');
      const contextualFilters = document.getElementById('contextual-filter-toolbar');

      function switchTab(targetTab) {{
        currentActiveTab = targetTab;
        localStorage.setItem('asc_dashboard_tab', targetTab);

        tabs.forEach(t => {{
          const active = t.getAttribute('data-tab') === targetTab;
          t.classList.toggle('active', active);
          t.setAttribute('aria-selected', active);
        }});
        panels.forEach(p => {{
          const active = p.id === 'tab-' + targetTab;
          p.classList.toggle('active', active);
        }});

        // Show filters on overview & chats, hide on modes & config
        if (contextualFilters) {{
          contextualFilters.style.display = (targetTab === 'overview' || targetTab === 'chats' || targetTab === 'questions') ? 'block' : 'none';
        }}
      }}

      tabs.forEach(btn => {{
        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
      }});
      switchTab(currentActiveTab);

      // Collapsible Card Headers
      document.querySelectorAll('.collapsible-header').forEach(header => {{
        header.addEventListener('click', () => {{
          const targetId = header.getAttribute('data-target');
          const body = document.getElementById(targetId);
          if (body) {{
            const isCollapsed = body.classList.toggle('collapsed');
            header.classList.toggle('collapsed', isCollapsed);
          }}
        }});
      }});

      // Floating SVG Chart Tooltips
      const tooltip = document.getElementById('chart-floating-tooltip');
      document.querySelectorAll('svg rect, svg circle, svg path').forEach(el => {{
        const title = el.querySelector('title');
        if (title && title.textContent) {{
          const text = title.textContent;
          el.addEventListener('mouseenter', (e) => {{
            if (!tooltip) return;
            tooltip.innerHTML = text.replace(/\\n/g, '<br>');
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 14) + 'px';
            tooltip.style.top = (e.clientY + 14) + 'px';
          }});
          el.addEventListener('mousemove', (e) => {{
            if (!tooltip) return;
            tooltip.style.left = (e.clientX + 14) + 'px';
            tooltip.style.top = (e.clientY + 14) + 'px';
          }});
          el.addEventListener('mouseleave', () => {{
            if (tooltip) tooltip.style.display = 'none';
          }});
        }}
      }});

      // ======================================================================
      // Multi-Dimensional Filtering Logic (100% Classic Parity)
      // ======================================================================
      function formatDate(d) {{
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${{year}}-${{month}}-${{day}}`;
      }}

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

      function updateActiveChips() {{
        if (!activeChipsContainer) return;
        let chipsHtml = '<span class="active-chips-label">Active:</span>';

        // Preset chip
        const activePresetBtn = document.querySelector('.preset-btn.active');
        const presetVal = activePresetBtn ? activePresetBtn.getAttribute('data-preset') : 'all';
        chipsHtml += `<span class="filter-chip">⚡ ${{activePresetBtn ? activePresetBtn.textContent : 'All Time'}}</span>`;

        // Date chip
        if (filterDateFrom && filterDateFrom.value && filterDateTo && filterDateTo.value) {{
          chipsHtml += `<span class="filter-chip">📅 ${{filterDateFrom.value}} to ${{filterDateTo.value}} <span class="filter-chip-remove" onclick="clearDateFilter()">✕</span></span>`;
        }}

        // Chat chip
        if (filterChat && filterChat.value !== 'all') {{
          const selOpt = filterChat.options[filterChat.selectedIndex];
          chipsHtml += `<span class="filter-chip">📂 ${{selOpt ? selOpt.textContent.slice(0, 25) : 'Chat'}} <span class="filter-chip-remove" onclick="clearChatFilter()">✕</span></span>`;
        }}

        // Complexity chip
        if (filterComplexity && filterComplexity.value !== 'all') {{
          chipsHtml += `<span class="filter-chip">🎯 ${{filterComplexity.value === 'single' ? 'Single Q' : 'Multi Q'}} <span class="filter-chip-remove" onclick="clearComplexityFilter()">✕</span></span>`;
        }}

        // Speed chip
        if (filterSpeed && filterSpeed.value !== 'all') {{
          chipsHtml += `<span class="filter-chip">⚡ ${{filterSpeed.value}} <span class="filter-chip-remove" onclick="clearSpeedFilter()">✕</span></span>`;
        }}

        activeChipsContainer.innerHTML = chipsHtml;
      }}

      window.clearDateFilter = function() {{
        if (filterDateFrom) filterDateFrom.value = '';
        if (filterDateTo) filterDateTo.value = '';
        applyFilters();
      }};
      window.clearChatFilter = function() {{
        if (filterChat) filterChat.value = 'all';
        applyFilters();
      }};
      window.clearComplexityFilter = function() {{
        if (filterComplexity) filterComplexity.value = 'all';
        applyFilters();
      }};
      window.clearSpeedFilter = function() {{
        if (filterSpeed) filterSpeed.value = 'all';
        applyFilters();
      }};

      // Render Chats Table
      function renderChats() {{
        if (!summaryTbody) return;
        const searchVal = (searchChats ? searchChats.value : '').toLowerCase().trim();
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

      // Render Questions Cards (Deep Hierarchical Structure)
      function renderQuestions() {{
        if (!detailsContainer) return;
        const searchVal = (searchQuestions ? searchQuestions.value : '').toLowerCase().trim();
        const chatEntries = Object.entries(chats);
        detailsContainer.innerHTML = '';
        let cardsCount = 0;

        for (const [cid, chat] of chatEntries) {{
          const topic = chat.topic_summary || 'Untitled Conversation';
          const runs = chat.runs || [];

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
                  const isRec = opt.includes('(Recommended)');
                  optionsHtml += `
                    <div class="option-item ${{isSelected ? 'selected' : ''}}">
                      <span><strong>${{optIdx + 1}}.</strong> ${{escapeHtml(opt)}}</span>
                      <div style="display:flex; gap:6px;">
                        ${{isSelected ? '<span class="option-badge">✓ Selected</span>' : ''}}
                        ${{isRec ? '<span style="font-size:0.68rem; padding:2px 7px; border-radius:9999px; background:rgba(6,182,212,0.18); color:#22d3ee; border:1px solid rgba(6,182,212,0.4);">⭐ Recommended</span>' : ''}}
                      </div>
                    </div>
                  `;
                }});

                qHtml += `
                  <div class="question-card" data-question-num="${{q.question_index || (qIdx + 1)}}">
                    <div class="question-prompt" onclick="toggleQuestionPrompt(this)">
                      <div class="question-prompt-left">
                        <span class="collapse-icon">▾</span>
                        <span class="question-num">Q${{q.question_index || (qIdx + 1)}}</span>
                        <span>${{escapeHtml(q.question)}}</span>
                      </div>
                      <div class="question-prompt-right">
                        <button class="btn-copy-qa" onclick="event.stopPropagation(); copyQACard(this)" data-q="${{encodeURIComponent(q.question || '')}}" data-ans="${{encodeURIComponent(q.selected_option_text || '')}}">
                          📋 Copy Q&A
                        </button>
                        <span class="badge-count" style="font-size: 0.72rem;">${{(q.options || []).length}} options</span>
                      </div>
                    </div>
                    <div class="options-list">
                      ${{optionsHtml}}
                    </div>
                  </div>
                `;
              }});

              runsHtml += `
                <div class="run-block" data-run-id="${{escapeHtml(run.run_id || '')}}">
                  <div class="run-header" onclick="toggleRunHeader(this)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="collapse-icon">▾</span>
                      <span style="font-weight: 700; color: var(--text-primary);">⚡ Run #${{rIdx + 1}} (${{escapeHtml(run.run_id || 'N/A')}})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                      <span>Duration: ${{dur}} | ${{runDate}}</span>
                    </div>
                  </div>
                  <div class="run-body">
                    ${{qHtml}}
                  </div>
                </div>
              `;
            }});

            const totalFilteredQs = matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0);

            card.innerHTML = `
              <div class="chat-card-header" onclick="toggleChatHeader(this)">
                <div class="chat-card-title">
                  <span class="collapse-icon">▾</span>
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
            <div style="text-align:center; padding: 40px; color: var(--text-muted);">
              <div style="font-size: 2rem; margin-bottom: 8px;">📭</div>
              <div style="font-weight: 700; font-size: 1.1rem; color: var(--text-primary); margin-bottom: 4px;">No Questions Found</div>
              <div>No questions match your filter criteria or search query.</div>
            </div>
          `;
        }}
      }}

      window.toggleChatHeader = function(hdr) {{
        const body = hdr.nextElementSibling;
        if (body) {{
          const isCollapsed = body.classList.toggle('collapsed');
          const ic = hdr.querySelector('.collapse-icon');
          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';
        }}
      }};

      window.toggleRunHeader = function(hdr) {{
        const body = hdr.nextElementSibling;
        if (body) {{
          const isCollapsed = body.classList.toggle('collapsed');
          const ic = hdr.querySelector('.collapse-icon');
          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';
        }}
      }};

      window.toggleQuestionPrompt = function(hdr) {{
        const body = hdr.nextElementSibling;
        if (body) {{
          const isCollapsed = body.classList.toggle('collapsed');
          const ic = hdr.querySelector('.collapse-icon');
          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';
        }}
      }};

      // 1-Click Copy Q&A
      window.copyQACard = function(btn) {{
        const q = decodeURIComponent(btn.getAttribute('data-q') || '');
        const ans = decodeURIComponent(btn.getAttribute('data-ans') || '');
        const text = `Question: ${{q}}\\nSelected Answer: ${{ans}}`;
        navigator.clipboard.writeText(text).then(() => {{
          playChime('copy');
          showToast('✅ Question & answer copied to clipboard!');
        }});
      }};

      // Expand All / Collapse All Questions
      const btnExpandAllQ = document.getElementById('btn-expand-all-questions');
      const btnCollapseAllQ = document.getElementById('btn-collapse-all-questions');

      if (btnExpandAllQ) {{
        btnExpandAllQ.addEventListener('click', () => {{
          if (!detailsContainer) return;
          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {{
            el.classList.remove('collapsed');
          }});
          detailsContainer.querySelectorAll('.collapse-icon').forEach(ic => {{
            ic.textContent = '▾';
          }});
        }});
      }}

      if (btnCollapseAllQ) {{
        btnCollapseAllQ.addEventListener('click', () => {{
          if (!detailsContainer) return;
          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {{
            el.classList.add('collapsed');
          }});
          detailsContainer.querySelectorAll('.collapse-icon').forEach(ic => {{
            ic.textContent = '▸';
          }});
        }});
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

        updateActiveChips();
        renderChats();
        renderQuestions();
      }}

      // Preset button handlers
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
            const y = new Date(now.getTime() - 24 * 3600 * 1000);
            const yStr = formatDate(y);
            if (filterDateFrom) filterDateFrom.value = yStr;
            if (filterDateTo) filterDateTo.value = yStr;
          }} else if (preset === '7d') {{
            const past7 = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
            if (filterDateFrom) filterDateFrom.value = formatDate(past7);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === '30d') {{
            const past30 = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
            if (filterDateFrom) filterDateFrom.value = formatDate(past30);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === 'week') {{
            const dayOfWeek = (now.getDay() + 6) % 7; // Monday as 0
            const mon = new Date(now.getTime() - dayOfWeek * 24 * 3600 * 1000);
            if (filterDateFrom) filterDateFrom.value = formatDate(mon);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }} else if (preset === 'month') {{
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            if (filterDateFrom) filterDateFrom.value = formatDate(firstDay);
            if (filterDateTo) filterDateTo.value = formatDate(now);
          }}

          applyFilters();
        }});
      }});

      // Event listeners for filter controls
      if (filterDateFrom) filterDateFrom.addEventListener('change', applyFilters);
      if (filterDateTo) filterDateTo.addEventListener('change', applyFilters);
      if (filterChat) filterChat.addEventListener('change', applyFilters);
      if (filterComplexity) filterComplexity.addEventListener('change', applyFilters);
      if (filterSpeed) filterSpeed.addEventListener('change', applyFilters);

      if (filterResetBtn) {{
        filterResetBtn.addEventListener('click', () => {{
          if (filterDateFrom) filterDateFrom.value = '';
          if (filterDateTo) filterDateTo.value = '';
          if (filterChat) filterChat.value = 'all';
          if (filterComplexity) filterComplexity.value = 'all';
          if (filterSpeed) filterSpeed.value = 'all';
          presetBtns.forEach(b => b.classList.remove('active'));
          const allBtn = document.querySelector('.preset-btn[data-preset="all"]');
          if (allBtn) allBtn.classList.add('active');
          applyFilters();
          showToast('Filters reset to default.');
        }});
      }}

      // Real-time Search input listeners
      if (searchChats) searchChats.addEventListener('input', renderChats);
      if (searchQuestions) searchQuestions.addEventListener('input', renderQuestions);

      // ======================================================================
      // Tab-Contextual Keyboard Shortcut [/] Fix
      // ======================================================================
      window.addEventListener('keydown', (e) => {{
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === '1') switchTab('overview');
        else if (e.key === '2') switchTab('chats');
        else if (e.key === '3') switchTab('questions');
        else if (e.key === '4') switchTab('modes');
        else if (e.key === '5') switchTab('config');
        else if (e.key === '/') {{
          e.preventDefault();
          let targetInput = null;
          if (currentActiveTab === 'chats') {{
            targetInput = searchChats;
          }} else if (currentActiveTab === 'questions') {{
            targetInput = searchQuestions;
          }} else if (currentActiveTab === 'config') {{
            targetInput = searchConfig;
          }} else {{
            // On Overview, switch to chats or focus chats search
            switchTab('chats');
            targetInput = searchChats;
          }}
          if (targetInput) {{
            targetInput.focus();
            targetInput.select();
          }}
        }}
        else if (e.key.toLowerCase() === 'l') {{
          e.preventDefault();
          toggleLogs();
        }}
        else if (e.key.toLowerCase() === 't') {{
          if (themeToggle) themeToggle.click();
        }}
        else if (e.key.toLowerCase() === 'm') {{
          if (btnAudio) btnAudio.click();
        }}
        else if (e.key === '?') {{
          if (shortcutsModal) shortcutsModal.classList.toggle('open');
        }}
        else if (e.key === 'Escape') {{
          if (shortcutsModal) shortcutsModal.classList.remove('open');
          if (logsOpen) toggleLogs(false);
        }}
      }});

      // Live Logs Drawer
      const logsDrawer = document.getElementById('logs-drawer');
      const btnToggleLogs = document.getElementById('btn-toggle-logs');
      const btnCloseLogs = document.getElementById('btn-close-logs');
      const logsTerminal = document.getElementById('logs-terminal');
      const logBadge = document.getElementById('log-count-badge');

      function toggleLogs(forceState) {{
        logsOpen = (forceState !== undefined) ? forceState : !logsOpen;
        if (logsDrawer) logsDrawer.classList.toggle('open', logsOpen);
        if (logsOpen) fetchLogs();
      }}

      if (btnToggleLogs) btnToggleLogs.addEventListener('click', () => toggleLogs());
      if (btnCloseLogs) btnCloseLogs.addEventListener('click', () => toggleLogs(false));

      function fetchLogs() {{
        if (!logsOpen) return;
        fetch(API_BASE + '/api/logs/tail?lines=80')
          .then(res => res.json())
          .then(data => {{
            if (data && data.data && Array.isArray(data.data.logs)) {{
              const lines = data.data.logs;
              logLines = lines.length;
              if (logBadge) logBadge.textContent = logLines;
              let colored = '';
              lines.forEach(l => {{
                let cls = '';
                if (l.includes('[ERROR]')) cls = 'log-line-err';
                else if (l.includes('[WARNING]') || l.includes('[WARN]')) cls = 'log-line-warn';
                else if (l.includes('[INFO]')) cls = 'log-line-info';
                colored += `<div class="${{cls}}">${{l}}</div>`;
              }});
              if (logsTerminal) {{
                logsTerminal.innerHTML = colored || '<div>Log file empty.</div>';
                if (autoScrollLogs) logsTerminal.scrollTop = logsTerminal.scrollHeight;
              }}
            }}
          }})
          .catch(() => {{}});
      }}
      setInterval(() => {{ if (logsOpen) fetchLogs(); }}, 2500);

      // Auto-Scroll Toggle
      const btnAutoScroll = document.getElementById('btn-toggle-autoscroll');
      if (btnAutoScroll) {{
        btnAutoScroll.addEventListener('click', () => {{
          autoScrollLogs = !autoScrollLogs;
          btnAutoScroll.textContent = 'Auto-Scroll: ' + (autoScrollLogs ? 'ON' : 'OFF');
        }});
      }}

      // Clear Logs Display
      const btnClearLogs = document.getElementById('btn-clear-logs');
      if (btnClearLogs) {{
        btnClearLogs.addEventListener('click', () => {{
          if (logsTerminal) logsTerminal.innerHTML = '<div>Console cleared. Waiting for next stream tick...</div>';
        }});
      }}

      // Automation Start/Stop Control
      const toggleBtn = document.getElementById('automation-toggle-btn');
      const controlIcon = document.getElementById('control-icon');
      const controlLabel = document.getElementById('control-label');
      const statusPill = document.getElementById('dashboard-status-pill');
      const statusText = document.getElementById('status-text');

      function updateStatusUI(running, paused) {{
        isAutomationActive = running;
        if (toggleBtn) {{
          toggleBtn.classList.toggle('state-running', running);
          toggleBtn.classList.toggle('state-stopped', !running);
          controlIcon.textContent = running ? '⏹️' : '▶️';
          controlLabel.textContent = running ? 'Stop Automation' : 'Start Automation';
        }}
        if (statusPill && statusText) {{
          statusPill.className = 'status-pill ' + (running ? (paused ? 'status-paused' : 'status-active') : 'status-idle');
          statusText.textContent = running ? (paused ? '🟡 Paused' : '🟢 Active') : '⚪ Inactive';
        }}
      }}

      if (toggleBtn) {{
        toggleBtn.addEventListener('click', () => {{
          const endpoint = isAutomationActive ? '/api/automation/stop' : '/api/automation/start';
          toggleBtn.disabled = true;
          fetch(API_BASE + endpoint, {{ method: 'POST' }})
            .then(res => res.json())
            .then(data => {{
              toggleBtn.disabled = false;
              if (data.success) {{
                playChime(isAutomationActive ? 'stop' : 'start');
                showToast(isAutomationActive ? '⏹️ Automation stopped' : '▶️ Automation started');
                updateStatusUI(!isAutomationActive, false);
              }}
            }})
            .catch(() => {{
              toggleBtn.disabled = false;
              showToast('❌ Server request failed. Ensure server is running on port 8501');
            }});
        }});
      }}

      function pollServerStatus() {{
        fetch(API_BASE + '/api/automation/status')
          .then(res => res.json())
          .then(data => {{
            if (data && data.success && data.data) {{
              updateStatusUI(data.data.running, data.data.paused);
            }}
          }})
          .catch(() => {{}});
      }}
      setInterval(pollServerStatus, 3000);

      // Mode Switch Controls
      const btnSetProd = document.getElementById('btn-set-prod');
      const btnSetTest = document.getElementById('btn-set-test');
      function switchMode(newMode) {{
        fetch(API_BASE + '/api/config/save', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ mode: newMode }})
        }})
        .then(res => res.json())
        .then(d => {{
          showToast(`⚡ Switched to ${{newMode.toUpperCase()}} mode!`);
          setTimeout(() => location.reload(), 600);
        }})
        .catch(() => showToast('Error saving mode configuration.'));
      }}
      if (btnSetProd) btnSetProd.addEventListener('click', () => switchMode('production'));
      if (btnSetTest) btnSetTest.addEventListener('click', () => switchMode('test'));

      // Config Unsaved Dock
      const unsavedDock = document.getElementById('unsaved-changes-dock');
      const cfgInputs = document.querySelectorAll('.cfg-input');
      cfgInputs.forEach(inp => {{
        inp.addEventListener('input', () => {{
          if (unsavedDock) unsavedDock.classList.add('visible');
        }});
      }});
      const btnDiscardCfg = document.getElementById('btn-discard-config');
      if (btnDiscardCfg) {{
        btnDiscardCfg.addEventListener('click', () => {{
          if (unsavedDock) unsavedDock.classList.remove('visible');
          showToast('Changes discarded.');
          setTimeout(() => location.reload(), 400);
        }});
      }}

      // Theme Toggle
      const themeToggle = document.getElementById('theme-toggle');
      if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
          const cur = document.documentElement.getAttribute('data-theme') || 'dark';
          const next = cur === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', next);
          localStorage.setItem('asc_theme', next);
        }});
      }}
      const savedTheme = localStorage.getItem('asc_theme');
      if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);

      // Audio Toggle
      const btnAudio = document.getElementById('btn-audio-toggle');
      if (btnAudio) {{
        btnAudio.addEventListener('click', () => {{
          audioMuted = !audioMuted;
          localStorage.setItem('asc_audio_muted', audioMuted);
          document.getElementById('audio-icon').textContent = audioMuted ? '🔕' : '🔔';
          showToast(audioMuted ? 'Audio Chimes Muted' : 'Audio Chimes Enabled');
          if (!audioMuted) playChime('copy');
        }});
      }}

      // Keyboard Shortcuts Modal
      const shortcutsModal = document.getElementById('shortcuts-modal');
      const btnHelp = document.getElementById('btn-help-shortcuts');
      const btnCloseModal = document.getElementById('btn-close-modal');

      if (btnHelp) btnHelp.addEventListener('click', () => shortcutsModal.classList.add('open'));
      if (btnCloseModal) btnCloseModal.addEventListener('click', () => shortcutsModal.classList.remove('open'));

      // Auto-refresh countdown
      let count = 10;
      const countEl = document.getElementById('refresh-countdown');
      setInterval(() => {{
        count--;
        if (countEl) countEl.textContent = count + 's';
        if (count <= 0) {{
          count = 10;
        }}
      }}, 1000);

      // Initialize
      applyFilters();

    }})();
  </script>
</body>
</html>"""


def generate_and_save_modern_dashboard(workspace_dir: Optional[Path] = None) -> Path:
    ws = workspace_dir or _WORKSPACE_DIR
    step4_dir = ws / "step_4_reporting"
    modern_dir = step4_dir / "Modern and Interactive Dashboard"
    modern_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = step4_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    html_content = build_modern_dashboard_html(workspace_dir=ws)

    # 1. Save in Modern and Interactive Dashboard/
    out_modern = modern_dir / "dashboard.html"
    out_modern.write_text(html_content, encoding="utf-8")

    # 2. Save in reports/modern_dashboard.html
    out_reports_modern = reports_dir / "modern_dashboard.html"
    out_reports_modern.write_text(html_content, encoding="utf-8")

    # 3. Save as primary reports/dashboard.html
    out_reports_main = reports_dir / "dashboard.html"
    out_reports_main.write_text(html_content, encoding="utf-8")

    return out_modern


if __name__ == "__main__":
    out = generate_and_save_modern_dashboard()
    print(f"Modern and Interactive Dashboard generated successfully at: {out}")
