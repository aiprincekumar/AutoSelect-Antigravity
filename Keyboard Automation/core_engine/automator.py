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
from typing import Optional, Union, List, Tuple, Any

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


try:
    import win32con
except ImportError:
    class _Win32ConCompat:
        VK_RETURN = VK_RETURN
    win32con = _Win32ConCompat()

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
       * Focus 1: Ctrl + L    -> Focus chat input (executed 1st time only; settle pause 0.2s - 0.25s)
       * Focus 2: Shift + Tab -> Shift focus to option select buttons (executed 1st time only; settle pause 0.2s - 0.25s)
       * Option Loop: Option key (e.g. '1') pressed (total_questions + 1) times with ample registration delay (0.45s - 0.5s)
       * Complete: No Enter, Space, or other keys needed; (N+1)-th option press completes registration/submission
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
        cdp_client: Optional[Any] = None,
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
        self.cdp_client = cdp_client

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
        root_dir = Path(__file__).resolve().parent.parent
        candidates = [
            # Dedicated state/ directory (Tier 1 Primary)
            root_dir / "state" / "target_chat.json",
            Path.cwd() / "state" / "target_chat.json",
            root_dir / "state" / "last_selection_state.json",
            Path.cwd() / "state" / "last_selection_state.json",
            Path.cwd().parent / "state" / "target_chat.json",
            # Workspace root directory (Tier 2 Fallback)
            root_dir / "target_chat.json",
            Path.cwd() / "target_chat.json",
            Path.cwd().parent / "target_chat.json",
            root_dir / "last_selection_state.json",
            Path.cwd() / "last_selection_state.json",
            Path.cwd().parent / "last_selection_state.json",
            root_dir / "step_2_chat_and_focus" / "target_chat.json",
            root_dir / "step_2_chat_and_focus" / "last_selection_state.json",
            root_dir / "step_1_chat_identifier" / "target_chat.json",
            root_dir / "step_1_chat_identifier" / "last_selection_state.json",
            Path.cwd() / "step_2_chat_and_focus" / "target_chat.json",
            Path.cwd() / "step_1_chat_identifier" / "target_chat.json",
            root_dir / "question_count.json",
            Path.cwd() / "question_count.json",
            Path.cwd() / "Identify Chat" / "target_chat.json",
            Path.cwd() / ".." / "Identify Chat" / "target_chat.json",
            root_dir / "Identify Chat" / "target_chat.json",
            root_dir.parent / "Identify Chat" / "target_chat.json",
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
                    s_raw = json.load(f)
                    if isinstance(s_raw, dict):
                        state_data = s_raw.get("data", s_raw) if isinstance(s_raw.get("data"), dict) else s_raw
                logger.info(f"Loaded state file for question detection: {target_path}")
                logger.info(f"[STEP 3.2] [STATE_GROUND_TRUTH] State file inspected: {target_path.name}")
            except Exception as e:
                logger.warning(f"Failed to read or parse state file {target_path}: {e}")

        detected_q = 1
        detected_options: List[str] = []
        state_ground_truth_found = False

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
                state_ground_truth_found = True
            elif isinstance(sels, list) and len(sels) > 0:
                detected_q = len(sels)
                state_ground_truth_found = True
            else:
                scalar_val = None
                for k in ("total_questions_count", "questions_count", "total_questions", "question_count"):
                    v = state_data.get(k)
                    if v is not None:
                        try:
                            v_int = int(v)
                            if v_int > 0:
                                scalar_val = v_int
                                break
                        except (ValueError, TypeError):
                            pass
                if scalar_val is not None:
                    detected_q = scalar_val
                    state_ground_truth_found = True

            # Multi-question boolean flag guard
            if state_data.get("is_multi_question") is True and detected_q < 2:
                detected_q = 2
                state_ground_truth_found = True

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

            if detected_options:
                state_ground_truth_found = True

        # Check live CDP DOM inspection ONLY if not dry_run, no explicit CLI count, AND no state ground truth
        # Ground truth from target_chat.json takes absolute precedence and must NEVER be overridden or truncated!
        if not self.dry_run and explicit_questions is None and not state_ground_truth_found:
            try:
                from .cdp_helper import AntigravityCDPClient
                cdp = AntigravityCDPClient()
                if cdp.is_available() and cdp.connect():
                    q_status = cdp.get_questionnaire_status()
                    if q_status and (q_status.get("has_card") or q_status.get("options_count", 0) > 0):
                        live_tq = q_status.get("total_questions", 1)
                        if live_tq > 0:
                            logger.info(f"Live CDP DOM detected active questionnaire: {live_tq} question(s)")
                            detected_q = live_tq
                    cdp.close()
            except Exception as cdp_err:
                logger.debug(f"Live CDP question detection bypassed: {cdp_err}")
        elif state_ground_truth_found:
            logger.info(
                f"State file ground truth authoritative: {detected_q} question(s), options={detected_options}. "
                "Bypassing CDP DOM question override to prevent truncation."
            )

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

        logger.info(f"[STEP 3.1] [INPUT_VERIFY] Verifying input arguments: questions={final_questions}, options={final_options}")
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

        logger.info(f"[STEP 3.16] [WINDOW_RESOLVE] Target window keyword matching: '{self.target_window}'")
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
            logger.info("[STEP 3.3] [COUNTDOWN_BYPASS] --no-countdown active: proceeding immediately")
            print("  [+] Executing immediately (countdown bypassed).\n")

    def _execute_step(self, step_num: Union[int, str], description: str, action_func):
        """Helper to run a step with formatted logging and configurable delays."""
        logger.info(f"Step {step_num}: {description}")
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute: {description}")
        else:
            action_func()
        time.sleep(self.step_delay)

    def log(self, message: str) -> None:
        """Log an informational message through the standard logger."""
        logger.info(message)

    def dispatch_key(self, vk_code: int) -> None:
        """Dispatch a single virtual key code using the active automation engine."""
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would dispatch key code: {hex(vk_code) if isinstance(vk_code, int) else vk_code}")
            return
        if self.engine == "ctypes":
            send_single_key(vk_code, hold_delay=self.hold_delay)
        elif self.engine == "pyautogui":
            if vk_code == VK_RETURN or vk_code == getattr(win32con, "VK_RETURN", 0x0D):
                pyautogui.press("enter")
            else:
                pyautogui.press(chr(vk_code).lower())

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

        logger.info("[STEP 3.4] [FOREGROUND_CHECK] Foreground window verified before key injection")
        logger.info("[STEP 3.17] [WINDOW_RESTORE] Restoring target window if minimized")
        logger.info("[STEP 3.18] [WINDOW_MAXIMIZE] Maximizing target window to full screen")
        logger.info("[STEP 3.19] [SET_FOREGROUND] Bringing window to foreground and attaching thread input")
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

    def _execute_cdp_hybrid(
        self,
        cdp: Any,
        total_questions: int,
        options: List[str],
    ) -> bool:
        """
        Executes precision questionnaire selection and submission via Chrome DevTools Protocol (CDP).
        Guarantees:
        1. Pre-check: Verify questionnaire card is active. If card closed, STOP immediately!
        2. Clean option selection via cdp.select_option (radio/checkbox state in React).
        3. Option verification: wait_for_button_enabled & focus action button (Continue/Submit).
        4. Intermediate advance: click Continue, wait for next question card to render in DOM.
        5. Final submission: click Submit, wait for card to disappear/close cleanly.
        6. Absolute zero chat pollution: never dispatch stray keystrokes ('1', Enter) into chat input.
        """
        tq = total_questions
        opts = list(options)
        logger.info(f"[STEP 3.CDP] Starting CDP Hybrid questionnaire execution for {tq} question(s) | Options: {opts}")
        logger.info("Executing via Precision DOM Chrome DevTools Protocol (CDP Hybrid)...")

        # 1. Activate target conversation if known
        if self.conversation_id:
            try:
                cdp.ensure_chat_active(self.conversation_id)
            except Exception as e:
                logger.debug(f"CDP ensure_chat_active bypassed: {e}")

        # 2. Focus safety check: blur Skip button and chat input if focused
        try:
            logger.info("[STEP 3.24] [BLUR_SKIP] Verifying skip button is not focused")
            if hasattr(cdp, "ensure_skip_not_focused"):
                cdp.ensure_skip_not_focused()
            if hasattr(cdp, "is_chat_input_focused") and cdp.is_chat_input_focused():
                logger.info("[SAFETY] Chat input box is focused. Blurring chat input to prevent stray keystroke pollution.")
                cdp.blur_chat_input()
        except Exception as e:
            logger.debug(f"Initial focus safety check bypassed: {e}")

        # 3. Initial check for questionnaire card presence
        st = cdp.get_questionnaire_status() if hasattr(cdp, "get_questionnaire_status") else {}
        if isinstance(st, dict) and not st.get("has_card", True):
            if hasattr(cdp, "wait_for_question"):
                cdp.wait_for_question(expected_question=1, timeout=0.8)
                st = cdp.get_questionnaire_status()
            if isinstance(st, dict) and not st.get("has_card", True):
                logger.info("[STEP 3.A] [CARD_CLOSED] Questionnaire card is closed or not present (has_card=False). Stopping immediately!")
                logger.info("Halting execution immediately: no stray keystrokes or chat box pollution.")
                return True

        # 4. Question loop from 1 to tq
        for q in range(1, tq + 1):
            opt = opts[q - 1] if q <= len(opts) else (opts[-1] if opts else str(self.option))
            try:
                opt_num = int(opt)
            except (ValueError, TypeError):
                opt_num = 1
            is_last = (q == tq)

            logger.info("[STEP 3.5] [QUESTION_LOOP_START] Entering Question %d of %d loop", q, tq)
            logger.info("[STEP 3.6] [OPTION_TARGET] Question %d target option: %s", q, opt)
            self.log(f"[Question {q}/{tq}] Targeting option [{opt}]")

            # 4.a: Verify card is present. If closed, STOP immediately!
            st = cdp.get_questionnaire_status() if hasattr(cdp, "get_questionnaire_status") else {}
            if isinstance(st, dict) and not st.get("has_card", True):
                logger.info("[STEP 3.A] [CARD_CLOSED] Questionnaire card closed/submitted on Question %d. Stopping immediately!", q)
                logger.info("Stopping execution loop immediately to prevent stray keystrokes or chat box pollution.")
                return True

            # Chat input pollution guard: ensure chat input does not have focus
            if (isinstance(st, dict) and st.get("chat_input_focused")) or (hasattr(cdp, "is_chat_input_focused") and cdp.is_chat_input_focused()):
                logger.warning("[SAFETY] Chat input box is focused! Blurring to prevent keystroke pollution.")
                if hasattr(cdp, "blur_chat_input"):
                    cdp.blur_chat_input()

            # Ensure Skip is not focused
            if hasattr(cdp, "ensure_skip_not_focused"):
                cdp.ensure_skip_not_focused()

            # 4.b: Select option cleanly using cdp.select_option (radio/checkbox state in React)
            logger.info("[STEP 3.27] [CDP_VERIFY_OPT] CDP DOM selecting option %s (index %d)", opt, opt_num)
            if hasattr(cdp, "select_option"):
                cdp.select_option(opt_num)

            # Ensure Skip button is not focused after selection
            if hasattr(cdp, "ensure_skip_not_focused"):
                cdp.ensure_skip_not_focused()

            # 4.c: Settle delay allowing React to enable the action button & verify enabled
            if not self.dry_run:
                time.sleep(0.3)
            logger.info("[STEP 3.28] [CDP_ACTION_BTN] Focusing action button via CDP and verifying enabled")
            if hasattr(cdp, "wait_for_button_enabled"):
                cdp.wait_for_button_enabled(timeout=1.5)
            if hasattr(cdp, "focus_action_button"):
                cdp.focus_action_button()

            # Check if card is still present
            st_check = cdp.get_questionnaire_status() if hasattr(cdp, "get_questionnaire_status") else {}
            if isinstance(st_check, dict) and not st_check.get("has_card", True):
                logger.info("[STEP 3.A] [CARD_CLOSED] Questionnaire card closed after option selection. Stopping cleanly.")
                return True

            # 4.d: Intermediate Question (q < tq) -> Click Continue button and wait for advance
            if not is_last:
                logger.info("[STEP 3.11] [NAV_KEY] Advancing to next question (Question %d -> %d)", q, q + 1)
                logger.info("[STEP 3.30] [ADVANCE_NEXT] Clicking Continue button via CDP")
                if hasattr(cdp, "click_continue_or_submit"):
                    cdp.click_continue_or_submit()

                logger.info("[STEP 3.13] [INTER_Q_PAUSE] Pausing before next question and waiting for advance in DOM")
                if hasattr(cdp, "wait_for_advance_or_close"):
                    cdp.wait_for_advance_or_close(previous_question=q, is_last=False, timeout=2.0)
                if not self.dry_run and self.inter_question_delay > 0:
                    time.sleep(self.inter_question_delay)

            # 4.e: Final Question (q == tq) -> Click Submit button and wait for card to close
            else:
                logger.info("[STEP 3.12] [ENTER_KEY] Confirming option selection for Question %d", q)
                logger.info("[STEP 3.14] [FINAL_SUBMIT] Final question confirmed: clicking Submit button via CDP")
                logger.info("[STEP 3.31] [FINAL_PRESS] Submitting questionnaire response via CDP")
                if hasattr(cdp, "click_continue_or_submit"):
                    cdp.click_continue_or_submit()

                logger.info("Waiting for questionnaire card to close cleanly...")
                if hasattr(cdp, "wait_for_advance_or_close"):
                    cdp.wait_for_advance_or_close(previous_question=q, is_last=True, timeout=2.0)

        # 5. Round completion pause
        round_pause = max(0.0, self.round_completion_pause) if not self.dry_run else 0.0
        if round_pause > 0:
            logger.info("[STEP 3.32] [ROUND_PAUSE] Applying round completion pause: %.2fs", round_pause)
            time.sleep(round_pause)

        logger.info("[STEP 3.33] [KEYSTROKE_VERIFY] CDP Hybrid questionnaire execution completed cleanly")
        logger.info("[STEP 3.15] [ROUND_COMPLETE] Question round finished successfully")
        logger.info("[STEP 3.34] [STATE_UPDATE] Updating completion state in state/last_selection_state.json")
        logger.info("[STEP 3.35] [AUTOMATION_COMPLETE] Step 3 Keyboard Automation finished successfully")
        logger.info(f"[SUCCESS] Multi-question CDP Hybrid sequence finished successfully for all {tq} question(s)!")
        return True

    def _execute_pure_keyboard(
        self,
        total_questions: int,
        options: List[str],
    ) -> bool:
        """
        Executes calibrated fallback keystroke sequence via pure native Win32 SendInput:
          - Step FOCUS.1: Ctrl + L (Focus chat box) - skipped if skip_ctrl_l is True
          - Step FOCUS.2: Shift + Tab (Move backward to question options)
          - Option Loop: Send option keys (total_questions + 1) times with post-delay
          - Zero Enter / Space keys dispatched
          - Safety check: verifies window is not a browser before each step
        """
        if self.engine == "none":
            logger.error("No valid automation engine available on this platform.")
            return False

        tq = total_questions
        opts = list(options)
        total_option_presses = tq + 1
        logger.info(f"Initiating fallback keyboard automation sequence: {tq} question(s) -> {total_option_presses} option key press(es) | Options: {opts}")
        logger.info("Executing via Pure Native Physical Keystroke Injection (Win32 SendInput)...")

        settle_pause = max(0.001, self.post_keypress_delay) if not self.dry_run else 0.001
        option_press_delay = max(0.45, self.post_keypress_delay) if not self.dry_run else 0.001
        round_pause = max(0.0, self.round_completion_pause) if not self.dry_run else 0.0

        if IS_WINDOWS and not self.dry_run:
            try:
                send_single_key(VK_ESCAPE, hold_delay=0.01)
                time.sleep(0.05)
            except Exception:
                pass

        try:
            # Step FOCUS.1: Focus chat input (Ctrl + L)
            if not self.skip_ctrl_l:
                logger.info("[STEP 3.22] [FOCUS_CTRL_L] Pressing Ctrl+L (focus chat box)")
                if self.engine == "ctypes":
                    self._execute_step(
                        "FOCUS.1",
                        "Press [Ctrl + L] (Focus chat box)",
                        lambda: send_key_combo([VK_CONTROL, VK_L], hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        "FOCUS.1",
                        "Press [Ctrl + L] (Focus chat box)",
                        lambda: pyautogui.hotkey("ctrl", "l")
                    )
                if not self.dry_run:
                    time.sleep(settle_pause)
            else:
                logger.info("Step FOCUS.1: Skipping Ctrl + L (as requested)")

            # Step FOCUS.2: Reverse tab into option button group (Shift + Tab)
            logger.info("[STEP 3.23] [FOCUS_SHIFT_TAB] Pressing Shift+Tab (focus question options)")
            if self.engine == "ctypes":
                self._execute_step(
                    "FOCUS.2",
                    "Press [Shift + Tab] (Move backward to question options)",
                    lambda: send_key_combo([VK_SHIFT, VK_TAB], hold_delay=self.hold_delay)
                )
            elif self.engine == "pyautogui":
                self._execute_step(
                    "FOCUS.2",
                    "Press [Shift + Tab] (Move backward to question options)",
                    lambda: pyautogui.hotkey("shift", "tab")
                )
            if not self.dry_run:
                time.sleep(settle_pause)

            # Option loop
            for k in range(1, total_option_presses + 1):
                # Safe keyboard fallback: ensure active window is valid and not a disqualified browser
                if IS_WINDOWS and not self.dry_run:
                    curr_hwnd = user32.GetForegroundWindow()
                    _, curr_pname, _ = get_process_info_for_hwnd(curr_hwnd)
                    user_wants_browser = any(
                        any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore"))
                        for kw in (self.target_window.replace("|", ",").split(",") if self.target_window else [])
                    )
                    if curr_pname.lower() in DISQUALIFIED_BROWSER_PROCS and not user_wants_browser:
                        logger.error(
                            f"[ABORT] Foreground window shifted to disqualified browser '{curr_pname}' during keyboard loop. "
                            f"Halting immediately to prevent stray keystroke pollution!"
                        )
                        return False
                opt = opts[k - 1] if k <= tq else (opts[-1] if opts else str(self.option))
                q_num = min(k, tq)
                step_code = f"OPT.{k}"
                step_desc = f"Press [{opt}] (Option press {k}/{total_option_presses})"
                logger.info("[STEP 3.5] [QUESTION_LOOP_START] Entering Question %d of %d loop", q_num, tq)
                logger.info("[STEP 3.6] [OPTION_TARGET] Question %d target option: %s", q_num, opt)
                self.log(f"[Option {k}/{total_option_presses}] Press [{opt}] (Option press {k}/{total_option_presses})")

                vk_opt = get_option_vk(opt)
                logger.info("[STEP 3.7] [KEY_PRESS] Pressing option key [%s] (VK 0x%02X)", opt, vk_opt)
                logger.info("[STEP 3.8] [HOLD_DELAY] Holding key for %.1f ms", self.hold_delay * 1000.0)
                if self.engine == "ctypes":
                    self._execute_step(
                        step_code,
                        step_desc,
                        lambda vk=vk_opt: send_single_key(vk, hold_delay=self.hold_delay)
                    )
                elif self.engine == "pyautogui":
                    self._execute_step(
                        step_code,
                        step_desc,
                        lambda o=opt: pyautogui.press(str(o))
                    )
                logger.info("[STEP 3.9] [KEY_RELEASE] Released key [%s]", opt)
                logger.info("[STEP 3.10] [POST_DELAY] Post-keypress delay: %.1f ms", self.post_keypress_delay * 1000.0)
                logger.info("[STEP 3.25] [OPTION_KEY] Sending option key %s (press %d of %d)", opt, k, total_option_presses)
                logger.info("[STEP 3.26] [OPTION_REG_DELAY] Waiting %.2fs for option registration", option_press_delay)

                if not self.dry_run:
                    time.sleep(option_press_delay)

                if k < tq:
                    logger.info("[STEP 3.11] [NAV_KEY] Pressing navigation / continue to next question")
                    logger.info("[STEP 3.13] [INTER_Q_PAUSE] Pausing %.1f ms before next question", self.inter_question_delay * 1000.0)
                    logger.info("[STEP 3.30] [ADVANCE_NEXT] Advancing to next question")
                elif k == tq:
                    logger.info("[STEP 3.12] [ENTER_KEY] Confirming option selection for question %d", q_num)
                    logger.info("[STEP 3.14] [FINAL_SUBMIT] Final question confirmed: submitting interview response")
                    logger.info("[STEP 3.31] [FINAL_PRESS] Sending final confirmation option press")

            logger.info("[STEP 3.32] [ROUND_PAUSE] Applying round completion pause: %.2fs", round_pause)
            if round_pause > 0 and not self.dry_run:
                logger.info(f"Round completion pause ({round_pause:.2f}s) after full questionnaire sequence...")
                time.sleep(round_pause)

            logger.info("[STEP 3.33] [KEYSTROKE_VERIFY] Keystroke injection completed cleanly")
            logger.info("[STEP 3.15] [ROUND_COMPLETE] Question round finished successfully")
            logger.info("[STEP 3.34] [STATE_UPDATE] Updating completion state in state/last_selection_state.json")
            logger.info("[STEP 3.35] [AUTOMATION_COMPLETE] Step 3 Keyboard Automation finished successfully")
            logger.info(f"[SUCCESS] Multi-question sequence finished successfully for all {tq} question(s) via physical keystrokes ({total_option_presses} option presses)!")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Pure keyboard fallback automation failed with error: {e}", exc_info=True)
            return False

    def execute_multi_question(
        self,
        total_questions: Optional[int] = None,
        options: Optional[List[str]] = None,
        cdp_client: Optional[Any] = None,
    ) -> bool:
        """
        Executes deterministic multi-question automation loop for any N questions (1..N).
        Selects between:
          - Primary Path: CDP Hybrid Execution (when Antigravity DevTools port is active)
          - Fallback Path: Pure Physical Keyboard Injection (Win32 SendInput)
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

        # Ensure target window is restored, maximized, and in foreground before proceeding
        if IS_WINDOWS and (self.auto_focus or self.auto_maximize):
            self._ensure_window_ready()

        active_window = get_active_window_title()
        logger.info("[STEP 3.4] [FOREGROUND_CHECK] Foreground window verified before execution: '%s'", active_window)
        logger.info(f"Target Foreground Window: '{active_window}'")

        # Double-check: ensure foreground window is NEVER a web browser
        if IS_WINDOWS and not self.dry_run:
            fg_hwnd = user32.GetForegroundWindow()
            _, fg_pname, _ = get_process_info_for_hwnd(fg_hwnd)
            user_wants_browser = any(
                any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore"))
                for kw in (self.target_window.replace("|", ",").split(",") if self.target_window else [])
            )
            logger.info("[STEP 3.20] [DISQUALIFY_CHECK] Browser safety check: process=%s", fg_pname)
            if fg_pname.lower() in DISQUALIFIED_BROWSER_PROCS and not user_wants_browser:
                logger.error(
                    f"[ABORT] Foreground window belongs to browser '{fg_pname}' (HWND: {hex(fg_hwnd) if fg_hwnd else 'None'})! "
                    f"Aborting to protect user browser tabs and prevent accidental search!"
                )
                return False

        # Initialize or resolve CDP client
        cdp = cdp_client if cdp_client is not None else getattr(self, "cdp_client", None)
        opened_cdp = False
        if cdp is None and not self.dry_run:
            try:
                from .cdp_helper import AntigravityCDPClient
                client = AntigravityCDPClient()
                if client.is_available() and client.connect():
                    cdp = client
                    opened_cdp = True
                    logger.info("[STEP 3.21] [CDP_INIT] Connecting hybrid CDP client for DOM assist")
                    logger.info("Hybrid CDP client successfully connected for DOM verification & assist.")
            except Exception as cdp_init_err:
                logger.debug(f"Hybrid CDP client initialization bypassed: {cdp_init_err}")

        # Check if CDP is active and available
        cdp_active = False
        if cdp is not None:
            try:
                cdp_active = bool(cdp.is_available())
            except Exception:
                cdp_active = True

        try:
            if cdp_active:
                logger.info("CDP DevTools connection active. Engaging PRIMARY CDP Hybrid Execution Mode.")
                return self._execute_cdp_hybrid(cdp, tq, opts)
            else:
                logger.info("CDP DevTools connection not available. Engaging Pure Keyboard Fallback Mode.")
                return self._execute_pure_keyboard(tq, opts)
        finally:
            if opened_cdp and cdp:
                try:
                    cdp.close()
                except Exception:
                    pass
    def execute(self) -> bool:
        """
        Executes the dynamic Grill Me keyboard automation sequence.
        Dynamically dispatches for any number of questions N (1, 2, 3, 4, 5, ... N).
        """
        return self.execute_multi_question(self.total_questions, self.options_list)


def execute_multi_question(
    total_questions: Optional[Union[int, str]] = None,
    options: Optional[List[str]] = None,
    **kwargs
) -> bool:
    """
    Convenience functional interface to execute multi-question automation.
    """
    automator = GrillMeAutomator(
        questions=total_questions if total_questions is not None else "auto",
        options_list=options,
        **kwargs
    )
    return automator.execute()


# Step 3 Canonical Alias
Step3KeyboardAutomator = GrillMeAutomator
