#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Activating Grill Me Chat in Antigravity - Method 1: File System & Transcript Parsing
=====================================================================================
Target: Antigravity AI Coding Agent Sessions
Workspace: AutoSelect-Commander / Activating Grill Me Chat in anti-gravity

Mission:
  Automatically detect which Antigravity chat/conversation currently has
  "Grill Me" / `ask_question` waiting for user response (unanswered question / pending selection),
  and provide an automated 2-step execution flow:
    - Step 1: Identification: Scan brain transcript logs, find pending `ask_question` tool calls,
              and extract Conversation ID, timestamp, user prompt, question text, and options.
    - Step 2: Selection: Select target conversation, inspect pending questions and available
              options, calculate recommended choice, and prepare/output the structured selection state.

Architecture:
  - Zero required external dependencies (100% Python Standard Library).
  - Optional Windows Win32 focus integration via native ctypes.
  - Standardized JSON Envelope output adhering to Dept 06 standards.
"""

from __future__ import annotations

import os
import sys
import json
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

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class SelectionResult:
    """Represents the prepared selection state ready for confirmation or automation."""
    conversation_id: str
    selected_at: str
    status: str
    questions_count: int
    selections: List[Dict[str, Any]] = field(default_factory=list)
    window_focused: bool = False
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Step 1: Identification Engine
# ============================================================================

class GrillMeDetector:
    """
    Method 1 Engine: File System & Transcript Parsing.
    Scans the Antigravity brain storage to identify active/unanswered ask_question prompts.
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
            transcript_file = cdir / ".system_generated" / "logs" / "transcript.jsonl"
            if not transcript_file.is_file():
                # Check fallback transcript_full.jsonl
                transcript_file = cdir / ".system_generated" / "logs" / "transcript_full.jsonl"
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
                # Clean prompt markers if present
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
                        # Extract question payloads
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
                        # The newest ask_question in this conversation has already been answered.
                        # Stop scanning older steps for this conversation.
                        return None

        return None

    def _is_step_answered(self, lines: List[Dict[str, Any]], question_step_idx: int) -> bool:
        """Check if any subsequent step after question_step_idx represents an answer/fulfillment."""
        for j in range(question_step_idx + 1, len(lines)):
            subsequent = lines[j]
            stype = subsequent.get("type", "")

            # Tool result for ask_question is typically recorded as GENERIC containing answers or Completed At
            if stype == "GENERIC":
                content = str(subsequent.get("content", ""))
                if "Completed At:" in content or "A1:" in content or "Answer" in content:
                    return True

            # If user sent another prompt, the agent was unblocked or the prompt was resolved
            if stype == "USER_INPUT":
                return True

            # If a subsequent PLANNER_RESPONSE executes without tool_calls waiting for ask_question
            if stype == "PLANNER_RESPONSE" and subsequent.get("status") == "DONE":
                # Check if it's continuing execution
                if not any(tc.get("name") == "ask_question" for tc in subsequent.get("tool_calls", [])):
                    return True

        return False

    def _extract_question_payloads(self, args: Dict[str, Any]) -> List[QuestionPayload]:
        """Extract structured QuestionPayload instances from raw tool arguments."""
        questions_raw = args.get("questions", [])

        # Handle JSON-string encoded argument
        if isinstance(questions_raw, str):
            try:
                questions_raw = json.loads(questions_raw)
            except Exception as e:
                logger.debug("Failed to decode JSON string questions: %s", e)
                questions_raw = []

        if not isinstance(questions_raw, list):
            questions_raw = [questions_raw] if isinstance(questions_raw, dict) else []

        payloads: List[QuestionPayload] = []
        for idx, item in enumerate(questions_raw, start=1):
            if not isinstance(item, dict):
                continue
            q_text = str(item.get("question", f"Question {idx}")).strip()
            opts_raw = item.get("options", [])
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
# Step 2: Selection Engine & Window Activation
# ============================================================================

class GrillMeSelector:
    """
    Method 1 Engine - Step 2: Selection.
    Selects a specific conversation, evaluates questions/options, prepares selection payload,
    and optionally activates the Antigravity window.
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
            # Determine which option to pick for this question
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
        return SelectionResult(
            conversation_id=chat.conversation_id,
            selected_at=now_iso,
            status="READY_FOR_CONFIRMATION",
            questions_count=len(chat.questions),
            selections=selections,
            dry_run=dry_run
        )

    def export_selection_state(
        self,
        result: SelectionResult,
        output_file: Optional[str] = None
    ) -> Path:
        """Export the selection state payload to a JSON file."""
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

        return out_path

    def focus_antigravity_window(self) -> bool:
        """
        Attempt to focus and maximize the Antigravity IDE/Chat window on Windows using native ctypes.
        Returns True if successful, False otherwise.
        """
        if sys.platform != "win32":
            return False

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            matched_hwnds: List[Tuple[int, str]] = []

            def enum_windows_callback(hwnd: int, lparam: int) -> bool:
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value
                    title_lower = title.lower()
                    if "antigravity" in title_lower or "gemini" in title_lower:
                        matched_hwnds.append((hwnd, title))
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

            if not matched_hwnds:
                return False

            target_hwnd, target_title = matched_hwnds[0]
            # Release Windows foreground lock
            user32.keybd_event(0x12, 0, 0, 0)
            user32.keybd_event(0x12, 0, 2, 0)

            user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
            user32.ShowWindow(target_hwnd, 3)  # SW_MAXIMIZE
            user32.SetForegroundWindow(target_hwnd)
            logger.info("Focused Antigravity Window: '%s' (HWND: %s)", target_title, target_hwnd)
            return True
        except Exception as e:
            logger.debug("Focus window attempt failed: %s", e)
            return False


# ============================================================================
# CLI Presentation & Terminal Formatting
# ============================================================================

def format_chat_card(chat: PendingGrillMeChat, index: int = 1) -> str:
    """Format an individual pending chat into a clear terminal card."""
    border = "=" * 76
    lines = [
        border,
        f"  [CHAT #{index}] ACTIVE GRILL ME WAITING FOR RESPONSE",
        border,
        f"  Conversation ID : {chat.conversation_id}",
        f"  Created At      : {chat.created_at}",
        f"  Step Index      : {chat.step_index} / {chat.total_steps}",
        f"  Initial Prompt  : {chat.topic_summary}",
        f"  Last User Input : {chat.last_user_prompt}",
        "-" * 76,
        f"  Pending Questions ({len(chat.questions)}):"
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
    lines = [
        border,
        "  [SELECTION RESULT] PREPARED CONFIRMATION STATE (STEP 2)",
        border,
        f"  Target Chat     : {result.conversation_id}",
        f"  Status          : {result.status}",
        f"  Selected At     : {result.selected_at}",
        f"  Dry Run Mode    : {'YES (Simulation)' if result.dry_run else 'NO (Live)'}",
        f"  Window Focused  : {'YES' if result.window_focused else 'NO'}",
        "-" * 76,
        "  Chosen Selections:"
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
# Main CLI Entrypoint
# ============================================================================

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Activating Grill Me Chat in Antigravity - Method 1: File System & Transcript Parsing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1: Scan and list all pending Grill Me chats
  python activating_grill_me.py --scan

  # Step 1 + Step 2: Auto-select latest pending chat and prepare selection
  python activating_grill_me.py --auto-select

  # Select a specific option number (e.g. Option 2)
  python activating_grill_me.py --auto-select --option 2

  # Output in standardized JSON envelope
  python activating_grill_me.py --auto-select --json

  # Dry-run test mode
  python activating_grill_me.py --dry-run
        """
    )

    parser.add_argument("--scan", action="store_true", help="Step 1: Scan and list all active pending Grill Me chats.")
    parser.add_argument("--select", type=str, nargs="?", const="", default=None,
                        help="Step 2: Select conversation by ID (or interactive if ID is omitted).")
    parser.add_argument("--auto-select", action="store_true",
                        help="Step 1 + 2: Automatically select the newest pending Grill Me chat.")
    parser.add_argument("--option", type=int, default=None,
                        help="Explicit option index to select (default: recommended option or 1).")
    parser.add_argument("--focus", action="store_true",
                        help="Bring Antigravity IDE/Chat window to foreground on selection.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in dry-run mode (no external modifications, pure inspection).")
    parser.add_argument("--json", action="store_true",
                        help="Output result as Dept 06 JSON response envelope.")
    parser.add_argument("--output-file", type=str, default=None,
                        help="File path to save the prepared selection state JSON.")
    parser.add_argument("--brain-dir", type=str, default=None,
                        help="Custom path to Antigravity brain directory.")

    args = parser.parse_args()

    detector = GrillMeDetector(brain_dir=args.brain_dir)
    selector = GrillMeSelector(detector=detector)

    # 1. Step 1: Scan Transcripts
    pending_chats = detector.scan_transcripts()

    # JSON output mode handling
    if args.json:
        if args.scan and not args.auto_select and args.select is None:
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

        # Auto-select or specific select in JSON mode
        target_chat = None
        if args.select:
            target_chat = selector.select_conversation(target_cid=args.select)
        elif pending_chats:
            target_chat = pending_chats[0]

        if not target_chat:
            err_envelope = {
                "success": False,
                "error": {
                    "code": "NO_PENDING_GRILL_ME",
                    "message": "No active Grill Me / ask_question prompt found waiting for response."
                },
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "brain_dir": str(detector.brain_dir)
                }
            }
            print(json.dumps(err_envelope, indent=2, ensure_ascii=False))
            return 1

        res = selector.prepare_selection(
            chat=target_chat,
            chosen_option_index=args.option,
            dry_run=args.dry_run
        )
        if args.focus:
            res.window_focused = selector.focus_antigravity_window()

        if args.output_file:
            selector.export_selection_state(res, args.output_file)

        envelope = {
            "success": True,
            "data": {
                "chat": target_chat.to_dict(),
                "selection": res.to_dict()
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "selection"
            }
        }
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return 0

    # Human-readable CLI Presentation
    print("\n" + "=" * 76)
    print("   ACTIVATING GRILL ME CHAT IN ANTIGRAVITY (Method 1: Transcript Parsing)")
    print("=" * 76)
    print(f"  Brain Directory : {detector.brain_dir}")
    print(f"  Directory Status: {'Valid (Found)' if detector.is_valid_brain_dir() else 'MISSING'}")
    print(f"  Pending Chats   : {len(pending_chats)}")
    print("=" * 76 + "\n")

    if not pending_chats:
        print("  [INFO] No Antigravity conversation currently has an unanswered Grill Me prompt.")
        print("         All conversations are either completed, idle, or awaiting model generation.\n")
        return 0

    # Display detected chats
    for idx, chat in enumerate(pending_chats, start=1):
        print(format_chat_card(chat, index=idx))
        print()

    # Determine execution flow
    do_selection = args.auto_select or (args.select is not None) or (not args.scan)

    if do_selection:
        chosen_chat: Optional[PendingGrillMeChat] = None
        if args.select:
            chosen_chat = selector.select_conversation(target_cid=args.select)
            if not chosen_chat:
                logger.error("Specified Conversation ID '%s' not found among pending chats.", args.select)
                return 1
        elif len(pending_chats) == 1 or args.auto_select:
            chosen_chat = pending_chats[0]
            print(f"  [AUTO-SELECT] Selecting latest active conversation: {chosen_chat.conversation_id}")
        else:
            # Interactive prompt if multiple exist and not explicitly specified
            print("  Multiple active Grill Me chats detected. Select conversation index (1-{}): ".format(len(pending_chats)), end="")
            try:
                choice = input().strip()
                c_idx = int(choice)
                if 1 <= c_idx <= len(pending_chats):
                    chosen_chat = pending_chats[c_idx - 1]
                else:
                    print("  Invalid selection index.")
                    return 1
            except Exception:
                chosen_chat = pending_chats[0]
                print(f"  Defaulting to most recent: {chosen_chat.conversation_id}")

        # Step 2: Prepare selection
        res = selector.prepare_selection(
            chat=chosen_chat,
            chosen_option_index=args.option,
            dry_run=args.dry_run
        )

        if args.focus:
            res.window_focused = selector.focus_antigravity_window()

        # Export state
        saved_path = selector.export_selection_state(res, args.output_file)
        print(format_selection_card(res, chosen_chat))
        print(f"\n  [SAVED] Selection state payload saved to: {saved_path}")
        print("  [READY] Step 1 (Identification) & Step 2 (Selection) completed successfully!\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
