#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
कम्प्लीट ऑटोमेशन पैकेज / Complete Automation Package
===================================================
Master hub and single interaction point for AutoSelect-Commander.
Exports:
  - CompleteAutomationController: Master pipeline orchestrator.
  - AutomationConfig: User configuration parser and data structure.
  - PipelineStep: Dataclass for pipeline steps.
  - discover_pipeline_steps: Workspace step discovery function.
"""

from .complete_automation import (
    CompleteAutomationController,
    AutomationConfig,
    TimingConfig,
    EnabledStepsConfig,
    PipelineStep,
    discover_pipeline_steps,
)

__all__ = [
    "CompleteAutomationController",
    "AutomationConfig",
    "TimingConfig",
    "EnabledStepsConfig",
    "PipelineStep",
    "discover_pipeline_steps",
]
