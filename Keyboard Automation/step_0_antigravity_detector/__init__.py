#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector
=============================================================
Package: step_0_antigravity_detector
Part of: AutoSelect-Commander Automation Suite
Workspace: Keyboard Automation (Step 0: Detector & Status Monitor)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)

Exports:
  - AntiGravityDetector: Modular, reusable core detector and status monitor engine.
  - DetectionResult: Structured detection payload (Dept 06 JSON envelope compatible).
  - get_antigravity_chat_stats: Live metrics calculation from brain transcripts.
  - resolve_brain_dir: Path resolution for Antigravity conversation storage.
  - DEFAULT_PRODUCTION_POLL_INTERVAL: 300 seconds (5 minutes).
  - DEFAULT_TEST_POLL_INTERVAL: 10 seconds.
  - DEFAULT_ACTIVE_HOURS: 12.0 hours.
"""

from .antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
    get_antigravity_chat_stats,
    resolve_brain_dir,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
    DEFAULT_ACTIVE_HOURS,
    DISQUALIFIED_BROWSER_PROCS,
    ANTIGRAVITY_PROCESS_NAMES,
)

__all__ = [
    "AntiGravityDetector",
    "DetectionResult",
    "get_antigravity_chat_stats",
    "resolve_brain_dir",
    "DEFAULT_PRODUCTION_POLL_INTERVAL",
    "DEFAULT_TEST_POLL_INTERVAL",
    "DEFAULT_ACTIVE_HOURS",
    "DISQUALIFIED_BROWSER_PROCS",
    "ANTIGRAVITY_PROCESS_NAMES",
]
