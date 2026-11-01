# -*- coding: utf-8 -*-
"""
Safety boundary guards, console window self-click protection,
and click target validation for AutoSelect-Commander.
"""

from typing import Optional, Tuple
from auto_commander.models import Rect
from auto_commander.platform.win32_window import AntigravityWindowManager


class ClickSafetyValidator:
    """Validates mouse click coordinates to ensure safety, containment, and prevent self-clicking."""

    @classmethod
    def validate_click_target(
        cls,
        x: int,
        y: int,
        target_hwnd: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Validates that click coordinates:
        1. Fall within physical display boundaries.
        2. Fall inside the target window's bounding box when targeting Antigravity.
        3. Never self-clicks the AutoSelect-Commander console.
           When Antigravity is the target window, the console is safely minimized or pushed
           behind so Antigravity receives the click cleanly without false safety blocks.
        """
        return AntigravityWindowManager.validate_click_target(x, y, target_hwnd=target_hwnd)

    @classmethod
    def is_console_foreground(cls) -> bool:
        """Returns True if own console window is currently the active foreground window."""
        return AntigravityWindowManager.is_console_foreground()

    @classmethod
    def minimize_console(cls) -> bool:
        """Minimizes the console window so it does not obstruct Antigravity."""
        return AntigravityWindowManager.minimize_console()

    @classmethod
    def get_console_window_rect(cls) -> Optional[Rect]:
        """Returns the bounding Rect of own console/terminal window."""
        return AntigravityWindowManager.get_console_window_rect()


# Module-level convenience functions
validate_click_target = ClickSafetyValidator.validate_click_target
is_console_foreground = ClickSafetyValidator.is_console_foreground
minimize_console = ClickSafetyValidator.minimize_console
get_console_window_rect = ClickSafetyValidator.get_console_window_rect
