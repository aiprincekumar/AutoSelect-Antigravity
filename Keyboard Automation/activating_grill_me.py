#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Activating Grill Me Chat in Antigravity - Master Identification & GUI Suite
=============================================================================
Target: Antigravity AI Coding Agent Sessions
Workspace: AutoSelect-Commander / Keyboard Automation (Master Suite)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Mission:
  Automatically detect which Antigravity chat/conversation currently has
  "Grill Me" / `ask_question` waiting for user response (unanswered question / pending selection),
  and provide an automated 1-click execution flow:
    - Step A: Identification - Scan brain transcript logs, find pending `ask_question` tool calls,
              and extract Conversation ID, timestamp, user prompt, question text, and options.
    - Step B: Presentation - Print clean terminal summary with questions and auto-detected
              recommended options, and export structured selection state (Dept 06 standard).
    - Step C: Focus - Un-minimize and bring Antigravity IDE window to the foreground using
              bulletproof Windows 10/11 foreground lock bypass (ShowWindow SW_RESTORE, Alt key pulse,
              AttachThreadInput, Z-order bump, and process/class matching).
    - Step D: GUI Selection - Autonomously select and activate that chat in the Antigravity GUI
              via mouse movement/click on the conversation row and `Ctrl + L` chat panel focus.

Architecture:
  - 100% Python Standard Library core (ctypes, json, os, sys, time, dataclasses).
  - Optional interop with PyAutoGUI and Pillow for enhanced visual mouse movements and screenshots.
  - Standardized JSON Envelope output adhering to Department 06 API standards.
"""

from __future__ import annotations

import os
import sys
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Safe stdout and stderr encoding configuration for Windows consoles
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger("ActivatingGrillMe")

# Optional PyAutoGUI integration
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None


# ============================================================================
# Win32 Native Subsystem (Focus Lock Bypass & Window Activation)
# ============================================================================
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Virtual-Key codes
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt key (used for foreground lock release)
    VK_RETURN = 0x0D
    VK_TAB = 0x09
    VK_L = 0x4C
    VK_1 = 0x31
    VK_2 = 0x32
    VK_3 = 0x33
    VK_4 = 0x34
    VK_5 = 0x35

    # ShowWindow constants
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_MAXIMIZE = 3
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_RESTORE = 9

    # Window Pos flags
    HWND_TOP = 0
    HWND_TOPMOST = -1
    HWND_NOTOPMOST = -2
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_SHOWWINDOW = 0x0040

    # ASFW_ANY constant for AllowSetForegroundWindow
    ASFW_ANY = -1

    # Mouse event flags
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]

    # Setup function prototypes
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int

    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int

    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL

    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.IsZoomed.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindowAsync.restype = wintypes.BOOL

    user32.OpenIcon.argtypes = [wintypes.HWND]
    user32.OpenIcon.restype = wintypes.BOOL

    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.restype = wintypes.BOOL

    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL

    user32.SetActiveWindow.argtypes = [wintypes.HWND]
    user32.SetActiveWindow.restype = wintypes.HWND

    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND

    user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
    user32.AllowSetForegroundWindow.restype = wintypes.BOOL

    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL

    user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.c_void_p]
    user32.GetWindowPlacement.restype = wintypes.BOOL

    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL

    user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user32.OpenInputDesktop.restype = wintypes.HANDLE

    user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
    user32.SetThreadDesktop.restype = wintypes.BOOL

    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    kernel32.GetConsoleWindow.argtypes = []
    kernel32.GetConsoleWindow.restype = wintypes.HWND

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL

    user32.EnumDesktopWindows.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPARAM]
    user32.EnumDesktopWindows.restype = wintypes.BOOL

    if hasattr(user32, "SwitchToThisWindow"):
        user32.SwitchToThisWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
        user32.SwitchToThisWindow.restype = None


def ensure_input_desktop():
    """Ensure current thread is attached to the active interactive input desktop."""
    if not IS_WINDOWS:
        return None
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return hdesk
    except Exception:
        pass
    return None


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class QuestionPayload:
    """Represents an individual question in an ask_question prompt."""
    question_index: int
    question: str
    options: List[str]
    is_multi_select: bool = False
    recommended_option_index: Optional[int] = None
    recommended_option_text: Optional[str] = None

    def __post_init__(self):
        # Auto-detect recommended option if present
        for idx, opt in enumerate(self.options, start=1):
            if opt.strip().startswith("(Recommended)") or "[Recommended]" in opt:
                self.recommended_option_index = idx
                self.recommended_option_text = opt
                break
        # Fallback to option 1 if no explicit recommendation
        if self.recommended_option_index is None and self.options:
            self.recommended_option_index = 1
            self.recommended_option_text = self.options[0]


@dataclass
class PendingGrillMeChat:
    """Represents an Antigravity conversation with an active, unanswered ask_question state."""
    conversation_id: str
    step_index: int
    created_at: str
    topic_summary: str
    last_user_prompt: str
    questions: List[QuestionPayload] = field(default_factory=list)
    transcript_path: str = ""
    is_last_step: bool = True
    total_steps: int = 0
    total_questions_count: int = 0
    is_multi_question: bool = False

    def __post_init__(self):
        if self.questions:
            self.total_questions_count = len(self.questions)
        self.is_multi_question = (self.total_questions_count > 1)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SelectionResult:
    """Represents the prepared selection state ready for confirmation or automation."""
    conversation_id: str
    selected_at: str
    status: str
    questions_count: int
    selections: List[Dict[str, Any]] = field(default_factory=list)
    window_focused: bool = False
    gui_chat_selected: bool = False
    dry_run: bool = False
    total_questions_count: int = 0
    is_multi_question: bool = False

    def __post_init__(self):
        if not self.total_questions_count:
            self.total_questions_count = self.questions_count
        if not self.is_multi_question:
            self.is_multi_question = self.total_questions_count > 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Step A: Identification Engine (Transcript Parsing)
# ============================================================================

class GrillMeDetector:
    """
    Method 1 Engine: File System & Transcript Parsing.
    Scans Antigravity brain storage to identify active/unanswered ask_question prompts.
    """

    DEFAULT_BRAIN_RELATIVE_PATH = os.path.join(".gemini", "antigravity", "brain")

    def __init__(self, brain_dir: Optional[str] = None):
        self.brain_dir = self._resolve_brain_dir(brain_dir)

    def _resolve_brain_dir(self, explicit_dir: Optional[str]) -> Path:
        """Resolve the Antigravity brain directory with multiple environment fallbacks."""
        if explicit_dir and os.path.isdir(explicit_dir):
            return Path(explicit_dir)

        # Environment variable override
        env_brain = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
        if env_brain and os.path.isdir(env_brain):
            return Path(env_brain)

        # User home standard path
        user_home = Path.home()
        standard_path = user_home / ".gemini" / "antigravity" / "brain"
        if standard_path.is_dir():
            return standard_path

        # Local AppData fallback
        app_data = os.environ.get("LOCALAPPDATA")
        if app_data:
            alt_path = Path(app_data) / "Google" / "Antigravity" / "brain"
            if alt_path.is_dir():
                return alt_path

        return standard_path

    def is_valid_brain_dir(self) -> bool:
        """Check if resolved brain directory exists on disk."""
        return self.brain_dir.is_dir()

    def scan_transcripts(self) -> List[PendingGrillMeChat]:
        """
        Scan all conversation subdirectories inside brain_dir.
        Returns a list of PendingGrillMeChat objects sorted by created_at descending.
        """
        if not self.is_valid_brain_dir():
            logger.warning("Brain directory does not exist or is inaccessible: %s", self.brain_dir)
            return []

        pending_chats: List[PendingGrillMeChat] = []

        try:
            subdirs = [p for p in self.brain_dir.iterdir() if p.is_dir()]
        except Exception as e:
            logger.error("Failed to list brain directory: %s", e)
            return []

        for cdir in subdirs:
            cid = cdir.name
            # Prioritize transcript_full.jsonl to prevent truncation on large questionnaires (N >= 4)
            full_file = cdir / ".system_generated" / "logs" / "transcript_full.jsonl"
            compact_file = cdir / ".system_generated" / "logs" / "transcript.jsonl"
            transcript_file = full_file if full_file.is_file() else compact_file
            if not transcript_file.is_file():
                continue

            pending = self._parse_conversation_transcript(cid, transcript_file)
            if pending:
                pending_chats.append(pending)

        # Sort pending chats by timestamp descending (most recent first)
        pending_chats.sort(key=lambda c: c.created_at, reverse=True)
        return pending_chats

    def _parse_conversation_transcript(self, conversation_id: str, transcript_path: Path) -> Optional[PendingGrillMeChat]:
        """Parse an individual transcript file and determine if it has an active pending question."""
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                lines = [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            logger.debug("Could not read/parse %s: %s", transcript_path, e)
            return None

        if not lines:
            return None

        # Track conversation topic and user prompts
        initial_user_prompt = ""
        last_user_prompt = ""
        for step in lines:
            if step.get("type") == "USER_INPUT":
                content = str(step.get("content", "")).strip()
                if "<USER_REQUEST>" in content:
                    try:
                        content = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                    except Exception:
                        pass
                if not initial_user_prompt and content:
                    initial_user_prompt = content
                if content:
                    last_user_prompt = content

        # Inspect tool calls for ask_question from newest to oldest
        total_steps = len(lines)
        for i in range(total_steps - 1, -1, -1):
            step = lines[i]
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "ask_question":
                    # Check if this ask_question call has been answered by any subsequent step
                    is_answered = self._is_step_answered(lines, i)
                    if not is_answered:
                        questions = self._extract_question_payloads(tc.get("args", {}))
                        created_at = step.get("created_at", "")
                        step_index = step.get("step_index", i)
                        is_last = (i == total_steps - 1)

                        topic_snippet = (initial_user_prompt[:80] + "...") if len(initial_user_prompt) > 80 else initial_user_prompt
                        last_prompt_snippet = (last_user_prompt[:120] + "...") if len(last_user_prompt) > 120 else last_user_prompt

                        return PendingGrillMeChat(
                            conversation_id=conversation_id,
                            step_index=step_index,
                            created_at=created_at,
                            topic_summary=topic_snippet or "<Untitled Session>",
                            last_user_prompt=last_prompt_snippet or "<No User Prompt Recorded>",
                            questions=questions,
                            transcript_path=str(transcript_path),
                            is_last_step=is_last,
                            total_steps=total_steps
                        )
                    else:
                        # Newest ask_question in this conversation was answered
                        return None

        return None

    def _is_step_answered(self, lines: List[Dict[str, Any]], question_step_idx: int) -> bool:
        """Check if any subsequent step after question_step_idx represents an answer/fulfillment."""
        for j in range(question_step_idx + 1, len(lines)):
            subsequent = lines[j]
            stype = subsequent.get("type", "")

            if stype == "GENERIC":
                content = str(subsequent.get("content", ""))
                if "Completed At:" in content or "A1:" in content or "Answer" in content:
                    return True

            if stype == "USER_INPUT":
                return True

            if stype == "PLANNER_RESPONSE" and subsequent.get("status") == "DONE":
                if not any(tc.get("name") == "ask_question" for tc in subsequent.get("tool_calls", [])):
                    return True

        return False

    def _extract_question_payloads(self, args: Dict[str, Any]) -> List[QuestionPayload]:
        """Extract structured QuestionPayload instances from raw tool arguments."""
        questions_raw = args.get("questions")

        # 1. Parse stringified JSON if needed (support strict=False for multiline Hindi/Unicode strings)
        if isinstance(questions_raw, str):
            try:
                questions_raw = json.loads(questions_raw, strict=False)
            except Exception:
                try:
                    cleaned = questions_raw.encode("utf-8").decode("unicode_escape", errors="ignore")
                    questions_raw = json.loads(cleaned, strict=False)
                except Exception as e:
                    logger.debug("Failed to decode JSON string questions: %s", e)
                    questions_raw = []

        # 2. Support single-question direct args format: {"question": "...", "options": [...]}
        if not questions_raw and ("question" in args or "options" in args):
            single_q = args.get("question", "Question 1")
            single_opts = args.get("options", [])
            if isinstance(single_opts, str):
                try:
                    single_opts = json.loads(single_opts, strict=False)
                except Exception:
                    single_opts = [single_opts]
            questions_raw = [{
                "question": single_q,
                "options": single_opts,
                "is_multi_select": bool(args.get("is_multi_select", False))
            }]

        if not isinstance(questions_raw, list):
            questions_raw = [questions_raw] if isinstance(questions_raw, dict) else []

        payloads: List[QuestionPayload] = []
        for idx, item in enumerate(questions_raw, start=1):
            if not isinstance(item, dict):
                continue
            q_text = str(item.get("question", f"Question {idx}")).strip()
            opts_raw = item.get("options", [])
            if isinstance(opts_raw, str):
                try:
                    opts_raw = json.loads(opts_raw, strict=False)
                except Exception:
                    opts_raw = [opts_raw]
            options = [str(opt).strip() for opt in opts_raw if str(opt).strip()]
            is_multi = bool(item.get("is_multi_select", False))

            payloads.append(QuestionPayload(
                question_index=idx,
                question=q_text,
                options=options,
                is_multi_select=is_multi
            ))

        return payloads


# ============================================================================
# Step C: Bulletproof Window Finder & Foreground Activation Subsystem
# ============================================================================

class AntigravityFocusManager:
    """
    Robust Windows 10/11 window finding, un-minimizing, and foreground activation.
    Overcomes Windows foreground lock, thread desktop boundaries, and minimized states.
    """

    TARGET_PROCESSES = ("antigravity.exe", "antigravity", "electron.exe")
    TARGET_CLASS = "Chrome_WidgetWin_1"
    TARGET_TITLES = ("antigravity", "gemini", "autoselect-commander", "taskbar hud")
    DISQUALIFIED_BROWSER_PROCS = {
        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
        "opera.exe", "vivaldi.exe", "iexplore.exe", "safari.exe"
    }

    @classmethod
    def get_process_name_for_hwnd(cls, hwnd: int) -> str:
        """Retrieve executable process name for a window handle."""
        if not IS_WINDOWS or not hwnd:
            return ""
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return ""

        # Try psutil first if available
        try:
            import psutil
            p = psutil.Process(pid.value)
            return p.name().lower()
        except Exception:
            pass

        # Native fallback via QueryFullProcessImageNameW
        try:
            h_proc = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
            if h_proc:
                buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                    kernel32.CloseHandle(h_proc)
                    return os.path.basename(buf.value).lower()
                kernel32.CloseHandle(h_proc)
        except Exception:
            pass

        return ""

    @classmethod
    def find_antigravity_window(cls) -> Optional[Tuple[int, str, dict]]:
        """
        Enumerate windows and score them to identify the real Antigravity IDE window.
        Returns: (hwnd, title, window_info_dict) or None
        """
        if not IS_WINDOWS:
            return None

        hdesk = ensure_input_desktop()
        console_hwnd = kernel32.GetConsoleWindow() if IS_WINDOWS else None

        candidates: List[Tuple[int, int, str, dict]] = []  # (score, hwnd, title, info)

        blacklisted_procs = {
            "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe", "wt.exe",
            "windowsterminal.exe", "python.exe", "pythonw.exe", "explorer.exe",
            "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
            "opera.exe", "vivaldi.exe", "iexplore.exe", "safari.exe"
        }

        def enum_cb(hwnd, lparam):
            if console_hwnd and hwnd == console_hwnd:
                return True
            try:
                if not user32.IsWindow(hwnd):
                    return True

                visible = bool(user32.IsWindowVisible(hwnd))
                iconic = bool(user32.IsIconic(hwnd))
                if not visible and not iconic:
                    return True

                pname = cls.get_process_name_for_hwnd(hwnd)
                if pname in blacklisted_procs:
                    return True

                # Title
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()
                t_lower = title.lower()

                # Class
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                cls_name = cls_buf.value.strip()

                # Rect
                rect = wintypes.RECT()
                rect_ok = bool(user32.GetWindowRect(hwnd, ctypes.byref(rect)))
                w = (rect.right - rect.left) if rect_ok else 0
                h = (rect.bottom - rect.top) if rect_ok else 0

                # Normal placement for minimized windows
                if iconic:
                    wp = WINDOWPLACEMENT()
                    wp.length = ctypes.sizeof(WINDOWPLACEMENT)
                    if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                        w = wp.rcNormalPosition.right - wp.rcNormalPosition.left
                        h = wp.rcNormalPosition.bottom - wp.rcNormalPosition.top

                score = 0

                # 1. Process matching (Antigravity.exe is the highest weight)
                is_antigravity_proc = any(target in pname for target in cls.TARGET_PROCESSES)
                if is_antigravity_proc:
                    score += 150
                    if cls_name == cls.TARGET_CLASS:
                        score += 50
                    if (w >= 400 and h >= 300) or iconic:
                        score += 30

                # 2. Window class matching
                if cls_name == cls.TARGET_CLASS:
                    score += 20

                # 3. Title matching
                for target_t in cls.TARGET_TITLES:
                    if target_t in t_lower:
                        score += 40
                        break

                # Self-exclusion from runner/terminal window titles
                if any(x in t_lower for x in ["run_activating", "activating_grill_me", "test_activating"]):
                    score -= 200

                if score > 0:
                    info = {
                        "hwnd": hwnd,
                        "title": title,
                        "class": cls_name,
                        "process_name": pname,
                        "visible": visible,
                        "minimized": iconic,
                        "width": w,
                        "height": h,
                        "rect": (rect.left, rect.top, rect.right, rect.bottom)
                    }
                    candidates.append((score, hwnd, title, info))
            except Exception:
                pass
            return True

        cb = WNDENUMPROC(enum_cb)
        if hdesk:
            try:
                user32.EnumDesktopWindows(hdesk, cb, 0)
            except Exception:
                user32.EnumWindows(cb, 0)
        else:
            user32.EnumWindows(cb, 0)

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        if best[0] > 0:
            return (best[1], best[2], best[3])

        return None

    @classmethod
    def bring_to_foreground(cls, hwnd: int) -> bool:
        """
        Bulletproof foreground activation on Windows 10/11:
        1. Attach thread to active interactive desktop.
        2. Unlock OS foreground lock via AllowSetForegroundWindow & virtual Alt key tap.
        3. If iconic/minimized: call ShowWindow(SW_RESTORE) + OpenIcon.
        4. ShowWindow(SW_SHOW).
        5. AttachThreadInput between current thread, target thread, and foreground thread.
        6. Z-order bump (HWND_TOPMOST -> HWND_NOTOPMOST).
        7. SetForegroundWindow, SwitchToThisWindow, BringWindowToTop, SetActiveWindow, SetFocus.
        8. Detach threads.
        9. Secondary pulse if needed.
        """
        if not IS_WINDOWS or not hwnd or not user32.IsWindow(hwnd):
            return False

        try:
            ensure_input_desktop()

            # Unlock OS foreground lock
            try:
                user32.AllowSetForegroundWindow(ASFW_ANY)
            except Exception:
                pass

            # Step 1: Window size & restore management
            # Rule: "विंडोज अगर बड़ा है तो बड़ा रहने दो और छोटा है तो बड़ा करो।"
            # If already maximized (IsZoomed == True), keep it maximized (SW_SHOW).
            # If not maximized (small windowed or minimized), maximize it (SW_MAXIMIZE).
            # NEVER call SW_RESTORE (9) on a maximized window!
            if user32.IsZoomed(hwnd):
                logger.info("Antigravity window (HWND: %d) is already maximized. Keeping it maximized (SW_SHOW)...", hwnd)
                user32.ShowWindow(hwnd, SW_SHOW)
                user32.ShowWindowAsync(hwnd, SW_SHOW)
            else:
                logger.info("Antigravity window (HWND: %d) is not maximized (small or minimized). Maximizing window (SW_MAXIMIZE)...", hwnd)
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
                time.sleep(0.1)

            # Step 3: Virtual Alt key tap to break foreground lock
            try:
                user32.keybd_event(VK_MENU, 0, 0, 0)
                user32.keybd_event(VK_MENU, 0, 2, 0)  # KEYEVENTF_KEYUP
            except Exception:
                pass

            # Step 4: AttachThreadInput
            cur_thread = kernel32.GetCurrentThreadId()
            target_thread = user32.GetWindowThreadProcessId(hwnd, None)
            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0

            attached_fg = False
            attached_target = False
            if fg_thread and fg_thread != cur_thread:
                attached_fg = bool(user32.AttachThreadInput(cur_thread, fg_thread, True))
            if target_thread and target_thread != cur_thread:
                attached_target = bool(user32.AttachThreadInput(cur_thread, target_thread, True))

            try:
                # Step 5: Z-Order bump
                user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                )
                user32.SetWindowPos(
                    hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                )

                # Step 6: Bring to Top & Force Foreground
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)

                if hasattr(user32, "SwitchToThisWindow"):
                    user32.SwitchToThisWindow(hwnd, True)

                user32.SetActiveWindow(hwnd)
                user32.SetFocus(hwnd)
            finally:
                if attached_fg:
                    user32.AttachThreadInput(cur_thread, fg_thread, False)
                if attached_target:
                    user32.AttachThreadInput(cur_thread, target_thread, False)

            time.sleep(0.2)

            # Secondary pulse verification
            curr_fg = user32.GetForegroundWindow()
            if curr_fg != hwnd:
                user32.SetForegroundWindow(hwnd)
                if hasattr(user32, "SwitchToThisWindow"):
                    user32.SwitchToThisWindow(hwnd, True)
                time.sleep(0.1)

            curr_fg = user32.GetForegroundWindow()
            success = (curr_fg == hwnd) or not bool(user32.IsIconic(hwnd))
            return success

        except Exception as e:
            logger.error("Error bringing Antigravity window to foreground: %s", e)
            return False


# ============================================================================
# Step D: GUI Chat Selection Engine
# ============================================================================

class AntigravityGuiSelector:
    """
    Autonomously selects and activates the pending chat in the Antigravity GUI.
    1. Focuses Antigravity window.
    2. Moves mouse to the chat row in the sidebar/panel and clicks to select it.
    3. Sends Ctrl + L to bring focus directly into the chat pane and input area.
    4. Optionally selects the recommended radio option and submits.
    """

    DEFAULT_CLICK_X = 580
    DEFAULT_CLICK_Y = 815

    @classmethod
    def load_calibrated_coordinates(cls) -> Tuple[int, int]:
        """Try loading calibrated coordinates from local config.json if available."""
        try:
            # Check local config.json in the same directory
            cfg_path = Path(__file__).resolve().parent / "config.json"
            if cfg_path.is_file():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    # Check steps.step1_chat or coordinates.chat_click_x
                    step1 = cfg.get("steps", {}).get("step1_chat", {})
                    coords = cfg.get("coordinates", {})
                    x = step1.get("x", coords.get("chat_click_x", cls.DEFAULT_CLICK_X))
                    y = step1.get("y", coords.get("chat_click_y", cls.DEFAULT_CLICK_Y))
                    return int(x), int(y)
        except Exception:
            pass
        return cls.DEFAULT_CLICK_X, cls.DEFAULT_CLICK_Y

    @classmethod
    def select_chat_in_gui(
        cls,
        hwnd: int,
        target_cid: str,
        topic: str = "",
        dry_run: bool = False,
        select_option_number: Optional[int] = None,
        auto_submit: bool = False
    ) -> bool:
        """
        Executes the GUI chat selection sequence via modular two-script engine:
        1. Delegates to Step 2 (step2_gui_chat_select.py) for CDP DOM precision selection.
        2. Falls back to calibrated sidebar click and Ctrl + L pane focus.
        """
        logger.info("Executing GUI Chat Selection for CID: %s...", target_cid)

        if dry_run:
            logger.info("  [DRY-RUN] Would click chat row and send Ctrl + L to focus chat pane.")
            return True

        # Delegate to Step 2 engine if available
        try:
            from step2_gui_chat_select import AntigravityGUISelector
            sel_res = AntigravityGUISelector.select_chat(
                target_cid=target_cid,
                topic=topic,
                hwnd=hwnd,
                dry_run=dry_run,
                select_option_number=select_option_number,
                auto_submit=auto_submit
            )
            if sel_res.get("success"):
                return True
        except Exception as e:
            logger.debug("Step 2 selector delegation fallback: %s", e)

        if not IS_WINDOWS:
            logger.warning("GUI Chat selection is only supported on Windows.")
            return False

        # 1. Ensure Antigravity window is foregrounded
        focused = AntigravityFocusManager.bring_to_foreground(hwnd)
        if not focused:
            logger.warning("Target window foregrounding reported partial state, continuing...")
        time.sleep(0.3)

        # 2. Get target coordinates
        x, y = cls.load_calibrated_coordinates()

        # Adjust coordinates relative to window bounds if window is windowed (not maximized)
        rect = wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            win_w = rect.right - rect.left
            win_h = rect.bottom - rect.top
            # If coordinates fall outside the window rect, adjust to middle-left sidebar area
            if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
                x = rect.left + min(350, int(win_w * 0.25))
                y = rect.top + min(400, int(win_h * 0.5))

        logger.info("Navigating mouse to Chat selection target: (X=%d, Y=%d)...", x, y)

        # 3. Mouse Movement & Tactile Click
        try:
            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                pyautogui.moveTo(x, y, duration=0.6, tween=pyautogui.easeOutQuad)
                time.sleep(0.3)  # Tactile hover delay so UI registers hover state
                pyautogui.click(x=x, y=y)
                time.sleep(0.2)
            else:
                # Native Win32 SetCursorPos & mouse_event
                user32.SetCursorPos(x, y)
                time.sleep(0.3)
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.08)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.2)
            logger.info("Chat selection click dispatched at (%d, %d).", x, y)
        except Exception as e:
            logger.warning("Mouse click dispatched with fallback warning: %s", e)

        # 4. Keyboard Shortcut: Ctrl + L (Focus Chat Pane & Input Prompt)
        time.sleep(0.3)
        logger.info("Sending shortcut [Ctrl + L] to activate Antigravity Chat panel...")
        try:
            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                pyautogui.hotkey("ctrl", "l")
            else:
                cls._send_key_combo([VK_CONTROL, VK_L])
            time.sleep(0.3)
        except Exception as e:
            logger.warning("Ctrl+L shortcut error: %s", e)

        # 5. Optional Option Selection and Submission
        if select_option_number is not None and select_option_number > 0:
            logger.info("Selecting Option [%d] in GUI...", select_option_number)
            try:
                # Shift + Tab to move focus to options radio buttons
                if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                    pyautogui.hotkey("shift", "tab")
                    time.sleep(0.2)
                    pyautogui.press(str(select_option_number))
                    time.sleep(0.2)
                    if auto_submit:
                        logger.info("Submitting option selection ([Enter])...")
                        pyautogui.press("enter")
                else:
                    cls._send_key_combo([VK_SHIFT, VK_TAB])
                    time.sleep(0.2)
                    vk_num = VK_1 + (select_option_number - 1)
                    cls._send_key_combo([vk_num])
                    time.sleep(0.2)
                    if auto_submit:
                        logger.info("Submitting option selection ([Enter])...")
                        cls._send_key_combo([VK_RETURN])
            except Exception as e:
                logger.warning("Option selection key sequence error: %s", e)

        time.sleep(0.2)
        logger.info("GUI Chat selection completed successfully.")
        return True

    @classmethod
    def _send_key_combo(cls, keys: List[int], hold_delay: float = 0.05):
        """Native Win32 key press and release helper."""
        if not IS_WINDOWS:
            return
        for k in keys:
            user32.keybd_event(k, 0, 0, 0)
            time.sleep(0.01)
        time.sleep(hold_delay)
        for k in reversed(keys):
            user32.keybd_event(k, 0, 2, 0)  # KEYEVENTF_KEYUP
            time.sleep(0.01)


# ============================================================================
# Step B: Selection Engine & State Packaging
# ============================================================================

class GrillMeSelector:
    """
    Step B Engine: Selection.
    Selects target conversation, evaluates questions/options, prepares selection payload,
    and coordinates window activation and GUI selection.
    """

    def __init__(self, detector: Optional[GrillMeDetector] = None):
        self.detector = detector or GrillMeDetector()

    def select_conversation(
        self,
        target_cid: Optional[str] = None,
        auto_latest: bool = True
    ) -> Optional[PendingGrillMeChat]:
        """
        Identify and select the target conversation.
        If target_cid is given, search specifically for that ID.
        If not given and auto_latest is True, pick the most recent pending chat.
        """
        pending_chats = self.detector.scan_transcripts()
        if not pending_chats:
            return None

        if target_cid:
            target_norm = target_cid.strip().lower()
            for chat in pending_chats:
                if chat.conversation_id.lower().startswith(target_norm):
                    return chat
            return None

        if auto_latest:
            return pending_chats[0]

        return None

    def prepare_selection(
        self,
        chat: PendingGrillMeChat,
        chosen_option_index: Optional[int] = None,
        use_recommended: bool = True,
        dry_run: bool = False
    ) -> SelectionResult:
        """
        Build the prepared selection state for the chosen conversation.
        Maps each question to the selected option index and text.
        """
        selections: List[Dict[str, Any]] = []

        for q in chat.questions:
            if chosen_option_index is not None and 1 <= chosen_option_index <= len(q.options):
                selected_idx = chosen_option_index
                selected_text = q.options[selected_idx - 1]
            elif use_recommended and q.recommended_option_index:
                selected_idx = q.recommended_option_index
                selected_text = q.recommended_option_text or q.options[selected_idx - 1]
            else:
                selected_idx = 1
                selected_text = q.options[0] if q.options else ""

            selections.append({
                "question_index": q.question_index,
                "question": q.question,
                "selected_option_index": selected_idx,
                "selected_option_text": selected_text,
                "is_multi_select": q.is_multi_select,
                "total_options": len(q.options),
                "is_recommended": (selected_idx == q.recommended_option_index)
            })

        now_iso = datetime.now(timezone.utc).isoformat()
        total_questions_count = len(chat.questions)
        is_multi_question = total_questions_count > 1
        return SelectionResult(
            conversation_id=chat.conversation_id,
            selected_at=now_iso,
            status="READY_FOR_CONFIRMATION",
            questions_count=total_questions_count,
            total_questions_count=total_questions_count,
            is_multi_question=is_multi_question,
            selections=selections,
            dry_run=dry_run
        )

    def export_selection_state(
        self,
        result: SelectionResult,
        output_file: Optional[str] = None
    ) -> Path:
        """Export the selection state payload to a JSON file (Dept 06 standard envelope)."""
        if output_file:
            out_path = Path(output_file)
        else:
            out_path = Path(__file__).parent / "last_selection_state.json"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "success": True,
            "data": result.to_dict(),
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "generator": "activating_grill_me.py (Method 1)"
            }
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)

        # Also sync target_chat.json for step2 compatibility if default path
        if not output_file:
            target_chat_path = Path(__file__).parent / "target_chat.json"
            try:
                with open(target_chat_path, "w", encoding="utf-8") as f:
                    json.dump(envelope, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return out_path


# ============================================================================
# CLI Presentation & Terminal Formatting
# ============================================================================

def format_chat_card(chat: PendingGrillMeChat, index: int = 1) -> str:
    """Format an individual pending chat into a clean terminal card."""
    border = "=" * 76
    count_label = "Multiple Questions" if chat.is_multi_question else "Single Question"
    lines = [
        border,
        f"  [CHAT #{index}] ACTIVE GRILL ME WAITING FOR RESPONSE",
        border,
        f"  Conversation ID : {chat.conversation_id}",
        f"  Created At      : {chat.created_at}",
        f"  Step Index      : {chat.step_index} / {chat.total_steps}",
        f"  Initial Prompt  : {chat.topic_summary}",
        f"  Last User Input : {chat.last_user_prompt}",
        f"  📊 Total Questions Count: {chat.total_questions_count} ({count_label})",
        "-" * 76,
        f"  Pending Questions ({chat.total_questions_count}):"
    ]
    for q in chat.questions:
        multi_badge = " [Multi-Select]" if q.is_multi_select else " [Single-Choice]"
        lines.append(f"\n    Q{q.question_index}: {q.question}{multi_badge}")
        for o_idx, opt in enumerate(q.options, start=1):
            rec_badge = " << (Recommended)" if o_idx == q.recommended_option_index else ""
            lines.append(f"       [{o_idx}] {opt}{rec_badge}")

    lines.append(border)
    return "\n".join(lines)


def format_selection_card(result: SelectionResult, chat: PendingGrillMeChat) -> str:
    """Format the prepared selection result into a confirmation card."""
    border = "*" * 76
    count_label = "Multiple Questions" if result.is_multi_question else "Single Question"
    lines = [
        border,
        "  [1-CLICK EXECUTION RESULT] GRILL ME ACTIVATION COMPLETED",
        border,
        f"  Target Chat     : {result.conversation_id}",
        f"  Status          : {result.status}",
        f"  Selected At     : {result.selected_at}",
        f"  📊 Total Questions Count: {result.total_questions_count} ({count_label})",
        f"  Window Focused  : {'YES (Brought to Foreground)' if result.window_focused else 'NO'}",
        f"  GUI Chat Click  : {'YES (Selected & Focused)' if result.gui_chat_selected else 'NO'}",
        f"  Dry Run Mode    : {'YES (Simulation Only)' if result.dry_run else 'NO (Live)'}",
        "-" * 76,
        "  Active Selections:"
    ]
    for sel in result.selections:
        q_idx = sel.get("question_index")
        s_idx = sel.get("selected_option_index")
        s_txt = sel.get("selected_option_text")
        rec = " [Auto-Selected Recommended]" if sel.get("is_recommended") else ""
        lines.append(f"    Q{q_idx} -> Option [{s_idx}]: {s_txt}{rec}")

    lines.append(border)
    return "\n".join(lines)


# ============================================================================
# Main CLI Entrypoint (Streamlined 1-Click Execution)
# ============================================================================

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Activating Grill Me Chat in Antigravity - Method 1: File System & Transcript Parsing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Streamlined 1-Click Execution:
  # Simply run without arguments to automatically scan, summarize, focus window, and select chat:
  python activating_grill_me.py

Advanced Options:
  # Dry-run test mode (inspect without moving mouse or clicking)
  python activating_grill_me.py --dry-run

  # Scan and list pending chats only (no focus or GUI click)
  python activating_grill_me.py --scan

  # Select specific conversation ID
  python activating_grill_me.py --select 0d5e735e-85e3-4a0d-bffd-5e3e4fcf72da

  # Choose specific option number across questions (default: recommended option)
  python activating_grill_me.py --option 2

  # Also trigger option radio selection & submit in GUI
  python activating_grill_me.py --select-option --auto-submit

  # Output in standardized JSON envelope
  python activating_grill_me.py --json
        """
    )

    parser.add_argument("--scan", action="store_true",
                        help="Scan and list all active pending Grill Me chats only (no focus/GUI click).")
    parser.add_argument("--select", type=str, nargs="?", const="", default=None,
                        help="Select a specific conversation by ID (or prefix).")
    parser.add_argument("--auto-select", action="store_true",
                        help="Explicitly enable auto-select newest chat (enabled by default).")
    parser.add_argument("--option", type=int, default=None,
                        help="Explicit option index to select (default: recommended option or 1).")
    parser.add_argument("--no-focus", action="store_true",
                        help="Disable bringing Antigravity window to foreground.")
    parser.add_argument("--no-click", action="store_true",
                        help="Disable GUI mouse click and chat selection.")
    parser.add_argument("--select-option", action="store_true",
                        help="Also select the recommended option radio button via keyboard.")
    parser.add_argument("--auto-submit", action="store_true",
                        help="Also press Enter to submit selection in GUI.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in dry-run simulation mode (no mouse moves, no clicks).")
    parser.add_argument("--json", action="store_true",
                        help="Output result as Department 06 JSON response envelope.")
    parser.add_argument("--output-file", type=str, default=None,
                        help="File path to save the prepared selection state JSON.")
    parser.add_argument("--brain-dir", type=str, default=None,
                        help="Custom path to Antigravity brain directory.")

    args = parser.parse_args()

    detector = GrillMeDetector(brain_dir=args.brain_dir)
    selector = GrillMeSelector(detector=detector)

    # 1. Step A: Scan Transcripts
    pending_chats = detector.scan_transcripts()

    # JSON output mode handling for scan-only
    if args.json and args.scan:
        envelope = {
            "success": True,
            "data": {
                "total_pending": len(pending_chats),
                "brain_dir": str(detector.brain_dir),
                "chats": [c.to_dict() for c in pending_chats]
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "scan"
            }
        }
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return 0

    # Scan-only mode in human-readable CLI
    if args.scan:
        print("\n" + "=" * 76)
        print("   PENDING GRILL ME CHATS SCAN RESULTS (Method 1: Transcript Parsing)")
        print("=" * 76)
        print(f"  Brain Directory : {detector.brain_dir}")
        print(f"  Pending Chats   : {len(pending_chats)}")
        print("=" * 76 + "\n")
        if not pending_chats:
            print("  [INFO] No Antigravity conversation currently has an unanswered Grill Me prompt.\n")
            return 0
        for idx, chat in enumerate(pending_chats, start=1):
            print(format_chat_card(chat, index=idx))
            print()
        return 0

    # If no pending chats exist:
    if not pending_chats:
        if args.json:
            envelope = {
                "success": True,
                "data": {
                    "total_pending": 0,
                    "message": "No active Grill Me / ask_question prompt waiting for response."
                },
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "brain_dir": str(detector.brain_dir)
                }
            }
            print(json.dumps(envelope, indent=2, ensure_ascii=False))
            return 0

        print("\n" + "=" * 76)
        print("   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (1-Click Automation)")
        print("=" * 76)
        print(f"  Brain Directory : {detector.brain_dir}")
        print("  Status          : NO PENDING GRILL ME CHATS FOUND")
        print("=" * 76)
        print("  [INFO] All Antigravity sessions are currently completed, idle, or running.")
        print("         No unanswered ask_question prompts are currently blocked.\n")
        return 0

    # 2. Pick target conversation (Streamlined 1-Click: auto-pick newest if not explicitly given)
    target_chat: Optional[PendingGrillMeChat] = None
    if args.select:
        target_chat = selector.select_conversation(target_cid=args.select)
        if not target_chat:
            logger.error("Specified Conversation ID '%s' not found among pending chats.", args.select)
            return 1
    else:
        target_chat = pending_chats[0]

    # 3. Step B: Prepare Selection State
    res = selector.prepare_selection(
        chat=target_chat,
        chosen_option_index=args.option,
        dry_run=args.dry_run
    )

    # 4. Step C: Bulletproof Window Focus (Default: Enabled)
    target_hwnd: Optional[int] = None
    if not args.no_focus:
        win_match = AntigravityFocusManager.find_antigravity_window()
        if win_match:
            target_hwnd, win_title, win_info = win_match
            logger.info("Found Antigravity Window: '%s' (HWND: %s)", win_title, target_hwnd)
            if not args.dry_run:
                res.window_focused = AntigravityFocusManager.bring_to_foreground(target_hwnd)
            else:
                logger.info("  [DRY-RUN] Would bring window HWND %s to foreground.", target_hwnd)
                res.window_focused = True
        else:
            logger.warning("Antigravity window not detected via process/class scan.")
            res.window_focused = False

    # 5. Step D: GUI Chat Selection (Default: Enabled)
    if not args.no_click and target_hwnd:
        opt_to_select = args.option if args.select_option else (1 if args.select_option else None)
        res.gui_chat_selected = AntigravityGuiSelector.select_chat_in_gui(
            hwnd=target_hwnd,
            target_cid=target_chat.conversation_id,
            topic=target_chat.topic_summary,
            dry_run=args.dry_run,
            select_option_number=opt_to_select,
            auto_submit=args.auto_submit
        )

    # Save selection state to JSON
    saved_path = selector.export_selection_state(res, args.output_file)

    # JSON output mode
    if args.json:
        envelope = {
            "success": True,
            "data": {
                "chat": target_chat.to_dict(),
                "selection": res.to_dict()
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "saved_state_file": str(saved_path),
                "action": "1-click-activation"
            }
        }
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return 0

    # Human-readable Presentation
    count_label = "Multiple Questions" if target_chat.is_multi_question else "Single Question"
    print("\n" + "=" * 76)
    print("   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (1-Click Execution)")
    print("=" * 76)
    print(f"  Target Conversation: {target_chat.conversation_id}")
    print(f"  Timestamp          : {target_chat.created_at}")
    print(f"  Topic / Goal       : {target_chat.topic_summary}")
    print(f"  📊 Total Questions Count: {target_chat.total_questions_count} ({count_label})")
    print("=" * 76 + "\n")

    print(format_chat_card(target_chat, index=1))
    print()
    print(format_selection_card(res, target_chat))
    print(f"\n  [SAVED] Selection state payload saved to: {saved_path}")
    print("  [SUCCESS] 1-Click Grill Me Chat activation completed smoothly!\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
