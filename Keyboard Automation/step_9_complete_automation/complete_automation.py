#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
कम्प्लीट ऑटोमेशन मास्टर कंट्रोलर / Step 9: Complete Automation Master Controller
========================================================================
Subsystem: Step 9: Complete Automation (Master User Interaction & Step Orchestrator)
Directory: step_9_complete_automation/
Part of: AutoSelect-Commander Automation Suite
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)

Single Point of User Interaction:
  - This folder ("step_9_complete_automation") and this script ("complete_automation.py")
    along with "config.json" and the 1-click batch files serve as the EXCLUSIVE
    interface for the user. The user never needs to touch individual step folders.
  - Controls timing schedules (when to activate which script and after how long).
  - Integrates Step 0 core for condition detection (Antigravity Open + Pending Grill-Me).
  - Orchestrates sequential execution: Step 1 -> Step 2 -> Step 3 -> Step 4.
  - Handles settle delays, step enabling/disabling, and graceful exit 10 cancellations.
"""

from __future__ import annotations

import os
import sys
import json
import time
import signal
import logging
import argparse
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Ensure root workspace and package directories are in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

# Reconfigure stdout/stderr for proper UTF-8 handling on Windows
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

# Import decoupled Step 0 core detector & canonical status dashboard
from step_0_antigravity_detector.antigravity_detector_core import (
    AntiGravityDetector,
    DetectionResult,
    get_antigravity_chat_stats,
    resolve_brain_dir,
    DEFAULT_PRODUCTION_POLL_INTERVAL,
    DEFAULT_TEST_POLL_INTERVAL,
    DEFAULT_ACTIVE_HOURS,
)
try:
    from step_0_antigravity_detector.step0_antigravity_detector import (
        display_dashboard,
        format_dashboard_box,
        clear_screen,
    )
except ImportError:
    from step_0_antigravity_detector.step0_antigravity_detector_test import (
        display_dashboard,
        format_dashboard_box,
        clear_screen,
    )

from core_engine.config_manager import (
    load_runtime_config,
    save_runtime_config,
    get_canonical_config_path,
    get_effective_poll_interval,
    get_settle_delay,
    is_step_enabled,
    apply_logging_config,
)
from core_engine.win32_api import (
    get_idle_duration_seconds,
    get_last_input_info,
)

# Standard Exit Codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_PENDING_CHATS = 10
EXIT_CODE_GENERAL_ERROR = 1

IS_WINDOWS = sys.platform == "win32"


@dataclass
class PipelineStep:
    """
    Representation of an individual automated step in the AutoSelect pipeline.
    """
    step_index: int
    key: str
    name: str
    script_path: Path
    is_optional: bool = False
    description: str = ""

    def exists(self) -> bool:
        """Check whether the step script physically exists on disk."""
        try:
            return self.script_path.is_file()
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "key": self.key,
            "name": self.name,
            "script_path": str(self.script_path),
            "is_optional": self.is_optional,
            "exists": self.exists(),
            "description": self.description,
        }


def discover_pipeline_steps(
    root_dir: Optional[Union[str, Path]] = None,
    include_future: bool = True,
    custom_scripts: Optional[Dict[int, Union[str, Path]]] = None
) -> List[PipelineStep]:
    """
    Discover all configured and dynamically available pipeline steps in the workspace.
    """
    if root_dir is None:
        r_dir = _root_dir
    else:
        r_dir = Path(root_dir).resolve()

    custom = custom_scripts or {}
    steps: List[PipelineStep] = []

    # 1. Step 1: Chat Identifier & Window Focus
    p1 = custom.get(1)
    if p1:
        s1_path = Path(p1).resolve()
    else:
        c1 = [
            r_dir / "step_1_chat_identifier" / "step1_find_and_focus.py",
            r_dir / "step1_find_and_focus.py",
        ]
        s1_path = next((c for c in c1 if c.is_file()), c1[0])
    steps.append(PipelineStep(
        step_index=1,
        key="step1_find_and_focus",
        name="Step 1: Chat Identifier & Focus",
        script_path=s1_path,
        is_optional=False,
        description="Scans transcripts, identifies target chat, saves state, and focuses Antigravity window."
    ))

    # 2. Step 2: GUI Chat Select & Pane Focus
    p2 = custom.get(2)
    if p2:
        s2_path = Path(p2).resolve()
    else:
        c2 = [
            r_dir / "step_2_chat_and_focus" / "step2_gui_chat_select.py",
            r_dir / "step2_gui_chat_select.py",
        ]
        s2_path = next((c for c in c2 if c.is_file()), c2[0])
    steps.append(PipelineStep(
        step_index=2,
        key="step2_gui_chat_select",
        name="Step 2: GUI Chat Select & Focus",
        script_path=s2_path,
        is_optional=False,
        description="Locates target chat in GUI sidebar via CDP/DOM, clicks, and focuses chat pane."
    ))

    # 3. Step 3: Keyboard Automation & Option Selection
    p3 = custom.get(3)
    if p3:
        s3_path = Path(p3).resolve()
    else:
        c3 = [
            r_dir / "step_3_select_the_recommendation" / "step3_keyboard_automation.py",
            r_dir / "step3_keyboard_automation.py",
        ]
        s3_path = next((c for c in c3 if c.is_file()), c3[0])
    steps.append(PipelineStep(
        step_index=3,
        key="step3_keyboard_automation",
        name="Step 3: Keyboard Automation",
        script_path=s3_path,
        is_optional=False,
        description="Injects keystrokes to select recommendation option and confirms response."
    ))

    # 4. Step 4: Reporting & Visual Dashboard
    p4 = custom.get(4)
    if p4:
        s4_path = Path(p4).resolve()
    else:
        c4 = [
            r_dir / "step_4_reporting" / "step4_reporting.py",
            r_dir / "step_4_reporting" / "step4_report.py",
            r_dir / "step4_reporting.py",
        ]
        try:
            for d in r_dir.glob("step_4_*"):
                if d.is_dir():
                    for pyf in d.glob("*.py"):
                        if not pyf.name.startswith(("test_", "__", "setup")):
                            c4.insert(0, pyf)
        except Exception:
            pass
        s4_path = next((c for c in c4 if c.is_file()), c4[0])
    steps.append(PipelineStep(
        step_index=4,
        key="step4_reporting",
        name="Step 4: Reporting & Telemetry",
        script_path=s4_path,
        is_optional=True,
        description="Automated execution reporting, audit trail logging, and visual dashboard."
    ))

    # 5. Dynamic Future Steps (step_{N}_* where 5 <= N < 9; Step 9 is this master orchestrator)
    # Exclude daemon/sentinel/background services like step_5_automation
    try:
        for sub_dir in sorted(r_dir.glob("step_*_*")):
            if not sub_dir.is_dir():
                continue
            if sub_dir.resolve() == _this_dir.resolve():
                continue
            # Sentinel and lifecycle daemons are external supervisors, NOT sequential pipeline steps
            if sub_dir.name.lower() in ("step_5_automation", "step_5_sentinel") or any(k in sub_dir.name.lower() for k in ("sentinel", "daemon", "lifecycle")):
                continue
            parts = sub_dir.name.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                idx = int(parts[1])
                if 5 <= idx < 9:
                    cand_scripts = [
                        p for p in sub_dir.glob("*.py")
                        if not p.name.startswith(("test_", "__", "setup"))
                        and not any(k in p.name.lower() for k in ("sentinel", "daemon", "server", "service", "lifecycle"))
                    ]
                    if cand_scripts:
                        cand_scripts.sort(key=lambda x: (0 if f"step{idx}" in x.name.lower() else 1, len(x.name)))
                        chosen = cand_scripts[0]
                        steps.append(PipelineStep(
                            step_index=idx,
                            key=f"step{idx}_{sub_dir.name}",
                            name=f"Step {idx}: {sub_dir.name}",
                            script_path=chosen,
                            is_optional=True,
                            description=f"Dynamically discovered pipeline step in {sub_dir.name}."
                        ))
    except Exception:
        pass

    if not include_future:
        steps = [s for s in steps if s.exists()]

    steps.sort(key=lambda s: s.step_index)
    return steps


@dataclass
class TimingConfig:
    step0_poll_interval_prod_seconds: float = 300.0
    step0_poll_interval_test_seconds: float = 10.0
    settle_delay_between_steps_seconds: float = 0.8
    user_activity_pause_threshold_seconds: float = 60.0
    step4_user_activity_delay_seconds: float = 10.0
    step4_poll_interval_seconds: float = 0.1
    step1_window_focus_delay_seconds: float = 0.2
    step2_dom_click_settle_delay_seconds: float = 0.3
    step3_countdown_seconds: float = 3.0
    step3_key_hold_delay_ms: float = 50.0
    step3_post_keypress_delay_ms: float = 250.0
    step3_inter_question_delay_ms: float = 500.0
    step3_round_completion_pause_ms: float = 1000.0


@dataclass
class EnabledStepsConfig:
    step1_find_and_focus: bool = True
    step2_gui_chat_select: bool = True
    step3_keyboard_automation: bool = True
    step4_reporting: bool = True


@dataclass
class AutomationConfig:
    mode: str = "production"
    timing: TimingConfig = field(default_factory=TimingConfig)
    enabled_steps: EnabledStepsConfig = field(default_factory=EnabledStepsConfig)
    require_grill_me: bool = True
    active_hours: float = 12.0
    log_file: str = "complete_automation.log"
    verbose: bool = True

    @classmethod
    def load_from_file(cls, path: Optional[Union[str, Path]] = None) -> "AutomationConfig":
        """Load configuration using canonical core_engine.config_manager."""
        data = load_runtime_config(path)
        mode = data.get("mode", "production")
        timing_data = data.get("timing", {})
        enabled_data = data.get("enabled_steps", {})
        ag_data = data.get("antigravity", {})
        log_data = data.get("logging", {})

        timing = TimingConfig(
            step0_poll_interval_prod_seconds=float(timing_data.get("step0_poll_interval_prod_seconds", 300.0)),
            step0_poll_interval_test_seconds=float(timing_data.get("step0_poll_interval_test_seconds", 10.0)),
            settle_delay_between_steps_seconds=float(timing_data.get("settle_delay_between_steps_seconds", 0.8)),
            user_activity_pause_threshold_seconds=float(timing_data.get("user_activity_pause_threshold_seconds", 60.0)),
            step4_user_activity_delay_seconds=float(timing_data.get("step4_user_activity_delay_seconds", 10.0)),
            step4_poll_interval_seconds=float(timing_data.get("step4_poll_interval_seconds", 0.1)),
            step1_window_focus_delay_seconds=float(timing_data.get("step1_window_focus_delay_seconds", 0.2)),
            step2_dom_click_settle_delay_seconds=float(timing_data.get("step2_dom_click_settle_delay_seconds", 0.3)),
            step3_countdown_seconds=float(timing_data.get("step3_countdown_seconds", 3.0)),
            step3_key_hold_delay_ms=float(timing_data.get("step3_key_hold_delay_ms", 50.0)),
            step3_post_keypress_delay_ms=float(timing_data.get("step3_post_keypress_delay_ms", 250.0)),
            step3_inter_question_delay_ms=float(timing_data.get("step3_inter_question_delay_ms", 500.0)),
            step3_round_completion_pause_ms=float(timing_data.get("step3_round_completion_pause_ms", 1000.0)),
        )

        enabled = EnabledStepsConfig(
            step1_find_and_focus=bool(enabled_data.get("step1_find_and_focus", True)),
            step2_gui_chat_select=bool(enabled_data.get("step2_gui_chat_select", True)),
            step3_keyboard_automation=bool(enabled_data.get("step3_keyboard_automation", True)),
            step4_reporting=bool(enabled_data.get("step4_reporting", True)),
        )

        return cls(
            mode=mode,
            timing=timing,
            enabled_steps=enabled,
            require_grill_me=bool(ag_data.get("require_grill_me", True)),
            active_hours=float(ag_data.get("active_hours", 12.0)),
            log_file=str(log_data.get("log_file", "complete_automation.log")),
            verbose=bool(log_data.get("verbose", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "timing": asdict(self.timing),
            "enabled_steps": asdict(self.enabled_steps),
            "antigravity": {
                "require_grill_me": self.require_grill_me,
                "active_hours": self.active_hours,
            },
            "logging": {
                "log_file": self.log_file,
                "verbose": self.verbose,
            }
        }


class CompleteAutomationController:
    """
    Master Controller for Complete Automation.
    Manages timers, detector conditions, step activation lifecycle, and logging.
    """

    def __init__(
        self,
        config: Optional[AutomationConfig] = None,
        config_path: Optional[Union[str, Path]] = None,
        state_file_path: Optional[Union[str, Path]] = None,
        python_exe_path: Optional[Union[str, Path]] = None,
        headless: Optional[bool] = None,
    ):
        if config is not None:
            self.config = config
        else:
            self.config = AutomationConfig.load_from_file(config_path)

        self.workspace_dir = _root_dir
        if state_file_path:
            self.state_file = Path(state_file_path).resolve()
        else:
            state_primary = _root_dir / "state" / "target_chat.json"
            state_fallback = _root_dir / "target_chat.json"
            if state_primary.is_file():
                self.state_file = state_primary.resolve()
            elif state_fallback.is_file():
                self.state_file = state_fallback.resolve()
            else:
                self.state_file = state_primary.resolve()
        self.pid_file = (self.workspace_dir / "step_4_reporting" / ".automation_process.json").resolve()
        self.python_exe = self._resolve_python_exe(python_exe_path)
        self.pipeline_steps = discover_pipeline_steps(root_dir=self.workspace_dir, include_future=True)

        # Mode determination
        self._is_test_mode_override: Optional[bool] = None
        if headless is None:
            self.headless = not self.is_test_mode  # Production is headless by default
        else:
            self.headless = headless

        self._stop_requested = False
        self._dashboard_opened: bool = False

        # Logger
        self.logger = logging.getLogger("CompleteAutomation")
        self._setup_logger()

        # Step 0 Core Detector instance
        interval = (
            self.config.timing.step0_poll_interval_test_seconds
            if self.is_test_mode
            else self.config.timing.step0_poll_interval_prod_seconds
        )
        self.detector = AntiGravityDetector(
            poll_interval=interval,
            headless=True,
            verbose=False,
            active_hours=self.config.active_hours,
            require_grill_me=self.config.require_grill_me,
        )

    @property
    def is_test_mode(self) -> bool:
        """Dynamic check whether current operating mode is test mode."""
        if getattr(self, "_is_test_mode_override", None) is not None:
            return bool(self._is_test_mode_override)
        return bool(getattr(self, "config", None) and str(self.config.mode).lower() == "test")

    @is_test_mode.setter
    def is_test_mode(self, value: bool) -> None:
        """Allow explicit override of test mode status."""
        self._is_test_mode_override = bool(value)

    def _resolve_python_exe(self, explicit_path: Optional[Union[str, Path]]) -> Path:
        """Resolve python interpreter in .venv or sys.executable."""
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.is_file():
                return p

        candidates = [
            _root_dir / ".venv" / "Scripts" / "python.exe",
            _this_dir.parent / ".venv" / "Scripts" / "python.exe",
            Path(sys.executable),
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()
        return Path(sys.executable).resolve()

    def _setup_logger(self):
        """Configure file and stream handlers."""
        for h in list(self.logger.handlers):
            try:
                h.close()
            except Exception:
                pass
        self.logger.handlers.clear()
        self.logger.setLevel(logging.INFO if self.config.verbose else logging.WARNING)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [Complete Automation] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        logs_dir = _this_dir.parent / "logs"
        if logs_dir.is_dir():
            log_p = logs_dir / self.config.log_file
        else:
            log_p = _this_dir / self.config.log_file
        try:
            fh = logging.FileHandler(str(log_p), encoding="utf-8")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        except Exception:
            pass

        if not self.headless:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            self.logger.addHandler(sh)

    def is_step_enabled(self, step: PipelineStep) -> bool:
        """Check if a specific pipeline step is enabled in config."""
        en = self.config.enabled_steps
        if step.step_index == 1:
            return en.step1_find_and_focus
        elif step.step_index == 2:
            return en.step2_gui_chat_select
        elif step.step_index == 3:
            return en.step3_keyboard_automation
        elif step.step_index == 4:
            return en.step4_reporting
        return True

    def execute_pipeline(
        self,
        extra_args: Optional[List[str]] = None,
        capture_output: bool = False,
    ) -> Tuple[bool, int, str, List[Dict[str, Any]]]:
        """
        Execute the full sequence of enabled pipeline steps (Step 1 -> 2 -> 3 -> 4)
        honoring configured settle delays and handling graceful exit code 10 cancellations.

        :return: (success: bool, exit_code: int, summary: str, step_reports: List[Dict])
        """
        step_reports: List[Dict[str, Any]] = []
        settle_delay = self.config.timing.settle_delay_between_steps_seconds
        executed_count = 0

        self.logger.info("Initiating Complete Automation Pipeline Execution...")

        for step in self.pipeline_steps:
            if not self.is_step_enabled(step):
                self.logger.info("Step %d (%s) is disabled in config.json. Skipping.", step.step_index, step.name)
                continue

            if not step.exists():
                if step.is_optional:
                    self.logger.info("Optional Step %d (%s) script not found on disk. Gracefully skipping.", step.step_index, step.name)
                    continue
                else:
                    err = f"Required Step {step.step_index} ({step.name}) script missing: {step.script_path}"
                    self.logger.error(err)
                    return False, EXIT_CODE_GENERAL_ERROR, err, step_reports

            # Apply settle delay between steps
            if executed_count > 0 and settle_delay > 0:
                self.logger.debug("Applying settle delay (%.2fs) before Step %d...", settle_delay, step.step_index)
                time.sleep(settle_delay)

            # Build command with explicit config timers
            cmd = [
                str(self.python_exe),
                str(step.script_path),
                "--state-file",
                str(self.state_file),
            ]
            if step.step_index == 1:
                cmd.extend(["--focus-delay", str(self.config.timing.step1_window_focus_delay_seconds)])
            elif step.step_index == 2:
                cmd.extend([
                    "--dom-settle-delay", str(self.config.timing.step2_dom_click_settle_delay_seconds),
                    "--settle-delay", str(self.config.timing.settle_delay_between_steps_seconds),
                ])
            elif step.step_index == 3:
                cmd.append("--no-countdown")
                cmd.extend([
                    "--step-delay", str(self.config.timing.step3_post_keypress_delay_ms / 1000.0),
                    "--hold-delay", str(self.config.timing.step3_key_hold_delay_ms / 1000.0),
                    "--inter-question-delay", str(self.config.timing.step3_inter_question_delay_ms / 1000.0),
                    "--round-completion-pause", str(self.config.timing.step3_round_completion_pause_ms / 1000.0),
                ])
                # Inspect state file to forward multi-question count and options sequence explicitly
                has_custom_q = extra_args and any(arg in ("-q", "--questions") for arg in extra_args)
                has_custom_ol = extra_args and any(arg in ("-ol", "--options-list") for arg in extra_args)
                if not has_custom_q and self.state_file and self.state_file.is_file():
                    try:
                        with open(self.state_file, "r", encoding="utf-8") as sf:
                            s_data = json.load(sf)
                            s_inner = s_data.get("data", s_data) if isinstance(s_data, dict) else {}

                            # Resolve question count
                            q_cnt = None
                            qs = s_inner.get("questions")
                            sels = s_inner.get("selections")
                            if isinstance(qs, list) and len(qs) > 0:
                                q_cnt = len(qs)
                            elif isinstance(sels, list) and len(sels) > 0:
                                q_cnt = len(sels)
                            else:
                                for k in ("total_questions_count", "questions_count", "total_questions", "question_count"):
                                    v = s_inner.get(k)
                                    if v is not None:
                                        try:
                                            v_int = int(v)
                                            if v_int > 0:
                                                q_cnt = v_int
                                                break
                                        except (ValueError, TypeError):
                                            pass

                            if s_inner.get("is_multi_question") is True and (q_cnt is None or q_cnt < 2):
                                q_cnt = 2

                            # Resolve options sequence
                            opts = []
                            if isinstance(sels, list) and sels:
                                for item in sels:
                                    if isinstance(item, dict):
                                        idx = item.get("selected_option_index") or item.get("recommended_option_index")
                                        if idx is not None:
                                            opts.append(str(idx))
                            elif isinstance(qs, list) and qs:
                                for item in qs:
                                    if isinstance(item, dict):
                                        idx = item.get("recommended_option_index") or item.get("selected_option_index")
                                        if idx is not None:
                                            opts.append(str(idx))

                            if q_cnt is not None and q_cnt > 0:
                                cmd.extend(["--questions", str(q_cnt)])
                                if not has_custom_ol and opts:
                                    while len(opts) < q_cnt:
                                        opts.append("1")
                                    cmd.extend(["--options-list", ",".join(opts[:q_cnt])])
                                self.logger.info(
                                    "Step 9 forwarded state ground truth to Step 3: %d question(s), options=%s",
                                    q_cnt, opts[:q_cnt] if opts else ["1"] * q_cnt
                                )
                    except Exception as s_err:
                        self.logger.warning("Could not pre-read state file in Step 9: %s", s_err)
            elif step.step_index == 4:
                cmd.extend([
                    "--delay", str(self.config.timing.step4_user_activity_delay_seconds),
                    "--poll-interval", str(self.config.timing.step4_poll_interval_seconds),
                ])
                if getattr(self, "_dashboard_opened", False):
                    cmd.append("--no-watch")

            if extra_args:
                cmd.extend(extra_args)

            self.logger.info("Executing Step %d (%s)...", step.step_index, step.name)

            run_kwargs: Dict[str, Any] = {
                "cwd": str(self.workspace_dir),
                "stdout": subprocess.PIPE if capture_output else None,
                "stderr": subprocess.PIPE if capture_output else None,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
                "shell": False,
            }
            if sys.platform == "win32" and self.headless:
                run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                run_kwargs["startupinfo"] = startupinfo

            try:
                proc = subprocess.run(
                    cmd,
                    **run_kwargs,
                )
            except Exception as e:
                err = f"Execution exception running Step {step.step_index} ({step.name}): {e}"
                self.logger.error(err)
                return False, EXIT_CODE_GENERAL_ERROR, err, step_reports

            executed_count += 1
            step_report = {
                "step_index": step.step_index,
                "key": step.key,
                "name": step.name,
                "script": str(step.script_path),
                "returncode": proc.returncode,
                "success": (proc.returncode in (0, EXIT_CODE_NO_PENDING_CHATS if step.step_index == 1 else 0)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            step_reports.append(step_report)

            # Step 1 Exit Code 10 Check: No Pending Grill-Me Chats -> Cleanly cancel remaining steps
            if step.step_index == 1 and proc.returncode == EXIT_CODE_NO_PENDING_CHATS:
                msg = "Step 1 reported no pending chats (Exit Code 10). Remaining steps cancelled cleanly."
                self.logger.info(msg)
                return True, EXIT_CODE_NO_PENDING_CHATS, msg, step_reports

            # Any step failure aborts pipeline
            if proc.returncode != 0:
                msg = f"Step {step.step_index} ({step.name}) failed with exit code {proc.returncode}. Aborting pipeline."
                self.logger.error(msg)
                return False, proc.returncode, msg, step_reports

            self.logger.info("Step %d (%s) completed successfully (exit 0).", step.step_index, step.name)
            if step.step_index == 4 and proc.returncode == 0:
                self._dashboard_opened = True

        summary = f"Complete Automation Pipeline completed successfully ({executed_count} steps executed)."
        self.logger.info(summary)
        return True, EXIT_CODE_SUCCESS, summary, step_reports

    def _update_process_state(self, is_paused: bool, idle_seconds: float) -> None:
        """Atomically persist live state to .automation_process.json."""
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            data: Dict[str, Any] = {}
            if self.pid_file.is_file():
                try:
                    with open(self.pid_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["pid"] = os.getpid()
            data["mode"] = self.config.mode
            data["is_paused"] = is_paused
            data["user_idle_seconds"] = round(idle_seconds, 1)
            data["last_updated"] = time.time()

            tmp = self.pid_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.pid_file)
        except Exception as e:
            self.logger.debug("Failed to write .automation_process.json: %s", e)

    def _wait_for_user_idle(self, pause_threshold: float) -> bool:
        """
        In Production mode: if user is active (idle < threshold), block until idle >= threshold.
        While waiting:
          - State is marked is_paused = True in memory and in .automation_process.json.
          - Timers and actions are completely halted.
        Returns True if pausing occurred, False if user was already idle.
        """
        was_paused = False
        while not self._stop_requested:
            idle_seconds = get_idle_duration_seconds()
            if idle_seconds < pause_threshold:
                if not was_paused:
                    was_paused = True
                    self.logger.info(
                        "User activity detected (idle time: %.1fs < %.1fs). Production automation is PAUSED.",
                        idle_seconds, pause_threshold
                    )
                    if not self.headless:
                        print(f"\n[PAUSED] User activity detected (idle: {idle_seconds:.1f}s < {pause_threshold:.1f}s). Automation paused.")
                self._update_process_state(is_paused=True, idle_seconds=idle_seconds)
                time.sleep(1.0)
            else:
                if was_paused:
                    self.logger.info(
                        "User idle threshold reached (idle time: %.1fs >= %.1fs). Production automation is ACTIVE. Resuming normal monitoring.",
                        idle_seconds, pause_threshold
                    )
                    if not self.headless:
                        print(f"\n[ACTIVE] User idle for {idle_seconds:.1f}s >= {pause_threshold:.1f}s. Resuming active monitoring...")
                self._update_process_state(is_paused=False, idle_seconds=idle_seconds)
                break
        return was_paused

    def stop(self):
        """Signal controller loop to stop cleanly."""
        self._stop_requested = True
        self.detector.stop()

    def run(self, once: bool = False) -> int:
        """
        Run the complete automation lifecycle.
        In test mode: provides clean Unicode numbers dashboard every 10s.
        In production mode: runs silent background polling every 60s/300s,
        automatically pausing whenever user is active (idle < threshold).
        """
        def _handle_signal(signum, frame):
            self.logger.info("Termination signal received. Exiting gracefully...")
            self.stop()

        signal.signal(signal.SIGINT, _handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handle_signal)

        interval = (
            self.config.timing.step0_poll_interval_test_seconds
            if self.is_test_mode
            else self.config.timing.step0_poll_interval_prod_seconds
        )
        self.detector.poll_interval = interval
        pause_threshold = self.config.timing.user_activity_pause_threshold_seconds

        # Record initial process state
        initial_idle = get_idle_duration_seconds() if not self.is_test_mode else 0.0
        initial_paused = (initial_idle < pause_threshold) if not self.is_test_mode else False
        self._update_process_state(is_paused=initial_paused, idle_seconds=initial_idle)

        if not self.headless:
            print("\n" + "=" * 78)
            print("  कम्प्लीट ऑटोमेशन मास्टर कंट्रोलर / Complete Automation Master Controller")
            print("=" * 78)
            print(f"  Operating Mode   : {self.config.mode.upper()}")
            print(f"  Polling Rate     : {interval:.1f}s ({interval / 60:.2f} min)")
            print(f"  Pause Threshold  : {pause_threshold:.1f}s (User Activity Auto-Pause)")
            print(f"  Settle Delay     : {self.config.timing.settle_delay_between_steps_seconds:.2f}s")
            print(f"  Python Engine    : {self.python_exe}")
            print(f"  State File       : {self.state_file}")
            print(f"  Step 1 Enabled   : {'YES' if self.config.enabled_steps.step1_find_and_focus else 'NO'}")
            print(f"  Step 2 Enabled   : {'YES' if self.config.enabled_steps.step2_gui_chat_select else 'NO'}")
            print(f"  Step 3 Enabled   : {'YES' if self.config.enabled_steps.step3_keyboard_automation else 'NO'}")
            print(f"  Step 4 Enabled   : {'YES' if self.config.enabled_steps.step4_reporting else 'NO'}")
            print("=" * 78 + "\n")

        check_count = 0
        while not self._stop_requested:
            # In Production Mode: check and wait for user to become idle before proceeding
            if not self.is_test_mode:
                self._wait_for_user_idle(pause_threshold)
                if self._stop_requested:
                    break

            check_count += 1
            res = self.detector.detect()

            if self.is_test_mode and not self.headless:
                display_dashboard(res, chat_stats=res.chat_stats, wipe_screen=True, poll_interval=interval)

            if res.trigger_matched:
                # In Production Mode: re-verify user did not begin typing/mouse movement right before pipeline
                if not self.is_test_mode:
                    self._wait_for_user_idle(pause_threshold)
                    if self._stop_requested:
                        break

                if not self.headless:
                    now_str = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{now_str}] [TRIGGER MATCHED] Antigravity is open and pending Grill-Me chat detected ({res.pending_grill_me_chats})!")
                    print("Initiating Complete Automation Pipeline execution now...")

                ok, code, msg, _ = self.execute_pipeline(capture_output=self.headless)

                if once:
                    if not self.headless:
                        print(f"\n[RESULT] {msg} (Exit Code: {code})")
                    self.logger.info("Single-run execution completed (Exit Code: %d). Stopping.", code)
                    return code

                if code == EXIT_CODE_NO_PENDING_CHATS:
                    self.logger.info(
                        "Step 1 reported no pending chats (Exit Code 10). Waiting for next monitoring interval (%.1fs)...",
                        interval
                    )
                    if not self.headless:
                        print(f"\n[INFO] {msg}")
                        print(f"Waiting for next monitoring check in {interval:.1f}s...")
                else:
                    mode_label = "Test" if self.is_test_mode else "Production"
                    self.logger.info(
                        "%s Mode: Pipeline cycle completed successfully. Continuing continuous autonomous background monitoring until manually stopped by user.",
                        mode_label
                    )
                    if not self.headless:
                        print(f"\n[RESULT] {msg} (Exit Code: {code})")
                        print(f"{mode_label} Mode: Pipeline cycle completed successfully. Continuing continuous autonomous background monitoring until manually stopped by user.")

            if once:
                return 0 if res.is_detected else 1

            # Sleep in 0.5s chunks for prompt Ctrl+C interrupt; halt timer if user is active in production mode
            sleep_remaining = interval
            while sleep_remaining > 0 and not self._stop_requested:
                if not self.is_test_mode:
                    idle_sec = get_idle_duration_seconds()
                    if idle_sec < pause_threshold:
                        self._wait_for_user_idle(pause_threshold)
                        if self._stop_requested:
                            break
                        self._update_process_state(is_paused=False, idle_seconds=get_idle_duration_seconds())
                time.sleep(min(0.5, sleep_remaining))
                sleep_remaining -= 0.5

        return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="कम्प्लीट ऑटोमेशन मास्टर कंट्रोलर / Complete Automation Master Controller"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to custom config.json file"
    )
    parser.add_argument(
        "--mode",
        choices=["production", "test"],
        default=None,
        help="Override operating mode: 'production' (5-minute poll) or 'test' (10-second poll)"
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Execute the 4-step pipeline directly without waiting for detector polling"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform a single detection check and exit"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Override polling interval in seconds"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in visible interactive mode (shows terminal output)"
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to target_chat.json state file"
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="Batch script compatibility flag to suppress pause prompt"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    config = AutomationConfig.load_from_file(args.config)
    if args.mode:
        config.mode = args.mode
    if args.interval:
        if config.mode == "test":
            config.timing.step0_poll_interval_test_seconds = args.interval
        else:
            config.timing.step0_poll_interval_prod_seconds = args.interval

    headless = not args.interactive if args.interactive else None

    controller = CompleteAutomationController(
        config=config,
        state_file_path=args.state_file,
        headless=headless,
    )

    if args.run_pipeline:
        ok, code, msg, _ = controller.execute_pipeline(capture_output=False)
        return code

    return controller.run(once=args.once)


if __name__ == "__main__":
    sys.exit(main())
