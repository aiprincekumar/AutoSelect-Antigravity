#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: Keyboard Automation Orchestrator Subsystem
==================================================
Pipeline Step: STEP 3 (Option Selection & Confirmation)
Suite: AutoSelect-Commander
Coordinates countdown, target window preparation, keystroke sequence dispatch,
browser safety aborts, pure native Win32 SendInput physical keystroke execution,
and dynamic multi-question step execution.
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Optional, Union, List, Tuple

from .constants import (
    STEP_ID,
    STEP_NUMBER,
    STEP_NAME,
    DEFAULT_TARGET_WINDOW,
    IS_WINDOWS,
    VK_CONTROL,
    VK_L,
    VK_SHIFT,
    VK_TAB,
    VK_RETURN,
    VK_ESCAPE,
    DISQUALIFIED_BROWSER_PROCS,
)
from .win32_api import (
    user32,
    get_active_window_title,
    get_process_info_for_hwnd,
)
from .input_injector import (
    get_option_vk,
    send_key_combo,
    send_single_key,
    PYAUTOGUI_AVAILABLE,
    pyautogui,
)
from .window_manager import (
    select_target_window,
    get_window_info,
    ensure_window_on_screen,
)
from .config_manager import (
    load_runtime_config,
    get_keyboard_timing,
    get_settle_delay,
)

logger = logging.getLogger("Step3KeyboardAutomation.Automator")


class GrillMeAutomator:
    """
    Automates the 'Grill Me' keyboard selection sequence with intelligent window auto-targeting:
    1. Scan & identify target window (e.g. Antigravity 2.0 Harness, IDE, or chat app)
    2. Check minimized state -> Restore window (SW_RESTORE / OpenIcon)
    3. Check maximized state -> Maximize to full screen (SW_MAXIMIZE)
    4. Robust foreground focus bypass (Alt key pulse, thread attach, Z-order bump)
    5. Settle delay for UI rendering
    6. Execute sequence via pure native Win32 SendInput physical keystrokes on the active GUI window:
       * Step A: Ctrl + L    -> Focus chat input (settle pause 0.2s - 0.25s)
       * Step B: Shift + Tab -> Shift focus to option select buttons (settle pause 0.2s - 0.25s)
       * Step C: Option key  -> Select option (e.g. '1') (settle pause 0.2s - 0.25s)
       * Step D: Enter Gate  -> Continue (Q1..QN-1, UI transition pause 0.4s - 0.5s) or Submit confirmation (QN)
    """

    DEFAULT_TARGET = DEFAULT_TARGET_WINDOW

    def __init__(
        self,
        engine: str = "auto",
        step_delay: Optional[float] = None,
        hold_delay: Optional[float] = None,
        option: str = "1",
        skip_ctrl_l: bool = False,
        skip_enter: bool = False,
        dry_run: bool = False,
        target_window: str = DEFAULT_TARGET,
        auto_focus: bool = True,
        auto_maximize: bool = True,
        settle_delay: Optional[float] = None,
        questions: Optional[Union[int, str]] = None,
        options_list: Optional[Union[List[Union[str, int]], str]] = None,
        state_file: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
        post_keypress_delay: Optional[float] = None,
        inter_question_delay: Optional[float] = None,
        round_completion_pause: Optional[float] = None,
        countdown: Optional[float] = None,
    ):
        self.config_path = config_path
        self.config = load_runtime_config(config_path)
        kb_timing = get_keyboard_timing(self.config)

        # Wire all granular delays directly to config.json
        self.hold_delay = max(0.001, float(hold_delay if hold_delay is not None else kb_timing["hold_delay_s"]))
        eff_post = post_keypress_delay if post_keypress_delay is not None else (step_delay if step_delay is not None else kb_timing["post_keypress_delay_s"])
        self.post_keypress_delay = max(0.001, float(eff_post))
        self.step_delay = self.post_keypress_delay
        self.inter_question_delay = max(0.001, float(inter_question_delay if inter_question_delay is not None else kb_timing["inter_question_delay_s"]))
        self.round_completion_pause = max(0.0, float(round_completion_pause if round_completion_pause is not None else kb_timing["round_completion_pause_s"]))
        self.countdown = max(0.0, float(countdown if countdown is not None else kb_timing["countdown"]))

        eff_settle = settle_delay if settle_delay is not None else get_settle_delay(self.config)
        self.settle_delay = max(0.0, float(eff_settle))
        self.option = str(option)
        self.skip_ctrl_l = skip_ctrl_l
        self.skip_enter = skip_enter
        self.dry_run = dry_run
        self.target_window = target_window or self.DEFAULT_TARGET
        self.auto_focus = auto_focus
        self.auto_maximize = auto_maximize
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None
        self.state_file = state_file
        self.conversation_id: Optional[str] = None

        # Resolve engine
        if engine == "pyautogui":
            if not PYAUTOGUI_AVAILABLE:
                logger.warning("PyAutoGUI requested but not installed. Falling back to native ctypes.")
                self.engine = "ctypes"
            else:
                self.engine = "pyautogui"
        elif engine == "ctypes":
            self.engine = "ctypes"
        else:
            # Auto: default to native ctypes (fast, zero dependencies)
            self.engine = "ctypes" if IS_WINDOWS else ("pyautogui" if PYAUTOGUI_AVAILABLE else "none")

        # Resolve total_questions and options_list (via CLI or state_file)
        self.total_questions, self.options_list = self._resolve_questions_and_options(
            questions=questions,
            options_list=options_list,
            state_file=state_file,
        )
        self.questions = self.total_questions

        logger.info(
            f"Initialized GrillMeAutomator (Engine: {self.engine}, DryRun: {self.dry_run}, "
            f"Target: '{self.target_window}', Questions: {self.total_questions}, "
            f"Options: {self.options_list}, AutoFocus: {self.auto_focus}, AutoMaximize: {self.auto_maximize})"
        )

    @staticmethod
    def _find_default_state_file() -> Optional[Path]:
        """
        Locates the target_chat.json file using relative directory probing.
        Probes common locations without recursive scans.
        """
        candidates = [
            Path(__file__).resolve().parent.parent / "target_chat.json",
            Path.cwd() / "target_chat.json",
            Path.cwd().parent / "target_chat.json",
            Path(__file__).resolve().parent.parent / "step_1_chat_identifier" / "target_chat.json",
            Path.cwd() / "step_1_chat_identifier" / "target_chat.json",
            Path.cwd() / "Identify Chat" / "target_chat.json",
            Path.cwd() / ".." / "Identify Chat" / "target_chat.json",
            Path(__file__).resolve().parent.parent / "Identify Chat" / "target_chat.json",
            Path(__file__).resolve().parent.parent.parent / "Identify Chat" / "target_chat.json",
        ]
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                if resolved.is_file():
                    return resolved
            except Exception:
                continue
        return None

    def _resolve_questions_and_options(
        self,
        questions: Optional[Union[int, str]],
        options_list: Optional[Union[List[Union[str, int]], str]],
        state_file: Optional[str],
    ) -> Tuple[int, List[str]]:
        """
        Resolves total questions count and options list from CLI overrides or state file.
        Gracefully defaults to single question (1) with default option if state file is missing/invalid.
        """
        # Parse explicit options_list if provided
        parsed_options: Optional[List[str]] = None
        if options_list is not None:
            if isinstance(options_list, str):
                parsed_options = [s.strip() for s in options_list.split(",") if s.strip()]
            elif isinstance(options_list, (list, tuple)):
                parsed_options = [str(x).strip() for x in options_list if str(x).strip()]

        # Check if questions is explicitly numeric
        explicit_questions: Optional[int] = None
        if questions is not None and str(questions).strip().lower() != "auto":
            try:
                explicit_questions = max(1, int(questions))
            except ValueError:
                logger.warning(f"Invalid questions argument '{questions}', treating as 'auto'")
                explicit_questions = None

        # If questions is explicitly defined and options_list is provided, return directly
        if explicit_questions is not None and parsed_options is not None:
            opts = list(parsed_options)
            while len(opts) < explicit_questions:
                opts.append(str(self.option))
            return explicit_questions, opts[:explicit_questions]

        # Attempt to inspect state file for auto-detection
        target_path: Optional[Path] = None
        if state_file:
            p = Path(state_file)
            if not p.is_absolute():
                candidates = [
                    Path.cwd() / p,
                    Path.cwd().parent / p,
                    Path(__file__).resolve().parent.parent / p,
                ]
                for c in candidates:
                    if c.is_file():
                        p = c
                        break
            p = p.resolve()
            if p.is_file():
                target_path = p
            else:
                logger.warning(f"Specified state file '{state_file}' does not exist.")
        else:
            target_path = self._find_default_state_file()

        state_data: Optional[dict] = None
        if target_path:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        state_data = content.get("data", content) if isinstance(content.get("data"), dict) else content
                logger.info(f"Loaded state file for question detection: {target_path}")
            except Exception as e:
                logger.warning(f"Failed to read or parse state file {target_path}: {e}")

        detected_q = 1
        detected_options: List[str] = []

        if state_data:
            # Check if Step 1 cancelled the workflow due to no pending chats
            if state_data.get("status") == "NO_PENDING_CHATS" or state_data.get("cancelled_remaining_steps") is True:
                if explicit_questions is None:
                    logger.info("State file indicates NO_PENDING_CHATS. Resolving total questions to 0 (Step 3 cancelled).")
                    return 0, []

            # Capture conversation_id if present
            self.conversation_id = state_data.get("conversation_id")

            # Ground truth question resolution hierarchy:
            # 1. Authoritative state_data['questions'] array length
            # 2. state_data['selections'] array length
            # 3. Explicit total_questions_count / questions_count scalar
            qs = state_data.get("questions")
            sels = state_data.get("selections")

            if isinstance(qs, list) and len(qs) > 0:
                detected_q = len(qs)
            elif isinstance(sels, list) and len(sels) > 0:
                detected_q = len(sels)
            elif state_data.get("total_questions_count") is not None:
                try:
                    detected_q = max(0, int(state_data["total_questions_count"]))
                except (ValueError, TypeError):
                    detected_q = 1
            elif state_data.get("questions_count") is not None:
                try:
                    detected_q = max(0, int(state_data["questions_count"]))
                except (ValueError, TypeError):
                    detected_q = 1
            else:
                detected_q = 1

            # Extract option choices from selections or questions
            if isinstance(sels, list) and sels:
                for item in sels:
                    if isinstance(item, dict):
                        idx = item.get("selected_option_index") or item.get("recommended_option_index")
                        if idx is not None:
                            detected_options.append(str(idx))
            elif isinstance(qs, list) and qs:
                for item in qs:
                    if isinstance(item, dict):
                        idx = item.get("recommended_option_index") or item.get("selected_option_index")
                        if idx is not None:
                            detected_options.append(str(idx))

        # Final determination of total_questions (strictly integer >= 0)
        final_questions = explicit_questions if explicit_questions is not None else detected_q
        final_questions = max(0, int(final_questions))

        # Final determination of options_list
        if parsed_options is not None:
            final_options = list(parsed_options)
        elif detected_options:
            final_options = list(detected_options)
        else:
            final_options = [str(self.option)] * final_questions

        # Dynamically scale / pad / truncate to exactly final_questions elements
        if len(final_options) > final_questions:
            final_options = final_options[:final_questions]
        else:
            while len(final_options) < final_questions:
                final_options.append(str(self.option))

        logger.info(
            f"Question resolution: Mode={'Explicit' if explicit_questions is not None else 'Auto-Detected'}, "
            f"Total Questions={final_questions}, Options Sequence={final_options}"
        )
        return final_questions, final_options

    def prepare_target_window(self) -> bool:
        """
        Locates target window by process name, class, or title keywords,
        restores if minimized, maximizes to full screen, and sets foreground focus.
        """
        if not IS_WINDOWS:
            logger.info("Window auto-focus/maximize is only available on Windows.")
            return False

        if not self.auto_focus and not self.auto_maximize:
            logger.info("Window auto-focus and auto-maximize are disabled by user configuration.")
            return True

        logger.info(f"Scanning for target window matching: '{self.target_window}'...")
        match = select_target_window(self.target_window)
        if not match:
            logger.warning(
                f"Target window matching '{self.target_window}' not found! "
                "Will proceed using active foreground window."
            )
            return False

        hwnd, title = match
        self.target_hwnd = hwnd
        self.target_title = title
        info = get_window_info(hwnd)
        pname_lower = info.get("process_name", "").lower()
        logger.info(
            f"Selected Window: HWND={hex(hwnd)}, Process={info['process_name']} (PID={info['pid']}), "
            f"Title='{title}', Class={info['class']}"
        )

        # Strict browser disqualification gatekeeper
        user_wants_browser = any(
            any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi"))
            for kw in (self.target_window.replace("|", ",").split(",") if self.target_window else [])
        )
        if pname_lower in DISQUALIFIED_BROWSER_PROCS and not user_wants_browser:
            logger.error(
                f"[REJECTED] Selected window belongs to disqualified browser '{pname_lower}'. "
                f"Refusing to focus or send keystrokes to browser!"
            )
            self.target_hwnd = None
            self.target_title = None
            return False

        if self.dry_run:
            logger.info(
                f"  [DRY RUN] Would restore if minimized, maximize={self.auto_maximize}, "
                f"and focus={self.auto_focus} window: '{title}'"
            )
            return True

        success = ensure_window_on_screen(
            hwnd=hwnd,
            auto_maximize=self.auto_maximize,
            auto_focus=self.auto_focus,
            settle_delay=self.settle_delay,
        )
        return success

    def run_countdown(self, seconds: Optional[int] = None):
        """Displays visual countdown in terminal allowing user or system to focus target window."""
        cd_seconds = int(seconds if seconds is not None else self.countdown)
        print("\n" + "=" * 65)
        print("  [*] GRILL ME AUTOMATION - HYBRID FOCUS & TARGETING")
        print("=" * 65)

        # Engage auto-targeting, maximize, and focus subsystem
        if self.auto_focus or self.auto_maximize:
            self.prepare_target_window()

        if cd_seconds > 0:
            print("Target window is positioned and focused.")
            print(f"Automation sequence will execute in {cd_seconds} seconds...\n")

            for remaining in range(cd_seconds, 0, -1):
                curr_title = get_active_window_title() if IS_WINDOWS else "Active Window"
                display_title = (curr_title[:45] + "...") if len(curr_title) > 48 else curr_title
                sys.stdout.write(f"\r  [-] Starting in {remaining:2d}s... | Active Window: [{display_title}]")
                sys.stdout.flush()
                time.sleep(1.0)

            sys.stdout.write(f"\r  [+] EXECUTION TRIGGERED NOW!                                  \n\n")
            sys.stdout.flush()
        else:
            print("  [+] Executing immediately (countdown bypassed).\n")

    def _execute_step(self, step_num: Union[int, str], description: str, action_func):
        """Helper to run a step with formatted logging and configurable delays."""
        logger.info(f"Step {step_num}: {description}")
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute: {description}")
        else:
            action_func()
        time.sleep(self.step_delay)

    def _ensure_window_ready(self) -> bool:
        """
        Ensures Antigravity window is restored, maximized (SW_MAXIMIZE),
        and brought cleanly to the foreground (SetForegroundWindow) with
        active OS focus lock release so physical keystrokes land directly
        on the real GUI window.
        """
        if not IS_WINDOWS:
            logger.info("Window focus and activation is only available on Windows.")
            return True

        if not self.auto_focus and not self.auto_maximize:
            logger.info("Window auto-focus and auto-maximize are disabled by user configuration.")
            return True

        # Find target window if not yet identified
        if not self.target_hwnd:
            self.prepare_target_window()

        if not self.target_hwnd:
            # Fallback to current foreground window if match wasn't found
            fg = user32.GetForegroundWindow()
            if fg and user32.IsWindow(fg):
                self.target_hwnd = fg
                info = get_window_info(fg)
                self.target_title = info.get("title", "")

        if not self.target_hwnd or not user32.IsWindow(self.target_hwnd):
            logger.warning("No target window HWND available to focus. Proceeding with active window.")
            return False

        # Guard against disqualified browser windows
        info = get_window_info(self.target_hwnd)
        pname_lower = info.get("process_name", "").lower()
        user_wants_browser = any(
            any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore"))
            for kw in (self.target_window.replace("|", ",").split(",") if self.target_window else [])
        )
        if pname_lower in DISQUALIFIED_BROWSER_PROCS and not user_wants_browser:
            logger.error(
                f"[REJECTED] Selected window belongs to disqualified browser '{pname_lower}'. "
                f"Refusing to focus or send keystrokes to browser!"
            )
            self.target_hwnd = None
            return False

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would ensure window HWND={hex(self.target_hwnd)} is maximized and focused.")
            return True

        logger.info(
            f"Ensuring Antigravity window (HWND={hex(self.target_hwnd)}, Title='{self.target_title}') "
            f"is restored, maximized to full screen, and brought to foreground..."
        )
        return ensure_window_on_screen(
            hwnd=self.target_hwnd,
            auto_maximize=self.auto_maximize,
            auto_focus=self.auto_focus,
            settle_delay=self.settle_delay,
        )

    def execute_multi_question(self, total_questions: Optional[int] = None, options: Optional[List[str]] = None) -> bool:
        """
        Executes deterministic multi-question keyboard automation loop for any N questions (1..N).
        Operates via pure native Windows ctypes SendInput physical keystrokes on the active GUI window:
          - Focus & Activation: _ensure_window_ready() brings Antigravity to foreground & maximizes.
          - For each question q_idx (1..N):
            * Step A / Q{q_idx}.1: Focus chat input (Ctrl + L)
              Settle pause (0.2s - 0.25s)
            * Step B / Q{q_idx}.2: Reverse tab into option button group (Shift + Tab)
              Settle pause (0.2s - 0.25s)
            * Step C / Q{q_idx}.3: Send option key (e.g. '1', or per-question option)
              Settle pause (0.2s - 0.25s)
            * Step D / Q{q_idx}.4: Enter Gate:
              - If q_idx < tq:
                * Send Enter (Advances Continue to next question)
                * UI transition pause (0.4s - 0.5s) so the next question card fully renders on GUI
              - If q_idx == tq:
                * Send Enter (Submits final batch answer)
        """
        tq = max(0, int(total_questions if total_questions is not None else self.total_questions))
        if tq == 0:
            logger.info("Total questions is 0 (status: NO_PENDING_CHATS or clean cancellation). Step 3 cancelled.")
            return True

        opts = list(options) if options is not None else list(self.options_list)
        if len(opts) > tq:
            opts = opts[:tq]
        else:
            while len(opts) < tq:
                opts.append(str(self.option))

        logger.info(f"Initiating dynamic keyboard automation loop: {tq} question(s) | Options: {opts}")
        logger.info("Executing via Pure Native Physical Keystroke Injection (Win32 SendInput)...")

        # Ensure target window is restored, maximized, and in foreground before physical keystrokes
        if IS_WINDOWS and (self.auto_focus or self.auto_maximize):
            self._ensure_window_ready()

        active_window = get_active_window_title()
        logger.info(f"Target Foreground Window: '{active_window}'")

        # Double-check: ensure foreground window is NEVER a web browser
        if IS_WINDOWS and not self.dry_run:
            fg_hwnd = user32.GetForegroundWindow()
            _, fg_pname, _ = get_process_info_for_hwnd(fg_hwnd)
            user_wants_browser = any(
                any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore"))
                for kw in (self.target_window.replace("|", ",").split(",") if self.target_window else [])
            )
            if fg_pname.lower() in DISQUALIFIED_BROWSER_PROCS and not user_wants_browser:
                logger.error(
                    f"[ABORT] Foreground window belongs to browser '{fg_pname}' (HWND: {hex(fg_hwnd) if fg_hwnd else 'None'})! "
                    f"Aborting key simulation to protect user browser tabs and prevent accidental search!"
                )
                return False

        if self.engine == "none":
            logger.error("No valid automation engine available on this platform.")
            return False

        # Define settle pause, UI transition pause, and round completion pause directly from config.json
        settle_pause = max(0.001, self.post_keypress_delay) if not self.dry_run else 0.001
        transition_pause = max(0.001, self.inter_question_delay) if not self.dry_run else 0.001
        round_pause = max(0.0, self.round_completion_pause) if not self.dry_run else 0.0

        # Ensure menu bar is dismissed prior to keystroke dispatch
        if IS_WINDOWS and not self.dry_run:
            try:
                send_single_key(VK_ESCAPE, hold_delay=0.01)
                time.sleep(0.05)
            except Exception:
                pass

        try:
            for q_idx in range(1, tq + 1):
                opt = opts[q_idx - 1]
                is_last = (q_idx == tq)

                if is_last:
                    logger.info(f"[Question {q_idx}/{tq}] Final Question: Selecting option {opt} and submitting with Enter!")
                else:
                    logger.info(f"[Question {q_idx}/{tq}] Selecting option {opt} and continuing with Enter...")

                # Step A / Q{q_idx}.1: Focus chat input (Ctrl + L)
                if not self.skip_ctrl_l:
                    if self.engine == "ctypes":
                        self._execute_step(
                            f"Q{q_idx}.1",
                            "Press [Ctrl + L] (Focus chat box)",
                            lambda: send_key_combo([VK_CONTROL, VK_L], hold_delay=self.hold_delay)
                        )
                    elif self.engine == "pyautogui":
                        self._execute_step(
                            f"Q{q_idx}.1",
                            "Press [Ctrl + L] (Focus chat box)",
                            lambda: pyautogui.hotkey("ctrl", "l")
                        )
                    # Settle pause (0.2s - 0.25s)
                    if not self.dry_run:
                        time.sleep(settle_pause)
                else:
                    logger.info(f"Step Q{q_idx}.1: Skipping Ctrl + L (as requested)")

                # Step B / Q{q_idx}.2: Reverse tab into option button group (Shift + Tab)
                if self.engine == "ctypes":
                    self._execute_step(
                        f"Q{q_idx}.2",
                        "Press [Shift + Tab] (Move backward to question options)",
                        lambda: send_key_combo([VK_SHIFT, VK_TAB], hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        f"Q{q_idx}.2",
                        "Press [Shift + Tab] (Move backward to question options)",
                        lambda: pyautogui.hotkey("shift", "tab")
                    )
                # Settle pause (0.2s - 0.25s)
                if not self.dry_run:
                    time.sleep(settle_pause)

                # Step C / Q{q_idx}.3: Select option key (e.g. '1', or per-question option)
                vk_opt = get_option_vk(opt)
                if self.engine == "ctypes":
                    self._execute_step(
                        f"Q{q_idx}.3",
                        f"Press [{opt}] (Select Option {opt})",
                        lambda: send_single_key(vk_opt, hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        f"Q{q_idx}.3",
                        f"Press [{opt}] (Select Option {opt})",
                        lambda: pyautogui.press(str(opt))
                    )
                # Settle pause (0.2s - 0.25s)
                if not self.dry_run:
                    time.sleep(settle_pause)

                # Step D / Q{q_idx}.4: Enter Gate (Advances on Q1..QN-1, Submits on QN)
                if not self.skip_enter:
                    enter_desc = (
                        f"Press [Enter] (Submit ALL {tq} answers on final question)"
                        if is_last else
                        f"Press [Enter] (Continue to Question {q_idx + 1})"
                    )
                    if self.engine == "ctypes":
                        self._execute_step(
                            f"Q{q_idx}.4",
                            enter_desc,
                            lambda: send_single_key(VK_RETURN, hold_delay=self.hold_delay)
                        )
                    elif self.engine == "pyautogui":
                        self._execute_step(
                            f"Q{q_idx}.4",
                            enter_desc,
                            lambda: pyautogui.press("enter")
                        )

                    # UI transition pause (0.4s - 0.5s) so the next question card fully renders on GUI before next Ctrl+L
                    if not is_last and not self.dry_run:
                        logger.info(f"UI transition pause ({transition_pause:.2f}s) allowing Question {q_idx + 1} card to render on GUI...")
                        time.sleep(transition_pause)
                else:
                    logger.info(f"Step Q{q_idx}.4: Skipping Enter per user flag (--skip-enter)")

            # Round completion pause directly from config.json (step3_round_completion_pause_ms)
            if round_pause > 0 and not self.dry_run:
                logger.info(f"Round completion pause ({round_pause:.2f}s) after full questionnaire sequence...")
                time.sleep(round_pause)

            logger.info(f"[SUCCESS] Multi-question sequence finished successfully for all {tq} question(s) via physical keystrokes!")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Multi-question automation failed with error: {e}", exc_info=True)
            return False

    def execute(self) -> bool:
        """
        Executes the dynamic Grill Me keyboard automation sequence.
        Dynamically dispatches for any number of questions N (1, 2, 3, 4, 5, ... N).
        """
        return self.execute_multi_question(self.total_questions, self.options_list)


def execute_multi_question(
    total_questions: int = 1,
    options: Optional[List[str]] = None,
    **kwargs
) -> bool:
    """
    Convenience functional interface to execute multi-question automation.
    """
    automator = GrillMeAutomator(
        questions=total_questions,
        options_list=options,
        **kwargs
    )
    return automator.execute()


# Step 3 Canonical Alias
Step3KeyboardAutomator = GrillMeAutomator
