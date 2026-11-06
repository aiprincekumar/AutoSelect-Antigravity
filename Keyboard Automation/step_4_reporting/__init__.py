"""
Step 4: Reporting & Visual Dashboard Subsystem
=============================================
Package: step_4_reporting
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Standard: Department 06 (Backend & API Engineering) & Department 04 (UI/UX Design)
"""

from .step4_reporting import (
    Step4ReportingEngine,
    AutomationHistory,
    RunRecord,
    ChatHistory,
    QuestionDetail,
    get_last_input_tick,
    watch_for_user_input,
)
from .autostart import (
    enable_autostart,
    disable_autostart,
    is_autostart_enabled,
    get_autostart_status,
    get_startup_folder,
    get_shortcut_path,
)

__all__ = [
    "Step4ReportingEngine",
    "AutomationHistory",
    "RunRecord",
    "ChatHistory",
    "QuestionDetail",
    "get_last_input_tick",
    "watch_for_user_input",
    "enable_autostart",
    "disable_autostart",
    "is_autostart_enabled",
    "get_autostart_status",
    "get_startup_folder",
    "get_shortcut_path",
]
