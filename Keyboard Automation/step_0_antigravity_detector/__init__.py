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
  - DEFAULT_PRODUCTION_POLL_INTERVAL: 300 seconds (5 minutes).
  - DEFAULT_TEST_POLL_INTERVAL: 10 seconds.
"""

from .antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
)

__all__ = [
    "AntiGravityDetector",
    "DetectionResult",
    "DEFAULT_PRODUCTION_POLL_INTERVAL",
    "DEFAULT_TEST_POLL_INTERVAL",
]
