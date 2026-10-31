# -*- coding: utf-8 -*-
"""
Configuration management and defaults for AutoSelect-Commander.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Config:
    """Runtime configuration settings for AutoSelect-Commander."""
    countdown_seconds: int = 10
    check_interval_ms: int = 1000
    mouse_interruption_threshold_px: int = 15
    smooth_glide_duration_s: float = 0.8
    cooldown_after_dismissal_s: int = 5
    failsafe_enabled: bool = True
    sound_notification: bool = True
    window_title_filter: str = ""  # Empty string = scan foreground and all visible windows
    floating_hud_enabled: bool = True
    floating_hud_alpha: float = 0.92
    ocr_enabled: bool = True
    action_bar_keywords: Tuple[str, ...] = (
        "Submit",
        "Skip",
        "पुष्टि करें",
        "Confirm",
        "Proceed",
    )
    target_keywords: Tuple[str, ...] = (
        "(Recommended)",
        "[Recommended]",
        "(अनुशंसित)",
        "[अनुशंसित]",
        "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
        "(Recommended) GitHub",
        "Proceed",
    )
    submit_keywords: Tuple[str, ...] = (
        "Submit",
        "Skip",
        "पुष्टि करें",
        "Confirm",
        "Proceed",
        "Submit / पुष्टि करें",
        "जारी रखें",
        "Continue",
        "Select",
        "OK",
    )
    detection_mode: str = "auto"  # 'auto', 'ocr', 'uia', 'vision'
    require_submit_button: bool = True  # Strictly requires Submit button to eliminate chat false positives

    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """Load configuration from JSON file or return defaults."""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(
                        countdown_seconds=int(data.get("countdown_seconds", 10)),
                        check_interval_ms=int(data.get("check_interval_ms", 1000)),
                        mouse_interruption_threshold_px=int(data.get("mouse_interruption_threshold_px", 15)),
                        smooth_glide_duration_s=float(data.get("smooth_glide_duration_s", 0.8)),
                        cooldown_after_dismissal_s=int(data.get("cooldown_after_dismissal_s", 5)),
                        failsafe_enabled=bool(data.get("failsafe_enabled", True)),
                        sound_notification=bool(data.get("sound_notification", True)),
                        window_title_filter=str(data.get("window_title_filter", "")),
                        floating_hud_enabled=bool(data.get("floating_hud_enabled", True)),
                        floating_hud_alpha=float(data.get("floating_hud_alpha", 0.92)),
                        ocr_enabled=bool(data.get("ocr_enabled", True)),
                        action_bar_keywords=tuple(data.get("action_bar_keywords", cls.action_bar_keywords)),
                        target_keywords=tuple(data.get("target_keywords", cls.target_keywords)),
                        submit_keywords=tuple(data.get("submit_keywords", cls.submit_keywords)),
                        detection_mode=str(data.get("detection_mode", "auto")),
                        require_submit_button=bool(data.get("require_submit_button", True)),
                    )
            except Exception as e:
                print(f"\033[93m[WARN] Failed to parse config.json ({e}). Using default settings.\033[0m")
        return cls()

    def save(self, config_path: str = "config.json") -> None:
        """Save current configuration to JSON file."""
        data = {
            "countdown_seconds": self.countdown_seconds,
            "check_interval_ms": self.check_interval_ms,
            "mouse_interruption_threshold_px": self.mouse_interruption_threshold_px,
            "smooth_glide_duration_s": self.smooth_glide_duration_s,
            "cooldown_after_dismissal_s": self.cooldown_after_dismissal_s,
            "failsafe_enabled": self.failsafe_enabled,
            "sound_notification": self.sound_notification,
            "window_title_filter": self.window_title_filter,
            "floating_hud_enabled": self.floating_hud_enabled,
            "floating_hud_alpha": self.floating_hud_alpha,
            "ocr_enabled": self.ocr_enabled,
            "action_bar_keywords": list(self.action_bar_keywords),
            "target_keywords": list(self.target_keywords),
            "submit_keywords": list(self.submit_keywords),
            "detection_mode": self.detection_mode,
            "require_submit_button": self.require_submit_button,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
