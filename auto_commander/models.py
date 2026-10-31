# -*- coding: utf-8 -*-
"""
Data models and geometric primitives for AutoSelect-Commander.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class Point:
    """2D Cartesian point representing screen coordinates."""
    x: int
    y: int

    def distance_to(self, other: "Point") -> float:
        import math
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Rect:
    """Bounding rectangle for windows, controls, or detected elements."""
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, px: int, py: int) -> bool:
        """Checks if a point (px, py) is strictly inside this rectangle."""
        return self.left <= px <= self.right and self.top <= py <= self.bottom


@dataclass
class DetectionResult:
    """Result of visual, OCR, or UIAutomation element detection."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    source: str  # 'WindowsOcr', 'UIAutomation', 'Vision', or 'LayoutInference'
    label: str

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)
