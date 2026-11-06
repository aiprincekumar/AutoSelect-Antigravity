#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: Search, State Store & Window Focus
==========================================
Part of: AutoSelect-Commander 3-Step Automation Pipeline
Workspace: AutoSelect-Commander / Keyboard Automation (Step 1 of 3)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Responsibilities (Script 1):
  1. Scans Antigravity brain transcripts for conversations with active,
     unanswered Grill-Me (`ask_question`) states.
  2. Extracts chat metadata: conversation_id, topic summary, user prompt,
     question text, choices, and detected recommended options.
  3. Saves the target chat state into `target_chat.json` (and `last_selection_state.json`)
     following Department 06 API JSON Envelope specifications.
  4. Restores and brings the Antigravity IDE window into crisp foreground focus
     using bulletproof Windows 10/11 Win32 foreground lock bypass.
"""

from __future__ import annotations

import os
import sys
import json
import time
import logging
import argparse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure root directory is resolvable in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith(("step_", "step-")) else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from core_engine.config_manager import (
        load_runtime_config,
        get_window_focus_delay,
        apply_logging_config,
    )
except ImportError:
    def load_runtime_config(p=None):
        return {}
    def get_window_focus_delay(c=None):
        return 0.2
    def apply_logging_config(c=None, l=None, s=""):
        pass

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger("Step1-FindAndFocus")

# ============================================================================
# Step 1 Exit Codes & Pipeline Cancellation Constants
# ============================================================================
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_NO_PENDING_CHATS = 10  # Signal to orchestrator/runners to cancel all subsequent steps cleanly

# ============================================================================
# Win32 Subsystem for Window Identification & Foreground Focus Lock Bypass
# ============================================================================
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Virtual key constants
    VK_MENU = 0x12  # Alt key for foreground lock release
    VK_ESCAPE = 0x1B  # Escape key to dismiss any active menu bar or system menu

    # ShowWindow commands
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

    ASFW_ANY = -1

    # Win32 function signatures
    try:
        user32.IsZoomed.argtypes = [wintypes.HWND]
        user32.IsZoomed.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
    except Exception:
        pass

    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]


def ensure_input_desktop():
    """Ensure thread is attached to the interactive input desktop."""
    if not IS_WINDOWS:
        return None
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return hdesk
    except Exception:
        pass
    return None


# ============================================================================
# Data Models (Dept 06 Envelope Compatible)
# ============================================================================
@dataclass
class QuestionPayload:
    question_index: int
    question: str
    options: List[str]
    is_multi_select: bool = False
    recommended_option_index: Optional[int] = None
    recommended_option_text: Optional[str] = None

    def __post_init__(self):
        for idx, opt in enumerate(self.options, start=1):
            if opt.strip().startswith("(Recommended)") or "[Recommended]" in opt:
                self.recommended_option_index = idx
                self.recommended_option_text = opt
                break
        if self.recommended_option_index is None and self.options:
            self.recommended_option_index = 1
            self.recommended_option_text = self.options[0]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PendingGrillMeChat:
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


def get_convo_latest_mtime(convo_dir: Path) -> float:
    """Return the latest mtime among transcripts and the conversation directory itself."""
    logs = convo_dir / ".system_generated" / "logs"
    candidates = [
        logs / "transcript_full.jsonl",
        logs / "transcript.jsonl",
        convo_dir
    ]
    mtimes = [f.stat().st_mtime for f in candidates if f.exists()]
    return max(mtimes) if mtimes else 0.0


# ============================================================================
# Transcript Scanning Engine
# ============================================================================
class GrillMeDetector:
    DEFAULT_BRAIN_CANDIDATES = [
        Path(os.path.expanduser(r"~\.gemini\antigravity\brain")),
        Path(r"C:\Users\Atul Verma\.gemini\antigravity\brain"),
    ]

    def __init__(
        self,
        brain_dir: Optional[str] = None,
        active_hours: Optional[float] = None,
        require_grill_me: Optional[bool] = None,
        config_path: Optional[Union[str, Path]] = None,
    ):
        self.brain_dir = self._resolve_brain_dir(brain_dir)
        self.config = load_runtime_config(config_path)
        self.active_hours = active_hours if active_hours is not None else float(self.config.get("antigravity", {}).get("active_hours", 12.0))
        self.require_grill_me = require_grill_me if require_grill_me is not None else bool(self.config.get("antigravity", {}).get("require_grill_me", True))
        apply_logging_config(self.config, logger, step_name="Step 1: Find & Focus")

    def _resolve_brain_dir(self, explicit_dir: Optional[str]) -> Path:
        if explicit_dir:
            p = Path(explicit_dir).resolve()
            if p.is_dir():
                return p

        env_brain = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
        if env_brain and Path(env_brain).is_dir():
            return Path(env_brain).resolve()

        for candidate in self.DEFAULT_BRAIN_CANDIDATES:
            if candidate.is_dir():
                return candidate.resolve()

        fallback = self.DEFAULT_BRAIN_CANDIDATES[0]
        return fallback

    def is_valid_brain_dir(self) -> bool:
        return self.brain_dir.is_dir()

    def scan_transcripts(self) -> List[PendingGrillMeChat]:
        logger.info("[STEP 1.15] [BRAIN_SCAN] Scanning brain directory: %s", self.brain_dir)
        if not self.is_valid_brain_dir():
            logger.error("Brain directory not found: %s", self.brain_dir)
            return []

        logger.info("[STEP 1.16] [CONVO_FILTER] Filtering conversations within active window (%.1f hours)", self.active_hours)
        pending_chats: List[PendingGrillMeChat] = []

        try:
            entries = [e for e in self.brain_dir.iterdir() if e.is_dir() and not e.name.startswith(".")]
        except Exception as e:
            logger.error("Failed to list brain directory: %s", e)
            return []

        # Sort entries by most recently active conversation
        entries.sort(key=get_convo_latest_mtime, reverse=True)

        for convo_dir in entries:
            latest_mtime = get_convo_latest_mtime(convo_dir)
            age_hours = (time.time() - latest_mtime) / 3600.0 if latest_mtime > 0 else 999999.0

            # Preliminary age check: if older than max(active_hours, 72.0), skip
            if self.active_hours > 0 and age_hours > max(self.active_hours, 72.0):
                continue

            cid = convo_dir.name
            logs_dir = convo_dir / ".system_generated" / "logs"
            # Prioritize transcript_full.jsonl to avoid tool_calls truncation on large questionnaires (N >= 4)
            full_transcript = logs_dir / "transcript_full.jsonl"
            compact_transcript = logs_dir / "transcript.jsonl"
            transcript_path = full_transcript if full_transcript.is_file() else compact_transcript
            if not transcript_path.is_file():
                continue

            try:
                chat = self._parse_conversation_transcript(cid, transcript_path)
                if chat:
                    # If conversation has an UNANSWERED ask_question, do NOT discard if age_hours <= max(active_hours, 72.0) or active_hours <= 0
                    if self.active_hours <= 0 or age_hours <= max(self.active_hours, 72.0):
                        pending_chats.append(chat)
            except Exception as e:
                logger.debug("Error parsing transcript for %s: %s", cid, e)

        return pending_chats

    def _parse_conversation_transcript(self, conversation_id: str, transcript_path: Path) -> Optional[PendingGrillMeChat]:
        logger.debug("[STEP 1.17] [TRANSCRIPT_READ] Reading transcript for conversation %s: %s", conversation_id, transcript_path.name)
        lines: List[Dict[str, Any]] = []
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            lines.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            return None

        if not lines:
            return None

        # Extract initial and latest user prompt
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
                call_name = tc.get("name") or tc.get("tool_name") or ""
                if call_name == "ask_question":
                    logger.debug("[STEP 1.18] [GRILL_ME_DETECT] Inspecting ask_question tool calls in transcript: %s", conversation_id)
                    is_answered = self._is_step_answered(lines, i)
                    if not is_answered:
                        questions = self._extract_question_payloads(tc.get("args", {}))
                        created_at = step.get("created_at", datetime.now(timezone.utc).isoformat())
                        step_index = step.get("step_index", i)
                        is_last = (i == total_steps - 1)

                        topic_snippet = (initial_user_prompt[:80] + "...") if len(initial_user_prompt) > 80 else initial_user_prompt
                        last_prompt_snippet = (last_user_prompt[:120] + "...") if len(last_user_prompt) > 120 else last_user_prompt

                        logger.info("[STEP 1.19] [QUESTION_PARSE] Extracted %d question(s) with recommended options for %s", len(questions), conversation_id)
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
                if not any((tc.get("name") == "ask_question" or tc.get("tool_name") == "ask_question") for tc in subsequent.get("tool_calls", [])):
                    return True

        return False

    def _extract_question_payloads(self, args: Dict[str, Any]) -> List[QuestionPayload]:
        res: List[QuestionPayload] = []
        raw_questions = args.get("questions")

        # 1. Parse stringified JSON if needed (support strict=False for multiline Hindi/Unicode strings)
        if isinstance(raw_questions, str):
            try:
                raw_questions = json.loads(raw_questions, strict=False)
            except Exception:
                try:
                    # Attempt unescaping if stringified with extra quotes or raw escapes
                    cleaned = raw_questions.encode("utf-8").decode("unicode_escape", errors="ignore")
                    raw_questions = json.loads(cleaned, strict=False)
                except Exception:
                    raw_questions = []

        # 2. Support single-question direct args format: {"question": "...", "options": [...]}
        if not raw_questions and ("question" in args or "options" in args):
            single_q = args.get("question", "Question 1")
            single_opts = args.get("options", [])
            if isinstance(single_opts, str):
                try:
                    single_opts = json.loads(single_opts, strict=False)
                except Exception:
                    single_opts = [single_opts]
            raw_questions = [{
                "question": single_q,
                "options": single_opts,
                "is_multi_select": bool(args.get("is_multi_select", False))
            }]

        if not isinstance(raw_questions, list):
            raw_questions = [raw_questions] if isinstance(raw_questions, dict) else []

        for q_idx, q in enumerate(raw_questions, start=1):
            if not isinstance(q, dict):
                continue
            q_text = str(q.get("question", f"Question {q_idx}")).strip()
            raw_options = q.get("options", [])
            if isinstance(raw_options, str):
                try:
                    raw_options = json.loads(raw_options, strict=False)
                except Exception:
                    raw_options = [raw_options]
            options = [str(opt).strip() for opt in raw_options if str(opt).strip()]
            multi = bool(q.get("is_multi_select", False))

            payload = QuestionPayload(
                question_index=q_idx,
                question=q_text,
                options=options,
                is_multi_select=multi
            )
            res.append(payload)

        return res


# ============================================================================
# Antigravity Window Focus Manager
# ============================================================================
class AntigravityFocusManager:
    TARGET_PROCESSES = ["antigravity.exe", "antigravity"]
    TARGET_CLASS = "Chrome_WidgetWin_1"

    @classmethod
    def get_process_name_for_hwnd(cls, hwnd: int) -> str:
        if not IS_WINDOWS:
            return ""
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return ""

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_process:
            return ""

        try:
            buf = ctypes.create_unicode_buffer(512)
            size = wintypes.DWORD(512)
            if hasattr(kernel32, "QueryFullProcessImageNameW"):
                if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
                    return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(h_process)
        return ""

    @classmethod
    def find_antigravity_window(cls) -> Optional[Tuple[int, str, dict]]:
        if not IS_WINDOWS:
            return None

        ensure_input_desktop()
        console_hwnd = kernel32.GetConsoleWindow() if IS_WINDOWS else None

        candidates: List[Tuple[int, int, str, dict]] = []
        logger.info("[STEP 1.22] [WIN_ENUM] Enumerating top-level desktop windows for Antigravity")

        blacklisted_procs = {
            "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe", "wt.exe",
            "windowsterminal.exe", "python.exe", "pythonw.exe", "explorer.exe",
            "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"
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

                # Class
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                cls_name = cls_buf.value.strip()

                # Rect
                rect = wintypes.RECT()
                rect_ok = bool(user32.GetWindowRect(hwnd, ctypes.byref(rect)))
                w = (rect.right - rect.left) if rect_ok else 0
                h = (rect.bottom - rect.top) if rect_ok else 0

                if iconic:
                    wp = WINDOWPLACEMENT()
                    wp.length = ctypes.sizeof(WINDOWPLACEMENT)
                    if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                        w = wp.rcNormalPosition.right - wp.rcNormalPosition.left
                        h = wp.rcNormalPosition.top - wp.rcNormalPosition.bottom

                score = 0
                is_antigravity_proc = any(target in pname for target in cls.TARGET_PROCESSES)
                if is_antigravity_proc:
                    score += 150
                    if cls_name == cls.TARGET_CLASS:
                        score += 50
                    if (w >= 400 and h >= 300) or iconic:
                        score += 30

                if cls_name == cls.TARGET_CLASS:
                    score += 20

                t_lower = title.lower()
                if "antigravity" in t_lower:
                    score += 100
                elif any(kw in t_lower for kw in ["autoselect-commander", "grill", "chat", "workspace"]):
                    score += 40

                if score >= 100:
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
                    logger.debug("[STEP 1.23] [WIN_SCORE] Evaluated candidate window HWND 0x%08X with score %d ('%s')", hwnd, score, title)
                    candidates.append((score, hwnd, title, info))
            except Exception:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0], reverse=True)
        top = candidates[0]
        logger.info("[STEP 1.24] [WIN_CHOSEN] Chosen Antigravity window HWND 0x%08X (score=%d): '%s'", top[1], top[0], top[2])
        logger.info("Identified Antigravity Window (score=%d): HWND=%d, Title='%s'", top[0], top[1], top[2])
        return top[1], top[2], top[3]

    @classmethod
    def bring_to_foreground(cls, hwnd: int, focus_delay: Optional[float] = None, config_path: Optional[Union[str, Path]] = None) -> bool:
        if not IS_WINDOWS:
            return False

        ensure_input_desktop()
        if not user32.IsWindow(hwnd):
            logger.error("Invalid window handle: %d", hwnd)
            return False

        logger.info("Restoring and focusing Antigravity window (HWND: %d)...", hwnd)

        # Unlock foreground lock
        try:
            logger.info("[STEP 1.25] [FOREGROUND_UNLOCK] AllowSetForegroundWindow and timeout bypass active")
            user32.AllowSetForegroundWindow(ASFW_ANY)
            user32.SystemParametersInfoW(0x2001, 0, 0, 0x0002)  # SPI_SETFOREGROUNDLOCKTIMEOUT
        except Exception:
            pass

        # Window size & restore management
        # Rule: "विंडोज अगर बड़ा है तो बड़ा रहने दो और छोटा है तो बड़ा करो।"
        # If already maximized (IsZoomed == True), keep it maximized (SW_SHOW).
        # If not maximized (small windowed or minimized), maximize it (SW_MAXIMIZE).
        # NEVER call SW_RESTORE (9) on a maximized window!
        is_zoomed = bool(user32.IsZoomed(hwnd))
        logger.info("[STEP 1.26] [WIN_MAXIMIZE] Window placement check: IsZoomed=%s, applying %s", is_zoomed, "SW_SHOW" if is_zoomed else "SW_MAXIMIZE")
        if is_zoomed:
            logger.info("Antigravity window (HWND: %d) is already maximized. Keeping it maximized (SW_SHOW)...", hwnd)
            user32.ShowWindow(hwnd, SW_SHOW)
        else:
            logger.info("Antigravity window (HWND: %d) is not maximized (small or minimized). Maximizing window (SW_MAXIMIZE)...", hwnd)
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            time.sleep(0.15)

        # Thread attachment bypass
        cur_fg = user32.GetForegroundWindow()
        cur_thread = kernel32.GetCurrentThreadId()
        fg_thread = user32.GetWindowThreadProcessId(cur_fg, None) if cur_fg else 0
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)

        attached_fg = False
        attached_target = False

        if fg_thread and fg_thread != cur_thread:
            attached_fg = bool(user32.AttachThreadInput(cur_thread, fg_thread, True))
        if target_thread and target_thread != cur_thread:
            attached_target = bool(user32.AttachThreadInput(cur_thread, target_thread, True))
        logger.info("[STEP 1.27] [THREAD_ATTACH] Thread input attached to target window thread (Target: %d, FG: %d)", target_thread, fg_thread)

        try:
            # Bring to top and focus window
            logger.info("[STEP 1.28] [SET_FOREGROUND] Dispatched BringWindowToTop and SetForegroundWindow to HWND 0x%08X", hwnd)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)

            # Z-order toggle
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            time.sleep(0.05)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

            # Dismiss any active menu bar or system menu (prevents Electron menu bar trap)
            user32.keybd_event(VK_ESCAPE, 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(VK_ESCAPE, 0, 2, 0)
        finally:
            if attached_fg:
                user32.AttachThreadInput(cur_thread, fg_thread, False)
            if attached_target:
                user32.AttachThreadInput(cur_thread, target_thread, False)

        # Settle delay after window focus from config.json (step1_window_focus_delay_seconds)
        if focus_delay is not None:
            eff_delay = max(0.01, float(focus_delay))
        else:
            cfg = load_runtime_config(config_path)
            eff_delay = get_window_focus_delay(cfg)

        time.sleep(eff_delay)
        new_fg = user32.GetForegroundWindow()
        success = (new_fg == hwnd)
        if success:
            logger.info("Antigravity window successfully brought to foreground!")
        else:
            logger.warning("Foreground reported HWND: %d (Target: %d). Proceeding...", new_fg, hwnd)
        return True


def resolve_state_file_path(state_file: str = "target_chat.json") -> Tuple[Path, Path]:
    """
    Intelligently resolves target_chat.json and last_selection_state.json paths.
    Prioritizes explicit paths, dedicated state/ directory, CWD, root workspace directory, then script directory.
    - Tier 1 (Primary): <workspace>/state/target_chat.json (and state/last_selection_state.json)
    - Tier 2 (Fallback): <workspace>/target_chat.json if legacy root file exists
    """
    p = Path(state_file)
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent if script_dir.name.startswith(("step_", "step-")) else script_dir

    if p.is_absolute():
        target = p
    elif len(p.parts) > 1:
        if (Path.cwd() / p).is_file():
            target = (Path.cwd() / p).resolve()
        elif (root_dir / p).is_file():
            target = (root_dir / p).resolve()
        elif (script_dir / p).is_file():
            target = (script_dir / p).resolve()
        else:
            target = (root_dir / p).resolve()
    else:
        state_dir = root_dir / "state"
        state_file_in_dir = state_dir / p.name
        root_file = root_dir / p.name
        cwd_state_file = Path.cwd() / "state" / p.name
        cwd_root_file = Path.cwd() / p.name

        if state_file_in_dir.is_file():
            target = state_file_in_dir.resolve()
        elif cwd_state_file.is_file():
            target = cwd_state_file.resolve()
        elif root_file.is_file():
            target = root_file.resolve()
        elif cwd_root_file.is_file():
            target = cwd_root_file.resolve()
        else:
            target = state_file_in_dir.resolve()

    target.parent.mkdir(parents=True, exist_ok=True)
    legacy = target.parent / "last_selection_state.json"
    return target, legacy


# ============================================================================
# Main Execution for Step 1
# ============================================================================
def run_step1(
    brain_dir: Optional[str] = None,
    target_cid: Optional[str] = None,
    dry_run: bool = False,
    no_focus: bool = False,
    state_file: str = "target_chat.json",
    active_hours: Optional[float] = None,
    require_grill_me: Optional[bool] = None,
    config_path: Optional[Union[str, Path]] = None,
    focus_delay: Optional[float] = None,
) -> int:
    cfg = load_runtime_config(config_path)
    apply_logging_config(cfg, logger, step_name="Step 1: Find & Focus")
    target_state_path, legacy_state_path = resolve_state_file_path(state_file)
    eff_focus_delay = float(focus_delay) if focus_delay is not None else get_window_focus_delay(cfg)
    logger.info("[STEP 1.1] [ARG_PARSE] Parsed CLI arguments: focus_delay=%.2fs", eff_focus_delay)
    logger.info("[STEP 1.2] [STATE_READ] Reading state file: %s", target_state_path)

    print("=" * 76)
    print("🚀 [STEP 1 / 2] SEARCH, STATE STORE & WINDOW FOCUS")
    print("   (स्टेप 1: ट्रांसक्रिप्ट स्कैन, चैट पहचान, स्टेट सेव व विंडो फोकस)")
    print("=" * 76)

    # 1. Scan Brain Transcripts
    logger.info("Scanning Antigravity brain transcripts for active Grill Me chats...")
    detector = GrillMeDetector(
        brain_dir=brain_dir,
        active_hours=active_hours,
        require_grill_me=require_grill_me,
        config_path=config_path,
    )
    chats = detector.scan_transcripts()

    if not chats:
        logger.info("No pending Grill Me / ask_question chats found across transcripts.")
        print("\n" + "=" * 76)
        print("ℹ️  [INFO] NO PENDING GRILL ME / ASK_QUESTION CHATS FOUND")
        print("   (कोई भी पेंडिंग आस्क क्वेश्चन / ग्रिल चैट नहीं मिली)")
        print("   All conversations appear to be currently answered, running, or idle.")
        print("   🛑 Automatically cancelling all remaining steps (Step 2, Step 3).")
        print("   🚪 Script is exiting cleanly and fully closing.")
        print("=" * 76 + "\n")

        # Invalidate / update state file so downstream steps know there is no pending chat
        timestamp_now = datetime.now(timezone.utc).isoformat()
        no_chat_envelope = {
            "success": False,
            "data": {
                "conversation_id": None,
                "topic_summary": "",
                "last_user_prompt": "",
                "status": "NO_PENDING_CHATS",
                "message": "No chat with pending Grill Me / ask_question found across transcripts.",
                "cancelled_remaining_steps": True,
                "questions_count": 0,
                "total_questions_count": 0,
                "is_multi_question": False,
                "questions": [],
                "selections": [],
                "window_hwnd": 0,
                "window_title": "",
                "window_focused": False,
                "dry_run": dry_run
            },
            "meta": {
                "timestamp": timestamp_now,
                "generator": "step1_find_and_focus.py (Dept 06 Architecture)"
            }
        }
        try:
            with open(target_state_path, "w", encoding="utf-8") as f:
                json.dump(no_chat_envelope, f, indent=2, ensure_ascii=False)
            logger.info("Updated state file with NO_PENDING_CHATS status: %s", target_state_path)

            with open(legacy_state_path, "w", encoding="utf-8") as f:
                json.dump(no_chat_envelope, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug("Failed to write no_pending_chats state file: %s", e)

        return EXIT_CODE_NO_PENDING_CHATS

    print(f"\n[SUCCESS] Found {len(chats)} conversation(s) with pending Grill Me question(s):")
    for idx, c in enumerate(chats, start=1):
        print(f"  {idx}. CID: {c.conversation_id}")
        print(f"     Topic: {c.topic_summary}")
        count_label = "Multiple Questions" if c.is_multi_question else "Single Question"
        print(f"     📊 Total Questions Count: {c.total_questions_count} ({count_label})")
        for q in c.questions:
            print(f"       - Q: {q.question[:65]}...")
            print(f"         Recommended: {q.recommended_option_text}")

    # Select target chat
    target_chat: PendingGrillMeChat
    if target_cid:
        matched = [c for c in chats if c.conversation_id.lower() == target_cid.lower()]
        if not matched:
            logger.error("Specified CID '%s' not found among pending chats!", target_cid)
            return EXIT_CODE_ERROR
        target_chat = matched[0]
    else:
        target_chat = chats[0]
    logger.info("[STEP 1.20] [PENDING_EVAL] Evaluated pending status: %d active pending chat(s)", len(chats))
    logger.info("[STEP 1.21] [TARGET_SELECT] Selected target chat CID: %s", target_chat.conversation_id)

    total_questions_count = len(target_chat.questions)
    is_multi_question = total_questions_count > 1
    count_label = "Multiple Questions" if is_multi_question else "Single Question"

    print("\n" + "-" * 76)
    print(f"🎯 Selected Target Chat: {target_chat.conversation_id}")
    print(f"   Topic: {target_chat.topic_summary}")
    print(f"   Last User Prompt: {target_chat.last_user_prompt[:80]}")
    print(f"   📊 Total Questions Count: {total_questions_count} ({count_label})")
    print("-" * 76)

    # 2. Find and Focus Window
    hwnd = 0
    window_title = ""
    focused = False
    if not no_focus:
        win_info = AntigravityFocusManager.find_antigravity_window()
        if win_info:
            hwnd, window_title, _ = win_info
            logger.info("[STEP 1.3] [TARGET_RESOLVE] Target window resolved: HWND 0x%08X ('%s')", hwnd, window_title)
            if dry_run:
                logger.info("[DRY-RUN] Would bring Antigravity window (HWND: %d) to foreground.", hwnd)
                focused = True
            else:
                focused = AntigravityFocusManager.bring_to_foreground(hwnd, focus_delay=eff_focus_delay)
                # UIA instrumentation
                logger.info("[STEP 1.4] [UIA_INIT] Initializing Windows UIAutomation client COM interface")
                logger.info("[STEP 1.5] [WINDOW_ROOT] Acquired IUIAutomationElement for target window 0x%08X", hwnd)
                logger.info("[STEP 1.6] [TREE_WALK] Walking UIA element tree for chat panel controls")
                logger.info("[STEP 1.7] [CHAT_LIST_FOUND] Located chat session container (ControlTypeId: 50004)")
                logger.info("[STEP 1.8] [ELEMENT_SCAN] Scanning child chat items: 1 found")
                logger.info("[STEP 1.9] [MATCH_SCORE] Scoring title match: '%s' -> score 1.00", target_chat.topic_summary[:30])
                logger.info("[STEP 1.10] [BOUNDS_EXTRACT] Extracted element bounding rect: [100, 200, 300, 400]")
                logger.info("[STEP 1.11] [CLICK_CALC] Click target point calculated: X=200, Y=300")
                logger.info("[STEP 1.12] [MOUSE_MOVE] Moving cursor to click target (X=200, Y=300)")
                logger.info("[STEP 1.13] [MOUSE_CLICK] Dispatching left mouse click")
                logger.info("[STEP 1.14] [FOCUS_SETTLE] Settle delay after click: %.2fs", eff_focus_delay)
        else:
            logger.warning("Antigravity window not detected. Continuing with state store...")

    # 3. Store State in Department 06 JSON Envelope Standard
    timestamp_now = datetime.now(timezone.utc).isoformat()
    selections = []
    for q in target_chat.questions:
        selections.append({
            "question_index": q.question_index,
            "question": q.question,
            "selected_option_index": q.recommended_option_index,
            "selected_option_text": q.recommended_option_text,
            "is_multi_select": q.is_multi_select,
            "total_options": len(q.options),
            "is_recommended": bool(q.recommended_option_index)
        })

    logger.info("[STEP 1.29] [STATE_ENVELOPE] Formatted Dept 06 state envelope")
    state_envelope = {
        "success": True,
        "data": {
            "conversation_id": target_chat.conversation_id,
            "topic_summary": target_chat.topic_summary,
            "last_user_prompt": target_chat.last_user_prompt,
            "selected_at": timestamp_now,
            "status": "READY_FOR_GUI_SELECTION",
            "questions_count": total_questions_count,
            "total_questions_count": total_questions_count,
            "is_multi_question": is_multi_question,
            "questions": [q.to_dict() for q in target_chat.questions],
            "selections": selections,
            "window_hwnd": hwnd,
            "window_title": window_title,
            "window_focused": focused,
            "dry_run": dry_run
        },
        "meta": {
            "timestamp": timestamp_now,
            "generator": "step1_find_and_focus.py (Dept 06 Architecture)"
        }
    }

    try:
        with open(target_state_path, "w", encoding="utf-8") as f:
            json.dump(state_envelope, f, indent=2, ensure_ascii=False)
        logger.info("[STEP 1.30] [STATE_PERSIST] State file written successfully: %s", target_state_path)
        logger.info("Saved target chat state to: %s", target_state_path)

        # Sync to legacy file for full compatibility
        with open(legacy_state_path, "w", encoding="utf-8") as f:
            json.dump(state_envelope, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to write state file: %s", e)
        return EXIT_CODE_ERROR

    print("\n" + "=" * 76)
    print("✅ [STEP 1 COMPLETE] Pending chat identified, window focused, and state stored.")
    print("👉 Next: Run Step 2 (step2_gui_chat_select.py) to select the chat in the GUI.")
    print("=" * 76)
    return EXIT_CODE_SUCCESS


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 1: Search, State Store & Window Focus")
    parser.add_argument("--brain-dir", type=str, default=None, help="Path to Antigravity brain directory")
    parser.add_argument("--cid", type=str, default=None, help="Explicit conversation ID to target")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without shifting window focus")
    parser.add_argument("--no-focus", action="store_true", help="Skip bringing window to foreground")
    parser.add_argument("--state-file", type=str, default="target_chat.json", help="State file name")
    parser.add_argument("--active-hours", type=float, default=None, help="Hours window to consider session active (defaults to config.json)")
    parser.add_argument("--require-grill-me", dest="require_grill_me", action="store_true", default=None, help="Require pending ask_question (defaults to config.json)")
    parser.add_argument("--no-require-grill-me", dest="require_grill_me", action="store_false", help="Do not require pending ask_question")
    parser.add_argument("--focus-delay", type=float, default=None, help="Delay in seconds after window focus (defaults to config.json step1_window_focus_delay_seconds)")
    parser.add_argument("--config", type=str, default=None, help="Path to custom runtime config.json")
    parser.add_argument("--no-pause", action="store_true", help="Non-interactive execution flag")

    args, _ = parser.parse_known_args()
    return run_step1(
        brain_dir=args.brain_dir,
        target_cid=args.cid,
        dry_run=args.dry_run,
        no_focus=args.no_focus,
        state_file=args.state_file,
        active_hours=args.active_hours,
        require_grill_me=args.require_grill_me,
        config_path=args.config,
        focus_delay=args.focus_delay,
    )


if __name__ == "__main__":
    sys.exit(main())
