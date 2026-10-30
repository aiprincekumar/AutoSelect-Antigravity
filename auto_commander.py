#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
AutoSelect-Commander: Visual Mouse Automation & Auto-Selector for Antigravity
===============================================================================
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Repository: C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
Version: 1.1.0
Description:
    Autonomous visual daemon that monitors the desktop surface for Antigravity
    interactive decision modals ('ask_question' cards), displays an on-screen
    floating HUD overlay and terminal countdown with instant mouse fail-safe,
    and smoothly glides the mouse cursor using cubic easing to auto-select
    '(Recommended)' options.
===============================================================================
"""

import argparse
import asyncio
import ctypes
import difflib
import io
import json
import math
import os
import random
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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

# Windows 10/11 WinRT Native OCR Support via winsdk
try:
    import winsdk.windows.media.ocr as win_ocr
    import winsdk.windows.graphics.imaging as win_imaging
    import winsdk.windows.storage.streams as win_streams
    WINSDK_OCR_AVAILABLE = True
except ImportError:
    win_ocr = win_imaging = win_streams = None
    WINSDK_OCR_AVAILABLE = False


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
    window_title_filter: str = ""  # Empty string = scan foreground and all visible windows
    floating_hud_enabled: bool = True
    floating_hud_alpha: float = 0.92
    ocr_enabled: bool = True
    target_keywords: Tuple[str, ...] = (
        "(Recommended)",
        "Recommended",
        "(अनुशंसित)",
        "अनुशंसित",
        "(Recommended) GitHub पर कमिट चेंजेस पुश करना",
        "(Recommended) GitHub",
        "Proceed",
    )
    detection_mode: str = "auto"  # 'auto', 'ocr', 'uia', 'vision'

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
                        window_title_filter=str(data.get("window_title_filter", "")),
                        floating_hud_enabled=bool(data.get("floating_hud_enabled", True)),
                        floating_hud_alpha=float(data.get("floating_hud_alpha", 0.92)),
                        ocr_enabled=bool(data.get("ocr_enabled", True)),
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
    source: str  # 'WindowsOcr', 'UIAutomation', or 'Vision'
    label: str

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


# =============================================================================
# 3. Windows Native WinRT OCR Detection Engine (Fast, Font-Invariant)
# =============================================================================
class WindowsOcrDetector:
    """Uses Windows 10/11 native WinRT OCR (Windows.Media.Ocr) to detect target keywords on screen."""

    def __init__(self, target_keywords: Tuple[str, ...], ocr_enabled: bool = True):
        self.target_keywords = target_keywords
        self.ocr_enabled = ocr_enabled

    def is_available(self) -> bool:
        """Returns True if WinRT OCR libraries are installed and enabled."""
        return bool(self.ocr_enabled and WINSDK_OCR_AVAILABLE and win_ocr is not None)

    async def _recognize_async(self, image_bytes: bytes):
        """Asynchronously feeds PNG bytes to Windows.Media.Ocr within current apartment."""
        if not win_ocr:
            return None
        try:
            engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                import winsdk.windows.globalization as glob
                lang = glob.Language("en-US")
                if win_ocr.OcrEngine.is_language_supported(lang):
                    engine = win_ocr.OcrEngine.try_create_from_language(lang)
            if not engine:
                return None

            stream = win_streams.InMemoryRandomAccessStream()
            dw = win_streams.DataWriter(stream)
            dw.write_bytes(image_bytes)
            await dw.store_async()
            stream.seek(0)
            decoder = await win_imaging.BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            return await engine.recognize_async(bitmap)
        except Exception:
            return None

    def scan_image(self, img: Image.Image, offset_x: int = 0, offset_y: int = 0) -> Optional[DetectionResult]:
        """Runs OCR on a PIL Image and matches against target keywords with fuzzy tolerance."""
        if not self.is_available() or img is None:
            return None

        try:
            import concurrent.futures
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            image_bytes = buf.getvalue()

            # Execute WinRT async OCR inside a clean worker thread (MTA apartment) with timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self._recognize_async(image_bytes))
                result = future.result(timeout=3.5)

            if not result or not result.lines:
                return None

            for line in result.lines:
                line_lower = line.text.lower()

                # Check line level matching first
                for kw in self.target_keywords:
                    kw_clean = kw.lower().strip("()[] ")
                    if not kw_clean:
                        continue

                    # Direct substring match in line or fuzzy word match
                    has_match = (kw_clean in line_lower)
                    if not has_match:
                        for word in line.words:
                            w_clean = word.text.lower().strip("()[] ")
                            if kw_clean in w_clean or difflib.SequenceMatcher(None, w_clean, kw_clean).ratio() >= 0.75:
                                has_match = True
                                break

                    if has_match:
                        # Find the best matching word or words in this line
                        matched_words = []
                        for word in line.words:
                            w_clean = word.text.lower().strip("()[] ")
                            if kw_clean in w_clean or difflib.SequenceMatcher(None, w_clean, kw_clean).ratio() >= 0.70:
                                matched_words.append(word)

                        if matched_words:
                            min_x = min(w.bounding_rect.x for w in matched_words)
                            min_y = min(w.bounding_rect.y for w in matched_words)
                            max_x = max(w.bounding_rect.x + w.bounding_rect.width for w in matched_words)
                            max_y = max(w.bounding_rect.y + w.bounding_rect.height for w in matched_words)

                            return DetectionResult(
                                x=int(min_x + offset_x),
                                y=int(min_y + offset_y),
                                width=int(max_x - min_x),
                                height=int(max_y - min_y),
                                confidence=0.98,
                                source="WindowsOcr",
                                label=kw,
                            )
        except Exception:
            return None
        return None

    def scan(self) -> Optional[DetectionResult]:
        """Scans foreground window first, then full screen if needed."""
        if not self.is_available() or ImageGrab is None:
            return None

        # Strategy 1: Fast scan on active foreground window
        try:
            if gw is not None:
                active_win = gw.getActiveWindow()
                if active_win and active_win.width > 100 and active_win.height > 80:
                    bbox = (
                        max(0, active_win.left),
                        max(0, active_win.top),
                        max(0, active_win.right),
                        max(0, active_win.bottom),
                    )
                    win_img = ImageGrab.grab(bbox=bbox)
                    res = self.scan_image(win_img, offset_x=bbox[0], offset_y=bbox[1])
                    if res:
                        return res
        except Exception:
            pass

        # Strategy 2: Full screen screenshot scan
        try:
            screen_img = ImageGrab.grab()
            return self.scan_image(screen_img, offset_x=0, offset_y=0)
        except Exception:
            return None


# =============================================================================
# 4. Windows UIAutomation Detection Engine (Fast, DPI-Invariant)
# =============================================================================
class UIAutomationDetector:
    """Scans the Windows UI Automation tree to locate Antigravity decision buttons."""

    def __init__(self, title_filter: str, target_keywords: Tuple[str, ...]):
        self.title_filter = title_filter.lower().strip() if title_filter else ""
        self.target_keywords = target_keywords

    def scan(self) -> Optional[DetectionResult]:
        if auto is None:
            return None

        try:
            # 1. Search the foreground window first for instant response
            fg_win = auto.GetForegroundControl()
            if fg_win:
                match = self._find_in_tree(fg_win)
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
                            label=match.Name or "Recommended",
                        )

            # 2. Search top-level windows
            root = auto.GetRootControl()
            if not root:
                return None

            top_windows = root.GetChildren()
            for win in top_windows:
                name = win.Name or ""
                # If title filter is specified, respect it; otherwise scan all top-level windows
                if self.title_filter:
                    if self.title_filter not in name.lower() and "simulation" not in name.lower() and "antigravity" not in name.lower():
                        continue

                match = self._find_in_tree(win)
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
                            label=match.Name or "Recommended",
                        )
        except Exception:
            return None
        return None

    def _find_in_tree(self, parent_control):
        """Recursively checks controls for keyword matches with depth limit."""
        try:
            ctrl_name = parent_control.Name or ""
            for kw in self.target_keywords:
                if kw.lower() in ctrl_name.lower():
                    return parent_control

            # Depth limit to keep inspection under 40ms
            for child in parent_control.GetChildren()[:30]:
                name = child.Name or ""
                for kw in self.target_keywords:
                    if kw.lower() in name.lower():
                        return child
                for grandchild in child.GetChildren()[:20]:
                    gname = grandchild.Name or ""
                    for kw in self.target_keywords:
                        if kw.lower() in gname.lower():
                            return grandchild
        except Exception:
            pass
        return None


# =============================================================================
# 5. Computer Vision / Multi-Scale Multi-Theme Template Matching Engine
# =============================================================================
class VisionDetector:
    """Uses OpenCV multi-scale multi-template matching to detect '(Recommended)' on screen."""

    def __init__(self, templates_dir: str = "assets/templates", target_keywords: Tuple[str, ...] = ()):
        self.templates_dir = templates_dir
        self.templates: List[Tuple[str, Any]] = []
        self._ensure_and_load_templates()

    def _ensure_and_load_templates(self):
        """Ensures template directory exists with multiple theme templates and loads them."""
        os.makedirs(self.templates_dir, exist_ok=True)

        # Generate a suite of theme templates if missing
        tpl_variants = [
            ("recommended_dark_16.png", (30, 30, 46), (166, 227, 161), 16),
            ("recommended_dark_14.png", (24, 24, 37), (205, 214, 244), 14),
            ("recommended_vscode_14.png", (37, 37, 38), (255, 255, 255), 14),
            ("recommended_light_16.png", (245, 245, 250), (20, 20, 30), 16),
        ]

        if Image and ImageDraw:
            for fname, bg, fg, sz in tpl_variants:
                path = os.path.join(self.templates_dir, fname)
                if not os.path.exists(path):
                    self._generate_template(path, bg, fg, sz)

        # Load all PNG templates from disk
        if cv2 is not None:
            for file in os.listdir(self.templates_dir):
                if file.lower().endswith(".png"):
                    path = os.path.join(self.templates_dir, file)
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        self.templates.append((file, img))

    def _generate_template(self, path: str, bg_color: Tuple[int, int, int], fg_color: Tuple[int, int, int], font_size: int):
        """Generates a clean synthetic template image."""
        w = int(font_size * 9.5)
        h = int(font_size * 2.2)
        img = Image.new("RGB", (w, h), color=bg_color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        draw.text((6, 4), "(Recommended)", fill=fg_color, font=font)
        img.save(path)

    def scan(self) -> Optional[DetectionResult]:
        if cv2 is None or ImageGrab is None or not self.templates:
            return None

        try:
            screenshot = ImageGrab.grab()
            screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

            best_match = None
            highest_score = 0.72  # Matching threshold

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
# 6. Multi-Engine Detection Orchestrator
# =============================================================================
class MultiEngineDetector:
    """Coordinates Windows Native OCR, UIAutomation, and Vision Detection."""

    def __init__(self, config: Config):
        self.config = config
        self.ocr_detector = WindowsOcrDetector(config.target_keywords, ocr_enabled=config.ocr_enabled)
        self.uia_detector = UIAutomationDetector(config.window_title_filter, config.target_keywords)
        self.vision_detector = VisionDetector(target_keywords=config.target_keywords)

    def detect(self) -> Optional[DetectionResult]:
        mode = self.config.detection_mode.lower()

        # Strategy 1: Windows Native OCR (Fastest & most robust)
        if mode in ("auto", "ocr"):
            if self.ocr_detector.is_available():
                res = self.ocr_detector.scan()
                if res:
                    return res

        # Strategy 2: UIAutomation Tree Search
        if mode in ("auto", "uia"):
            res = self.uia_detector.scan()
            if res:
                return res

        # Strategy 3: Computer Vision Multi-Scale Template Fallback
        if mode in ("auto", "vision"):
            res = self.vision_detector.scan()
            if res:
                return res

        return None


# Backward-compatibility alias
DualModeDetector = MultiEngineDetector


# =============================================================================
# 7. Floating On-Screen HUD Overlay (Tkinter Top-Most Window)
# =============================================================================
class FloatingHUD:
    """Always-on-top semi-transparent floating on-screen countdown HUD."""

    def __init__(self, alpha: float = 0.92):
        self.alpha = alpha
        self.root = None
        self.master = None
        self.lbl_title = None
        self.lbl_status = None
        self.total_seconds = 30.0
        self.is_visible = False

    def show(self, total_seconds: float, label: str, master=None):
        """Displays the floating HUD at the top center of the primary display."""
        try:
            import tkinter as tk
            self.total_seconds = total_seconds
            self.master = master

            if master is not None:
                self.root = tk.Toplevel(master)
            else:
                self.root = tk.Tk()

            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            try:
                self.root.attributes("-alpha", self.alpha)
            except Exception:
                pass

            # Center at top of screen
            sw = self.root.winfo_screenwidth()
            w, h = 580, 56
            x = (sw - w) // 2
            y = 20
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.configure(bg="#181825", highlightbackground="#89B4FA", highlightthickness=2)

            clean_label = label.replace("\n", " ")
            if len(clean_label) > 38:
                clean_label = clean_label[:35] + "..."

            self.lbl_title = tk.Label(
                self.root,
                text=f"⏱️ AutoSelect-Commander | Auto-Selecting: {clean_label}",
                fg="#89B4FA",
                bg="#181825",
                font=("Segoe UI", 10, "bold"),
            )
            self.lbl_title.pack(pady=(4, 2))

            self.lbl_status = tk.Label(
                self.root,
                text="[████████████████████] Initializing...",
                fg="#A6E3A1",
                bg="#181825",
                font=("Consolas", 10, "bold"),
            )
            self.lbl_status.pack()

            self.root.update_idletasks()
            self.root.update()
            self.is_visible = True
        except Exception:
            self.is_visible = False
            self.root = None

    def update_countdown(self, remaining: float):
        """Updates the countdown bar and seconds remaining."""
        if not self.is_visible or not self.root:
            return
        try:
            pct = max(0.0, min(1.0, remaining / self.total_seconds))
            bar_len = 22
            filled = int(bar_len * pct)
            bar = "█" * filled + "░" * (bar_len - filled)

            if remaining > 10.0:
                color = "#A6E3A1"  # Mint Green
            elif remaining > 5.0:
                color = "#F9E2AF"  # Warm Yellow
            else:
                color = "#F38BA8"  # Soft Red

            self.lbl_status.config(
                text=f"[{bar}] {remaining:4.1f}s remaining | Move mouse to cancel",
                fg=color,
            )
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def flash_cancelled(self):
        """Flashes red notification indicating human took over."""
        if not self.is_visible or not self.root:
            return
        try:
            self.root.configure(highlightbackground="#F38BA8")
            self.lbl_title.config(text="⚠️ INTERRUPTED — Developer Control Restored", fg="#F38BA8")
            self.lbl_status.config(text="Auto-selection aborted. Returning to monitoring.", fg="#CDD6F4")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1.0)
        except Exception:
            pass
        finally:
            self.close()

    def flash_success(self):
        """Flashes green notification indicating success."""
        if not self.is_visible or not self.root:
            return
        try:
            self.root.configure(highlightbackground="#A6E3A1")
            self.lbl_title.config(text="✅ AUTO-SELECTED (RECOMMENDED) OPTION", fg="#A6E3A1")
            self.lbl_status.config(text="Option selected! Agent unblocked and resuming autonomously.", fg="#A6E3A1")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1.0)
        except Exception:
            pass
        finally:
            self.close()

    def close(self):
        """Closes and destroys the HUD window safely."""
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
        self.is_visible = False


# =============================================================================
# 8. Smooth Human-Like Mouse Controller
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
# 9. Real-Time ANSI Terminal Dashboard
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
        ocr_status = "WinRT OCR Active" if WINSDK_OCR_AVAILABLE else "OCR Disabled/Not Installed"
        banner = f"""
{cls.CYAN}{cls.BOLD}╔══════════════════════════════════════════════════════════════════════════════╗
║                   AutoSelect-Commander for Antigravity                       ║
║        Visual Mouse Automation & Autonomous (Recommended) Selector           ║
╚══════════════════════════════════════════════════════════════════════════════╝{cls.RESET}
 {cls.GREEN}● Status:{cls.RESET} Active Daemon Running       {cls.GREEN}● Failsafe:{cls.RESET} Instant Mouse Movement (> {config.mouse_interruption_threshold_px}px)
 {cls.GREEN}● Countdown:{cls.RESET} {config.countdown_seconds}s Timeout                {cls.GREEN}● Floating HUD:{cls.RESET} {'Enabled (Top-Most)' if config.floating_hud_enabled else 'Disabled'}
 {cls.GREEN}● Engines:{cls.RESET} Multi (OCR + UIA + Vision)  {cls.GREEN}● WinRT OCR:{cls.RESET} {ocr_status}
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
        print(f"\n{cls.GREEN}{cls.BOLD}[MODAL DETECTED]{cls.RESET} Engine: {cls.MAGENTA}{result.source}{cls.RESET} | Target: '{result.label}' at ({cx}, {cy})")

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
# 10. Main Engine Orchestrator
# =============================================================================
class AutoCommanderEngine:
    """Autonomous State Machine for modal detection, countdown, floating HUD, and fail-safe dispatch."""

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
                if self.config.floating_hud_enabled:
                    self.hud.flash_success()
                if self.config.sound_notification:
                    try:
                        import winsound
                        winsound.MessageBeep(winsound.MB_OK)
                    except Exception:
                        pass
                self.current_state = "COOLDOWN"
            else:
                print("\033[93m[NOTICE] Click cancelled due to motion or boundary condition.\033[0m")
                if self.config.floating_hud_enabled:
                    self.hud.flash_cancelled()
                self.current_state = "COOLDOWN"


# =============================================================================
# 11. Built-In Interactive Live Visual Simulator (--test / --simulate)
# =============================================================================
def launch_simulator():
    """Spawns mock Antigravity modal, floating HUD, and physically glides mouse to Option 1."""
    try:
        import tkinter as tk
    except ImportError:
        print("[ERROR] Tkinter is required for simulator mode.")
        return

    print("\n\033[96m[SIMULATION MODE] Launching mock Antigravity Decision Modal & Floating HUD...\033[0m")
    root = tk.Tk()
    root.title("Antigravity - Interactive Decision Modal (Live Demo)")
    root.geometry("680x400+320+220")
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
        wraplength=600,
        justify="left",
    )
    desc.pack(pady=4)

    def on_opt1_clicked():
        btn1.config(bg="#A6E3A1", fg="#11111B")
        status_lbl.config(
            text="✅ Option 1 CLICKED! AutoSelect-Commander Succeeded with 100% Precision!",
            fg="#A6E3A1",
            font=("Segoe UI", 11, "bold"),
        )
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        root.after(1600, root.destroy)

    def on_opt2_clicked():
        status_lbl.config(text="Option 2 clicked manually by developer.", fg="#F9E2AF")
        root.after(1600, root.destroy)

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
    btn2.pack(pady=4, fill="x", padx=40)

    status_lbl = tk.Label(
        root,
        text="AutoSelect-Commander active. Countdown in progress...",
        font=("Segoe UI", 9, "italic"),
        fg="#9399B2",
        bg="#1E1E2E",
        pady=10,
    )
    status_lbl.pack()

    # Create Floating HUD attached to root
    hud = FloatingHUD(alpha=0.92)
    countdown_duration = 5.0
    hud.show(countdown_duration, "Option 1: (Recommended) GitHub", master=root)

    # Mouse motion tracker
    start_time = time.time()
    initial_mouse = pyautogui.position() if pyautogui else (0, 0)
    cancelled = [False]
    mouse_ctrl = MouseController(glide_duration=0.8, failsafe_enabled=True)

    def sim_tick():
        if cancelled[0]:
            return

        elapsed = time.time() - start_time
        remaining = max(0.0, countdown_duration - elapsed)

        # Check for user mouse movement fail-safe
        if pyautogui:
            curr_pos = pyautogui.position()
            dist = math.hypot(curr_pos[0] - initial_mouse[0], curr_pos[1] - initial_mouse[1])
            if dist > 15:
                cancelled[0] = True
                hud.flash_cancelled()
                status_lbl.config(
                    text=f"⚠️ Auto-selection CANCELLED! Human mouse movement detected ({dist:.1f}px).",
                    fg="#F38BA8",
                    font=("Segoe UI", 10, "bold"),
                )
                return

        hud.update_countdown(remaining)

        if remaining <= 0:
            # Reached zero -> Glide cursor and click Option 1!
            hud.lbl_status.config(text="[ACTION] Auto-selecting Option 1...", fg="#89B4FA")
            hud.root.update()

            root.update_idletasks()
            btn1.update_idletasks()

            # Target exact center of Button 1
            bx = btn1.winfo_rootx() + btn1.winfo_width() // 2
            by = btn1.winfo_rooty() + btn1.winfo_height() // 2

            def check_cancel():
                return cancelled[0]

            success = mouse_ctrl.glide_and_click(bx, by, check_interrupted_fn=check_cancel)
            if success:
                hud.flash_success()
                on_opt1_clicked()
            else:
                hud.flash_cancelled()
            return

        root.after(50, sim_tick)

    # Start simulation tick after 200ms
    root.after(200, sim_tick)
    root.mainloop()


# =============================================================================
# 12. Screen & Window Diagnostics Probe (--diagnostics)
# =============================================================================
def run_diagnostics(config: Config):
    """Deep screen, window, and text diagnostic probe."""
    print("=" * 80)
    print("           AutoSelect-Commander Screen & Window Diagnostics")
    print("=" * 80)

    # 1. Environment & Screen Resolution
    print("\n[1] DISPLAY ENVIRONMENT")
    if pyautogui:
        sw, sh = pyautogui.size()
        pos = pyautogui.position()
        print(f"  • Primary Resolution : {sw}x{sh}")
        print(f"  • Current Mouse Pos  : {pos}")
    else:
        print("  • PyAutoGUI not available.")

    # 2. Windows Native OCR Status
    print("\n[2] WINDOWS WINRT OCR STATUS")
    ocr_det = WindowsOcrDetector(config.target_keywords, ocr_enabled=config.ocr_enabled)
    print(f"  • WinSDK Available   : {WINSDK_OCR_AVAILABLE}")
    print(f"  • OCR Engine Ready   : {ocr_det.is_available()}")
    if ocr_det.is_available():
        try:
            eng = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            if eng:
                print(f"  • Engine Language    : {eng.recognizer_language.display_name} ({eng.recognizer_language.language_tag})")
        except Exception:
            pass

    # 3. Visible Windows Probe
    print("\n[3] VISIBLE WINDOWS PROBE")
    if gw is not None:
        try:
            active_win = gw.getActiveWindow()
            if active_win:
                print(f"  • Active Window      : \"{active_win.title}\" | Box: ({active_win.left}, {active_win.top}, {active_win.width}x{active_win.height})")
            else:
                print("  • Active Window      : None / Desktop")

            all_wins = [w for w in gw.getAllWindows() if w.title.strip()]
            print(f"  • Total Titled Wins  : {len(all_wins)}")
            for idx, w in enumerate(all_wins[:8], 1):
                print(f"    [{idx}] \"{w.title[:50]}\" ({w.width}x{w.height} at {w.left},{w.top})")
        except Exception as e:
            print(f"  • Error enumerating windows: {e}")
    else:
        print("  • pygetwindow not available.")

    # 4. OCR Live Screen Text Probe
    print("\n[4] OCR LIVE SCREEN TEXT PROBE")
    if ocr_det.is_available() and ImageGrab is not None:
        try:
            print("  • Capturing desktop surface for OCR text extraction...")
            screen_img = ImageGrab.grab()
            buf = io.BytesIO()
            screen_img.save(buf, format="PNG")
            ocr_res = asyncio.run(ocr_det._recognize_async(buf.getvalue()))
            if ocr_res and ocr_res.lines:
                print(f"  • Lines Extracted    : {len(ocr_res.lines)}")
                print("  • Sample Detected Lines (first 10):")
                for line in ocr_res.lines[:10]:
                    print(f"    - \"{line.text}\"")

                # Check if target keywords are found
                matches = []
                for line in ocr_res.lines:
                    for kw in config.target_keywords:
                        if kw.lower().strip("()[] ") in line.text.lower():
                            matches.append((kw, line.text))
                if matches:
                    print(f"  • \033[92mTARGET KEYWORD MATCHES FOUND ({len(matches)}):\033[0m")
                    for kw, txt in matches:
                        print(f"    ➜ Target: '{kw}' in \"{txt}\"")
                else:
                    print("  • No target decision keywords found on screen right now.")
            else:
                print("  • No text detected on current desktop.")
        except Exception as e:
            print(f"  • OCR Screen Grab Notice: {e}")
            print("    (Note: If running in non-interactive background agent session, screen grab is restricted by Windows OS Session boundaries.)")
    else:
        print("  • OCR probe skipped (OCR or ImageGrab unavailable).")

    # 5. UIAutomation Tree Probe
    print("\n[5] UIAUTOMATION TREE PROBE")
    if auto is not None:
        try:
            root = auto.GetRootControl()
            children = root.GetChildren() if root else []
            print(f"  • Root UIA Control   : {root.Name if root else 'None'} ({len(children)} children)")
            fg = auto.GetForegroundControl()
            print(f"  • Foreground Control : {fg.Name if fg else 'None'}")
        except Exception as e:
            print(f"  • UIA Probe error: {e}")
    else:
        print("  • uiautomation library not available.")

    print("\n" + "=" * 80)
    print("Diagnostics complete.")
    print("=" * 80)


# =============================================================================
# 13. CLI Entry Point
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="AutoSelect-Commander: Visual Mouse Automation for Antigravity"
    )
    parser.add_argument(
        "--test",
        "--simulate",
        action="store_true",
        help="Launch interactive simulation window for instant visual end-to-end verification",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Run deep screen, window, and OCR text diagnostics probe",
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
        choices=["auto", "ocr", "uia", "vision"],
        default=None,
        help="Override detection mode: 'auto', 'ocr', 'uia', or 'vision'",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Override countdown duration in seconds",
    )
    args = parser.parse_args()

    # Load configuration
    cfg = Config.load(args.config)
    if args.mode:
        cfg.detection_mode = args.mode
    if args.timeout:
        cfg.countdown_seconds = args.timeout

    if args.diagnostics:
        run_diagnostics(cfg)
        return

    if args.test:
        launch_simulator()
        return

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
