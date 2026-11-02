# -*- coding: utf-8 -*-
"""
Windows UIAutomation (UIA) Detection Engine.
Fast, DPI-invariant, direct accessibility tree traversal to find interactive decision buttons.
"""

from typing import Optional, Tuple

try:
    import uiautomation as auto
except ImportError:
    auto = None

from auto_commander.detectors.base import BaseDetector
from auto_commander.models import DetectionResult


class UIAutomationDetector(BaseDetector):
    """Scans the Windows UI Automation tree to locate Antigravity decision buttons."""

    def __init__(self, title_filter: str, target_keywords: Tuple[str, ...]):
        self.title_filter = title_filter.lower().strip() if title_filter else ""
        self.target_keywords = target_keywords

    def is_available(self) -> bool:
        """Returns True if uiautomation library is imported and available."""
        return auto is not None

    def scan(self) -> Optional[DetectionResult]:
        if not self.is_available():
            return None

        try:
            # 1. Search the foreground window first for instant response
            fg_win = auto.GetForegroundControl()
            if fg_win:
                win_name = (fg_win.Name or "").lower()
                # Skip console or commander terminal
                if "autoselect-commander launcher" not in win_name and "command prompt" not in win_name:
                    match = self._find_in_tree(fg_win)
                    if match:
                        rect = match.BoundingRectangle
                        if rect.width() > 10 and rect.height() > 5:
                            return DetectionResult(
                                x=rect.left,
                                y=rect.top,
                                width=rect.width(),
                                height=rect.height(),
                                confidence=0.99,
                                source="UIAutomation",
                                label=match.Name or "Recommended",
                            )

            # 2. Search top-level windows
            root = auto.GetRootControl()
            if not root:
                return None

            top_windows = root.GetChildren()
            for win in top_windows:
                name = (win.Name or "").lower()
                # Exclude own command window
                if "autoselect-commander launcher" in name or "cmd.exe" in name:
                    continue

                if self.title_filter:
                    if (
                        self.title_filter not in name
                        and "simulation" not in name
                        and "antigravity" not in name
                    ):
                        continue

                match = self._find_in_tree(win)
                if match:
                    rect = match.BoundingRectangle
                    if rect.width() > 10 and rect.height() > 5:
                        return DetectionResult(
                            x=rect.left,
                            y=rect.top,
                            width=rect.width(),
                            height=rect.height(),
                            confidence=0.99,
                            source="UIAutomation",
                            label=match.Name or "Recommended",
                        )
        except Exception:
            return None
        return None

    def find_by_keywords(self, keywords: Tuple[str, ...]) -> Optional[DetectionResult]:
        """Searches UIA tree specifically for elements matching given keywords (e.g. Submit button)."""
        if not self.is_available():
            return None
        try:
            fg_win = auto.GetForegroundControl()
            if fg_win:
                match = self._find_in_tree_for_keywords(fg_win, keywords)
                if match:
                    rect = match.BoundingRectangle
                    if rect.width() > 10 and rect.height() > 5:
                        return DetectionResult(
                            x=rect.left,
                            y=rect.top,
                            width=rect.width(),
                            height=rect.height(),
                            confidence=0.99,
                            source="UIAutomation",
                            label=match.Name or "Submit",
                        )
        except Exception:
            pass
        return None

    def _find_in_tree(self, parent_control):
        """Recursively checks controls for target keyword matches with depth limit."""
        return self._find_in_tree_for_keywords(parent_control, self.target_keywords)

    def _find_in_tree_for_keywords(self, parent_control, keywords: Tuple[str, ...]):
        try:
            ctrl_name = parent_control.Name or ""
            for kw in keywords:
                if kw.lower() in ctrl_name.lower():
                    return parent_control

            # Depth limit to keep inspection under 40ms
            for child in parent_control.GetChildren()[:30]:
                name = child.Name or ""
                for kw in keywords:
                    if kw.lower() in name.lower():
                        return child
                for grandchild in child.GetChildren()[:20]:
                    gname = grandchild.Name or ""
                    for kw in keywords:
                        if kw.lower() in gname.lower():
                            return grandchild
        except Exception:
            pass
        return None
