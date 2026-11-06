#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Source of Truth Configuration Subsystem (config_manager.py)
==================================================================
Pipeline Role: Universal Configuration Manager & System State Synchronization
Part of: AutoSelect-Commander Automation Suite
Standard: Department 06 (Backend & API Engineering) & Department 02 (Solution Architecture)
Primary Developer: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Responsibilities:
  1. Canonical File Location: Resolves `step_9_complete_automation/config.json`.
  2. Typed Fail-Safe Loading: Loads runtime config with deep default merging and type coercion.
  3. Atomic Safe Writing: Safely commits configuration updates using atomic temporary file replacement.
  4. Cross-Step Synchronization: Powers Step 0, Step 1, Step 2, Step 3, Step 4, and Step 9 from
     the exact same single configuration source of truth.
"""

from __future__ import annotations

import os
import sys
import json
import copy
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

# Base workspace resolution
_this_dir = Path(__file__).resolve().parent
_workspace_dir = _this_dir.parent if _this_dir.name == "core_engine" else _this_dir

DEFAULT_RUNTIME_CONFIG: Dict[str, Any] = {
    "_comment": "Step 9: Complete Automation Configuration - AutoSelect Antigravity Master Configuration",
    "mode": "production",
    "timing": {
        "step0_poll_interval_prod_seconds": 300.0,
        "step0_poll_interval_test_seconds": 10.0,
        "settle_delay_between_steps_seconds": 0.8,
        "user_activity_pause_threshold_seconds": 60.0,
        "step4_user_activity_delay_seconds": 10.0,
        "step4_poll_interval_seconds": 0.1,
        "step1_window_focus_delay_seconds": 0.2,
        "step2_dom_click_settle_delay_seconds": 0.3,
        "step3_countdown_seconds": 3.0,
        "step3_key_hold_delay_ms": 50.0,
        "step3_post_keypress_delay_ms": 250.0,
        "step3_inter_question_delay_ms": 500.0,
        "step3_round_completion_pause_ms": 1000.0,
    },
    "enabled_steps": {
        "step1_find_and_focus": True,
        "step2_gui_chat_select": True,
        "step3_keyboard_automation": True,
        "step4_reporting": True,
    },
    "antigravity": {
        "require_grill_me": True,
        "active_hours": 12.0,
    },
    "logging": {
        "log_file": "complete_automation.log",
        "verbose": True,
    },
}

STEP_KEY_MAP: Dict[Union[str, int], str] = {
    1: "step1_find_and_focus",
    2: "step2_gui_chat_select",
    3: "step3_keyboard_automation",
    4: "step4_reporting",
    "step1": "step1_find_and_focus",
    "step2": "step2_gui_chat_select",
    "step3": "step3_keyboard_automation",
    "step4": "step4_reporting",
    "step1_find_and_focus": "step1_find_and_focus",
    "step2_gui_chat_select": "step2_gui_chat_select",
    "step3_keyboard_automation": "step3_keyboard_automation",
    "step4_reporting": "step4_reporting",
}


def get_canonical_config_path(base_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Locates the canonical step_9_complete_automation/config.json with robust fallbacks.
    Returns an absolute resolved Path.
    """
    root = Path(base_dir).resolve() if base_dir else _workspace_dir
    candidates = [
        root / "step_9_complete_automation" / "config.json",
        root / "Complete Automation" / "config.json",
        root / "config.json",
        Path.cwd() / "step_9_complete_automation" / "config.json",
        Path.cwd() / "config.json",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    # Default canonical location if file not yet on disk
    return (root / "step_9_complete_automation" / "config.json").resolve()


def get_state_dir(base_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Returns the canonical dedicated runtime state directory (<workspace>/state).
    Guarantees the directory exists on disk.
    """
    root = Path(base_dir).resolve() if base_dir else _workspace_dir
    state_dir = (root / "state").resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_logs_dir(base_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Returns the canonical dedicated runtime logs directory (<workspace>/logs).
    Guarantees the directory exists on disk.
    """
    root = Path(base_dir).resolve() if base_dir else _workspace_dir
    logs_dir = (root / "logs").resolve()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def resolve_runtime_log_file(
    filename: str = "complete_automation.log",
    base_dir: Optional[Union[str, Path]] = None,
    for_writing: bool = False,
) -> Path:
    """
    Resilient log file path resolver:
      Tier 1 (Primary): <workspace>/logs/<filename>
      Tier 2 (Fallback): <workspace>/step_9_complete_automation/<filename>
      Tier 3 (Fallback): <workspace>/<filename>
    """
    p = Path(filename)
    if p.is_absolute():
        if for_writing:
            p.parent.mkdir(parents=True, exist_ok=True)
        return p.resolve()

    root = Path(base_dir).resolve() if base_dir else _workspace_dir
    logs_dir = root / "logs"

    if for_writing:
        logs_dir.mkdir(parents=True, exist_ok=True)
        return (logs_dir / p.name).resolve()

    primary = (logs_dir / p.name).resolve()
    if primary.is_file():
        return primary

    step9_log = (root / "step_9_complete_automation" / p.name).resolve()
    if step9_log.is_file():
        return step9_log

    fallback_root = (root / p.name).resolve()
    if fallback_root.is_file():
        return fallback_root

    # Default to Tier 1
    return primary


def resolve_runtime_state_file(
    filename: str = "target_chat.json",
    base_dir: Optional[Union[str, Path]] = None,
    for_writing: bool = False,
) -> Path:
    """
    Resilient two-tier state file path resolver:
      Tier 1 (Primary): <workspace>/state/<filename>
      Tier 2 (Fallback): <workspace>/<filename> (backward-compatible legacy fallback)

    Behavior:
      - When `for_writing=True`: Always targets Tier 1 (<workspace>/state/<filename>)
        and guarantees the `state/` directory exists.
      - When reading (`for_writing=False`):
        1. Checks Tier 1 (<workspace>/state/<filename>). If exists, returns it.
        2. Checks Tier 2 fallback (<workspace>/<filename>). If exists, returns it.
        3. Checks current working directory fallbacks (CWD/state/<filename> then CWD/<filename>).
        4. If not found anywhere, defaults to Tier 1 (<workspace>/state/<filename>).
    """
    p = Path(filename)
    if p.is_absolute():
        if for_writing:
            p.parent.mkdir(parents=True, exist_ok=True)
        return p.resolve()

    root = Path(base_dir).resolve() if base_dir else _workspace_dir
    state_dir = root / "state"

    if for_writing:
        state_dir.mkdir(parents=True, exist_ok=True)
        return (state_dir / p.name).resolve()

    # If explicit path has multiple parts (e.g. 'state/target_chat.json' or 'custom/foo.json')
    if len(p.parts) > 1:
        if (root / p).is_file():
            return (root / p).resolve()
        if (Path.cwd() / p).is_file():
            return (Path.cwd() / p).resolve()
        return (root / p).resolve()

    # Tier 1: Dedicated state directory
    primary = (state_dir / p.name).resolve()
    if primary.is_file():
        return primary

    # Tier 2: Root directory fallback
    fallback_root = (root / p.name).resolve()
    if fallback_root.is_file():
        return fallback_root

    # CWD checks
    cwd_state = (Path.cwd() / "state" / p.name).resolve()
    if cwd_state.is_file():
        return cwd_state
    cwd_root = (Path.cwd() / p.name).resolve()
    if cwd_root.is_file():
        return cwd_root

    # Default to Tier 1
    return primary


def resolve_state_pair(
    state_file: Optional[Union[str, Path]] = None,
    base_dir: Optional[Union[str, Path]] = None,
    for_writing: bool = False,
) -> Tuple[Path, Path]:
    """
    Resolves both target_chat.json and last_selection_state.json paths atomically.
    Returns (target_chat_path, last_selection_state_path).
    """
    fname = Path(state_file).name if state_file else "target_chat.json"
    target = resolve_runtime_state_file(filename=fname, base_dir=base_dir, for_writing=for_writing)
    legacy = target.parent / "last_selection_state.json"
    if for_writing:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target, legacy


def get_default_runtime_config() -> Dict[str, Any]:
    """Returns a deep copy of the standard default runtime configuration."""
    return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)


def load_runtime_config(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Loads runtime configuration from disk, deeply merging with default values.
    Guarantees all sections and keys exist with proper types.
    """
    target_path = Path(path).resolve() if path else get_canonical_config_path()
    cfg = get_default_runtime_config()

    if not target_path.is_file():
        return cfg

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return cfg

        # Merge top-level comments & mode
        if "_comment" in data:
            cfg["_comment"] = str(data["_comment"])
        if "mode" in data and str(data["mode"]).lower() in ("production", "test"):
            cfg["mode"] = str(data["mode"]).lower()

        # Merge timing section
        timing_data = data.get("timing")
        if isinstance(timing_data, dict):
            for k in cfg["timing"]:
                if k in timing_data:
                    try:
                        cfg["timing"][k] = float(timing_data[k])
                    except (ValueError, TypeError):
                        pass
            for k, v in timing_data.items():
                if k not in cfg["timing"]:
                    try:
                        cfg["timing"][k] = float(v)
                    except (ValueError, TypeError):
                        pass

        # Merge enabled_steps section
        enabled_data = data.get("enabled_steps")
        if isinstance(enabled_data, dict):
            for k in cfg["enabled_steps"]:
                if k in enabled_data:
                    cfg["enabled_steps"][k] = bool(enabled_data[k])

        # Merge antigravity section
        ag_data = data.get("antigravity")
        if isinstance(ag_data, dict):
            if "require_grill_me" in ag_data:
                cfg["antigravity"]["require_grill_me"] = bool(ag_data["require_grill_me"])
            if "active_hours" in ag_data:
                try:
                    cfg["antigravity"]["active_hours"] = float(ag_data["active_hours"])
                except (ValueError, TypeError):
                    pass

        # Merge logging section
        log_data = data.get("logging")
        if isinstance(log_data, dict):
            if "log_file" in log_data and log_data["log_file"]:
                cfg["logging"]["log_file"] = str(log_data["log_file"]).strip()
            if "verbose" in log_data:
                cfg["logging"]["verbose"] = bool(log_data["verbose"])

        return cfg
    except Exception:
        return cfg


def save_runtime_config(
    config_data: Dict[str, Any],
    path: Optional[Union[str, Path]] = None,
) -> bool:
    """
    Saves runtime configuration to disk using atomic temporary replacement.
    Returns True on success, False otherwise.
    """
    if not isinstance(config_data, dict):
        return False

    target_path = Path(path).resolve() if path else get_canonical_config_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = target_path.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        temp_path.replace(target_path)
        return True
    except Exception as e:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass
        return False


def get_effective_poll_interval(config_data: Optional[Dict[str, Any]] = None) -> float:
    """
    Returns the effective Step 0 polling interval in seconds based on operating mode.
    - production mode -> step0_poll_interval_prod_seconds (default: 300.0)
    - test mode -> step0_poll_interval_test_seconds (default: 10.0)
    """
    cfg = config_data if config_data is not None else load_runtime_config()
    mode = cfg.get("mode", "production")
    timing = cfg.get("timing", {})
    if mode == "test":
        return float(timing.get("step0_poll_interval_test_seconds", 10.0))
    return float(timing.get("step0_poll_interval_prod_seconds", 300.0))


def get_settle_delay(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns the inter-step settle delay in seconds (default: 0.8s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("settle_delay_between_steps_seconds", 0.8))


def get_user_activity_delay(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns Step 4 user inactivity buffer in seconds (default: 10.0s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("step4_user_activity_delay_seconds", 10.0))


def get_user_activity_pause_threshold(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns user activity pause threshold in seconds (default: 60.0s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("user_activity_pause_threshold_seconds", 60.0))


def get_window_focus_delay(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns Step 1 window focus settle delay in seconds (default: 0.2s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("step1_window_focus_delay_seconds", 0.2))


def get_dom_click_settle_delay(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns Step 2 DOM click settle delay in seconds (default: 0.3s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("step2_dom_click_settle_delay_seconds", 0.3))


def get_step4_poll_interval(config_data: Optional[Dict[str, Any]] = None) -> float:
    """Returns Step 4 user activity polling interval in seconds (default: 0.1s)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    return float(cfg.get("timing", {}).get("step4_poll_interval_seconds", 0.1))


def get_step4_timeout(config_data: Optional[Dict[str, Any]] = None) -> Optional[float]:
    """Returns Step 4 user activity watcher timeout in seconds (default: None)."""
    cfg = config_data if config_data is not None else load_runtime_config()
    val = cfg.get("timing", {}).get("step4_timeout_seconds", cfg.get("timing", {}).get("step4_max_wait_seconds", None))
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def get_keyboard_timing(config_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Returns Step 3 keyboard automation timing dictionary:
      - countdown: float (seconds)
      - hold_delay_s: float (seconds)
      - post_keypress_delay_s: float (seconds)
      - inter_question_delay_s: float (seconds)
      - round_completion_pause_s: float (seconds)
    """
    cfg = config_data if config_data is not None else load_runtime_config()
    timing = cfg.get("timing", {})
    return {
        "countdown": float(timing.get("step3_countdown_seconds", 3.0)),
        "hold_delay_s": float(timing.get("step3_key_hold_delay_ms", 50.0)) / 1000.0,
        "post_keypress_delay_s": float(timing.get("step3_post_keypress_delay_ms", 250.0)) / 1000.0,
        "inter_question_delay_s": float(timing.get("step3_inter_question_delay_ms", 500.0)) / 1000.0,
        "round_completion_pause_s": float(timing.get("step3_round_completion_pause_ms", 1000.0)) / 1000.0,
    }


def get_step_timing(step_idx: int, config_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Returns granular timing parameters for a given step index (0..4, 9).
    """
    cfg = config_data if config_data is not None else load_runtime_config()
    timing = cfg.get("timing", {})
    if step_idx == 0:
        return {
            "step0_poll_interval_prod_seconds": float(timing.get("step0_poll_interval_prod_seconds", 300.0)),
            "step0_poll_interval_test_seconds": float(timing.get("step0_poll_interval_test_seconds", 10.0)),
        }
    elif step_idx == 1:
        return {
            "step1_window_focus_delay_seconds": float(timing.get("step1_window_focus_delay_seconds", 0.2)),
        }
    elif step_idx == 2:
        return {
            "step2_dom_click_settle_delay_seconds": float(timing.get("step2_dom_click_settle_delay_seconds", 0.3)),
            "settle_delay_between_steps_seconds": float(timing.get("settle_delay_between_steps_seconds", 0.8)),
        }
    elif step_idx == 3:
        return get_keyboard_timing(cfg)
    elif step_idx == 4:
        return {
            "step4_user_activity_delay_seconds": float(timing.get("step4_user_activity_delay_seconds", 10.0)),
            "step4_poll_interval_seconds": float(timing.get("step4_poll_interval_seconds", 0.1)),
        }
    else:
        return {
            "settle_delay_between_steps_seconds": float(timing.get("settle_delay_between_steps_seconds", 0.8)),
        }


def is_step_enabled(
    step_key_or_index: Union[str, int],
    config_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Checks whether a specific pipeline step is enabled in configuration.
    Supports step index (1..4) or canonical keys ('step1_find_and_focus', etc.).
    """
    cfg = config_data if config_data is not None else load_runtime_config()
    enabled_steps = cfg.get("enabled_steps", {})
    canonical_key = STEP_KEY_MAP.get(step_key_or_index, str(step_key_or_index))
    return bool(enabled_steps.get(canonical_key, True))


def apply_logging_config(
    config_data: Optional[Dict[str, Any]] = None,
    logger_instance: Optional[logging.Logger] = None,
    step_name: str = "",
) -> None:
    """
    Applies unified logging configuration (verbosity & log file) to a logger or root.
    """
    cfg = config_data if config_data is not None else load_runtime_config()
    log_cfg = cfg.get("logging", {})
    verbose = log_cfg.get("verbose", True)
    log_file = log_cfg.get("log_file", "complete_automation.log")

    level = logging.INFO if verbose else logging.WARNING
    target_logger = logger_instance or logging.getLogger()
    target_logger.setLevel(level)

    # Attach file handler if not already attached for this file
    if log_file:
        try:
            # Resolve log path relative to logs/ or canonical config parent
            log_path = resolve_runtime_log_file(log_file, base_dir=_workspace_dir, for_writing=True)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            already_attached = any(
                isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == str(log_path.resolve())
                for h in target_logger.handlers
            )
            if not already_attached:
                fh = logging.FileHandler(str(log_path), encoding="utf-8")
                fh.setLevel(level)
                fmt = logging.Formatter(
                    f"%(asctime)s [%(levelname)s] [{step_name or 'AutoSelect'}] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                fh.setFormatter(fmt)
                target_logger.addHandler(fh)
        except Exception:
            pass
