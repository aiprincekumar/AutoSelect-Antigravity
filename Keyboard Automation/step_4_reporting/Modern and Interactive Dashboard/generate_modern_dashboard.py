#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

Modern and Interactive Dashboard Generator (generate_modern_dashboard.py)

========================================================================

Subsystem: Modern and Interactive Dashboard Engine (V3 - Full Architecture Alignment)

Part of: AutoSelect Antigravity Reporting Suite

Department: Department 04 (UI/UX Design System) & Department 05 (Frontend Engineering)

Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)



Key Architectural Solutions:

  1. Real-Time 3-State Status Polling:

     - Correctly binds `is_paused` and `idle_seconds` from `/api/automation/status`.

     - 🟡 Paused (User Active) with glowing amber pulse when idle < 60s.

     - 🟢 Active (Autonomous) with pulsing emerald glow.

     - ⚪ Inactive with standby telemetry indicator.

  2. Complete Configuration Engine with Dual Sub-Tabs:

     - ⚡ System Runtime Configuration (step_9_complete_automation/config.json)

       * Mode Pill Selector & Lifecycle callout blocks.

       * 4 Pipeline Step Toggles (Step 1, 2, 3, 4).

       * Complete 12 Millisecond Timing & Delay Inputs with full descriptions.

       * Governance, Safety & Auto-Pause (LastActivitySentinel 60s, continuous loop 300s).

       * Logging & Telemetry Hygiene.

       * Formatted JSON Live Preview Drawer.

     - 🎨 Dashboard & Telemetry Preferences (dashboard_config.json)

       * Auto-refresh frequency (10s, 30s, 60s, OFF).

       * User activity delay, default tab, selection policy, visual motion, and audio chimes.

       * Unified Action Buttons: Save to config.json, Reset to Defaults, Export JSON.

  3. Strict Collapsible Governance:

     - OVERVIEW TAB: ZERO collapsible sections. 100% full-width, permanently open, responsive layout.

     - CHATS & QUESTIONS TABS: By default COLLAPSED on initial load. Single/smooth expansion on click.

     - Global Expand All / Collapse All buttons.

  4. Full-Width Responsive SVG Architecture:

     - Topology diagram and all 7 SVG charts scale to 100% full width of their containers.

  5. Complete Classic Filter Parity:

     - Presets, Date pickers, Conversation selector, Complexity, Speed, Reset button, and Active Chips.

  6. Tab-Contextual Keyboard Shortcut [/]:

     - Automatically routes to the active tab's search input.

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

    is_prod = (current_mode == "production")

    badge_bg = 'rgba(16, 185, 129, 0.15)' if is_prod else 'rgba(245, 158, 11, 0.15)'

    badge_color = '#34d399' if is_prod else '#fbbf24'

    badge_border = 'rgba(16, 185, 129, 0.35)' if is_prod else 'rgba(245, 158, 11, 0.35)'

    badge_icon = '⚡' if is_prod else '🧪'

    badge_text = 'LIVE' if is_prod else 'TEST'

    badge_title = 'Operating in Continuous Live Mode (Continuous Loop) • Click to toggle to TEST' if is_prod else 'Operating in Single-Run Test Mode (Auto-Stop on Completion) • Click to toggle to LIVE'



    # Extract all 12 timing parameters from config.json with safe fallbacks

    timing_cfg = runtime_cfg.get("timing", {})

    step0_poll_prod = timing_cfg.get("step0_poll_interval_prod_seconds", 1.0)

    step0_poll_test = timing_cfg.get("step0_poll_interval_test_seconds", 0.1)

    settle_delay = timing_cfg.get("settle_delay_between_steps_seconds", 1.0)

    user_pause_threshold = timing_cfg.get("user_activity_pause_threshold_seconds", 60.0)

    step4_delay = timing_cfg.get("step4_user_activity_delay_seconds", 10.0)

    step4_poll = timing_cfg.get("step4_poll_interval_seconds", 0.5)

    step1_focus = timing_cfg.get("step1_window_focus_delay_seconds", 0.5)

    step2_dom_settle = timing_cfg.get("step2_dom_click_settle_delay_seconds", 1.0)

    step3_countdown = timing_cfg.get("step3_countdown_seconds", 3)

    step3_hold_ms = timing_cfg.get("step3_key_hold_delay_ms", 80)

    step3_post_ms = timing_cfg.get("step3_post_keypress_delay_ms", 100)

    step3_inter_q_ms = timing_cfg.get("step3_inter_question_delay_ms", 200)

    step3_round_ms = timing_cfg.get("step3_round_completion_pause_ms", 500)



    # Antigravity Governance Configuration

    antigravity_cfg = runtime_cfg.get("antigravity", {})

    require_grill_me = antigravity_cfg.get("require_grill_me", True)

    active_hours = antigravity_cfg.get("active_hours", 12.0)



    # Logging Engine Configuration

    logging_cfg = runtime_cfg.get("logging", {})

    log_file = logging_cfg.get("log_file", "complete_automation.log")

    log_verbose = logging_cfg.get("verbose", True)



    # Enabled steps

    enabled_steps = runtime_cfg.get("enabled_steps", {})

    step1_enabled = enabled_steps.get("step1_find_and_focus", True)

    step2_enabled = enabled_steps.get("step2_gui_chat_select", True)

    step3_enabled = enabled_steps.get("step3_keyboard_automation", True)

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

  <title>AutoSelect Antigravity Dashboard</title>

  <style>

    :root {{

      --bg-primary: #07090f;

      --bg-surface: #0e1422;

      --bg-surface-elevated: #151d30;

      --bg-surface-highlight: #1e2942;

      --bg-surface-glass: rgba(14, 20, 34, 0.88);

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

      --bg-surface-glass: rgba(255, 255, 255, 0.92);

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

      padding: 16px 20px 60px;

      -webkit-font-smoothing: antialiased;

      transition: background-color 0.25s ease, color 0.25s ease;

      min-height: 100vh;

    }}



    .container {{

      max-width: 1400px;

      width: 100%;

      margin: 0 auto;

    }}



    /* ========================================================================

       Header & Modern Dual-Cluster Architecture

       ======================================================================== */

    header, .app-header {{

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

      position: relative;

      overflow: hidden;

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

      padding: 5px 12px;

      border-radius: 9999px;

      font-size: 0.75rem;

      font-weight: 700;

      white-space: nowrap;

      transition: var(--transition);

    }}



    .pulse-dot {{

      width: 8px;

      height: 8px;

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

      box-shadow: 0 0 14px rgba(16, 185, 129, 0.25);

    }}

    .status-active .pulse-dot {{

      background: var(--accent-emerald);

      box-shadow: 0 0 10px var(--accent-emerald);

      animation: pulseAnim 1.2s infinite;

    }}



    .status-paused {{

      background: rgba(245, 158, 11, 0.15) !important;

      color: #f59e0b !important;

      border: 1px solid rgba(245, 158, 11, 0.5) !important;

      box-shadow: 0 0 14px rgba(245, 158, 11, 0.3) !important;

    }}

    .status-paused .pulse-dot {{

      background: #f59e0b !important;

      box-shadow: 0 0 10px #f59e0b !important;

      animation: pulseAnim 1.4s infinite !important;

    }}



    @keyframes pulseAnim {{

      0%, 100% {{ transform: scale(1); opacity: 1; }}

      50% {{ transform: scale(1.4); opacity: 0.55; }}

    }}



    .status-pill.status-mode-badge {{

      cursor: pointer;

      user-select: none;

      transition: var(--transition);

      font-weight: 700;

    }}

    .status-pill.status-mode-badge:hover {{

      filter: brightness(1.25);

      transform: translateY(-1px);

      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);

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

      padding: 8px 18px;

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

      background: rgba(14, 20, 34, 0.75);

      backdrop-filter: blur(16px);

      -webkit-backdrop-filter: blur(16px);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 6px;

      margin-bottom: 22px;

      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);

      overflow-x: auto;

    }}



    .tab-btn {{

      display: inline-flex;

      align-items: center;

      gap: 8px;

      padding: 10px 20px;

      border: 1px solid transparent;

      background: transparent;

      color: var(--text-secondary);

      font-size: 0.88rem;

      font-weight: 600;

      border-radius: var(--radius-md);

      cursor: pointer;

      transition: var(--transition);

      white-space: nowrap;

    }}



    .tab-btn:hover {{

      color: var(--text-primary);

      background: var(--bg-surface-elevated);

      border-color: var(--border-subtle);

    }}



    .tab-btn.active {{

      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);

      color: #ffffff;

      border-color: rgba(99, 102, 241, 0.5);

      box-shadow: 0 4px 16px var(--accent-indigo-glow);

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



    

    /* Modern Chats Dual-View & Conversation Cards */

    .chats-view-switcher {{

      display: inline-flex;

      background: var(--bg-surface-elevated);

      padding: 4px;

      border-radius: var(--radius-md);

      border: 1px solid var(--border-subtle);

      gap: 4px;

    }}



    .view-btn {{

      padding: 6px 14px;

      font-size: 0.82rem;

      font-weight: 600;

      border-radius: var(--radius-sm);

      border: 1px solid transparent;

      cursor: pointer;

      display: inline-flex;

      align-items: center;

      gap: 6px;

      transition: var(--transition);

      background: transparent;

      color: var(--text-secondary);

    }}



    .view-btn.active {{

      background: var(--accent-indigo) !important;

      color: #ffffff !important;

      box-shadow: 0 2px 8px var(--accent-indigo-glow);

    }}



    .chats-card-grid {{

      display: grid;

      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));

      gap: 16px;

      margin-top: 14px;

    }}



    .modern-chat-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 18px 20px;

      display: flex;

      flex-direction: column;

      justify-content: space-between;

      gap: 14px;

      box-shadow: var(--shadow-sm);

      transition: var(--transition);

      position: relative;

      overflow: hidden;

    }}



    .modern-chat-card::before {{

      content: "";

      position: absolute;

      top: 0;

      left: 0;

      width: 4px;

      height: 100%;

      background: linear-gradient(180deg, var(--accent-indigo), var(--accent-cyan));

      opacity: 0.8;

    }}



    .modern-chat-card:hover {{

      transform: translateY(-2px);

      border-color: var(--border-accent);

      box-shadow: 0 8px 24px rgba(99, 102, 241, 0.18);

    }}



    .chat-card-top-row {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      gap: 10px;

    }}



    .chat-avatar-badge {{

      display: inline-flex;

      align-items: center;

      gap: 8px;

    }}



    .chat-avatar-icon {{

      width: 32px;

      height: 32px;

      border-radius: var(--radius-sm);

      background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25));

      border: 1px solid rgba(99, 102, 241, 0.35);

      display: flex;

      align-items: center;

      justify-content: center;

      font-size: 1rem;

    }}



    .chat-topic-title {{

      font-size: 1.02rem;

      font-weight: 700;

      color: var(--text-primary);

      line-height: 1.4;

      display: -webkit-box;

      -webkit-line-clamp: 2;

      -webkit-box-orient: vertical;

      overflow: hidden;

    }}



    .chat-metrics-bar {{

      display: flex;

      gap: 8px;

      flex-wrap: wrap;

    }}



    .chat-metric-pill {{

      font-size: 0.76rem;

      font-weight: 600;

      font-family: var(--font-mono);

      padding: 3px 9px;

      border-radius: var(--radius-sm);

      background: var(--bg-surface-elevated);

      border: 1px solid var(--border-subtle);

      color: var(--text-secondary);

      display: inline-flex;

      align-items: center;

      gap: 4px;

    }}



    .chat-card-actions {{

      display: flex;

      gap: 8px;

      align-items: center;

      padding-top: 10px;

      border-top: 1px solid var(--border-subtle);

    }}



    .btn-chat-action {{

      background: var(--bg-surface-elevated);

      border: 1px solid var(--border-subtle);

      color: var(--text-primary);

      padding: 6px 12px;

      border-radius: var(--radius-sm);

      font-size: 0.78rem;

      font-weight: 600;

      cursor: pointer;

      display: inline-flex;

      align-items: center;

      gap: 5px;

      transition: var(--transition);

    }}



    .btn-chat-action:hover {{

      background: var(--accent-indigo);

      color: #fff;

      border-color: var(--accent-indigo);

      box-shadow: 0 2px 10px var(--accent-indigo-glow);

    }}



    /* Questions Tab Developer Decision Studio */

    .questions-quick-filters {{

      display: flex;

      gap: 8px;

      flex-wrap: wrap;

      margin-bottom: 16px;

      align-items: center;

    }}



    .q-filter-chip {{

      background: var(--bg-surface-elevated);

      border: 1px solid var(--border-subtle);

      color: var(--text-secondary);

      font-size: 0.78rem;

      font-weight: 600;

      padding: 5px 12px;

      border-radius: 9999px;

      cursor: pointer;

      transition: var(--transition);

    }}



    .q-filter-chip:hover {{

      color: var(--text-primary);

      border-color: var(--accent-indigo);

      background: var(--bg-surface-highlight);

    }}



    .q-filter-chip.active {{

      background: var(--accent-indigo);

      color: #ffffff;

      border-color: var(--accent-indigo);

      box-shadow: 0 2px 8px var(--accent-indigo-glow);

    }}



    .question-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-md);

      margin-bottom: 12px;

      overflow: hidden;

      transition: var(--transition);

      position: relative;

    }}



    .question-card::before {{

      content: "";

      position: absolute;

      top: 0;

      left: 0;

      bottom: 0;

      width: 4px;

      background: var(--accent-indigo);

    }}



    .question-card.rec-matched::before {{

      background: var(--accent-emerald);

    }}



    .question-card:hover {{

      border-color: var(--border-accent);

      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);

    }}



    .option-item {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      padding: 10px 14px;

      border-radius: var(--radius-md);

      border: 1px solid var(--border-subtle);

      background: var(--bg-surface-elevated);

      font-size: 0.86rem;

      color: var(--text-secondary);

      transition: var(--transition);

      gap: 10px;

    }}



    .option-item:hover {{

      border-color: var(--border-hover);

      background: var(--bg-surface-highlight);

      color: var(--text-primary);

    }}



    .option-item.selected {{

      border-color: var(--accent-emerald);

      background: rgba(16, 185, 129, 0.1);

      color: var(--text-primary);

      font-weight: 600;

      box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);

    }}



    /* ========================================================================

       Full Interactive Multi-Dimensional Filter Toolbar (Classic Parity)

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

       Tab Panels

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

       Overview Tab (100% FULL-WIDTH, NO COLLAPSIBLE SECTIONS)

       ======================================================================== */

    .hero-kpis-grid {{

      display: grid;

      grid-template-columns: repeat(2, 1fr);

      gap: 16px;

      margin-bottom: 16px;

      width: 100%;

    }}



    .hero-kpi-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 22px 26px;

      box-shadow: var(--shadow-md);

      position: relative;

      overflow: hidden;

      transition: var(--transition);

      display: flex;

      justify-content: space-between;

      align-items: center;

      width: 100%;

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

      width: 100%;

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



    /* Permanent Full-Width Overview Cards */

    .overview-diagram-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 20px 24px;

      margin-bottom: 24px;

      width: 100%;

      box-shadow: var(--shadow-sm);

    }}



    .overview-card-header {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      margin-bottom: 16px;

    }}



    .overview-card-title {{

      font-size: 1rem;

      font-weight: 700;

      display: flex;

      align-items: center;

      gap: 8px;

    }}



    .overview-card-subtitle {{

      font-size: 0.78rem;

      color: var(--text-muted);

    }}



    .diagram-body {{

      width: 100%;

      overflow-x: auto;

    }}



    .diagram-body svg,

    .chart-card svg {{

      width: 100% !important;

      height: auto !important;

      display: block;

    }}



    .charts-grid {{

      display: grid;

      grid-template-columns: repeat(2, 1fr);

      gap: 18px;

      margin-bottom: 24px;

      width: 100%;

    }}



    .chart-card-wide {{

      grid-column: 1 / -1;

      width: 100%;

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

      padding: 20px 22px;

      box-shadow: var(--shadow-sm);

      width: 100%;

    }}



    .chart-card-header {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      margin-bottom: 14px;

    }}



    .chart-card-title {{

      font-size: 0.95rem;

      font-weight: 700;

      display: flex;

      align-items: center;

      gap: 8px;

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

       Questions Tab (Default Collapsed Hierarchical Q&A Tree)

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



    /* By default, collapsed */

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

       Mode Switch Tab • Ultra-Modern Interactive Lifecycle Standard

       ======================================================================== */

    .modes-panel-container {{

      display: flex;

      flex-direction: column;

      gap: 22px;

      width: 100%;

    }}



    .modes-hero-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-xl);

      padding: 24px 28px;

      box-shadow: var(--shadow-md);

      position: relative;

      overflow: hidden;

    }}



    .modes-hero-header {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      flex-wrap: wrap;

      gap: 16px;

      margin-bottom: 22px;

      padding-bottom: 16px;

      border-bottom: 1px solid var(--border-subtle);

    }}



    .modes-title-group {{

      display: flex;

      align-items: center;

      gap: 14px;

    }}



    .modes-hero-icon {{

      font-size: 2rem;

      background: rgba(99, 102, 241, 0.15);

      border: 1px solid rgba(99, 102, 241, 0.35);

      width: 50px;

      height: 50px;

      display: flex;

      align-items: center;

      justify-content: center;

      border-radius: var(--radius-lg);

    }}



    .modes-hero-title {{

      font-size: 1.15rem;

      font-weight: 800;

      color: var(--text-primary);

      margin: 0 0 4px 0;

      letter-spacing: -0.01em;

    }}



    .modes-hero-subtitle {{

      font-size: 0.82rem;

      color: var(--text-secondary);

      margin: 0;

      line-height: 1.4;

    }}



    .modes-hero-actions {{

      display: flex;

      align-items: center;

      gap: 10px;

    }}



    .modes-switcher-bar {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      flex-wrap: wrap;

      gap: 12px;

      background: var(--bg-surface-elevated);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 10px 18px;

      margin-bottom: 22px;

    }}



    .modes-switcher-label {{

      display: flex;

      align-items: center;

      gap: 8px;

      font-size: 0.85rem;

      font-weight: 700;

      color: var(--text-primary);

    }}



    .modes-segmented-group {{

      display: inline-flex;

      background: var(--bg-primary);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-md);

      padding: 4px;

      gap: 6px;

    }}



    .banner-mode-btn {{

      padding: 8px 16px;

      font-size: 0.82rem;

      font-weight: 700;

      border-radius: var(--radius-sm);

      border: 1px solid transparent;

      background: transparent;

      color: var(--text-secondary);

      cursor: pointer;

      display: inline-flex;

      align-items: center;

      gap: 8px;

      transition: var(--transition);

    }}



    .banner-mode-btn:hover {{

      color: var(--text-primary);

      background: var(--bg-surface-highlight);

    }}



    .banner-mode-btn.active[data-mode="production"] {{

      background: #059669;

      color: #ffffff;

      border-color: #10b981;

      box-shadow: 0 0 16px rgba(16, 185, 129, 0.4);

    }}



    .banner-mode-btn.active[data-mode="test"] {{

      background: #d97706;

      color: #ffffff;

      border-color: #f59e0b;

      box-shadow: 0 0 16px rgba(245, 158, 11, 0.4);

    }}



    .banner-mode-indicator {{

      font-size: 0.68rem;

      padding: 2px 7px;

      border-radius: 9999px;

      background: rgba(255, 255, 255, 0.22);

      font-family: var(--font-mono);

      font-weight: 700;

    }}



    .mode-lifecycle-grid {{

      display: grid;

      grid-template-columns: repeat(2, 1fr);

      gap: 20px;

    }}



    @media (max-width: 900px) {{

      .mode-lifecycle-grid {{

        grid-template-columns: 1fr;

      }}

    }}



    .lifecycle-card {{

      background: var(--bg-surface-elevated);

      border: 2px solid var(--border-subtle);

      border-radius: var(--radius-xl);

      padding: 22px 24px;

      display: flex;

      flex-direction: column;

      justify-content: space-between;

      gap: 16px;

      cursor: pointer;

      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

      position: relative;

    }}



    .lifecycle-card:hover {{

      border-color: var(--border-hover);

      background: var(--bg-surface-highlight);

      transform: translateY(-2px);

      box-shadow: var(--shadow-lg);

    }}



    .lifecycle-card.card-production.active-mode-card {{

      border-color: #10b981;

      background: linear-gradient(180deg, rgba(16, 185, 129, 0.1) 0%, var(--bg-surface-elevated) 100%);

      box-shadow: 0 0 28px rgba(16, 185, 129, 0.22);

    }}



    .lifecycle-card.card-test.active-mode-card {{

      border-color: #f59e0b;

      background: linear-gradient(180deg, rgba(245, 158, 11, 0.1) 0%, var(--bg-surface-elevated) 100%);

      box-shadow: 0 0 28px rgba(245, 158, 11, 0.22);

    }}



    .lifecycle-card-top {{

      display: flex;

      justify-content: space-between;

      align-items: flex-start;

      gap: 12px;

      flex-wrap: wrap;

    }}



    .lifecycle-card-title {{

      display: flex;

      align-items: center;

      gap: 10px;

    }}



    .lifecycle-card-title .card-icon {{

      font-size: 1.5rem;

    }}



    .lifecycle-card-title strong {{

      font-size: 1.05rem;

      color: var(--text-primary);

      display: block;

    }}



    .card-title-hindi {{

      font-size: 0.76rem;

      color: var(--text-muted);

      font-weight: 500;

    }}



    .lifecycle-card-badge {{

      font-size: 0.72rem;

      font-weight: 700;

      padding: 3px 10px;

      border-radius: 9999px;

      display: inline-flex;

      align-items: center;

      gap: 5px;

    }}



    .badge-prod-mode {{

      background: rgba(16, 185, 129, 0.18);

      color: #34d399;

      border: 1px solid rgba(16, 185, 129, 0.4);

    }}



    .badge-test-mode {{

      background: rgba(245, 158, 11, 0.18);

      color: #fbbf24;

      border: 1px solid rgba(245, 158, 11, 0.4);

    }}



    .lifecycle-card-desc {{

      font-size: 0.84rem;

      color: var(--text-secondary);

      line-height: 1.5;

      margin: 0;

    }}



    .lifecycle-card-features {{

      display: flex;

      flex-wrap: wrap;

      gap: 8px;

    }}



    .lifecycle-feature-tag {{

      font-size: 0.74rem;

      font-weight: 600;

      padding: 4px 10px;

      border-radius: var(--radius-sm);

      background: var(--bg-primary);

      border: 1px solid var(--border-subtle);

      color: var(--text-secondary);

    }}



    .lifecycle-card-btn {{

      width: 100%;

      padding: 10px;

      font-size: 0.85rem;

      font-weight: 700;

      border-radius: var(--radius-md);

      cursor: pointer;

      display: flex;

      justify-content: center;

      align-items: center;

      gap: 8px;

      border: 1px solid transparent;

      transition: var(--transition);

    }}



    .modes-comparison-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-xl);

      padding: 22px 26px;

      box-shadow: var(--shadow-sm);

    }}



    .modes-comparison-header {{

      margin-bottom: 16px;

      padding-bottom: 12px;

      border-bottom: 1px solid var(--border-subtle);

      display: flex;

      align-items: center;

      gap: 12px;

    }}



    .comparison-icon {{

      font-size: 1.5rem;

    }}



    .comparison-title {{

      font-size: 1rem;

      font-weight: 800;

      color: var(--text-primary);

      margin: 0 0 2px 0;

    }}



    .comparison-subtitle {{

      font-size: 0.78rem;

      color: var(--text-muted);

      margin: 0;

    }}



    .modes-comparison-table {{

      width: 100%;

      border-collapse: collapse;

      font-size: 0.82rem;

    }}



    .modes-comparison-table th {{

      text-align: left;

      padding: 10px 14px;

      color: var(--text-secondary);

      font-weight: 700;

      border-bottom: 1px solid var(--border-subtle);

      background: var(--bg-surface-elevated);

    }}



    .modes-comparison-table td {{

      padding: 12px 14px;

      border-bottom: 1px solid var(--border-subtle);

      vertical-align: middle;

      color: var(--text-secondary);

    }}



    .modes-comparison-table tr:last-child td {{

      border-bottom: none;

    }}



    .modes-comparison-table code {{

      font-family: var(--font-mono);

      font-size: 0.78rem;

      color: var(--accent-cyan);

      background: var(--bg-surface-elevated);

      padding: 2px 6px;

      border-radius: var(--radius-sm);

    }}



    /* ========================================================================

       Configuration Tab & Dual Sub-Tabs (System vs Dashboard Config)

       ======================================================================== */

    .config-subnav {{

      display: flex;

      gap: 8px;

      margin-bottom: 18px;

      border-bottom: 1px solid var(--border-subtle);

      padding-bottom: 8px;

    }}



    .config-subnav-btn {{

      padding: 8px 16px;

      font-size: 0.82rem;

      font-weight: 700;

      border-radius: var(--radius-md);

      border: 1px solid var(--border-subtle);

      background: var(--bg-surface-elevated);

      color: var(--text-secondary);

      cursor: pointer;

      transition: var(--transition);

    }}



    .config-subnav-btn:hover {{

      color: var(--text-primary);

      background: var(--bg-surface-highlight);

    }}



    .config-subnav-btn.active {{

      background: var(--accent-indigo);

      color: #ffffff;

      border-color: var(--accent-indigo);

      box-shadow: 0 0 12px var(--accent-indigo-glow);

    }}



    .config-subpanel {{

      display: none;

    }}

    .config-subpanel.active {{

      display: block;

      animation: fadeIn 0.2s ease;

    }}



    .config-group-card {{

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      padding: 20px 22px;

      margin-bottom: 18px;

      box-shadow: var(--shadow-sm);

    }}



    .config-group-header {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      margin-bottom: 14px;

      padding-bottom: 10px;

      border-bottom: 1px solid var(--border-subtle);

    }}



    .config-group-title {{

      font-size: 0.95rem;

      font-weight: 700;

      display: flex;

      align-items: center;

      gap: 8px;

    }}



    .config-grid-3col {{

      display: grid;

      grid-template-columns: repeat(3, 1fr);

      gap: 14px;

    }}



    .config-grid-2col {{

      display: grid;

      grid-template-columns: repeat(2, 1fr);

      gap: 14px;

    }}



    @media (max-width: 900px) {{

      .config-grid-3col,

      .config-grid-2col {{

        grid-template-columns: 1fr;

      }}

    }}



    .cfg-field {{

      display: flex;

      flex-direction: column;

      gap: 6px;

      background: var(--bg-surface-elevated);

      padding: 12px 14px;

      border-radius: var(--radius-md);

      border: 1px solid var(--border-subtle);

    }}



    .cfg-label {{

      font-size: 0.78rem;

      font-weight: 700;

      color: var(--text-primary);

    }}



    .cfg-desc {{

      font-size: 0.72rem;

      color: var(--text-muted);

      line-height: 1.35;

    }}



    .cfg-input {{

      padding: 8px 12px;

      border-radius: var(--radius-sm);

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      color: var(--text-primary);

      font-size: 0.85rem;

      font-family: var(--font-mono);

      outline: none;

    }}



    .cfg-input:focus {{

      border-color: var(--accent-indigo);

      box-shadow: 0 0 10px var(--accent-indigo-glow);

    }}



    .toggle-row {{

      display: flex;

      justify-content: space-between;

      align-items: center;

    }}



    .switch-toggle {{

      position: relative;

      display: inline-block;

      width: 44px;

      height: 24px;

    }}



    .switch-toggle input {{

      opacity: 0;

      width: 0;

      height: 0;

    }}



    .slider {{

      position: absolute;

      cursor: pointer;

      top: 0; left: 0; right: 0; bottom: 0;

      background-color: var(--bg-surface-highlight);

      transition: .25s;

      border-radius: 34px;

      border: 1px solid var(--border-subtle);

    }}



    .slider:before {{

      position: absolute;

      content: "";

      height: 16px;

      width: 16px;

      left: 3px;

      bottom: 3px;

      background-color: white;

      transition: .25s;

      border-radius: 50%;

    }}



    input:checked + .slider {{

      background-color: var(--accent-emerald);

    }}



    input:checked + .slider:before {{

      transform: translateX(20px);

    }}



    .config-actions-bar {{

      display: flex;

      justify-content: space-between;

      align-items: center;

      gap: 12px;

      padding: 16px 20px;

      background: var(--bg-surface);

      border: 1px solid var(--border-subtle);

      border-radius: var(--radius-lg);

      margin-top: 18px;

      flex-wrap: wrap;

    }}



    /* Live JSON Drawer */

    .json-preview-box {{

      margin-top: 14px;

      padding: 14px;

      background: #050811;

      border-radius: var(--radius-md);

      border: 1px solid var(--border-subtle);

      font-family: var(--font-mono);

      font-size: 0.74rem;

      color: #94a3b8;

      max-height: 240px;

      overflow-y: auto;

      white-space: pre-wrap;

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

    .log-line-err  {{ color: #f43f5e; font-weight: 600; }}

    .log-line-step {{ color: #c084fc; font-weight: 600; }}

    .log-line-ok   {{ color: #34d399; font-weight: 600; }}

    /* On-Page Live Automation Activity & Micro-Step Feed (Event-Driven) */
    .live-feed-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      margin-bottom: 22px;
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-sm);
      transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
    }}
    .live-feed-card.active-event {{
      border-color: rgba(99, 102, 241, 0.45);
      box-shadow: 0 0 20px rgba(99, 102, 241, 0.18);
    }}
    .live-feed-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .live-feed-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .live-feed-status-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--text-muted);
      display: inline-block;
      transition: background 0.3s;
    }}
    .live-feed-status-dot.active {{
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
      animation: pulseDot 1.5s infinite ease-in-out;
    }}
    .live-feed-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .live-feed-badge {{
      font-size: 0.72rem;
      font-family: var(--font-mono);
      padding: 2px 8px;
      border-radius: var(--radius-full);
      background: rgba(99, 102, 241, 0.12);
      color: var(--accent-indigo);
      border: 1px solid rgba(99, 102, 241, 0.25);
    }}
    .live-feed-btn {{
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface-elevated);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all var(--transition-fast);
    }}
    .live-feed-btn:hover {{
      color: var(--text-primary);
      border-color: var(--border-strong);
    }}
    .live-feed-terminal {{
      background: #050811;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      font-family: var(--font-mono);
      font-size: 0.78rem;
      line-height: 1.55;
      color: #94a3b8;
      max-height: 140px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }}
    .live-feed-item {{
      padding: 2px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }}
    .live-feed-item:last-child {{
      border-bottom: none;
    }}
    .live-feed-time {{
      color: #64748b;
      font-size: 0.72rem;
      flex-shrink: 0;
    }}
    .live-feed-msg {{
      flex: 1;
    }}
    @keyframes pulseDot {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.35); opacity: 0.6; }}
    }}

    /* Header Action Button & Dual-State Refresh Control */
    #btn-header-refresh {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: all 0.25s ease;
    }}
    #refresh-spin-icon {{
      display: inline-block;
      line-height: 1;
      font-size: 1rem;
      transform-origin: center;
      transition: transform 0.2s ease;
    }}
    #btn-header-refresh.btn-event-active {{
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(6, 182, 212, 0.22)) !important;
      border: 1px solid rgba(16, 185, 129, 0.5) !important;
      color: #10b981 !important;
      animation: activeGlowPulse 2s infinite ease-in-out;
      font-weight: 600;
    }}
    #btn-header-refresh.btn-event-active #refresh-spin-icon {{
      animation: spin 1.2s linear infinite;
    }}
    @keyframes activeGlowPulse {{
      0%, 100% {{ box-shadow: 0 0 8px rgba(16, 185, 129, 0.25); }}
      50% {{ box-shadow: 0 0 16px rgba(16, 185, 129, 0.6); }}
    }}

    /* Embedded Step-Wise Horizontal Progress Bar inside Header */
    .header-embedded-progress-track {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      width: 100%;
      height: 3px;
      background: rgba(255, 255, 255, 0.05);
      overflow: hidden;
      pointer-events: auto;
      z-index: 20;
    }}

    .header-embedded-progress-fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #6366f1 0%, #06b6d4 50%, #10b981 100%);
      box-shadow: 0 0 8px rgba(6, 182, 212, 0.7);
      transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
      border-radius: 0 2px 2px 0;
      opacity: 0;
    }}

    .header-embedded-progress-fill.active {{
      opacity: 1;
    }}

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



    /* Copy Command Button & Filter Collapse Support */

    .btn-copy-cmd {{

      padding: 4px 10px;

      font-size: 0.74rem;

      border-radius: var(--radius-sm);

      background: var(--bg-surface-elevated);

      border: 1px solid var(--border-subtle);

      color: var(--text-secondary);

      cursor: pointer;

      transition: var(--transition);

    }}

    .btn-copy-cmd:hover {{

      background: var(--accent-indigo);

      color: #ffffff;

      border-color: var(--accent-indigo);

    }}



    .filter-toolbar.collapsed .filter-presets-row,

    .filter-toolbar.collapsed .filter-controls-row,

    .filter-toolbar.collapsed .active-chips-row {{

      display: none;

    }}



    @keyframes spin {{

      100% {{ transform: rotate(360deg); }}

    }}

  </style>

</head>

<body>

  <div class="container">

    <!-- Header with Dual Cluster Architecture -->

    <header class="app-header">

      <div class="header-left">

        <div class="logo-badge">⚡</div>

        <div class="header-titles">

          <h1>AutoSelect Antigravity Dashboard <span class="version-pill">MODERN & INTERACTIVE</span></h1>

          <p>Autonomous Execution Telemetry, Process Control & Grill-Me Decision Ledger</p>

        </div>

      </div>



      <div class="header-right">

        <!-- Cluster 1: System Health Indicators (Active, Paused, Inactive) -->

        <div class="health-cluster">

          <span class="status-pill status-bridge-online" id="server-bridge-pill" title="Control Server Port 8501">

            <span class="pulse-dot"></span>

            <span id="bridge-text">Bridge Online</span>

          </span>

          <span class="status-pill status-idle" id="dashboard-status-pill" title="Standby">

            <span class="pulse-dot"></span>

            <span id="status-text">⚪ Inactive</span>

          </span>

          <span class="status-pill status-mode-badge" id="header-mode-badge" role="button" tabindex="0" style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; cursor: pointer; user-select: none; font-weight: 700;" title="{badge_title}">

            {badge_icon} {badge_text}

          </span>

        </div>



        <!-- Cluster 2: Action Controls -->

        <div class="action-cluster">

          <button class="btn btn-automation state-stopped" id="automation-toggle-btn" title="Toggle Complete Automation Pipeline">

            <span id="control-icon">▶️</span>

            <span id="control-label">Start Automation</span>

          </button>

          <button class="btn" id="btn-open-automation-modal" title="1-Click Launch Scripts & Commands (Dept 04 & 06 Standard)" style="background: rgba(16,185,129,0.12); color: #34d399; border-color: rgba(16,185,129,0.35);">

            <span>🚀</span>

            <span>Scripts</span>

          </button>

          <button class="btn btn-classic-switch" id="btn-switch-classic" onclick="window.location.href = window.location.protocol.startsWith('http') ? '/classic' : '../Simple and Classic Dashboard/dashboard.html'" title="Switch to Simple & Classic Dashboard">

            <span>🏛️</span>

            <span>Classic</span>

          </button>

          <button class="btn" id="btn-toggle-logs" title="Toggle Live Console Logs Stream (L)">

            <span>📟</span>

            <span>Logs</span>

            <span class="log-unread-badge" id="log-count-badge">0</span>

          </button>

          <button class="btn" id="btn-audio-toggle" title="Toggle Futuristic Audio Chimes (M)">

            <span id="audio-icon">🔔</span>

          </button>

          <button class="btn" id="theme-toggle" title="Toggle Dark/Light Theme (T)">🌓</button>

          <button class="btn" id="btn-header-refresh" title="Synchronous Telemetry Refresh from Disk">

            <span id="refresh-spin-icon">🔄</span>

          </button>

          <button class="btn" id="btn-help-shortcuts" title="Keyboard Shortcuts Help (?)">⌨️</button>

        </div>

      </div>

      <!-- Embedded Step-Wise Horizontal Progress Bar inside Header -->
      <div class="header-embedded-progress-track" id="header-progress-track" title="Pipeline Progress: Idle (0%)">
        <div class="header-embedded-progress-fill" id="header-progress-bar" style="width: 0%;"></div>
      </div>

    </header>



    <!-- Live Pulse Ticker Strip -->

    <div class="live-ticker-strip">

      <div class="ticker-left">

        <span class="ticker-beacon"><span class="beacon-dot"></span> LIVE TELEMETRY</span>

        <span class="ticker-msg" id="ticker-status-msg">Complete Automation Daemon Ready • Ready to spawn complete_automation.py</span>

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



    <!-- Full Interactive Multi-Dimensional Filter Toolbar (Classic Parity) -->

    <section class="filter-toolbar" id="contextual-filter-toolbar" aria-label="Filters Toolbar">

      <div class="filter-toolbar-header">

        <div class="filter-toolbar-title">

          <span>🔍</span>

          <span>Interactive Multi-Dimensional Filter Toolbar</span>

        </div>

        <div style="display: flex; align-items: center; gap: 8px;">

          <div class="filter-stats-badge" id="filter-stats-badge">

            Showing <span id="filter-count" style="font-weight: 700; color: var(--text-primary);">{total_runs}</span> of <span id="filter-total">{total_runs}</span> runs

          </div>

          <button type="button" class="btn" id="filter-collapse-btn" style="padding: 2px 8px; font-size: 0.72rem;" title="Collapse/Expand Filters">▾ Collapse</button>

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



      <!-- Row 2: Granular Controls -->

      <div class="filter-controls-row">

        <div class="filter-control-group">

          <label class="filter-label" for="filter-date-from">Date Range</label>

          <div class="filter-date-inputs">

            <input type="date" id="filter-date-from" class="filter-input-date" title="Filter From Date">

            <span class="filter-date-sep">to</span>

            <input type="date" id="filter-date-to" class="filter-input-date" title="Filter To Date">

          </div>

        </div>



        <div class="filter-control-group">

          <label class="filter-label" for="filter-chat">Conversation</label>

          <select id="filter-chat" class="filter-select">

            <option value="all">All Conversations ({total_chats})</option>

            {chat_options_html}

          </select>

        </div>



        <div class="filter-control-group">

          <label class="filter-label" for="filter-complexity">Complexity</label>

          <select id="filter-complexity" class="filter-select">

            <option value="all">All Runs</option>

            <option value="single">Single Question Runs</option>

            <option value="multi">Multi-Question Runs (&gt;= 2)</option>

          </select>

        </div>



        <div class="filter-control-group">

          <label class="filter-label" for="filter-speed">Speed / Latency</label>

          <select id="filter-speed" class="filter-select">

            <option value="all">All Speeds</option>

            <option value="fast">Fast (&lt; 3s)</option>

            <option value="moderate">Moderate (3s - 8s)</option>

            <option value="heavy">Heavy (&gt; 8s)</option>

          </select>

        </div>



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



    <!-- TAB 1: OVERVIEW (PERMANENTLY OPEN, 100% FULL-WIDTH, NO COLLAPSIBLES) -->

    <main id="tab-overview" class="tab-panel active" role="tabpanel" aria-labelledby="tab-btn-overview">

      <!-- Visible On-Page Live Automation Activity & Micro-Step Feed (Event-Driven) -->
      <section class="live-feed-card" id="onpage-live-feed-card" aria-label="Live Automation Activity Feed">
        <div class="live-feed-header">
          <div class="live-feed-title">
            <span class="live-feed-status-dot" id="live-feed-dot"></span>
            <span>⚡ Live Automation Activity & Micro-Step Feed</span>
            <span class="live-feed-badge" id="live-feed-badge">IDLE</span>
          </div>
          <div class="live-feed-actions">
            <span style="font-size: 0.72rem; color: var(--text-muted);" id="live-feed-time">Event Stream Active</span>
            <button type="button" class="live-feed-btn" id="btn-feed-open-drawer" title="Expand Full Interactive Terminal Drawer">
              <span>🖥️ View Full Log</span>
            </button>
          </div>
        </div>
        <div class="live-feed-terminal" id="live-feed-stream" role="log" aria-live="polite">
          <div class="live-feed-item" style="color: #64748b;">
            <span class="live-feed-time">Waiting:</span>
            <span class="live-feed-msg">Connecting to live automation event stream...</span>
          </div>
        </div>
      </section>

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



      <!-- Permanent Full-Width 5-Step Pipeline Topology Diagram -->

      <div class="overview-diagram-card">

        <div class="overview-card-header">

          <div class="overview-card-title">

            <span>⚡ 5-Step Pipeline Topology & Subsystem Bus</span>

          </div>

          <span class="overview-card-subtitle">Live End-to-End Orchestration Architecture</span>

        </div>

        <div class="diagram-body">

          {pipeline_svg}

        </div>

      </div>



      <!-- Permanent 7 Visual Analytics SVG Charts Grid -->

      <div class="charts-grid">

        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>📈 Velocity Timeline & Run Latency</span>

            </div>

          </div>

          <div>

            {velocity_svg}

          </div>

        </div>



        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>🎯 Productivity & Efficiency Gauge</span>

            </div>

          </div>

          <div>

            {gauge_svg}

          </div>

        </div>



        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>🗓️ 24-Hour Execution Activity Heatmap</span>

            </div>

          </div>

          <div>

            {heatmap_svg}

          </div>

        </div>



        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>📊 Option Selection Breakdown</span>

            </div>

          </div>

          <div>

            {option_breakdown_svg}

          </div>

        </div>



        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>📶 Chat Distribution & Run Volume</span>

            </div>

          </div>

          <div>

            {distribution_svg}

          </div>

        </div>



        <div class="chart-card">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>🍩 Conversation Topic Share</span>

            </div>

          </div>

          <div>

            {topic_share_svg}

          </div>

        </div>



        <div class="chart-card chart-card-wide">

          <div class="chart-card-header">

            <div class="chart-card-title">

              <span>📉 Run Duration & Latency Trend</span>

            </div>

          </div>

          <div>

            {latency_trend_svg}

          </div>

        </div>

      </div>

    </main>



    <!-- TAB 2: CHATS -->

    <main id="tab-chats" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-chats">

      <div class="stats-strip">

        <div class="stat-pill">

          <span class="stat-icon" style="font-size: 1.5rem; margin-right: 8px;">📂</span>

          <div>

            <div class="stat-num">{total_chats}</div>

            <div style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">Total Unique Chats</div>

          </div>

        </div>

        <div class="stat-pill">

          <span class="stat-icon" style="font-size: 1.5rem; margin-right: 8px;">⚡</span>

          <div>

            <div class="stat-num">{total_runs}</div>

            <div style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">Lifetime Pipeline Runs</div>

          </div>

        </div>

        <div class="stat-pill">

          <span class="stat-icon" style="font-size: 1.5rem; margin-right: 8px;">🎯</span>

          <div>

            <div class="stat-num">{avg_runs_per_chat:.1f}</div>

            <div style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">Avg Runs / Chat</div>

          </div>

        </div>

      </div>



      <div class="controls-bar" style="justify-content: space-between; flex-wrap: wrap; gap: 12px;">

        <div class="search-input-wrap" style="flex: 1 1 300px;">

          <span class="search-icon-pos">🔍</span>

          <input type="text" id="search-chats" class="search-input" placeholder="Search chats by Conversation ID or topic summary...">

          <span class="search-shortcut-hint">Press [/]</span>

        </div>

        <div class="chats-view-switcher">

          <button type="button" class="view-btn active" id="btn-view-cards" onclick="setChatsView('cards')">

            <span>🎴 Visual Cards</span>

          </button>

          <button type="button" class="view-btn" id="btn-view-table" onclick="setChatsView('table')">

            <span>📑 Compact Table</span>

          </button>

        </div>

      </div>



      <!-- View 1: Modern Card Grid Explorer (Default) -->

      <div id="chats-cards-view" class="chats-cards-grid-container" style="display: block;">

        <div id="chats-card-grid" class="chats-card-grid">

          <!-- Rendered dynamically by JavaScript -->

        </div>

      </div>



      <!-- View 2: Compact Structured Data Table -->

      <div id="chats-table-view" class="overview-diagram-card" style="display: none; margin-top: 14px;">

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

              <!-- Rendered dynamically by JavaScript -->

            </tbody>

          </table>

        </div>

      </div>

    </main>



    <!-- TAB 3: QUESTIONS (BY DEFAULT COLLAPSED ACCORDION TREE) -->

    <main id="tab-questions" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-questions">

      <div class="controls-bar" style="justify-content: space-between; flex-wrap: wrap; gap: 12px;">

        <div class="search-input-wrap" style="flex: 1 1 300px;">

          <span class="search-icon-pos">🔍</span>

          <input type="text" id="search-questions" class="search-input" placeholder="Search questions, options, topics, or conversation IDs...">

          <span class="search-shortcut-hint">Press [/]</span>

        </div>

        <div style="display: flex; gap: 8px;">

          <button type="button" class="btn" id="btn-expand-all-questions">▾ Expand All</button>

          <button type="button" class="btn" id="btn-collapse-all-questions">▸ Collapse All</button>

        </div>

      </div>



      <div class="questions-quick-filters">

        <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">Filter Focus:</span>

        <button type="button" class="q-filter-chip active" data-qfilter="all" onclick="setQFilter('all', this)">All Questions</button>

        <button type="button" class="q-filter-chip" data-qfilter="recommended" onclick="setQFilter('recommended', this)">⭐ Recommended Matches</button>

        <button type="button" class="q-filter-chip" data-qfilter="multi" onclick="setQFilter('multi', this)">⚡ Multi-Option</button>

      </div>



      <div id="details-container">

        <!-- Rendered dynamically by JavaScript in collapsed mode -->

      </div>

    </main>



    <!-- TAB 4: MODE SWITCH (ULTRA-MODERN INTERACTIVE LIFECYCLE STANDARD) -->

    <main id="tab-modes" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-modes">

      <div class="modes-panel-container">

        <!-- Hero Header & Execution Controller Card -->

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

              <span class="status-pill status-idle" id="modes-status-pill">⚪ Automation Inactive</span>

              <button type="button" class="btn btn-automation state-stopped" id="modes-automation-toggle-btn" title="Toggle AutoSelect Antigravity Automation directly from Mode Switch">

                <span id="modes-control-icon">▶️</span>

                <span id="modes-control-label">Start Automation</span>

              </button>

            </div>

          </div>



          <!-- Segmented Pill Mode Switcher Bar -->

          <div class="modes-switcher-bar">

            <div class="modes-switcher-label" id="modes-active-mode-label">

              <span id="modes-active-dot" style="color: {'#10b981' if is_prod else '#f59e0b'};">●</span>

              <span id="modes-active-text">Active Operating Mode: <strong>{'PRODUCTION (उत्पादन मोड)' if is_prod else 'TEST (परीक्षण मोड)'}</strong></span>

            </div>

            <div class="modes-segmented-group" role="radiogroup" aria-label="Active Execution Mode Switcher">

              <button type="button" class="banner-mode-btn {'active' if is_prod else ''}" id="banner-mode-prod-btn" data-mode="production" title="Switch to Production Mode (Continuous Autonomous Loop)">

                <span>🛡️ Production</span>

                <span class="banner-mode-indicator">Continuous Loop</span>

              </button>

              <button type="button" class="banner-mode-btn {'active' if not is_prod else ''}" id="banner-mode-test-btn" data-mode="test" title="Switch to Test Mode (Single-Run Auto-Stop)">

                <span>🧪 Test Mode</span>

                <span class="banner-mode-indicator">Auto-Stop</span>

              </button>

            </div>

          </div>



          <!-- Two Rich Interactive Mode Cards -->

          <div class="mode-lifecycle-grid">

            <!-- 1. Production Mode Card -->

            <div class="lifecycle-card card-production {'active-mode-card' if is_prod else ''}" id="mode-card-prod" role="button" tabindex="0" title="Click to activate Production Mode">

              <div class="lifecycle-card-top">

                <div class="lifecycle-card-title">

                  <span class="card-icon">🛡️</span>

                  <div>

                    <strong>Production Mode</strong>

                    <span class="card-title-hindi">(प्रोडक्शन लेवल - Continuous Autonomous Loop)</span>

                  </div>

                </div>

                <span class="lifecycle-card-badge badge-prod-mode" id="mode-badge-prod">

                  <span>●</span>

                  <span id="mode-badge-text-prod">{'CURRENT ACTIVE' if is_prod else 'Continuous Loop'}</span>

                </span>

              </div>

              <p class="lifecycle-card-desc">

                जब <strong>Production Level</strong> सिलेक्ट करके स्टार्ट करते हैं, तो यह बैकग्राउंड में अनवरत <strong>(Continuous Loop - 300s चक्र)</strong> चलता रहेगा जब तक कि आप मैन्युअली <strong>Stop</strong> बटन न दबाएँ।

              </p>

              <div class="lifecycle-card-features">

                <span class="lifecycle-feature-tag">🔄 Continuous 300s Polling Loop</span>

                <span class="lifecycle-feature-tag">♾️ Runs Indefinitely in Background</span>

                <span class="lifecycle-feature-tag">👤 Manual User Stop Required</span>

                <span class="lifecycle-feature-tag">🚀 Full Multi-Step Hardware Automation</span>

              </div>

              <button type="button" class="lifecycle-card-btn {'btn-automation' if is_prod else 'btn'}" id="btn-set-prod">

                {'✓ Active in Production' if is_prod else '⚡ Switch to Production Mode'}

              </button>

            </div>



            <!-- 2. Test Mode Card -->

            <div class="lifecycle-card card-test {'active-mode-card' if not is_prod else ''}" id="mode-card-test" role="button" tabindex="0" title="Click to activate Test Mode">

              <div class="lifecycle-card-top">

                <div class="lifecycle-card-title">

                  <span class="card-icon">🧪</span>

                  <div>

                    <strong>Test Mode</strong>

                    <span class="card-title-hindi">(टेस्ट रन - Single-Run &amp; Auto-Stop)</span>

                  </div>

                </div>

                <span class="lifecycle-card-badge badge-test-mode" id="mode-badge-test">

                  <span>●</span>

                  <span id="mode-badge-text-test">{'CURRENT ACTIVE' if not is_prod else 'Single-Run Auto-Stop'}</span>

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

              <button type="button" class="lifecycle-card-btn {'btn' if is_prod else 'btn-automation'}" id="btn-set-test" style="{'background: rgba(245,158,11,0.18); color: #fbbf24; border-color: rgba(245,158,11,0.4);' if is_prod else 'background: #d97706; color: #ffffff;'}">

                {'✓ Active in Test Mode' if not is_prod else '⚡ Switch to Test Mode'}

              </button>

            </div>

          </div>

        </div>



        <!-- Operational Lifecycle & Parameter Comparison Table -->

        <div class="modes-comparison-card">

          <div class="modes-comparison-header">

            <span class="comparison-icon">⚖️</span>

            <div>

              <h3 class="comparison-title">Operational Lifecycle &amp; Parameters Comparison</h3>

              <p class="comparison-subtitle">विस्तृत कार्यप्रणाली तुलना • Comprehensive breakdown of runtime parameters, stop conditions, and resource allocation</p>

            </div>

          </div>

          <div class="table-container">

            <table class="modes-comparison-table diff-table">

              <thead>

                <tr>

                  <th style="min-width: 180px;">Operational Parameter / आयाम</th>

                  <th>🛡️ Production Mode (प्रोडक्शन मोड)</th>

                  <th>🧪 Test Mode (टेस्ट रन)</th>

                  <th style="min-width: 140px;">Department Standard</th>

                </tr>

              </thead>

              <tbody>

                <tr>

                  <td><strong>Execution Cycle / निष्पादन आवृत्ति</strong></td>

                  <td><span class="lifecycle-card-badge badge-prod-mode">Continuous Autonomous Loop</span></td>

                  <td><span class="lifecycle-card-badge badge-test-mode">Single Cycle (1 Run Only)</span></td>

                  <td>Dept 06 &amp; Dept 12</td>

                </tr>

                <tr>

                  <td><strong>Stop Condition / स्टॉप नियम</strong></td>

                  <td><strong>Manual Stop Only</strong> — User जब तक Stop बटन नहीं दबाता, तब तक 300s loop अनवरत चलता रहता है</td>

                  <td><strong>Automatic Auto-Stop</strong> — Chat/Question processing complete होते ही process खुद सुरक्षित exit हो जाता है</td>

                  <td>Rule 26 Zero-Hang</td>

                </tr>

                <tr>

                  <td><strong>Step 0 Polling Interval / पोलिंग अंतराल</strong></td>

                  <td><code>300.0s</code> (5 मिनट का स्थिर प्रोडक्शन अंतराल)</td>

                  <td><code>10.0s</code> (त्वरित परीक्षण एवं डिबग चक्र)</td>

                  <td>Dept 14 Telemetry</td>

                </tr>

                <tr>

                  <td><strong>Target Scope / लक्षित उपयोग</strong></td>

                  <td>24/7 autonomous monitoring &amp; unattended execution</td>

                  <td>Local verification, step testing, single question verification</td>

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



    <!-- TAB 5: COMPLETE CONFIGURATION (DUAL SUB-TABS: SYSTEM RUNTIME vs DASHBOARD) -->

    <main id="tab-config" class="tab-panel" role="tabpanel" aria-labelledby="tab-btn-config">

      <div class="controls-bar" style="margin-bottom: 14px;">

        <div class="search-input-wrap">

          <span class="search-icon-pos">🔍</span>

          <input type="text" class="search-input" id="search-config" placeholder="Search settings (timing, delay, poll, threshold, step)...">

          <span class="search-shortcut-hint">Press [/]</span>

        </div>

      </div>



      <!-- Config Sub-Navigation Pills -->

      <div class="config-subnav">

        <button type="button" class="config-subnav-btn active" id="subtab-btn-runtime" data-subtab="runtime">

          ⚡ System Runtime Configuration (config.json)

        </button>

        <button type="button" class="config-subnav-btn" id="subtab-btn-dashboard" data-subtab="dashboard">

          🎨 Dashboard &amp; Telemetry Preferences

        </button>

      </div>



      <!-- SUB-PANEL 1: SYSTEM RUNTIME CONFIGURATION -->

      <div class="config-subpanel active" id="subpanel-runtime">

        <!-- 1. Pipeline Steps Toggles -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>⚡</span>

              <span>Pipeline Steps Toggles</span>

            </div>

            <span style="font-size: 0.72rem; color: var(--text-muted);">Enable/Disable Execution Seams</span>

          </div>

          <div class="config-grid-2col">

            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Step 1: Window Focus &amp; Activation</span>

                  <div class="cfg-desc">Finds and brings Antigravity target window to foreground</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-step1-enabled" {'checked' if step1_enabled else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>



            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Step 2: UIA DOM Element Extraction</span>

                  <div class="cfg-desc">Scans accessibility DOM tree to click target chat thread</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-step2-enabled" {'checked' if step2_enabled else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>



            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Step 3: Keyboard Grill-Me Selection</span>

                  <div class="cfg-desc">Hardware scan code keystrokes to select and confirm options</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-step3-enabled" {'checked' if step3_enabled else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>



            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Step 4: Reporting &amp; Visual Dashboard</span>

                  <div class="cfg-desc">Telemetry recording, dynamic charts &amp; user inactivity HUD</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-step4-enabled" {'checked' if step4_enabled else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>

          </div>

        </div>



        <!-- 2. All 12 Precise Millisecond Timings & Delays -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>⏱️</span>

              <span>Precise Millisecond Timings &amp; Delays</span>

            </div>

            <span style="font-size: 0.72rem; color: var(--text-muted);">Complete Hardware &amp; Polling Control</span>

          </div>

          <div class="config-grid-3col">

            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-prod-poll">Production Poll Interval (s)</label>

              <div class="cfg-desc">Main idle polling cycle in production mode</div>

              <input type="number" step="0.5" class="cfg-input" id="cfg-timing-prod-poll" value="{step0_poll_prod}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-test-poll">Test Mode Poll Interval (s)</label>

              <div class="cfg-desc">Accelerated validation cycle for testing</div>

              <input type="number" step="0.05" class="cfg-input" id="cfg-timing-test-poll" value="{step0_poll_test}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-settle">Step Transition Settle (s)</label>

              <div class="cfg-desc">Pause between step transitions for UI stability</div>

              <input type="number" step="0.1" class="cfg-input" id="cfg-timing-settle" value="{settle_delay}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-activity-delay">User Inactivity Delay (s)</label>

              <div class="cfg-desc">Wait time after mouse/key detection before opening report</div>

              <input type="number" step="0.5" class="cfg-input" id="cfg-timing-activity-delay" value="{step4_delay}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step4-poll">Step 4 Telemetry Polling (s)</label>

              <div class="cfg-desc">Polling interval for user mouse and keystroke detection</div>

              <input type="number" step="0.05" class="cfg-input" id="cfg-timing-step4-poll" value="{step4_poll}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step1-focus">Step 1 Focus Settle Delay (s)</label>

              <div class="cfg-desc">Buffer after bringing target window to foreground</div>

              <input type="number" step="0.05" class="cfg-input" id="cfg-timing-step1-focus" value="{step1_focus}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step2-dom-settle">Step 2 DOM Click Settle (s)</label>

              <div class="cfg-desc">Pause after simulated click on chat row in GUI</div>

              <input type="number" step="0.05" class="cfg-input" id="cfg-timing-step2-dom-settle" value="{step2_dom_settle}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step3-countdown">Step 3 Pre-Execution Countdown (s)</label>

              <div class="cfg-desc">Countdown before keystrokes are transmitted</div>

              <input type="number" step="0.5" class="cfg-input" id="cfg-timing-step3-countdown" value="{step3_countdown}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step3-hold-ms">Step 3 Key Hold Delay (ms)</label>

              <div class="cfg-desc">Hardware scan code hold duration during keyboard press</div>

              <input type="number" step="10" class="cfg-input" id="cfg-timing-step3-hold-ms" value="{step3_hold_ms}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step3-post-ms">Step 3 Post Keypress Delay (ms)</label>

              <div class="cfg-desc">Pause after each individual key stroke</div>

              <input type="number" step="25" class="cfg-input" id="cfg-timing-step3-post-ms" value="{step3_post_ms}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step3-inter-q-ms">Step 3 Inter-Question Delay (ms)</label>

              <div class="cfg-desc">Pause between answering consecutive question prompts</div>

              <input type="number" step="50" class="cfg-input" id="cfg-timing-step3-inter-q-ms" value="{step3_inter_q_ms}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-timing-step3-round-ms">Step 3 Round Cooldown Pause (ms)</label>

              <div class="cfg-desc">Cooldown pause after completing entire questionnaire</div>

              <input type="number" step="100" class="cfg-input" id="cfg-timing-step3-round-ms" value="{step3_round_ms}">

            </div>

          </div>

        </div>



        <!-- 3. Governance, Safety & Auto-Pause Sentinel -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>🛡️</span>

              <span>Governance, Safety &amp; Auto-Pause Sentinel</span>

            </div>

            <span style="font-size: 0.72rem; color: var(--text-muted);">Win32 User32 Activity Protection</span>

          </div>

          <div class="config-grid-2col">

            <div class="cfg-field">

              <label class="cfg-label" for="cfg-pause-threshold">User Activity Pause Threshold (s)</label>

              <div class="cfg-desc">If user moves keyboard/mouse within this window, automation enters PAUSED state</div>

              <input type="number" step="5" class="cfg-input" id="cfg-pause-threshold" value="{user_pause_threshold}">

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-continuous-delay">Continuous Loop Delay (s)</label>

              <div class="cfg-desc">Sleep interval between continuous autonomous monitoring cycles</div>

              <input type="number" step="10" class="cfg-input" id="cfg-continuous-delay" value="{timing_cfg.get('continuous_loop_delay_seconds', 300.0)}">

            </div>

          </div>

        </div>



        <!-- 4. Antigravity Window & Session Governance -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>🪐</span>

              <span>Antigravity Window &amp; Session Governance</span>

            </div>

            <span style="font-size: 0.72rem; color: var(--text-muted);">Session Age &amp; Active Verification</span>

          </div>

          <div class="config-grid-2col">

            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Require Grill-Me Detection</span>

                  <div class="cfg-desc">Only act on Antigravity windows with active interactive questionnaire</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-antigravity-require-grillme" {'checked' if require_grill_me else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-antigravity-active-hours">Active Window Max Age (hours)</label>

              <div class="cfg-desc">Maximum conversation age in hours before skipping stale sessions</div>

              <input type="number" step="0.5" min="0.5" max="168" class="cfg-input" id="cfg-antigravity-active-hours" value="{active_hours}">

            </div>

          </div>

        </div>



        <!-- 5. Logging & Telemetry Engine -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>📝</span>

              <span>Logging &amp; Telemetry Engine</span>

            </div>

            <span style="font-size: 0.72rem; color: var(--text-muted);">Disk Stream &amp; Verbose Diagnostics</span>

          </div>

          <div class="config-grid-2col">

            <div class="cfg-field">

              <div class="toggle-row">

                <div>

                  <span class="cfg-label">Verbose Debug Logging</span>

                  <div class="cfg-desc">Stream detailed Win32, UIA element tree and scan code events</div>

                </div>

                <label class="switch-toggle">

                  <input type="checkbox" id="cfg-logging-verbose" {'checked' if log_verbose else ''}>

                  <span class="slider"></span>

                </label>

              </div>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-logging-file">Active Log File Name</label>

              <div class="cfg-desc">Target log file path for continuous automation daemon</div>

              <input type="text" class="cfg-input" id="cfg-logging-file" value="{log_file}">

            </div>

          </div>

        </div>



        <!-- 6. Formatted JSON Live Preview Drawer -->

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>📄</span>

              <span>Raw Runtime Config (config.json)</span>

            </div>

            <button type="button" class="btn" id="btn-toggle-json-drawer" style="padding: 2px 8px; font-size: 0.72rem;">Toggle Preview</button>

          </div>

          <div class="json-preview-box" id="json-preview-container" style="display: none;">{runtime_config_json_str}</div>

        </div>

      </div>



      <!-- SUB-PANEL 2: DASHBOARD & TELEMETRY PREFERENCES -->

      <div class="config-subpanel" id="subpanel-dashboard">

        <div class="config-group-card">

          <div class="config-group-header">

            <div class="config-group-title">

              <span>🎨</span>

              <span>Dashboard Telemetry &amp; Presentation Preferences</span>

            </div>

          </div>

          <div class="config-grid-2col">

            <div class="cfg-field">

              <label class="cfg-label" for="cfg-auto-refresh">Auto-Refresh Strategy &amp; Cadence</label>

              <div class="cfg-desc">Reactive event-driven synchronization or manual reload</div>

              <select id="cfg-auto-refresh" class="filter-select">

                <option value="event" selected>⚡ Event-Driven (Real-Time &amp; Stage Transitions)</option>

                <option value="0">🛑 Manual Refresh Only (Refresh Button)</option>

                <option value="30">⏱️ Periodic Fallback (30 Seconds)</option>

                <option value="60">⏱️ Periodic Fallback (60 Seconds)</option>

              </select>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-default-tab">Default Landing Tab</label>

              <div class="cfg-desc">Initial tab activated on dashboard startup</div>

              <select id="cfg-default-tab" class="filter-select">

                <option value="overview">Overview (KPIs &amp; Visual Charts)</option>

                <option value="chats">Chats (Conversations Breakdown)</option>

                <option value="questions">Questions (Detailed Q&amp;A Ledger)</option>

                <option value="modes">Mode Switch</option>

                <option value="config">Config</option>

              </select>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-selection-policy">Option Selection Policy</label>

              <div class="cfg-desc">Rule used when evaluating interactive question choices</div>

              <select id="cfg-selection-policy" class="filter-select">

                <option value="recommended">Recommended Option First (Recommended)</option>

                <option value="first_available">First Available Choice (Index 1)</option>

                <option value="highest_confidence">Highest Match Score</option>

              </select>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-visual-effects">Visual Animation Effects</label>

              <div class="cfg-desc">Enable smooth 60fps glassmorphism and count-up animations</div>

              <select id="cfg-visual-effects" class="filter-select">

                <option value="rich">Rich 60FPS Glassmorphism &amp; Glows</option>

                <option value="reduced">Reduced Motion (Low CPU)</option>

              </select>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="cfg-sound-notify">Futuristic Web Audio Chimes</label>

              <div class="cfg-desc">Synthesized audio cues on Start, Stop, and Copy actions</div>

              <select id="cfg-sound-notify" class="filter-select">

                <option value="enabled">Enabled (Browser AudioContext)</option>

                <option value="disabled">Muted / Disabled</option>

              </select>

            </div>



            <div class="cfg-field">

              <label class="cfg-label" for="btn-test-chime">Synthesizer Audition</label>

              <div class="cfg-desc">Test the real-time browser AudioContext cue</div>

              <button type="button" class="btn" id="btn-test-chime" style="width: 100%; justify-content: center;">🔔 Test Audio Chime</button>

            </div>



            <div class="cfg-field">

              <label class="cfg-label">Telemetry History</label>

              <div class="cfg-desc">Export historical runs JSON dataset</div>

              <button type="button" class="btn" id="cfg-export-btn" style="width: 100%; justify-content: center;">📥 Export History JSON</button>

            </div>



            <div class="cfg-field">

              <label class="cfg-label">Preferences Reset</label>

              <div class="cfg-desc">Clear saved theme, tab and audio preferences</div>

              <button type="button" class="btn" id="cfg-reset-btn" style="width: 100%; justify-content: center; color: var(--accent-rose);">🔄 Reset Preferences</button>

            </div>

          </div>

        </div>

      </div>



      <!-- Unified Configuration Actions Bar -->

      <div class="config-actions-bar">

        <div style="display: flex; gap: 8px; flex-wrap: wrap;">

          <button type="button" class="btn" id="btn-copy-cli-cmd" title="Copy CLI Command to Clipboard">📋 Copy CLI Command</button>

          <button type="button" class="btn" id="btn-download-runtime-cfg" title="Download config.json directly">📥 Download config.json</button>

          <button type="button" class="btn" id="btn-export-config" title="Export Configuration JSON">📤 Export JSON</button>

          <button type="button" class="btn" id="btn-reset-config-defaults" style="color: var(--accent-rose);">🔄 Reset to Defaults</button>

        </div>

        <div>

          <button type="button" class="btn btn-automation" id="btn-save-runtime-config">💾 Save Configuration to config.json</button>

        </div>

      </div>

    </main>



    <!-- 1-Click Automation Execution & Monitor Modal (Classic Parity) -->

    <div class="modal-backdrop" id="automation-modal" role="dialog" aria-modal="true" aria-labelledby="automation-modal-title">

      <div class="modal-card" style="max-width: 640px;">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">

          <div style="display: flex; align-items: center; gap: 8px;">

            <span style="font-size: 1.2rem;">🚀</span>

            <div>

              <h3 style="font-size: 1rem; font-weight: 700; margin: 0;" id="automation-modal-title">AutoSelect Antigravity Automation</h3>

              <p style="font-size: 0.74rem; color: var(--text-muted); margin: 0;">1-Click Server &amp; Terminal Execution Scripts</p>

            </div>

          </div>

          <button type="button" class="btn" id="btn-close-automation-modal" style="padding: 2px 7px;">✕</button>

        </div>



        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 14px;">

          <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--accent-emerald); font-size: 0.82rem; margin-bottom: 4px;">

            <span>🟢</span>

            <span>Autonomous Background Monitoring Engine</span>

          </div>

          <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 0; line-height: 1.4;">

            AutoSelect Antigravity constantly monitors Antigravity chats. When an interactive questionnaire appears, it brings the window to the foreground and autonomously confirms the recommended option.

          </p>

        </div>



        <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;">

          <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px 12px;">

            <div>

              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Silent Background Daemon (No Terminal Window)</div>

              <code style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-cyan);">wscript start_dashboard_background.vbs</code>

            </div>

            <button type="button" class="btn btn-sm btn-copy-cmd" data-cmd="wscript start_dashboard_background.vbs" id="btn-copy-automation-vbs">📋 Copy</button>

          </div>



          <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px 12px;">

            <div>

              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Interactive Local Server &amp; Dashboard</div>

              <code style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-cyan);">.\\run_dashboard.bat</code>

            </div>

            <button type="button" class="btn btn-sm btn-copy-cmd" data-cmd=".\\run_dashboard.bat" id="btn-copy-automation-run-bat">📋 Copy</button>

          </div>



          <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px 12px;">

            <div>

              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Direct Python Automation Pipeline</div>

              <code style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-cyan);">python step_9_complete_automation/complete_automation.py</code>

            </div>

            <button type="button" class="btn btn-sm btn-copy-cmd" data-cmd="python step_9_complete_automation/complete_automation.py" id="btn-copy-automation-cmd">📋 Copy</button>

          </div>



          <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px 12px;">

            <div>

              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">One-Shot Batch Automation</div>

              <code style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-cyan);">.\\run_automation.bat</code>

            </div>

            <button type="button" class="btn btn-sm btn-copy-cmd" data-cmd=".\\run_automation.bat" id="btn-copy-automation-bat">📋 Copy</button>

          </div>



          <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px 12px;">

            <div>

              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Safe Dry-Run Simulation (No Hardware Keystrokes)</div>

              <code style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-cyan);">python step_9_complete_automation/complete_automation.py --dry-run</code>

            </div>

            <button type="button" class="btn btn-sm btn-copy-cmd" data-cmd="python step_9_complete_automation/complete_automation.py --dry-run" id="btn-copy-automation-dry-run">📋 Copy</button>

          </div>

        </div>



        <div style="display: flex; justify-content: flex-end;">

          <button type="button" class="btn" id="btn-close-automation-modal-footer">Close</button>

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

      <button class="btn btn-automation" id="btn-save-config-dock" style="padding: 4px 12px; font-size: 0.75rem;">Save to config.json</button>

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

      const tickerStatusMsg = document.getElementById('ticker-status-msg');



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



      // Main Horizontal Tabs & Contextual Filter Toolbar visibility

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



        // Show filters on overview, chats, and questions; hide on modes and config

        if (contextualFilters) {{

          contextualFilters.style.display = (targetTab === 'overview' || targetTab === 'chats' || targetTab === 'questions') ? 'block' : 'none';

        }}

      }}



      tabs.forEach(btn => {{

        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));

      }});

      switchTab(currentActiveTab);



      // Config Sub-Tabs (System Runtime vs Dashboard Preferences)

      const subtabBtns = document.querySelectorAll('.config-subnav-btn');

      const subpanels = document.querySelectorAll('.config-subpanel');

      subtabBtns.forEach(btn => {{

        btn.addEventListener('click', () => {{

          subtabBtns.forEach(b => b.classList.remove('active'));

          subpanels.forEach(p => p.classList.remove('active'));

          btn.classList.add('active');

          const subId = btn.getAttribute('data-subtab');

          const targetPanel = document.getElementById('subpanel-' + subId);

          if (targetPanel) targetPanel.classList.add('active');

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



      // Multi-Dimensional Filtering Logic

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



        if (selChat !== 'all' && cid !== selChat) return false;



        if (run && run.timestamp) {{

          const runDateStr = run.timestamp.split('T')[0];

          if (fromVal && runDateStr < fromVal) return false;

          if (toVal && runDateStr > toVal) return false;

        }}



        if (run) {{

          const qCount = run.questions_count !== undefined ? run.questions_count : (run.questions ? run.questions.length : 0);

          if (selComplexity === 'single' && qCount !== 1) return false;

          if (selComplexity === 'multi' && qCount < 2) return false;

        }}



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



        const activePresetBtn = document.querySelector('.preset-btn.active');

        chipsHtml += `<span class="filter-chip">⚡ ${{activePresetBtn ? activePresetBtn.textContent : 'All Time'}}</span>`;



        if (filterDateFrom && filterDateFrom.value && filterDateTo && filterDateTo.value) {{

          chipsHtml += `<span class="filter-chip">📅 ${{filterDateFrom.value}} to ${{filterDateTo.value}} <span class="filter-chip-remove" onclick="clearDateFilter()">✕</span></span>`;

        }}



        if (filterChat && filterChat.value !== 'all') {{

          const selOpt = filterChat.options[filterChat.selectedIndex];

          chipsHtml += `<span class="filter-chip">📂 ${{selOpt ? selOpt.textContent.slice(0, 25) : 'Chat'}} <span class="filter-chip-remove" onclick="clearChatFilter()">✕</span></span>`;

        }}



        if (filterComplexity && filterComplexity.value !== 'all') {{

          chipsHtml += `<span class="filter-chip">🎯 ${{filterComplexity.value === 'single' ? 'Single Q' : 'Multi Q'}} <span class="filter-chip-remove" onclick="clearComplexityFilter()">✕</span></span>`;

        }}



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



      // Render Chats: Dual Engine (Cards Explorer & Data Table)

      const chatsCardGrid = document.getElementById('chats-card-grid');



      function renderChats() {{

        const searchVal = (searchChats ? searchChats.value : '').toLowerCase().trim();

        const chatEntries = Object.entries(chats);

        if (summaryTbody) summaryTbody.innerHTML = '';

        if (chatsCardGrid) chatsCardGrid.innerHTML = '';

        let matchCount = 0;



        for (const [cid, chat] of chatEntries) {{

          const topic = chat.topic_summary || 'Untitled Conversation';

          const prompt = chat.last_user_prompt || '';

          const runs = chat.runs || [];



          const textMatch = !searchVal ||

            cid.toLowerCase().includes(searchVal) ||

            topic.toLowerCase().includes(searchVal) ||

            prompt.toLowerCase().includes(searchVal);



          if (!textMatch) continue;



          const matchingRuns = runs.filter(run => runMatchesFilters(cid, chat, run));

          const chatFilterMatch = runs.length > 0 ? (matchingRuns.length > 0) : (filterChat ? filterChat.value === 'all' || filterChat.value === cid : true);



          if (chatFilterMatch) {{

            matchCount++;

            const displayRunCount = runs.length > 0 ? matchingRuns.length : (chat.run_count || 0);

            const displayQsCount = runs.length > 0 ? matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0) : (chat.total_questions || 0);

            const lastTimeStr = chat.last_run_timestamp ? new Date(chat.last_run_timestamp).toLocaleString() : 'N/A';



            // 1. Classic Table Row (Full feature parity & test assertions)

            if (summaryTbody) {{

              const tr = document.createElement('tr');

              tr.innerHTML = `

                <td><span class="chat-id-tag">${{escapeHtml(cid)}}</span></td>

                <td><strong>${{escapeHtml(topic)}}</strong></td>

                <td><span class="badge-count">${{displayRunCount}}</span></td>

                <td><span class="badge-count">${{displayQsCount}}</span></td>

                <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">${{lastTimeStr}}</td>

              `;

              summaryTbody.appendChild(tr);

            }}



            // 2. High-Tech Visual Conversation Card (Modern Default Experience)

            if (chatsCardGrid) {{

              const card = document.createElement('div');

              card.className = 'modern-chat-card';

              card.innerHTML = `

                <div class="chat-card-top-row">

                  <div class="chat-avatar-badge">

                    <div class="chat-avatar-icon">🤖</div>

                    <span class="chat-id-tag" title="Click to copy ID" onclick="navigator.clipboard.writeText('${{escapeHtml(cid)}}'); showToast('Copied ID: ${{escapeHtml(cid)}}'); playChime('copy');" style="cursor: pointer;">${{escapeHtml(cid)}} 📋</span>

                  </div>

                  <span class="chat-metric-pill" style="color: var(--accent-emerald); border-color: rgba(16, 185, 129, 0.35); background: rgba(16, 185, 129, 0.08);">🟢 Automated</span>

                </div>



                <div>

                  <h3 class="chat-topic-title">${{escapeHtml(topic)}}</h3>

                  <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 6px; font-family: var(--font-mono);">

                    🕒 Last Active: ${{lastTimeStr}}

                  </div>

                </div>



                <div class="chat-metrics-bar">

                  <span class="chat-metric-pill">⚡ <strong>${{displayRunCount}}</strong> Runs</span>

                  <span class="chat-metric-pill">❓ <strong>${{displayQsCount}}</strong> Questions</span>

                  ${{prompt ? `<span class="chat-metric-pill" style="max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{escapeHtml(prompt)}}">💬 ${{escapeHtml(prompt)}}</span>` : ''}}

                </div>



                <div class="chat-card-actions">

                  <button type="button" class="btn-chat-action" onclick="jumpToChatQuestions('${{escapeHtml(cid)}}')">

                    <span>❓ View Questions (${{displayQsCount}})</span>

                  </button>

                  <button type="button" class="btn-chat-action" onclick="navigator.clipboard.writeText('${{escapeHtml(cid)}}'); showToast('Copied Conversation ID'); playChime('copy');">

                    <span>📋 Copy ID</span>

                  </button>

                </div>

              `;

              chatsCardGrid.appendChild(card);

            }}

          }}

        }}



        if (matchCount === 0) {{

          if (summaryTbody) {{

            summaryTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching chat records found.</td></tr>`;

          }}

          if (chatsCardGrid) {{

            chatsCardGrid.innerHTML = `

              <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; background: var(--bg-surface); border: 1px dashed var(--border-subtle); border-radius: var(--radius-lg);">

                <div style="font-size: 2.2rem; margin-bottom: 10px;">🔍</div>

                <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Matching Conversations</div>

                <div style="font-size: 0.84rem; color: var(--text-secondary);">Try clearing your search query or adjusting the date/speed filters above.</div>

              </div>

            `;

          }}

        }}

      }}



      window.setChatsView = function(view) {{

        localStorage.setItem('asc_chats_view', view);

        const cardsView = document.getElementById('chats-cards-view');

        const tableView = document.getElementById('chats-table-view');

        const btnCards = document.getElementById('btn-view-cards');

        const btnTable = document.getElementById('btn-view-table');



        if (view === 'table') {{

          if (cardsView) cardsView.style.display = 'none';

          if (tableView) tableView.style.display = 'block';

          if (btnCards) {{ btnCards.classList.remove('active'); btnCards.style.background = 'transparent'; btnCards.style.color = 'var(--text-secondary)'; }}

          if (btnTable) {{ btnTable.classList.add('active'); btnTable.style.background = 'var(--accent-indigo)'; btnTable.style.color = '#fff'; }}

        }} else {{

          if (cardsView) cardsView.style.display = 'block';

          if (tableView) tableView.style.display = 'none';

          if (btnCards) {{ btnCards.classList.add('active'); btnCards.style.background = 'var(--accent-indigo)'; btnCards.style.color = '#fff'; }}

          if (btnTable) {{ btnTable.classList.remove('active'); btnTable.style.background = 'transparent'; btnTable.style.color = 'var(--text-secondary)'; }}

        }}

      }};



      window.jumpToChatQuestions = function(cid) {{

        switchTab('questions');

        if (searchQuestions) {{

          searchQuestions.value = cid;

          applyFilters();

        }}

        showToast('Filtered Questions for conversation: ' + cid);

        playChime('copy');

      }};



      // Render Questions Cards (Developer Decision Studio with Modern Radio Option Cards)

      let currentQFilter = 'all';



      window.setQFilter = function(filterType, btn) {{

        currentQFilter = filterType;

        document.querySelectorAll('.q-filter-chip').forEach(b => b.classList.remove('active'));

        if (btn) btn.classList.add('active');

        renderQuestions();

      }};



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

            let questions = run.questions || [];

            if (currentQFilter === 'recommended') {{

              questions = questions.filter(q => (q.selected_option_text || '').includes('(Recommended)'));

              if (questions.length === 0) return false;

            }} else if (currentQFilter === 'multi') {{

              questions = questions.filter(q => (q.options || []).length > 2);

              if (questions.length === 0) return false;

            }}

            if (!searchVal) return true;

            if (cid.toLowerCase().includes(searchVal) || topic.toLowerCase().includes(searchVal)) return true;

            return questions.some(q =>

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

              let questions = run.questions || [];

              if (currentQFilter === 'recommended') {{

                questions = questions.filter(q => (q.selected_option_text || '').includes('(Recommended)'));

              }} else if (currentQFilter === 'multi') {{

                questions = questions.filter(q => (q.options || []).length > 2);

              }}



              let qHtml = '';

              questions.forEach((q, qIdx) => {{

                let optionsHtml = '';

                const isRecMatched = (q.selected_option_text || '').includes('(Recommended)');



                (q.options || []).forEach((opt, optIdx) => {{

                  const isSelected = (optIdx + 1 === q.selected_option_index) ||

                                     (q.selected_option_text && opt.trim() === q.selected_option_text.trim());

                  const isRec = opt.includes('(Recommended)');

                  optionsHtml += `

                    <div class="option-item ${{isSelected ? 'selected' : ''}}">

                      <div style="display:flex; align-items:center; gap:8px;">

                        <span style="font-size: 0.9rem; color: ${{isSelected ? 'var(--accent-emerald)' : 'var(--text-muted)'}};">${{isSelected ? '◉' : '○'}}</span>

                        <span><strong>${{optIdx + 1}}.</strong> ${{escapeHtml(opt)}}</span>

                      </div>

                      <div style="display:flex; gap:6px; align-items:center;">

                        ${{isSelected ? '<span class="option-badge">✓ Selected Decision</span>' : ''}}

                        ${{isRec ? '<span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:9999px; background:rgba(6,182,212,0.18); color:#22d3ee; border:1px solid rgba(6,182,212,0.4);">⭐ Recommended Choice</span>' : ''}}

                      </div>

                    </div>

                  `;

                }});



                qHtml += `

                  <div class="question-card ${{isRecMatched ? 'rec-matched' : ''}}" data-question-num="${{q.question_index || (qIdx + 1)}}">

                    <div class="question-prompt" onclick="toggleQuestionPrompt(this)">

                      <div class="question-prompt-left">

                        <span class="collapse-icon">▸</span>

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

                    <div class="options-list collapsed">

                      ${{optionsHtml}}

                    </div>

                  </div>

                `;

              }});



              runsHtml += `

                <div class="run-block" data-run-id="${{escapeHtml(run.run_id || '')}}">

                  <div class="run-header" onclick="toggleRunHeader(this)">

                    <div style="display: flex; align-items: center; gap: 8px;">

                      <span class="collapse-icon">▸</span>

                      <span style="font-weight: 700; color: var(--text-primary);">⚡ Run #${{rIdx + 1}} (${{escapeHtml(run.run_id || 'N/A')}})</span>

                    </div>

                    <div style="display: flex; align-items: center; gap: 12px;">

                      <span>Duration: ${{dur}} | ${{runDate}}</span>

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

              <div class="chat-card-header" onclick="toggleChatHeader(this)">

                <div class="chat-card-title">

                  <span class="collapse-icon">▸</span>

                  <span class="chat-id-tag">${{escapeHtml(cid)}}</span>

                  <span>${{escapeHtml(topic)}}</span>

                </div>

                <div class="chat-card-meta">

                  <span class="badge-count">${{matchingRuns.length}} run(s)</span>

                  <span class="badge-count">${{totalFilteredQs}} question(s)</span>

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



      window.copyQACard = function(btn) {{

        const q = decodeURIComponent(btn.getAttribute('data-q') || '');

        const ans = decodeURIComponent(btn.getAttribute('data-ans') || '');

        const text = `Question: ${{q}}\\nSelected Answer: ${{ans}}`;

        navigator.clipboard.writeText(text).then(() => {{

          playChime('copy');

          showToast('✅ Question & answer copied to clipboard!');

        }});

      }};



      // Global Expand All / Collapse All Questions

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



      // Preset buttons

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

            const dayOfWeek = (now.getDay() + 6) % 7;

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



      if (searchChats) searchChats.addEventListener('input', renderChats);

      if (searchQuestions) searchQuestions.addEventListener('input', renderQuestions);



      // ======================================================================

      // Tab-Contextual Keyboard Shortcut [/]

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



      // ======================================================================

      // 3-State Status Polling: Active, Paused (User Active), Inactive

      // ======================================================================

      const toggleBtn = document.getElementById('automation-toggle-btn');

      const controlIcon = document.getElementById('control-icon');

      const controlLabel = document.getElementById('control-label');

      const statusPill = document.getElementById('dashboard-status-pill');

      const statusText = document.getElementById('status-text');



      function updateStepProgress(step, isRunning, customPercent, customTitle) {{
        const progressBar = document.getElementById('header-progress-bar');
        const progressTrack = document.getElementById('header-progress-track');
        if (!progressBar) return;

        let pct = 0;
        let titleText = 'Pipeline Progress: Idle (0%)';

        if (!isRunning) {{
          pct = 0;
          titleText = 'Pipeline Progress: Idle (0%)';
          progressBar.classList.remove('active');
          progressBar.style.width = '0%';
          progressBar.style.opacity = '0';
          if (progressTrack) progressTrack.title = titleText;
          return;
        }}

        if (customPercent !== undefined && customPercent !== null) {{
          pct = Number(customPercent);
          titleText = customTitle || `Pipeline Progress: ${{pct}}%`;
        }} else {{
          // Default 4-step pipeline percentages
          switch (step) {{
            case 0:
              pct = 10;
              titleText = 'Step 0/4 Running: AntiGravity Detector (10%)';
              break;
            case 0.5:
              pct = 25;
              titleText = 'Step 0/4 Complete: AntiGravity Detected (25%)';
              break;
            case 1:
              pct = 35;
              titleText = 'Step 1/4 Running: Chat Identifier & Focus (35%)';
              break;
            case 1.5:
              pct = 50;
              titleText = 'Step 1/4 Complete: Chat Identifier & Focus (50%)';
              break;
            case 2:
              pct = 60;
              titleText = 'Step 2/4 Running: GUI Chat Select & Focus (60%)';
              break;
            case 2.5:
              pct = 75;
              titleText = 'Step 2/4 Complete: GUI Chat Select & Focus (75%)';
              break;
            case 3:
              pct = 85;
              titleText = 'Step 3/4 Running: Keyboard Automation (85%)';
              break;
            case 3.5:
            case 4:
              pct = 100;
              titleText = 'Step 3/4 Complete: Pipeline Finished (100%)';
              break;
            default:
              pct = 10;
              titleText = 'Pipeline Active • Step 0/4 (10%)';
              break;
          }}
        }}

        pct = Math.max(0, Math.min(100, pct));
        progressBar.classList.add('active');
        progressBar.style.width = pct + '%';
        progressBar.style.opacity = pct > 0 ? '1' : '0';
        if (progressTrack) progressTrack.title = customTitle || titleText;
      }}

      function detectStepFromLogLine(line) {{
        if (!line || typeof line !== 'string') return null;
        const upper = line.toUpperCase();

        if (upper.includes('PIPELINE COMPLETED SUCCESSFULLY') || upper.includes('[STEP 9.9]') || upper.includes('CYCLE COMPLETED')) {{
          return {{ step: 4, pct: 100, title: 'Pipeline Complete (100%)' }};
        }}
        if ((upper.includes('[STEP 9.8]') && upper.includes('STEP 3')) || upper.includes('STEP 3 COMPLETED') || upper.includes('KEYBOARD AUTOMATION COMPLETED')) {{
          return {{ step: 3.5, pct: 100, title: 'Step 3/4 Complete: Keyboard Automation (100%)' }};
        }}
        if (upper.includes('[STEP 3.') || upper.includes('[STEP 3:') || upper.includes('KEYBOARD AUTOMATION')) {{
          return {{ step: 3, pct: 85, title: 'Step 3/4 Running: Keyboard Automation (85%)' }};
        }}
        if ((upper.includes('[STEP 9.8]') && upper.includes('STEP 2')) || upper.includes('STEP 2 COMPLETED') || upper.includes('CHAT SELECTED')) {{
          return {{ step: 2.5, pct: 75, title: 'Step 2/4 Complete: GUI Chat Select & Focus (75%)' }};
        }}
        if (upper.includes('[STEP 2.') || upper.includes('[STEP 2:') || upper.includes('GUI CHAT SELECT') || upper.includes('SELECTING TARGET CHAT')) {{
          return {{ step: 2, pct: 60, title: 'Step 2/4 Running: GUI Chat Select & Focus (60%)' }};
        }}
        if ((upper.includes('[STEP 9.8]') && upper.includes('STEP 1')) || upper.includes('STEP 1 COMPLETED') || upper.includes('[STEP 9.14]')) {{
          return {{ step: 1.5, pct: 50, title: 'Step 1/4 Complete: Chat Identifier & Focus (50%)' }};
        }}
        if (upper.includes('[STEP 1.') || upper.includes('[STEP 1:') || upper.includes('CHAT IDENTIFIER') || upper.includes('IDENTIFYING ACTIVE CHAT')) {{
          return {{ step: 1, pct: 35, title: 'Step 1/4 Running: Chat Identifier & Focus (35%)' }};
        }}
        if (upper.includes('TRIGGER MATCHED') || upper.includes('[STEP 9.12]') || upper.includes('ANTIGRAVITY DETECTED')) {{
          return {{ step: 0.5, pct: 25, title: 'Step 0/4 Complete: AntiGravity Detected (25%)' }};
        }}
        if (upper.includes('[STEP 0.') || upper.includes('DETECTOR_POLL') || upper.includes('[STEP 9.10]') || upper.includes('POLLING ANTIGRAVITY')) {{
          return {{ step: 0, pct: 10, title: 'Step 0/4 Running: AntiGravity Detector (10%)' }};
        }}
        if (upper.includes('[STEP 9.')) {{
          return {{ step: 0, pct: 10, title: 'Pipeline Active • Step 0/4 (10%)' }};
        }}
        return null;
      }}

      function updateStatusUI(running, isPaused, idleSec, threshold, currentStep, stepPercent, stepTitle) {{

        isAutomationActive = running;

        if (!running) {{
          updateStepProgress(null, false, 0, 'Pipeline Progress: Idle (0%)');
        }} else if (stepPercent !== undefined && stepPercent !== null) {{
          updateStepProgress(currentStep, true, stepPercent, stepTitle);
        }}

        if (toggleBtn) {{

          toggleBtn.classList.toggle('state-running', running);

          toggleBtn.classList.toggle('state-stopped', !running);

          controlIcon.textContent = running ? '⏹️' : '▶️';

          controlLabel.textContent = running ? 'Stop Automation' : 'Start Automation';

        }}

        const modesToggleBtn = document.getElementById('modes-automation-toggle-btn');

        const modesCtrlIcon = document.getElementById('modes-control-icon');

        const modesCtrlLabel = document.getElementById('modes-control-label');

        const modesStatusPill = document.getElementById('modes-status-pill');



        if (modesToggleBtn) {{

          modesToggleBtn.classList.toggle('state-running', running);

          modesToggleBtn.classList.toggle('state-stopped', !running);

          if (modesCtrlIcon) modesCtrlIcon.textContent = running ? '⏹️' : '▶️';

          if (modesCtrlLabel) modesCtrlLabel.textContent = running ? 'Stop Automation' : 'Start Automation';

        }}



        if (modesStatusPill) {{

          if (running) {{

            if (isPaused) {{

              modesStatusPill.className = 'status-pill status-paused';

              modesStatusPill.textContent = '🟡 Paused (User Active)';

            }} else {{

              modesStatusPill.className = 'status-pill status-active';

              modesStatusPill.textContent = '🟢 Active (Autonomous)';

            }}

          }} else {{

            modesStatusPill.className = 'status-pill status-idle';

            modesStatusPill.textContent = '⚪ Automation Inactive';

          }}

        }}



        if (statusPill && statusText) {{

          if (running) {{

            if (isPaused) {{

              statusPill.className = 'status-pill status-paused';

              statusText.textContent = '🟡 Paused (User Active)';

              statusPill.title = `Automation paused: user input detected (idle: ${{idleSec || 0}}s < ${{threshold || 60}}s)`;

              if (tickerStatusMsg) {{

                tickerStatusMsg.textContent = `[PAUSED] User activity detected (idle: ${{idleSec || 0}}s < ${{threshold || 60}}s) • Automation sleeping until 60s inactivity`;

              }}

            }} else {{

              statusPill.className = 'status-pill status-active';

              statusText.textContent = '🟢 Active (Autonomous)';

              statusPill.title = 'Automation active: autonomous background monitoring enabled';

              if (tickerStatusMsg) {{

                tickerStatusMsg.textContent = `[ACTIVE] Autonomous engine executing • Background monitoring live (PID: active)`;

              }}

            }}

          }} else {{

            statusPill.className = 'status-pill status-idle';

            statusText.textContent = '⚪ Inactive';

            statusPill.title = 'Automation stopped: daemon ready to spawn';

            if (tickerStatusMsg) {{

              tickerStatusMsg.textContent = `Complete Automation Daemon Ready • Ready to spawn complete_automation.py`;

            }}

          }}

        }}

        syncHeaderActionButton(running);

      }}

      function syncHeaderActionButton(running) {{
        const btnHeaderRefresh = document.getElementById('btn-header-refresh');
        const spinIcon = document.getElementById('refresh-spin-icon');
        const liveFeedDot = document.getElementById('live-feed-dot');
        const liveFeedBadge = document.getElementById('live-feed-badge');
        const liveFeedCard = document.getElementById('onpage-live-feed-card');
        const headerProgressBar = document.getElementById('header-progress-bar');

        if (liveFeedDot) liveFeedDot.classList.toggle('active', running);
        if (liveFeedCard) liveFeedCard.classList.toggle('active-event', running);
        if (liveFeedBadge) {{
          liveFeedBadge.textContent = running ? 'RUNNING' : 'IDLE';
          liveFeedBadge.style.color = running ? '#10b981' : 'var(--text-muted)';
          liveFeedBadge.style.borderColor = running ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-subtle)';
        }}

        if (!running) {{
          updateStepProgress(null, false, 0, 'Pipeline Progress: Idle (0%)');
        }}

        if (!btnHeaderRefresh) return;

        if (running) {{
          btnHeaderRefresh.classList.add('btn-event-active');
          btnHeaderRefresh.title = 'Automation Running in Background • Click to Refresh Telemetry';
          if (spinIcon) {{
            spinIcon.textContent = '🔄';
            spinIcon.style.display = 'inline-block';
            spinIcon.style.animation = 'spin 1.2s linear infinite';
          }}
        }} else {{
          btnHeaderRefresh.classList.remove('btn-event-active');
          btnHeaderRefresh.title = 'Synchronous Telemetry Refresh from Disk';
          if (spinIcon) {{
            spinIcon.textContent = '🔄';
            spinIcon.style.display = 'inline-block';
            spinIcon.style.animation = 'none';
          }}
        }}
      }}



      function pollServerStatus() {{

        fetch(API_BASE + '/api/automation/status')

          .then(res => res.json())

          .then(data => {{

            if (data && data.success && data.data) {{

              const d = data.data;

              updateStatusUI(!!d.running, !!d.is_paused, d.idle_seconds, d.pause_threshold, d.current_step, d.step_percent, d.step_title);

              if (d.mode && typeof d.mode === 'string') {{

                const serverMode = d.mode.trim().toLowerCase();

                if (Date.now() - lastUserModeChangeTime > 4000) {{

                  if (serverMode !== currentExecutionMode.toLowerCase()) {{

                    currentExecutionMode = serverMode;

                    applyExecutionModeUI(currentExecutionMode);

                  }}

                }}

              }}

            }}

          }})

          .catch(() => {{}});

      }}

      setInterval(pollServerStatus, 2500);



      // Server-Sent Events (SSE) Live Status Stream with fallback to polling (Phase 03)

      try {{

        if (typeof EventSource !== 'undefined') {{

          const eventSource = new EventSource(API_BASE + '/api/automation/events');

          eventSource.addEventListener('status', (e) => {{

            try {{

              const payload = JSON.parse(e.data);

              if (payload && payload.success && payload.data) {{

                const d = payload.data;

                updateStatusUI(!!d.running, !!d.is_paused, d.idle_seconds, d.pause_threshold, d.current_step, d.step_percent, d.step_title);

                if (d.mode && typeof d.mode === 'string') {{

                  const serverMode = d.mode.trim().toLowerCase();

                  if (serverMode !== currentExecutionMode.toLowerCase()) {{

                    currentExecutionMode = serverMode;

                    applyExecutionModeUI(currentExecutionMode);

                  }}

                }}

              }}

            }} catch (_) {{}}

          }});

          eventSource.addEventListener('log', (e) => {{
            try {{
              const payload = JSON.parse(e.data);
              if (payload && Array.isArray(payload.lines) && payload.lines.length > 0) {{
                appendLiveFeedLines(payload.lines, payload.timestamp, !!payload.initial);
                if (payload.total_lines !== undefined && logBadge) {{
                  logBadge.textContent = payload.total_lines;
                }}
              }}
            }} catch (_) {{}}
          }});

          // 1. Task Start Event: Wire active WIP UI state immediately
          eventSource.addEventListener('task_start', (e) => {{
            try {{
              const payload = JSON.parse(e.data);
              const d = payload.data || {{}};
              isAutomationActive = true;
              syncHeaderActionButton(true);
              updateStatusUI(true, false, d.idle_seconds || 0, d.pause_threshold || 60, 0, 10, 'Stage 0: Pre-Flight');
              const tickerStatusMsg = document.getElementById('ticker-status-msg');
              if (tickerStatusMsg) {{
                tickerStatusMsg.textContent = '🚀 Task Started • AutoSelect Antigravity Automation Active';
              }}
              showToast('🚀 Automation task started!', 'success');
              playChime('start');
            }} catch (_) {{}}
          }});

          // 2. Stage Transition Event: Update stage progress and ticker reactively
          eventSource.addEventListener('stage_transition', (e) => {{
            try {{
              const payload = JSON.parse(e.data);
              const stageNum = payload.stage;
              const stageName = payload.stage_name || `Stage ${{stageNum}}`;
              isAutomationActive = true;
              syncHeaderActionButton(true);
              const tickerStatusMsg = document.getElementById('ticker-status-msg');
              if (tickerStatusMsg) {{
                tickerStatusMsg.textContent = `⚡ ${{stageName}} • Active`;
              }}
              let pct = 10;
              if (stageNum === 1) pct = 25;
              else if (stageNum === 2) pct = 50;
              else if (stageNum === 3) pct = 75;
              else if (stageNum === 4) pct = 95;
              else if (stageNum === 9) pct = 15;
              updateStepProgress(stageNum, true, pct, `${{stageName}} (${{pct}}%)`);
              showToast(`⚡ ${{stageName}} in progress...`, 'info');
            }} catch (_) {{}}
          }});

          // 3. Active WIP Telemetry Event: Update elapsed time & status without page reload
          eventSource.addEventListener('active_wip', (e) => {{
            try {{
              const payload = JSON.parse(e.data);
              const d = payload.data || {{}};
              const stageName = payload.stage_name || 'Active Execution';
              isAutomationActive = true;
              syncHeaderActionButton(true);
              const tickerStatusMsg = document.getElementById('ticker-status-msg');
              if (tickerStatusMsg && !d.is_paused) {{
                const elapsed = payload.elapsed_seconds ? ` (${{payload.elapsed_seconds}}s elapsed)` : '';
                tickerStatusMsg.textContent = `🔄 ${{stageName}}${{elapsed}} • Automation Running`;
              }}
              if (d.mode && typeof d.mode === 'string') {{
                const serverMode = d.mode.trim().toLowerCase();
                if (serverMode !== currentExecutionMode.toLowerCase()) {{
                  currentExecutionMode = serverMode;
                  applyExecutionModeUI(currentExecutionMode);
                }}
              }}
            }} catch (_) {{}}
          }});

          // 4. Task Complete Event: Stop spinner, update status pill, cleanly sync history
          eventSource.addEventListener('task_complete', (e) => {{
            try {{
              const payload = JSON.parse(e.data);
              isAutomationActive = false;
              syncHeaderActionButton(false);
              updateStepProgress(null, false, 0, 'Pipeline Progress: Completed (100%)');
              updateStatusUI(false, false, 0, 60);
              const tickerStatusMsg = document.getElementById('ticker-status-msg');
              if (tickerStatusMsg) {{
                tickerStatusMsg.textContent = '✅ Automation Task Completed • Telemetry Synced';
              }}
              showToast('✅ Automation completed! Updating telemetry...', 'success');
              playChime('stop');
              setTimeout(() => {{
                location.reload();
              }}, 800);
            }} catch (_) {{}}
          }});

          eventSource.onerror = () => {{

            // On error or disconnect, EventSource auto-retries while setInterval polling provides fallback

          }};

        }}

      }} catch (_) {{}}



      if (toggleBtn) {{

        toggleBtn.addEventListener('click', () => {{

          const endpoint = isAutomationActive ? '/api/automation/stop' : '/api/automation/start';

          toggleBtn.disabled = true;

          const bodyPayload = isAutomationActive ? {{}} : {{ mode: currentExecutionMode }};

          fetch(API_BASE + endpoint, {{

            method: 'POST',

            headers: {{ 'Content-Type': 'application/json' }},

            body: JSON.stringify(bodyPayload)

          }})

            .then(res => res.json())

            .then(data => {{

              toggleBtn.disabled = false;

              if (data.success) {{

                playChime(isAutomationActive ? 'stop' : 'start');

                showToast(isAutomationActive ? '⏹️ Automation stopped' : `▶️ Automation started in ${{currentExecutionMode.toUpperCase()}} mode!`);

                pollServerStatus();

              }}

            }})

            .catch(() => {{

              toggleBtn.disabled = false;

              showToast('❌ Server request failed. Ensure server is running on port 8501');

            }});

        }});

      }}



      // Live Logs Drawer

      const logsDrawer = document.getElementById('logs-drawer');

      const btnToggleLogs = document.getElementById('btn-toggle-logs');

      const btnCloseLogs = document.getElementById('btn-close-logs');

      const logsTerminal = document.getElementById('logs-terminal');

      const logBadge = document.getElementById('log-count-badge');

      let logsInterval = null;

      // Real-time on-page activity feed elements
      const liveFeedStream = document.getElementById('live-feed-stream');
      const liveFeedTime = document.getElementById('live-feed-time');
      const btnFeedOpenDrawer = document.getElementById('btn-feed-open-drawer');
      let liveFeedHistory = [];

      if (btnFeedOpenDrawer) {{
        btnFeedOpenDrawer.addEventListener('click', () => {{
          toggleLogs(true);
        }});
      }}

      function formatLogLineHTML(rawLine) {{
        let cls = '';
        const upper = rawLine.toUpperCase();
        if (upper.includes('[ERROR]') || upper.includes('ERROR:')) cls = 'log-line-err';
        else if (upper.includes('[WARNING]') || upper.includes('[WARN]')) cls = 'log-line-warn';
        else if (upper.includes('[SUCCESS]') || upper.includes('PASSED') || upper.includes('SUCCESS:')) cls = 'log-line-ok';
        else if (upper.includes('[STEP') || upper.includes('STEP 0') || upper.includes('STEP 1') || upper.includes('STEP 2') || upper.includes('STEP 3') || upper.includes('STEP 4') || upper.includes('STEP 9')) cls = 'log-line-step';
        else if (upper.includes('[INFO]')) cls = 'log-line-info';

        const escaped = rawLine.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<div class="${{cls}}">${{escaped}}</div>`;
      }}

      function appendLiveFeedLines(newLines, timestamp, isInitial) {{
        if (!Array.isArray(newLines) || newLines.length === 0) return;

        for (let i = 0; i < newLines.length; i++) {{
          const detected = detectStepFromLogLine(newLines[i]);
          if (detected) {{
            updateStepProgress(detected.step, true, detected.pct, detected.title);
          }}
        }}

        if (liveFeedTime) {{
          const nowStr = timestamp ? (new Date(timestamp).toLocaleTimeString()) : (new Date().toLocaleTimeString());
          liveFeedTime.textContent = 'Updated ' + nowStr;
        }}

        if (isInitial) {{
          liveFeedHistory = newLines.slice(-20);
        }} else {{
          newLines.forEach(l => {{
            liveFeedHistory.push(l);
            if (liveFeedHistory.length > 80) liveFeedHistory.shift();
          }});
        }}

        if (liveFeedStream) {{
          const recentToShow = liveFeedHistory.slice(-5);
          let html = '';
          recentToShow.forEach(l => {{
            let cls = '';
            const upper = l.toUpperCase();
            if (upper.includes('[ERROR]') || upper.includes('ERROR:')) cls = 'log-line-err';
            else if (upper.includes('[WARNING]') || upper.includes('[WARN]')) cls = 'log-line-warn';
            else if (upper.includes('[SUCCESS]') || upper.includes('PASSED') || upper.includes('SUCCESS:')) cls = 'log-line-ok';
            else if (upper.includes('[STEP') || upper.includes('STEP 0') || upper.includes('STEP 1') || upper.includes('STEP 2') || upper.includes('STEP 3') || upper.includes('STEP 4') || upper.includes('STEP 9')) cls = 'log-line-step';
            else if (upper.includes('[INFO]')) cls = 'log-line-info';

            const escaped = l.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            html += `<div class="live-feed-item"><span class="live-feed-msg ${{cls}}">${{escaped}}</span></div>`;
          }});
          liveFeedStream.innerHTML = html;
          liveFeedStream.scrollTop = liveFeedStream.scrollHeight;
        }}

        if (logsTerminal) {{
          const wasAtBottom = (logsTerminal.scrollHeight - logsTerminal.scrollTop - logsTerminal.clientHeight) <= 50;
          let drawerHtml = '';
          liveFeedHistory.forEach(l => {{
            drawerHtml += formatLogLineHTML(l);
          }});
          logsTerminal.innerHTML = drawerHtml;
          if (wasAtBottom) logsTerminal.scrollTop = logsTerminal.scrollHeight;
        }}
      }}



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

                lines = data.data.logs.split(/\\r?\\n/).map(l => l.trim()).filter(l => l.length > 0);

              }} else if (typeof data.data.raw === 'string') {{

                lines = data.data.raw.split(/\\r?\\n/).map(l => l.trim()).filter(l => l.length > 0);

              }}

            }}

            logLines = lines.length;

            if (logBadge) logBadge.textContent = logLines;
            appendLiveFeedLines(lines, null, true);
            if (!logsOpen) return;

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
          fetch(API_BASE + '/api/logs/clear', {{ method: 'POST' }})
            .then(res => res.json())
            .then(d => {{
              if (logsTerminal) logsTerminal.innerHTML = '<div style="color: #64748b; padding: 6px;">Console cleared. Waiting for next stream tick...</div>';
              logLines = 0;
              if (logBadge) logBadge.textContent = '0';
              showToast('Logs cleared successfully.');
            }})
            .catch(err => {{
              if (logsTerminal) logsTerminal.innerHTML = '<div style="color: #64748b; padding: 6px;">Console cleared locally.</div>';
              logLines = 0;
              if (logBadge) logBadge.textContent = '0';
            }});
        }});
      }}



      // Mode Switch Controls (Ultra-Modern Interactive Lifecycle Standard)

      const btnSetProd = document.getElementById('btn-set-prod');

      const btnSetTest = document.getElementById('btn-set-test');

      const cardProd = document.getElementById('mode-card-prod') || document.getElementById('banner-card-prod');

      const cardTest = document.getElementById('mode-card-test') || document.getElementById('banner-card-test');

      const bannerBtnProd = document.getElementById('banner-mode-prod-btn');

      const bannerBtnTest = document.getElementById('banner-mode-test-btn');

      const modesToggleBtn = document.getElementById('modes-automation-toggle-btn');



      let lastUserModeChangeTime = 0;

      let currentExecutionMode = localStorage.getItem('asc_execution_mode') || '{current_mode}';



      function applyExecutionModeUI(mode) {{

        const isTest = (String(mode).toLowerCase() === 'test');

        currentExecutionMode = isTest ? 'test' : 'production';

        localStorage.setItem('asc_execution_mode', currentExecutionMode);

        localStorage.setItem('asc_automation_last_mode', currentExecutionMode);



        // Header Mode Badge Dynamic Sync (Phase 03)

        const headerModeBadge = document.getElementById('header-mode-badge');

        if (headerModeBadge) {{

          headerModeBadge.innerHTML = isTest ? '🧪 TEST' : '⚡ LIVE';

          headerModeBadge.style.background = isTest ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)';

          headerModeBadge.style.color = isTest ? '#fbbf24' : '#34d399';

          headerModeBadge.style.borderColor = isTest ? 'rgba(245, 158, 11, 0.35)' : 'rgba(16, 185, 129, 0.35)';

          headerModeBadge.title = isTest ? 'Operating in Single-Run Test Mode (Auto-Stop on Completion) • Click to toggle to LIVE' : 'Operating in Continuous Live Mode (Continuous Loop) • Click to toggle to TEST';

        }}



        // 1. Update Segmented Switcher Buttons

        const bannerProd = document.getElementById('banner-mode-prod-btn');

        const bannerTest = document.getElementById('banner-mode-test-btn');

        if (bannerProd) bannerProd.classList.toggle('active', !isTest);

        if (bannerTest) bannerTest.classList.toggle('active', isTest);



        // 2. Update Interactive Lifecycle Cards Highlight

        const cProd = document.getElementById('mode-card-prod') || document.getElementById('banner-card-prod');

        const cTest = document.getElementById('mode-card-test') || document.getElementById('banner-card-test');

        if (cProd) cProd.classList.toggle('active-mode-card', !isTest);

        if (cTest) cTest.classList.toggle('active-mode-card', isTest);



        // 3. Update Active Mode Label and Indicator Dot

        const activeDot = document.getElementById('modes-active-dot');

        const activeText = document.getElementById('modes-active-text');

        if (activeDot) activeDot.style.color = isTest ? '#f59e0b' : '#10b981';

        if (activeText) {{

          activeText.innerHTML = `Active Operating Mode: <strong>${{isTest ? 'TEST (परीक्षण मोड)' : 'PRODUCTION (उत्पादन मोड)'}}</strong>`;

        }}



        // 4. Update Mode Switch Tab Badge in Horizontal Tab Navigation

        const tabBadge = document.getElementById('tab-modes-badge');

        if (tabBadge) {{

          tabBadge.textContent = isTest ? 'Test' : 'Prod';

          tabBadge.style.background = isTest ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)';

          tabBadge.style.color = isTest ? '#fbbf24' : '#34d399';

        }}



        // 5. Update Lifecycle Card Badges

        const badgeTxtProd = document.getElementById('mode-badge-text-prod');

        const badgeTxtTest = document.getElementById('mode-badge-text-test');

        if (badgeTxtProd) badgeTxtProd.textContent = !isTest ? 'CURRENT ACTIVE' : 'Continuous Loop';

        if (badgeTxtTest) badgeTxtTest.textContent = isTest ? 'CURRENT ACTIVE' : 'Single-Run Auto-Stop';



        // 6. Update Card Action Buttons

        const bSetProd = document.getElementById('btn-set-prod');

        const bSetTest = document.getElementById('btn-set-test');

        if (bSetProd) {{

          bSetProd.textContent = !isTest ? '✓ Active in Production' : '⚡ Switch to Production Mode';

          bSetProd.className = `lifecycle-card-btn ${{!isTest ? 'btn-automation' : 'btn'}}`;

        }}

        if (bSetTest) {{

          bSetTest.textContent = isTest ? '✓ Active in Test Mode' : '⚡ Switch to Test Mode';

          bSetTest.className = `lifecycle-card-btn ${{isTest ? 'btn-automation' : 'btn'}}`;

          bSetTest.style.background = isTest ? '#d97706' : 'rgba(245,158,11,0.18)';

          bSetTest.style.color = isTest ? '#ffffff' : '#fbbf24';

        }}

      }}



      function switchMode(newMode) {{

        const isTest = (newMode === 'test');

        lastUserModeChangeTime = Date.now();

        playChime('copy');

        applyExecutionModeUI(newMode);

        showToast(isTest ? '🧪 Activated Test Mode (Single-Run & Auto-Stop)' : '⚡ Activated Live Mode (Continuous Autonomous Loop)');



        // Background server persistence & silent dashboard refresh

        let payload = {{ mode: newMode }};

        try {{

          const full = collectConfigData();

          payload = Object.assign({{}}, full, {{ mode: newMode }});

        }} catch (_) {{}}



        fetch(API_BASE + '/api/config/save', {{

          method: 'POST',

          headers: {{ 'Content-Type': 'application/json' }},

          body: JSON.stringify(payload)

        }})

        .then(res => res.json())

        .then(() => {{

          fetch(API_BASE + '/api/dashboard/refresh', {{ method: 'POST' }}).catch(() => {{}});

        }})

        .catch(() => {{}});

      }}



      if (btnSetProd) btnSetProd.addEventListener('click', (e) => {{ e.stopPropagation(); switchMode('production'); }});

      if (btnSetTest) btnSetTest.addEventListener('click', (e) => {{ e.stopPropagation(); switchMode('test'); }});

      if (cardProd) cardProd.addEventListener('click', () => switchMode('production'));

      if (cardTest) cardTest.addEventListener('click', () => switchMode('test'));

      if (bannerBtnProd) bannerBtnProd.addEventListener('click', () => switchMode('production'));

      if (bannerBtnTest) bannerBtnTest.addEventListener('click', () => switchMode('test'));



      // Direct Header Mode Badge Click & Keydown to toggle mode

      const headerModeBadgeEl = document.getElementById('header-mode-badge');

      if (headerModeBadgeEl) {{

        headerModeBadgeEl.addEventListener('click', () => {{

          const nextMode = (currentExecutionMode === 'test') ? 'production' : 'test';

          switchMode(nextMode);

        }});

        headerModeBadgeEl.addEventListener('keydown', (e) => {{

          if (e.key === 'Enter' || e.key === ' ') {{

            e.preventDefault();

            headerModeBadgeEl.click();

          }}

        }});

      }}



      if (modesToggleBtn) {{

        modesToggleBtn.addEventListener('click', () => {{

          if (toggleBtn) toggleBtn.click();

        }});

      }}



      // Config Form Handling & JSON Drawer

      const btnToggleJson = document.getElementById('btn-toggle-json-drawer');

      const jsonDrawer = document.getElementById('json-preview-container');

      if (btnToggleJson && jsonDrawer) {{

        btnToggleJson.addEventListener('click', () => {{

          const isHidden = jsonDrawer.style.display === 'none';

          jsonDrawer.style.display = isHidden ? 'block' : 'none';

          btnToggleJson.textContent = isHidden ? 'Hide Preview' : 'Toggle Preview';

        }});

      }}



      function collectConfigData() {{

        const reqGrill = document.getElementById('cfg-antigravity-require-grillme');

        const actHrs = document.getElementById('cfg-antigravity-active-hours');

        const logVerb = document.getElementById('cfg-logging-verbose');

        const logF = document.getElementById('cfg-logging-file');



        return {{

          mode: currentExecutionMode,

          timing: {{

            step0_poll_interval_prod_seconds: parseFloat(document.getElementById('cfg-timing-prod-poll').value) || 1.0,

            step0_poll_interval_test_seconds: parseFloat(document.getElementById('cfg-timing-test-poll').value) || 0.1,

            settle_delay_between_steps_seconds: parseFloat(document.getElementById('cfg-timing-settle').value) || 1.0,

            user_activity_pause_threshold_seconds: parseFloat(document.getElementById('cfg-pause-threshold').value) || 60.0,

            step4_user_activity_delay_seconds: parseFloat(document.getElementById('cfg-timing-activity-delay').value) || 10.0,

            step4_poll_interval_seconds: parseFloat(document.getElementById('cfg-timing-step4-poll').value) || 0.5,

            step1_window_focus_delay_seconds: parseFloat(document.getElementById('cfg-timing-step1-focus').value) || 0.5,

            step2_dom_click_settle_delay_seconds: parseFloat(document.getElementById('cfg-timing-step2-dom-settle').value) || 1.0,

            step3_countdown_seconds: parseInt(document.getElementById('cfg-timing-step3-countdown').value, 10) || 3,

            step3_key_hold_delay_ms: parseInt(document.getElementById('cfg-timing-step3-hold-ms').value, 10) || 80,

            step3_post_keypress_delay_ms: parseInt(document.getElementById('cfg-timing-step3-post-ms').value, 10) || 100,

            step3_inter_question_delay_ms: parseInt(document.getElementById('cfg-timing-step3-inter-q-ms').value, 10) || 200,

            step3_round_completion_pause_ms: parseInt(document.getElementById('cfg-timing-step3-round-ms').value, 10) || 500,

            continuous_loop_delay_seconds: parseFloat(document.getElementById('cfg-continuous-delay').value) || 300.0,

          }},

          enabled_steps: {{

            step1_find_and_focus: document.getElementById('cfg-step1-enabled').checked,

            step2_gui_chat_select: document.getElementById('cfg-step2-enabled').checked,

            step3_keyboard_automation: document.getElementById('cfg-step3-enabled').checked,

            step4_reporting: document.getElementById('cfg-step4-enabled').checked,

          }},

          antigravity: {{

            require_grill_me: reqGrill ? reqGrill.checked : true,

            active_hours: actHrs ? (parseFloat(actHrs.value) || 12.0) : 12.0,

          }},

          logging: {{

            verbose: logVerb ? logVerb.checked : true,

            log_file: logF ? logF.value.trim() : 'complete_automation.log',

          }}

        }};

      }}



      function saveConfigChanges() {{

        const payload = collectConfigData();

        fetch(API_BASE + '/api/config/save', {{

          method: 'POST',

          headers: {{ 'Content-Type': 'application/json' }},

          body: JSON.stringify(payload)

        }})

        .then(res => res.json())

        .then(d => {{

          playChime('copy');

          showToast('✅ Configuration successfully saved to config.json!');

          const unsavedDock = document.getElementById('unsaved-changes-dock');

          if (unsavedDock) unsavedDock.classList.remove('visible');

          setTimeout(() => location.reload(), 800);

        }})

        .catch(() => showToast('❌ Failed to save configuration to local server.'));

      }}



      const btnSaveRuntimeCfg = document.getElementById('btn-save-runtime-config');

      const btnSaveDock = document.getElementById('btn-save-config-dock');

      if (btnSaveRuntimeCfg) btnSaveRuntimeCfg.addEventListener('click', saveConfigChanges);

      if (btnSaveDock) btnSaveDock.addEventListener('click', saveConfigChanges);



      // Copy CLI Command

      const btnCopyCli = document.getElementById('btn-copy-cli-cmd');

      if (btnCopyCli) {{

        btnCopyCli.addEventListener('click', () => {{

          const cmd = 'python step_9_complete_automation/complete_automation.py';

          navigator.clipboard.writeText(cmd).then(() => {{

            playChime('copy');

            showToast('📋 Copied CLI command to clipboard!');

          }});

        }});

      }}



      // Download config.json directly

      const btnDownloadCfg = document.getElementById('btn-download-runtime-cfg');

      if (btnDownloadCfg) {{

        btnDownloadCfg.addEventListener('click', () => {{

          const payload = collectConfigData();

          const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'config.json';

          a.click();

          URL.revokeObjectURL(url);

          playChime('copy');

          showToast('📥 Downloaded config.json successfully.');

        }});

      }}



      // Export Configuration JSON

      const btnExportCfg = document.getElementById('btn-export-config');

      if (btnExportCfg) {{

        btnExportCfg.addEventListener('click', () => {{

          const payload = collectConfigData();

          const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'config_export.json';

          a.click();

          URL.revokeObjectURL(url);

          showToast('📤 Configuration JSON exported.');

        }});

      }}



      // Export History JSON

      const btnExportHist = document.getElementById('cfg-export-btn');

      if (btnExportHist) {{

        btnExportHist.addEventListener('click', () => {{

          const blob = new Blob([JSON.stringify(rawData, null, 2)], {{ type: 'application/json' }});

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'automation_history.json';

          a.click();

          URL.revokeObjectURL(url);

          playChime('copy');

          showToast('📥 Exported automation_history.json successfully.');

        }});

      }}



      // Reset Dashboard Preferences

      const btnResetDash = document.getElementById('cfg-reset-btn');

      if (btnResetDash) {{

        btnResetDash.addEventListener('click', () => {{

          localStorage.removeItem('asc_theme');

          localStorage.removeItem('asc_dashboard_tab');

          localStorage.removeItem('asc_audio_muted');

          showToast('🔄 Dashboard preferences reset to factory defaults.');

          setTimeout(() => location.reload(), 500);

        }});

      }}



      // Test Audio Chime Audition

      const btnTestChime = document.getElementById('btn-test-chime');

      if (btnTestChime) {{

        btnTestChime.addEventListener('click', () => {{

          playChime('start');

          setTimeout(() => playChime('copy'), 220);

          showToast('🔔 Web Audio Chime played!');

        }});

      }}



      // Filter Toolbar Collapse / Expand Toggle

      const filterCollapseBtn = document.getElementById('filter-collapse-btn');

      const filterToolbar = document.getElementById('contextual-filter-toolbar');

      if (filterCollapseBtn && filterToolbar) {{

        filterCollapseBtn.addEventListener('click', () => {{

          const isCollapsed = filterToolbar.classList.toggle('collapsed');

          filterCollapseBtn.textContent = isCollapsed ? '▸ Expand' : '▾ Collapse';

        }});

      }}



      // 1-Click Automation Scripts Modal Controls

      const automationModal = document.getElementById('automation-modal');

      const btnOpenAutoModal = document.getElementById('btn-open-automation-modal');

      const btnCloseAutoModal = document.getElementById('btn-close-automation-modal');

      const btnCloseAutoFooter = document.getElementById('btn-close-automation-modal-footer');



      if (btnOpenAutoModal && automationModal) {{

        btnOpenAutoModal.addEventListener('click', () => automationModal.classList.add('open'));

      }}

      if (btnCloseAutoModal && automationModal) {{

        btnCloseAutoModal.addEventListener('click', () => automationModal.classList.remove('open'));

      }}

      if (btnCloseAutoFooter && automationModal) {{

        btnCloseAutoFooter.addEventListener('click', () => automationModal.classList.remove('open'));

      }}



      // Copy buttons inside automation modal

      document.querySelectorAll('.btn-copy-cmd').forEach(btn => {{

        btn.addEventListener('click', () => {{

          const cmd = btn.getAttribute('data-cmd') || '';

          navigator.clipboard.writeText(cmd).then(() => {{

            playChime('copy');

            showToast('📋 Copied script command to clipboard: ' + cmd);

          }});

        }});

      }});



      // Dual-State Header Refresh Button via Server API
      const btnHeaderRefresh = document.getElementById('btn-header-refresh');

      if (btnHeaderRefresh) {{
        btnHeaderRefresh.addEventListener('click', () => {{
          btnHeaderRefresh.disabled = true;
          const spinIcon = document.getElementById('refresh-spin-icon');
          if (spinIcon) {{
            spinIcon.style.display = 'inline-block';
            spinIcon.style.animation = 'spin 0.6s linear infinite';
          }}
          showToast('🔄 Synchronizing telemetry from disk and regenerating dashboard...');
          fetch(API_BASE + '/api/dashboard/refresh', {{ method: 'POST' }})
            .then(res => res.json())
            .then(d => {{
              playChime('copy');
              showToast('✅ Telemetry synchronized! Reloading...');
              setTimeout(() => location.reload(), 400);
            }})
            .catch(() => {{
              location.reload();
            }});
        }});
      }}



      // Config Unsaved Dock

      const unsavedDock = document.getElementById('unsaved-changes-dock');

      const cfgInputs = document.querySelectorAll('.cfg-input, .switch-toggle input');

      cfgInputs.forEach(inp => {{

        inp.addEventListener('input', () => {{

          if (unsavedDock) unsavedDock.classList.add('visible');

        }});

        inp.addEventListener('change', () => {{

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



      // Reactive Event-Driven Refresh Configuration (#cfg-auto-refresh)
      // When idle (no task running), ZERO automatic periodic page reloads occur!
      // Telemetry updates in real-time via SSE (/api/automation/events) on task_start, stage_transition, active_wip, and task_complete.
      const cfgAutoRefreshSelect = document.getElementById('cfg-auto-refresh');
      let refreshMode = cfgAutoRefreshSelect ? cfgAutoRefreshSelect.value : 'event';
      let refreshIntervalSeconds = (cfgAutoRefreshSelect && !isNaN(parseInt(cfgAutoRefreshSelect.value, 10))) ? parseInt(cfgAutoRefreshSelect.value, 10) : 0;
      let refreshTimerSecondsRemaining = refreshIntervalSeconds;

      if (cfgAutoRefreshSelect) {{
        cfgAutoRefreshSelect.addEventListener('change', () => {{
          refreshMode = cfgAutoRefreshSelect.value;
          const parsed = parseInt(cfgAutoRefreshSelect.value, 10);
          refreshIntervalSeconds = isNaN(parsed) ? 0 : parsed;
          refreshTimerSecondsRemaining = refreshIntervalSeconds;
          if (refreshMode === 'event') {{
            showToast('⚡ Event-Driven Mode active: Zero idle reloads, live SSE updates on task activity.');
          }} else if (refreshIntervalSeconds > 0) {{
            showToast(`⏱️ Periodic refresh fallback set to ${{refreshIntervalSeconds}}s.`);
          }} else {{
            showToast('🛑 Manual refresh mode active. Use the Refresh button to sync.');
          }}
        }});
      }}

      // Background watchdog: Keeps header action button in sync while active.
      // Strictly guards against any idle periodic reloads!
      setInterval(() => {{
        if (isAutomationActive) {{
          syncHeaderActionButton(true);
        }}

        // Strict Guard: Idle state or Event-Driven / Manual mode -> Never reload automatically!
        if (!isAutomationActive || refreshMode === 'event' || isNaN(refreshIntervalSeconds) || refreshIntervalSeconds <= 0) {{
          return;
        }}

        refreshTimerSecondsRemaining--;
        if (refreshTimerSecondsRemaining <= 0) {{
          refreshTimerSecondsRemaining = refreshIntervalSeconds;
          pollServerStatus();
        }}
      }}, 1000);



      // Initialize

      pollServerStatus();

      applyFilters();

      applyExecutionModeUI(currentExecutionMode);



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





generate_modern_dashboard = generate_and_save_modern_dashboard


if __name__ == "__main__":
    out_path = generate_and_save_modern_dashboard()
    print(f"Modern dashboard successfully generated at: {out_path}")





if __name__ == "__main__":

    out = generate_and_save_modern_dashboard()

    print(f"Modern and Interactive Dashboard generated successfully at: {out}")

