# -*- coding: utf-8 -*-
"""
Core Engine Orchestrator and State Machine for AutoSelect-Commander.
Manages states:
  SCANNING -> [STEP 0: Chat Navigation if (?)] -> COUNTDOWN -> STEP 1 -> STEP 2 -> COOLDOWN.
"""

import math
import signal
import sys
import time
from typing import Tuple

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

from auto_commander.config import Config
from auto_commander.detectors.orchestrator import MultiEngineDetector
from auto_commander.gui.dashboard import TerminalDashboard
from auto_commander.gui.hud import FloatingHUD
from auto_commander.models import DetectionResult
from auto_commander.platform.mouse_ctrl import MouseController
from auto_commander.platform.win32_window import AntigravityWindowManager


class AutoCommanderEngine:
    """Autonomous State Machine for chat navigation, modal detection, countdown, floating HUD, and fail-safe dispatch."""

    def __init__(self, config: Config):
        self.config = config
        self.detector = MultiEngineDetector(config)
        self.mouse_ctrl = MouseController(
            glide_duration=config.smooth_glide_duration_s,
            failsafe_enabled=config.failsafe_enabled,
        )
        self.hud = FloatingHUD(alpha=config.floating_hud_alpha)
        self.is_running = True
        self.current_state = "SCANNING"  # SCANNING, COUNTDOWN, COOLDOWN, SHUTDOWN
        self.initial_mouse_pos = (0, 0)
        self.user_interrupted = False
        self.active_hwnd = None

        # Setup OS signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Setup keyboard listener for hotkeys ('q', 'Q', ESC)
        self._setup_keyboard_listener()

    def _handle_signal(self, signum, frame):
        print(f"\n\033[93m[SHUTDOWN] Signal received ({signum}). Exiting cleanly...\033[0m")
        self.stop()
        sys.exit(0)

    def _setup_keyboard_listener(self):
        """Monitors keyboard in background thread for instant emergency exit."""
        if keyboard is None:
            return

        def on_press(key):
            try:
                if key == keyboard.Key.esc or (hasattr(key, "char") and key.char in ("q", "Q")):
                    if self.current_state == "COUNTDOWN":
                        self.user_interrupted = True
                    else:
                        print("\n\033[93m[EXIT] 'Q' or ESC pressed. Stopping AutoSelect-Commander...\033[0m")
                        self.stop()
            except Exception:
                pass

        try:
            self.kb_listener = keyboard.Listener(on_press=on_press)
            self.kb_listener.daemon = True
            self.kb_listener.start()
        except Exception:
            self.kb_listener = None

    def stop(self):
        self.is_running = False
        self.current_state = "SHUTDOWN"
        if self.hud:
            self.hud.close()

    def _get_mouse_position(self) -> Tuple[int, int]:
        if pyautogui:
            return pyautogui.position()
        return (0, 0)

    def _check_mouse_interrupted(self) -> bool:
        """Calculates Euclidean distance of mouse movement from countdown snapshot."""
        curr_x, curr_y = self._get_mouse_position()
        init_x, init_y = self.initial_mouse_pos
        dist = math.hypot(curr_x - init_x, curr_y - init_y)
        if dist > self.config.mouse_interruption_threshold_px:
            return True
        return False

    def run(self):
        TerminalDashboard.print_banner(self.config)
        tick = 0
        last_not_open_log = 0.0

        while self.is_running:
            try:
                # -------------------------------------------------------------
                # State 1: SCANNING
                # -------------------------------------------------------------
                if self.current_state == "SCANNING":
                    tick += 1

                    # Check Antigravity process and window state
                    is_ready, msg, hwnd = AntigravityWindowManager.check_and_foreground(
                        title_filter=self.config.window_title_filter
                    )
                    self.active_hwnd = hwnd

                    if not is_ready:
                        now = time.time()
                        if now - last_not_open_log >= 5.0:
                            print(f"\n{TerminalDashboard.YELLOW}[ANTIGRAVITY]{TerminalDashboard.RESET} {msg}")
                            last_not_open_log = now
                        time.sleep(self.config.check_interval_ms / 1000.0)
                        continue

                    TerminalDashboard.render_scanning(tick)

                    # Step 1: Check if an interactive decision modal is directly visible in active chat
                    result = self.detector.detect(target_hwnd=self.active_hwnd)
                    if result:
                        TerminalDashboard.render_detected(result)
                        self._execute_countdown(result)
                        time.sleep(self.config.check_interval_ms / 1000.0)
                        continue

                    # Step 0: If no active decision modal in view, scan for a chat tab/sidebar item with (?) badge
                    pending_chat = self.detector.detect_pending_chat(target_hwnd=self.active_hwnd)
                    if pending_chat:
                        chat_cx, chat_cy = pending_chat.center
                        print(
                            f"\n{TerminalDashboard.CYAN}[STEP 0]{TerminalDashboard.RESET} "
                            f"Action required (?) detected on chat item at ({chat_cx}, {chat_cy})! Switching conversation..."
                        )

                        # Ensure Antigravity is in the foreground before gliding to the chat tab
                        if not self.active_hwnd:
                            self.active_hwnd = AntigravityWindowManager.find_antigravity_window(
                                title_filter=self.config.window_title_filter
                            )
                        if self.active_hwnd:
                            AntigravityWindowManager.bring_to_foreground(self.active_hwnd)

                        # Glide to chat item and firm click to bring it into view
                        switched = self.mouse_ctrl.glide_and_click(
                            chat_cx,
                            chat_cy,
                            check_interrupted_fn=self._check_mouse_interrupted,
                            target_hwnd=self.active_hwnd,
                        )

                        if switched:
                            # Allow chat view to render
                            time.sleep(0.4)
                            # Ensure Antigravity is in foreground for subsequent modal detection
                            if self.active_hwnd:
                                AntigravityWindowManager.bring_to_foreground(self.active_hwnd)
                            # Re-scan for newly exposed decision modal
                            result = self.detector.detect(target_hwnd=self.active_hwnd)
                            if result:
                                TerminalDashboard.render_detected(result)
                                self._execute_countdown(result)

                    time.sleep(self.config.check_interval_ms / 1000.0)

                # -------------------------------------------------------------
                # State 2: COOLDOWN
                # -------------------------------------------------------------
                elif self.current_state == "COOLDOWN":
                    cooldown = self.config.cooldown_after_dismissal_s
                    for c in range(cooldown, 0, -1):
                        if not self.is_running:
                            break
                        TerminalDashboard.render_cooldown(c)
                        time.sleep(1.0)
                    self.current_state = "SCANNING"

            except pyautogui.FailSafeException if pyautogui else Exception:
                print("\n\033[91m[FAILSAFE] PyAutoGUI screen corner failsafe triggered! Halting.\033[0m")
                if self.config.floating_hud_enabled:
                    self.hud.flash_cancelled()
                self.current_state = "COOLDOWN"
            except Exception:
                time.sleep(1.0)

    def _execute_countdown(self, result: DetectionResult):
        """Runs the visual countdown with live on-screen floating HUD and 50Hz mouse fail-safe."""
        self.current_state = "COUNTDOWN"
        self.user_interrupted = False
        self.initial_mouse_pos = self._get_mouse_position()

        total_seconds = float(self.config.countdown_seconds)
        start_time = time.time()
        poll_interval = 0.05  # 50 Hz fail-safe polling

        # Show Floating On-Screen HUD Overlay
        if self.config.floating_hud_enabled:
            self.hud.show(total_seconds, result.label)

        # Play sound alert if enabled
        if self.config.sound_notification:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

        while self.is_running and not self.user_interrupted:
            elapsed = time.time() - start_time
            remaining = total_seconds - elapsed

            # Update Floating HUD
            if self.config.floating_hud_enabled:
                self.hud.update_countdown(remaining)

            # Check if user moved the physical mouse
            if self._check_mouse_interrupted():
                curr_x, curr_y = self._get_mouse_position()
                dist = math.hypot(curr_x - self.initial_mouse_pos[0], curr_y - self.initial_mouse_pos[1])
                TerminalDashboard.render_interrupted(dist, self.config.mouse_interruption_threshold_px)
                if self.config.floating_hud_enabled:
                    self.hud.flash_cancelled()
                self.current_state = "COOLDOWN"
                return

            # Check if user requested keyboard abort
            if self.user_interrupted:
                print("\n\033[93m[USER ABORT] Countdown cancelled via keyboard.\033[0m")
                if self.config.floating_hud_enabled:
                    self.hud.flash_cancelled()
                self.current_state = "COOLDOWN"
                return

            # Countdown reached 0 -> Execute 2-Step Auto-Selection!
            if remaining <= 0:
                break

            TerminalDashboard.render_countdown(remaining, total_seconds, result)
            time.sleep(poll_interval)

        # ---------------------------------------------------------------------
        # 2-Step Execution: Step 1 (Option) -> Step 2 (Submit)
        # ---------------------------------------------------------------------
        if not self.user_interrupted and self.is_running:
            target_cx, target_cy = result.center
            TerminalDashboard.render_clicking(1, 2, f"Option 1 ({result.label})", target_cx, target_cy)

            # Ensure Antigravity is in the foreground before clicking Option 1
            if self.active_hwnd:
                AntigravityWindowManager.bring_to_foreground(self.active_hwnd)

            if self.config.floating_hud_enabled:
                self.hud.update_step("⏱️ Step 1/2: Auto-Selecting Option 1...", "Gliding to (Recommended) option...", "#89B4FA")

            success_step1 = self.mouse_ctrl.glide_and_click(
                target_cx,
                target_cy,
                check_interrupted_fn=self._check_mouse_interrupted,
                target_hwnd=self.active_hwnd,
            )

            if not success_step1:
                print("\033[93m[NOTICE] Step 1 cancelled due to motion or boundary condition.\033[0m")
                if self.config.floating_hud_enabled:
                    self.hud.flash_cancelled()
                self.current_state = "COOLDOWN"
                return

            print(f"{TerminalDashboard.GREEN}✓ Step 1 Complete: Option 1 Selected.{TerminalDashboard.RESET}")
            time.sleep(0.35)

            # Step 2: Detect and click Submit button
            submit_result = self.detector.detect_submit_button(option_result=result)
            if submit_result:
                sub_cx, sub_cy = submit_result.center
                TerminalDashboard.render_clicking(2, 2, "Submit button", sub_cx, sub_cy)

                # Ensure Antigravity is in the foreground before clicking Submit button
                if self.active_hwnd:
                    AntigravityWindowManager.bring_to_foreground(self.active_hwnd)

                if self.config.floating_hud_enabled:
                    self.hud.update_step("⏱️ Step 2/2: Confirming Submission...", "Gliding to Submit button...", "#A6E3A1")

                success_step2 = self.mouse_ctrl.glide_and_click(
                    sub_cx,
                    sub_cy,
                    check_interrupted_fn=self._check_mouse_interrupted,
                    target_hwnd=self.active_hwnd,
                )

                if success_step2:
                    TerminalDashboard.render_completed()
                    if self.config.floating_hud_enabled:
                        self.hud.flash_success("✅ 2-STEP AUTO-SELECTION & SUBMISSION COMPLETE!", "Form submitted! Agent unblocked and resuming autonomously.")
                    if self.config.sound_notification:
                        try:
                            import winsound
                            winsound.MessageBeep(winsound.MB_OK)
                        except Exception:
                            pass
                    self.current_state = "COOLDOWN"
                else:
                    print("\033[93m[NOTICE] Step 2 cancelled due to motion or boundary condition.\033[0m")
                    if self.config.floating_hud_enabled:
                        self.hud.flash_cancelled()
                    self.current_state = "COOLDOWN"
            else:
                print(f"{TerminalDashboard.YELLOW}[WARN] Could not locate Submit button after option click.{TerminalDashboard.RESET}")
                if self.config.floating_hud_enabled:
                    self.hud.flash_success("✅ Option 1 Selected!", "Submit button not found; waiting for user action.")
                self.current_state = "COOLDOWN"
