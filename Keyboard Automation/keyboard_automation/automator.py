#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grill Me Automation Orchestrator Subsystem
==========================================
Coordinates countdown, target window preparation, keystroke sequence dispatch,
browser safety aborts, and step execution.
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Optional, Union, List, Tuple

from .constants import (
    DEFAULT_TARGET_WINDOW,
    IS_WINDOWS,
    VK_CONTROL,
    VK_L,
    VK_SHIFT,
    VK_TAB,
    VK_RETURN,
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

logger = logging.getLogger("GrillMeAutomation.Automator")


class GrillMeAutomator:
    """
    Automates the 'Grill Me' keyboard selection sequence with intelligent window auto-targeting:
    1. Scan & identify target window (e.g. Antigravity 2.0 Harness, IDE, or chat app)
    2. Check minimized state -> Restore window (SW_RESTORE / OpenIcon)
    3. Check maximized state -> Maximize to full screen (SW_MAXIMIZE)
    4. Robust foreground focus bypass (Alt key pulse, thread attach, Z-order bump)
    5. Settle delay (default 500ms) for UI rendering
    6. Execute sequence:
       - Ctrl + L    -> Focus chat input
       - Shift + Tab -> Shift focus to option select buttons
       - Option key  -> Select option (default '1')
       - Enter       -> Submit confirmation
    """

    DEFAULT_TARGET = DEFAULT_TARGET_WINDOW

    def __init__(
        self,
        engine: str = "auto",
        step_delay: float = 0.35,
        hold_delay: float = 0.05,
        option: str = "1",
        skip_ctrl_l: bool = False,
        skip_enter: bool = False,
        dry_run: bool = False,
        target_window: str = DEFAULT_TARGET,
        auto_focus: bool = True,
        auto_maximize: bool = True,
        settle_delay: float = 0.5,
        questions: Optional[Union[int, str]] = None,
        options_list: Optional[Union[List[Union[str, int]], str]] = None,
        state_file: Optional[str] = None,
    ):
        self.step_delay = max(0.05, step_delay)
        self.hold_delay = max(0.01, hold_delay)
        self.option = str(option)
        self.skip_ctrl_l = skip_ctrl_l
        self.skip_enter = skip_enter
        self.dry_run = dry_run
        self.target_window = target_window or self.DEFAULT_TARGET
        self.auto_focus = auto_focus
        self.auto_maximize = auto_maximize
        self.settle_delay = max(0.0, settle_delay)
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None
        self.state_file = state_file

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
            Path.cwd() / "target_chat.json",
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
            p = Path(state_file).resolve()
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
            # Check question count fields
            q_count = state_data.get("total_questions_count") or state_data.get("questions_count")
            if q_count is not None:
                try:
                    detected_q = max(1, int(q_count))
                except (ValueError, TypeError):
                    detected_q = 1
            elif state_data.get("is_multi_question"):
                qs = state_data.get("questions")
                sels = state_data.get("selections")
                if isinstance(qs, list) and qs:
                    detected_q = len(qs)
                elif isinstance(sels, list) and sels:
                    detected_q = len(sels)
                else:
                    detected_q = 2

            # Check if selections array contains selected options
            selections = state_data.get("selections")
            if isinstance(selections, list) and len(selections) >= detected_q:
                for item in selections[:detected_q]:
                    if isinstance(item, dict) and "selected_option_index" in item:
                        detected_options.append(str(item["selected_option_index"]))

        # Final determination of total_questions
        final_questions = explicit_questions if explicit_questions is not None else detected_q

        # Final determination of options_list
        if parsed_options is not None:
            final_options = list(parsed_options)
        elif detected_options and len(detected_options) == final_questions:
            final_options = detected_options
        else:
            final_options = [str(self.option)] * final_questions

        while len(final_options) < final_questions:
            final_options.append(str(self.option))
        final_options = final_options[:final_questions]

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

    def run_countdown(self, seconds: int = 5):
        """Displays visual countdown in terminal allowing user or system to focus target window."""
        print("\n" + "=" * 65)
        print("  [*] GRILL ME AUTOMATION - HYBRID FOCUS & TARGETING")
        print("=" * 65)

        # Engage auto-targeting, maximize, and focus subsystem
        if self.auto_focus or self.auto_maximize:
            self.prepare_target_window()

        if seconds > 0:
            print("Target window is positioned and focused.")
            print(f"Automation sequence will execute in {seconds} seconds...\n")

            for remaining in range(seconds, 0, -1):
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

    def execute_multi_question(self, total_questions: int, options: Optional[List[str]] = None) -> bool:
        """
        Executes deterministic multi-question keyboard automation loop.
        Ensures Enter is strictly pressed ONLY on the final question.

        Sequence for question 1..N:
          Step A: Focus chat input (Ctrl + L)
          Step B: Reverse tab to option buttons (Shift + Tab)
          Step C: Select option key (e.g. '1')
          Step D: Conditional Enter Gate:
                  - Questions 1..N-1: Suppress Enter (advance loop)
                  - Question N (final): Press Enter (submit batch)
        """
        opts = list(options) if options else [str(self.option)] * total_questions
        while len(opts) < total_questions:
            opts.append(str(self.option))

        logger.info(f"Initiating multi-question automation loop: {total_questions} questions | Options: {opts}")

        # Ensure target window is prepared and focused if not done already
        if IS_WINDOWS and (self.auto_focus or self.auto_maximize):
            if not self.target_hwnd:
                self.prepare_target_window()
            elif self.auto_focus and not self.dry_run:
                curr_fg = user32.GetForegroundWindow()
                if curr_fg != self.target_hwnd:
                    logger.info("Ensuring target window is brought to foreground before keystrokes...")
                    ensure_window_on_screen(
                        self.target_hwnd,
                        auto_maximize=self.auto_maximize,
                        auto_focus=True,
                        settle_delay=0.1
                    )

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

        try:
            for q_idx in range(1, total_questions + 1):
                opt = opts[q_idx - 1]
                is_last = (q_idx == total_questions)
                logger.info(f"--- Processing Question {q_idx}/{total_questions} [Select Option: '{opt}'] ---")

                # Step A: Focus chat input (Ctrl + L)
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
                else:
                    logger.info(f"Step Q{q_idx}.1: Skipping Ctrl + L (as requested)")

                # Step B: Reverse tab to option buttons (Shift + Tab)
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

                # Step C: Select option key (e.g. '1')
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

                # Step D: Conditional Enter Gate
                if is_last:
                    if not self.skip_enter:
                        if self.engine == "ctypes":
                            self._execute_step(
                                f"Q{q_idx}.4",
                                "Press [Enter] (Submit ALL answers on final question)",
                                lambda: send_single_key(VK_RETURN, hold_delay=self.hold_delay)
                            )
                        elif self.engine == "pyautogui":
                            self._execute_step(
                                f"Q{q_idx}.4",
                                "Press [Enter] (Submit ALL answers on final question)",
                                lambda: pyautogui.press("enter")
                            )
                    else:
                        logger.info(f"Step Q{q_idx}.4: Skipping Enter on final question (user flag --skip-enter)")
                else:
                    logger.info(f"Step Q{q_idx}.4: [SUPPRESS ENTER] Intermediate question {q_idx}/{total_questions} completed. Advancing...")
                    time.sleep(self.step_delay)

            logger.info("[SUCCESS] Multi-question sequence finished successfully!")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Multi-question automation failed with error: {e}", exc_info=True)
            return False

    def execute(self) -> bool:
        """Executes the full automated key sequence."""
        # Ensure target window is prepared and focused if not done already
        if IS_WINDOWS and (self.auto_focus or self.auto_maximize):
            if not self.target_hwnd:
                self.prepare_target_window()
            elif self.auto_focus and not self.dry_run:
                curr_fg = user32.GetForegroundWindow()
                if curr_fg != self.target_hwnd:
                    logger.info("Ensuring target window is brought to foreground before keystrokes...")
                    ensure_window_on_screen(
                        self.target_hwnd,
                        auto_maximize=self.auto_maximize,
                        auto_focus=True,
                        settle_delay=0.1
                    )

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

        # Branch to multi-question workflow if total_questions > 1
        if self.total_questions > 1:
            return self.execute_multi_question(self.total_questions, self.options_list)

        try:
            step = 1

            # Step 1: Ctrl + L (Focus Chat Box)
            if not self.skip_ctrl_l:
                if self.engine == "ctypes":
                    self._execute_step(
                        step,
                        "Press [Ctrl + L] (Focus chat input)",
                        lambda: send_key_combo([VK_CONTROL, VK_L], hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        step,
                        "Press [Ctrl + L] (Focus chat input)",
                        lambda: pyautogui.hotkey("ctrl", "l")
                    )
                step += 1
            else:
                logger.info("Skipping Step: Ctrl + L (as requested)")

            # Step 2: Shift + Tab (Shift focus to option buttons)
            if self.engine == "ctypes":
                self._execute_step(
                    step,
                    "Press [Shift + Tab] (Move backward to options)",
                    lambda: send_key_combo([VK_SHIFT, VK_TAB], hold_delay=self.hold_delay)
                )
            elif self.engine == "pyautogui":
                self._execute_step(
                    step,
                    "Press [Shift + Tab] (Move backward to options)",
                    lambda: pyautogui.hotkey("shift", "tab")
                )
            step += 1

            # Step 3: Option Key (Select Option 1 by default)
            vk_opt = get_option_vk(self.option)
            if self.engine == "ctypes":
                self._execute_step(
                    step,
                    f"Press [{self.option}] (Select Option {self.option})",
                    lambda: send_single_key(vk_opt, hold_delay=self.hold_delay)
                )
            elif self.engine == "pyautogui":
                self._execute_step(
                    step,
                    f"Press [{self.option}] (Select Option {self.option})",
                    lambda: pyautogui.press(str(self.option))
                )
            step += 1

            # Step 4: Enter (Submit Confirmation)
            if not self.skip_enter:
                if self.engine == "ctypes":
                    self._execute_step(
                        step,
                        "Press [Enter] (Submit confirmation)",
                        lambda: send_single_key(VK_RETURN, hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        step,
                        "Press [Enter] (Submit confirmation)",
                        lambda: pyautogui.press("enter")
                    )
                step += 1
            else:
                logger.info("Skipping Step: Enter (as requested)")

            logger.info("[SUCCESS] All automation steps completed successfully!")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Automation failed with error: {e}", exc_info=True)
            return False


def execute_multi_question(
    total_questions: int = 2,
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

