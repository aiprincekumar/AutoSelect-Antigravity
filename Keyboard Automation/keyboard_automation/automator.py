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
import logging
from typing import Optional

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
    ):
        self.step_delay = max(0.05, step_delay)
        self.hold_delay = max(0.01, hold_delay)
        self.option = option
        self.skip_ctrl_l = skip_ctrl_l
        self.skip_enter = skip_enter
        self.dry_run = dry_run
        self.target_window = target_window or self.DEFAULT_TARGET
        self.auto_focus = auto_focus
        self.auto_maximize = auto_maximize
        self.settle_delay = max(0.0, settle_delay)
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None

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

        logger.info(
            f"Initialized GrillMeAutomator (Engine: {self.engine}, DryRun: {self.dry_run}, "
            f"Target: '{self.target_window}', AutoFocus: {self.auto_focus}, AutoMaximize: {self.auto_maximize})"
        )

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

    def _execute_step(self, step_num: int, description: str, action_func):
        """Helper to run a step with formatted logging and configurable delays."""
        logger.info(f"Step {step_num}: {description}")
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute: {description}")
        else:
            action_func()
        time.sleep(self.step_delay)

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
