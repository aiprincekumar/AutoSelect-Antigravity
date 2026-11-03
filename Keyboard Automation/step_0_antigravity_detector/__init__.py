#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
स्टेप 0 - एंटी-ग्रेविटी डिटेक्टर / Step 0 - AntiGravity Detector
=============================================================
Package: step_0_antigravity_detector
Part of: AutoSelect-Commander Automation Pipeline
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Universal Rule 15/26

Exports:
  - AntiGravityDetector: Modular, reusable core detector engine.
  - DetectionResult: Structured detection payload (Dept 06 JSON envelope compatible).
  - PipelineStep: Dataclass representing individual steps in the automation pipeline.
  - discover_pipeline_steps: Dynamic discovery of pipeline steps (Steps 1, 2, 3, future 4).
  - DEFAULT_PRODUCTION_POLL_INTERVAL: 300 seconds (5 minutes).
  - DEFAULT_TEST_POLL_INTERVAL: 10 seconds.
  - DEFAULT_STEP_SETTLE_DELAY: 0.8 seconds.
  - EXIT_CODE_NO_PENDING_CHATS: 10.
"""

from .antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
    PipelineStep,
    discover_pipeline_steps,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
    DEFAULT_STEP_SETTLE_DELAY,
    EXIT_CODE_NO_PENDING_CHATS,
)

__all__ = [
    "AntiGravityDetector",
    "DetectionResult",
    "PipelineStep",
    "discover_pipeline_steps",
    "DEFAULT_PRODUCTION_POLL_INTERVAL",
    "DEFAULT_TEST_POLL_INTERVAL",
    "DEFAULT_STEP_SETTLE_DELAY",
    "EXIT_CODE_NO_PENDING_CHATS",
]
