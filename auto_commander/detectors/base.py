# -*- coding: utf-8 -*-
"""
Abstract base class and interface for AutoSelect-Commander detection engines.
"""

from abc import ABC, abstractmethod
from typing import Optional
from auto_commander.models import DetectionResult


class BaseDetector(ABC):
    """Abstract interface that all modal and option detectors implement."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine's required dependencies and runtime are ready."""
        pass

    @abstractmethod
    def scan(self) -> Optional[DetectionResult]:
        """Scans the desktop or target window and returns the best matching DetectionResult."""
        pass
