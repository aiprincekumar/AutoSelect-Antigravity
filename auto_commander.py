#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
AutoSelect-Commander: Visual Mouse Automation & Auto-Selector for Antigravity
===============================================================================
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Repository: C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
Version: 1.0.0
Description:
    Autonomous visual daemon that monitors the desktop surface for Antigravity
    interactive decision modals ('ask_question' cards), displays a 30s terminal
    countdown with instant mouse-movement fail-safe, and smoothly glides the mouse
    cursor using cubic easing to auto-select '(Recommended)' options.
===============================================================================
"""

import argparse
import ctypes
import json
import math
import os
import random
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Enable High-DPI Awareness on Windows to prevent coordinate drift
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Enable Windows Console Virtual Terminal Processing (ANSI Escapes)
try:
    kernel32 = ctypes.windll.kernel32
    h_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_ulong()
    if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
        kernel32.SetConsoleMode(h_out, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
except Exception:
    pass

# Third-party library imports with graceful status tracking
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Moving mouse to screen corner triggers emergency abort
    pyautogui.PAUSE = 0.05
except ImportError:
    pyautogui = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageGrab
except ImportError:
    Image = ImageDraw = ImageFont = ImageGrab = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

try:
    from pynput import keyboard, mouse
except ImportError:
    keyboard = mouse = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import uiautomation as auto
except ImportError:
    auto = None


# =============================================================================
# 1. Configuration Manager
# =============================================================================
@dataclass
class Config:
    countdown_seconds: int = 30
    check_interval_ms: int = 1000
    mouse_interruption_threshold_px: int = 15
    smooth_glide_duration_s: float = 0.8
    cooldown_after_dismissal_s: int = 5
    failsafe_enabled: bool = True
    sound_notification: bool = True
    window_title_filter: str = "Antigravity"
    target_keywords: Tuple[str, ...] = (
        "(Recommended)",
        "Recommended",
        "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
        "(Recommended) GitHub",
        "Proceed",
    )
    detection_mode: str = "auto"  # 'auto', 'uia', 'vision'

    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """Load configuration from JSON file or return defaults."""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(
                        countdown_seconds=int(data.get("countdown_seconds", 30)),
                        check_interval_ms=int(data.get("check_interval_ms", 1000)),
                        mouse_interruption_threshold_px=int(data.get("mouse_interruption_threshold_px", 15)),
                        smooth_glide_duration_s=float(data.get("smooth_glide_duration_s", 0.8)),
                        cooldown_after_dismissal_s=int(data.get("cooldown_after_dismissal_s", 5)),
                        failsafe_enabled=bool(data.get("failsafe_enabled", True)),
                        sound_notification=bool(data.get("sound_notification", True)),
                        window_title_filter=str(data.get("window_title_filter", "Antigravity")),
                        target_keywords=tuple(data.get("target_keywords", cls.target_keywords)),
                        detection_mode=str(data.get("detection_mode", "auto")),
                    )
            except Exception as e:
                print(f"\033[93m[WARN] Failed to parse config.json ({e}). Using default settings.\033[0m")
        return cls()


# =============================================================================
# 2. Detection Result Data Structure
# =============================================================================
@dataclass
class DetectionResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    source: str  # 'UIAutomation' or 'ComputerVision'
    label: str

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


# =============================================================================
# 3. Windows UIAutomation Detection Engine (Fast, DPI-Invariant)
# =============================================================================
class UIAutomationDetector:
    """Scans the Windows UI Automation tree to locate Antigravity decision buttons."""

    def __init__(self, title_filter: str, target_keywords: Tuple[str, ...]):
        self.title_filter = title_filter.lower()
        self.target_keywords = target_keywords

    def scan(self) -> Optional[DetectionResult]:
        if auto is None:
            return None

        try:
            root = auto.GetRootControl()
            if not root:
                return None

            top_windows = root.GetChildren()
            for win in top_windows:
                name = win.Name or ""
                # Match window title filter or check active windows
                if self.title_filter and self.title_filter not in name.lower() and "simulation" not in name.lower():
                    continue

                # Search through descendants for target keywords
                for keyword in self.target_keywords:
                    # Look for controls matching keyword in Name or AutomationId
                    match = self._find_keyword_control(win, keyword)
                    if match:
                        rect = match.BoundingRectangle
                        if rect.width() > 10 and rect.height() > 5:
                            return DetectionResult(
                                x=rect.left,
                                y=rect.top,
                                width=rect.width(),
                                height=rect.height(),
                                confidence=0.99,
                                source="UIAutomation",
                                label=keyword,
                            )
        except Exception:
            return None
        return None

    def _find_keyword_control(self, parent_control, keyword: str):
        """Recursively checks controls for keyword matches."""
        try:
            ctrl_name = parent_control.Name or ""
            if keyword.lower() in ctrl_name.lower():
                return parent_control

            # Depth limit to 3 to keep inspection under 50ms
            for child in parent_control.GetChildren()[:25]:
                name = child.Name or ""
                if keyword.lower() in name.lower():
                    return child
                for grandchild in child.GetChildren()[:15]:
                    gname = grandchild.Name or ""
                    if keyword.lower() in gname.lower():
                        return grandchild
        except Exception:
            pass
        return None


# =============================================================================
# 4. Computer Vision / Template Matching Fallback Engine
# =============================================================================
class VisionDetector:
    """Uses OpenCV multi-scale template matching to detect '(Recommended)' on screen."""

    def __init__(self, templates_dir: str = "assets/templates", target_keywords: Tuple[str, ...] = ()):
        self.templates_dir = templates_dir
        self.templates = []
        self._ensure_and_load_templates()

    def _ensure_and_load_templates(self):
        """Ensures template directory exists with default templates and loads them."""
        os.makedirs(self.templates_dir, exist_ok=True)

        # Check if templates exist, if not, generate default high-contrast templates
        dark_tpl_path = os.path.join(self.templates_dir, "recommended_dark.png")
        light_tpl_path = os.path.join(self.templates_dir, "recommended_light.png")

        if not os.path.exists(dark_tpl_path) and Image and ImageDraw:
            self._generate_synthetic_template(dark_tpl_path, bg_color=(30, 30, 46), fg_color=(240, 240, 255))
        if not os.path.exists(light_tpl_path) and Image and ImageDraw:
            self._generate_synthetic_template(light_tpl_path, bg_color=(245, 245, 250), fg_color=(20, 20, 30))

        # Load all PNG templates from disk
        if cv2 is not None:
            for file in os.listdir(self.templates_dir):
                if file.lower().endswith(".png"):
                    path = os.path.join(self.templates_dir, file)
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        self.templates.append((file, img))

    def _generate_synthetic_template(self, path: str, bg_color: Tuple[int, int, int], fg_color: Tuple[int, int, int]):
        """Generates a clean synthetic template image."""
        img = Image.new("RGB", (160, 36), color=bg_color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("segoeui.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 8), "(Recommended)", fill=fg_color, font=font)
        img.save(path)

    def scan(self) -> Optional[DetectionResult]:
        if cv2 is None or ImageGrab is None or not self.templates:
            return None

        try:
            # Capture full desktop screen
            screenshot = ImageGrab.grab()
            screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

            best_match = None
            highest_score = 0.72  # Matching threshold

            # Multi-scale template matching (0.85x, 1.0x, 1.15x)
            scales = [0.85, 1.0, 1.15]
            for tpl_name, tpl_gray in self.templates:
                th, tw = tpl_gray.shape[:2]
                for scale in scales:
                    new_w = int(tw * scale)
                    new_h = int(th * scale)
                    if new_w >= screen_gray.shape[1] or new_h >= screen_gray.shape[0]:
                        continue

                    resized_tpl = cv2.resize(tpl_gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    res = cv2.matchTemplate(screen_gray, resized_tpl, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    if max_val > highest_score:
                        highest_score = max_val
                        best_match = DetectionResult(
                            x=max_loc[0],
                            y=max_loc[1],
                            width=new_w,
                            height=new_h,
                            confidence=float(max_val),
                            source=f"Vision ({tpl_name})",
                            label="(Recommended)",
                        )

            return best_match
        except Exception:
            return None


# =============================================================================
# 5. Dual-Mode Detection Orchestrator
# =============================================================================
class DualModeDetector:
    """Coordinates UIAutomation and Vision Detection based on configuration."""

    def __init__(self, config: Config):
        self.config = config
        self.uia_detector = UIAutomationDetector(config.window_title_filter, config.target_keywords)
        self.vision_detector = VisionDetector(target_keywords=config.target_keywords)

    def detect(self) -> Optional[DetectionResult]:
        mode = self.config.detection_mode.lower()

        # Mode: UIAutomation only or auto primary
        if mode in ("auto", "uia"):
            res = self.uia_detector.scan()
            if res:
                return res

        # Mode: Vision only or auto fallback
        if mode in ("auto", "vision"):
            res = self.vision_detector.scan()
            if res:
                return res

        return None


# =============================================================================
# 6. Smooth Human-Like Mouse Controller
# =============================================================================
class MouseController:
    """Dispatches human-like cubic easing cursor motion and natural clicks."""

    def __init__(self, glide_duration: float = 0.8, failsafe_enabled: bool = True):
        self.glide_duration = glide_duration
        if pyautogui:
            pyautogui.FAILSAFE = failsafe_enabled

    def glide_and_click(self, target_x: int, target_y: int, check_interrupted_fn=None) -> bool:
        if not pyautogui:
            return False

        try:
            # Add minor random offset (+-3 px) for human-like natural landing
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            dest_x = target_x + offset_x
            dest_y = target_y + offset_y

            # Smooth glide using cubic ease-in-out
            pyautogui.moveTo(
                dest_x,
                dest_y,
                duration=self.glide_duration,
                tween=pyautogui.easeInOutQuad,
            )

            # Check if user moved mouse during glide
            if check_interrupted_fn and check_interrupted_fn():
                return False

            # Natural click with small dwell duration
            time.sleep(0.08)
            pyautogui.click()
            time.sleep(0.12)
            return True
        except Exception as e:
            print(f"\033[91m[ERROR] Mouse controller exception: {e}\033[0m")
            return False


# =============================================================================
# 7. Real-Time ANSI Terminal Dashboard
# =============================================================================
class TerminalDashboard:
    """Renders ANSI colored banner, status updates, and interactive countdown bar."""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[2K\r"

    @classmethod
    def print_banner(cls, config: Config):
        banner = f"""
{cls.CYAN}{cls.BOLD}╔══════════════════════════════════════════════════════════════════════════════╗
║                   AutoSelect-Commander for Antigravity                       ║
║        Visual Mouse Automation & Autonomous (Recommended) Selector           ║
╚══════════════════════════════════════════════════════════════════════════════╝{cls.RESET}
 {cls.GREEN}● Status:{cls.RESET} Active Daemon Running       {cls.GREEN}● Failsafe:{cls.RESET} Instant Mouse Movement (> {config.mouse_interruption_threshold_px}px)
 {cls.GREEN}● Countdown:{cls.RESET} {config.countdown_seconds}s Timeout                {cls.GREEN}● Easing:{cls.RESET} Cubic EaseInOutQuad ({config.smooth_glide_duration_s}s)
 {cls.GREEN}● Detection:{cls.RESET} Dual (UIA + OpenCV)      {cls.GREEN}● Target:{cls.RESET} {config.target_keywords[0]}
 {cls.YELLOW}● Emergency Abort:{cls.RESET} Shake/Move Mouse, Press 'Q' or ESC, or Move to Screen Corner
────────────────────────────────────────────────────────────────────────────────
"""
        print(banner)

    @classmethod
    def render_scanning(cls, tick: int):
        dots = "." * ((tick % 3) + 1)
        dots_padded = dots.ljust(4)
        sys.stdout.write(f"{cls.CLEAR_LINE}{cls.CYAN}[SCANNING]{cls.RESET} Monitoring screen for Antigravity decision modals{dots_padded}")
        sys.stdout.flush()

    @classmethod
    def render_detected(cls, result: DetectionResult):
        cx, cy = result.center
        print(f"\n{cls.GREEN}{cls.BOLD}[MODAL DETECTED]{cls.RESET} Source: {cls.MAGENTA}{result.source}{cls.RESET} | Target: '{result.label}' at ({cx}, {cy})")

    @classmethod
    def render_countdown(cls, remaining: float, total: float, result: DetectionResult):
        cx, cy = result.center
        bar_length = 30
        pct = max(0.0, min(1.0, remaining / total))
        filled = int(bar_length * pct)
        bar = "█" * filled + "░" * (bar_length - filled)
        color = cls.GREEN if remaining > 10 else (cls.YELLOW if remaining > 5 else cls.RED)
        sys.stdout.write(
            f"{cls.CLEAR_LINE}{color}[COUNTDOWN]{cls.RESET} [{bar}] {cls.BOLD}{remaining:4.1f}s{cls.RESET} remaining | Target: ({cx}, {cy}) | {cls.YELLOW}Move mouse to cancel{cls.RESET}"
        )
        sys.stdout.flush()

    @classmethod
    def render_interrupted(cls, distance: float, threshold: float):
        print(f"\n{cls.RED}{cls.BOLD}[FAIL-SAFE TRIGGERED]{cls.RESET} Human mouse movement detected ({distance:.1f}px > {threshold}px)!")
        print(f"{cls.YELLOW}➜ Yielded full control back to developer. Entering cooldown suppression.{cls.RESET}\n")

    @classmethod
    def render_clicking(cls, x: int, y: int):
        print(f"\n{cls.CYAN}{cls.BOLD}[ACTION]{cls.RESET} Gliding cursor smoothly to ({x}, {y}) and clicking (Recommended)...")

    @classmethod
    def render_completed(cls):
        print(f"{cls.GREEN}{cls.BOLD}[SUCCESS]{cls.RESET} Option successfully auto-selected! Agent unblocked and resuming.\n")

    @classmethod
    def render_cooldown(cls, seconds_left: int):
        sys.stdout.write(f"{cls.CLEAR_LINE}{cls.YELLOW}[COOLDOWN]{cls.RESET} Resuming scan in {seconds_left}s...")
        sys.stdout.flush()


# =============================================================================
# 8. Main Engine Orchestrator
# =============================================================================
class AutoCommanderEngine:
    """Autonomous State Machine for modal detection, countdown, and fail-safe dispatch."""

    def __init__(self, config: Config):
        self.config = config
        self.detector = DualModeDetector(config)
        self.mouse_ctrl = MouseController(
            glide_duration=config.smooth_glide_duration_s,
            failsafe_enabled=config.failsafe_enabled,
        )
        self.is_running = True
        self.current_state = "SCANNING"  # SCANNING, COUNTDOWN, COOLDOWN, SHUTDOWN
        self.initial_mouse_pos = (0, 0)
        self.user_interrupted = False

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

        while self.is_running:
            try:
                # -------------------------------------------------------------
                # State 1: SCANNING
                # -------------------------------------------------------------
                if self.current_state == "SCANNING":
                    tick += 1
                    TerminalDashboard.render_scanning(tick)

                    result = self.detector.detect()
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
                self.current_state = "COOLDOWN"
            except Exception as e:
                time.sleep(1.0)

    def _execute_countdown(self, result: DetectionResult):
        """Runs the 30-second visual countdown with 50Hz mouse fail-safe polling."""
        self.current_state = "COUNTDOWN"
        self.user_interrupted = False
        self.initial_mouse_pos = self._get_mouse_position()

        total_seconds = float(self.config.countdown_seconds)
        start_time = time.time()
        poll_interval = 0.05  # 50 Hz fail-safe polling

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

            # Check if user moved the physical mouse
            if self._check_mouse_interrupted():
                curr_x, curr_y = self._get_mouse_position()
                dist = math.hypot(curr_x - self.initial_mouse_pos[0], curr_y - self.initial_mouse_pos[1])
                TerminalDashboard.render_interrupted(dist, self.config.mouse_interruption_threshold_px)
                self.current_state = "COOLDOWN"
                return

            # Check if user requested keyboard abort
            if self.user_interrupted:
                print("\n\033[93m[USER ABORT] Countdown cancelled via keyboard.\033[0m")
                self.current_state = "COOLDOWN"
                return

            # Countdown reached 0 -> Execute Auto-Selection!
            if remaining <= 0:
                break

            TerminalDashboard.render_countdown(remaining, total_seconds, result)
            time.sleep(poll_interval)

        # ---------------------------------------------------------------------
        # Final Verification & Smooth Mouse Glide
        # ---------------------------------------------------------------------
        if not self.user_interrupted and self.is_running:
            target_cx, target_cy = result.center
            TerminalDashboard.render_clicking(target_cx, target_cy)

            # Perform human-like mouse glide & click
            success = self.mouse_ctrl.glide_and_click(
                target_cx,
                target_cy,
                check_interrupted_fn=self._check_mouse_interrupted,
            )

            if success:
                TerminalDashboard.render_completed()
                # Beep on success
                if self.config.sound_notification:
                    try:
                        import winsound
                        winsound.MessageBeep(winsound.MB_OK)
                    except Exception:
                        pass
                self.current_state = "COOLDOWN"
            else:
                print("\033[93m[NOTICE] Click cancelled due to motion or boundary condition.\033[0m")
                self.current_state = "COOLDOWN"


# =============================================================================
# 9. Built-In Interactive Simulator (--test / --simulate)
# =============================================================================
def launch_simulator():
    """Opens a lightweight mock Antigravity modal for instant 100% end-to-end verification."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("[ERROR] Tkinter is required for simulator mode.")
        return

    print("\n\033[96m[SIMULATION MODE] Launching mock Antigravity Decision Modal...\033[0m")
    root = tk.Tk()
    root.title("Antigravity - Interactive Simulation Window")
    root.geometry("640x360+300+200")
    root.configure(bg="#1E1E2E")
    root.attributes("-topmost", True)

    header = tk.Label(
        root,
        text="Interactive Pair-Programming Decision Required",
        font=("Segoe UI", 13, "bold"),
        fg="#89B4FA",
        bg="#1E1E2E",
        pady=10,
    )
    header.pack()

    desc = tk.Label(
        root,
        text="Task complete. Would you like to push the committed changes to GitHub online repository?",
        font=("Segoe UI", 10),
        fg="#CDD6F4",
        bg="#1E1E2E",
        wraplength=580,
        justify="left",
    )
    desc.pack(pady=5)

    def on_opt1_clicked():
        status_lbl.config(text="Option 1 CLICKED! AutoSelect-Commander succeeded!", fg="#A6E3A1")
        root.after(1500, root.destroy)

    def on_opt2_clicked():
        status_lbl.config(text="Option 2 Clicked manually by developer.", fg="#F9E2AF")
        root.after(1500, root.destroy)

    # Option 1 (Recommended) Button
    btn1 = tk.Button(
        root,
        text="Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना",
        font=("Segoe UI", 11, "bold"),
        bg="#313244",
        fg="#A6E3A1",
        activebackground="#45475A",
        activeforeground="#A6E3A1",
        relief="raised",
        bd=2,
        padx=15,
        pady=8,
        command=on_opt1_clicked,
    )
    btn1.pack(pady=12, fill="x", padx=40)

    # Option 2 Button
    btn2 = tk.Button(
        root,
        text="Option 2: नहीं, अभी रहने दो क्योंकि टेस्टिंग पेंडिंग है",
        font=("Segoe UI", 10),
        bg="#313244",
        fg="#BAC2DE",
        activebackground="#45475A",
        activeforeground="#BAC2DE",
        relief="raised",
        bd=1,
        padx=15,
        pady=6,
        command=on_opt2_clicked,
    )
    btn2.pack(pady=5, fill="x", padx=40)

    status_lbl = tk.Label(
        root,
        text="Waiting for AutoSelect-Commander or manual click...",
        font=("Segoe UI", 9, "italic"),
        fg="#9399B2",
        bg="#1E1E2E",
        pady=10,
    )
    status_lbl.pack()

    # Launch daemon in companion thread
    cfg = Config.load()
    cfg.countdown_seconds = 5  # Quick 5s countdown for fast simulation testing
    cfg.window_title_filter = "Simulation"
    cfg.cooldown_after_dismissal_s = 2

    engine = AutoCommanderEngine(cfg)
    daemon_thread = threading.Thread(target=engine.run, daemon=True)
    daemon_thread.start()

    root.mainloop()
    engine.stop()


# =============================================================================
# 10. CLI Entry Point
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="AutoSelect-Commander: Visual Mouse Automation for Antigravity"
    )
    parser.add_argument(
        "--test",
        "--simulate",
        action="store_true",
        help="Launch interactive simulation window for instant end-to-end verification",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to custom config.json file (default: config.json)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "uia", "vision"],
        default=None,
        help="Override detection mode: 'auto', 'uia', or 'vision'",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Override countdown duration in seconds",
    )
    args = parser.parse_args()

    if args.test:
        launch_simulator()
        return

    # Load configuration
    cfg = Config.load(args.config)
    if args.mode:
        cfg.detection_mode = args.mode
    if args.timeout:
        cfg.countdown_seconds = args.timeout

    # Initialize and run engine
    engine = AutoCommanderEngine(cfg)
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n\033[93m[EXIT] Stopped by user.\033[0m")
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
