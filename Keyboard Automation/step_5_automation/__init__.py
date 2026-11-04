"""
Step 5 Automation: Antigravity Lifecycle Sentinel Subsystem
==========================================================
Autonomous process sentinel that bridges the Antigravity application lifecycle
with the local dashboard server and Step 0-4 automated task pipeline.
"""

from .antigravity_lifecycle_sentinel import (
    AntigravityLifecycleSentinel,
    is_antigravity_running,
    is_port_listening,
)

__all__ = [
    "AntigravityLifecycleSentinel",
    "is_antigravity_running",
    "is_port_listening",
]
