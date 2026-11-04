#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Activity & Inactivity Detection Subsystem (user_activity.py)
================================================================
Pipeline Role: Real-Time User Input Monitoring & Idle Duration Calculation
Part of: AutoSelect-Commander Automation Suite
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Provides:
  - `get_last_input_info() -> int`: Tick count of last physical keyboard/mouse input.
  - `get_idle_duration_seconds() -> float`: Seconds elapsed since last input.
  - `is_user_active(threshold_seconds: float = 60.0) -> bool`: True if idle time < threshold.
  - `wait_for_user_idle(...)`: Blocks gracefully until user has been idle for >= threshold.
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Any
from .win32_api import (
    IS_WINDOWS,
    LASTINPUTINFO,
    get_last_input_info,
    get_idle_duration_seconds,
)

logger = logging.getLogger("AutoSelect.UserActivity")


def is_user_active(threshold_seconds: float = 60.0) -> bool:
    """
    Check if the user has interacted with keyboard or mouse recently.
    Returns True if idle time < threshold_seconds, False otherwise.
    """
    idle = get_idle_duration_seconds()
    return idle < threshold_seconds


def wait_for_user_idle(
    threshold_seconds: float = 60.0,
    poll_interval: float = 1.0,
    stop_event: Optional[Any] = None,
    timeout: Optional[float] = None,
) -> float:
    """
    Wait until the user has remained idle (no input) for at least `threshold_seconds`.
    Returns the final idle duration in seconds.
    """
    start_time = time.time()
    while True:
        if stop_event and hasattr(stop_event, "is_set") and stop_event.is_set():
            return get_idle_duration_seconds()

        if timeout is not None and (time.time() - start_time) >= timeout:
            return get_idle_duration_seconds()

        idle = get_idle_duration_seconds()
        if idle >= threshold_seconds:
            return idle

        time.sleep(poll_interval)


__all__ = [
    "LASTINPUTINFO",
    "get_last_input_info",
    "get_idle_duration_seconds",
    "is_user_active",
    "wait_for_user_idle",
]
