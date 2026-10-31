#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
AutoSelect-Commander: Visual Mouse Automation & Auto-Selector for Antigravity
===============================================================================
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
Repository: C:\Users\Atul Verma\Desktop\AutoSelect-Commander\
Version: 1.2.0
Description:
    Autonomous visual daemon that monitors the desktop surface for Antigravity
    interactive decision modals ('ask_question' cards), displays an on-screen
    floating HUD overlay and terminal countdown with instant mouse fail-safe,
    auto-foregrounds minimized or background Antigravity windows, and smoothly
    glides the mouse cursor using cubic easing to perform the complete 2-step flow:
    Step 1: Select '(Recommended)' option with a firm click.
    Step 2: Confirm and submit via 'Submit / पुष्टि करें' button.
===============================================================================
"""

import argparse
import asyncio
import ctypes
from ctypes import wintypes
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

# Reconfigure stdout/stderr to UTF-8 to prevent charmap UnicodeEncodeError on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
# 1. Antigravity Window & Process Tracker with Auto-Foregrounding
# =============================================================================
class AntigravityWindowManager:
    """Detects if Antigravity is open/running, and automatically restores/foregrounds it."""

    PROCESS_NAMES = ("antigravity.exe", "antigravity")
    WINDOW_TITLE_KEYWORDS = ("antigravity", "autoselect-commander", "ask_question")

    @classmethod
    def is_process_running(cls) -> bool:
        """Checks if Antigravity process is active in the Windows process table."""
        try:
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002

            class PROCESSENTRY32W(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260),
                ]

            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if h_snap != -1:
                pe = PROCESSENTRY32W()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                has_next = kernel32.Process32FirstW(h_snap, ctypes.byref(pe))
                found = False
                while has_next:
                    exe = pe.szExeFile.lower()
                    for target in cls.PROCESS_NAMES:
                        if target in exe:
                            found = True
                            break
                    if found:
                        break
                    has_next = kernel32.Process32NextW(h_snap, ctypes.byref(pe))
                kernel32.CloseHandle(h_snap)
                if found:
                    return True
        except Exception:
            pass

        # Fallback via pygetwindow
        if gw is not None:
            try:
                for w in gw.getAllWindows():
                    if w.title and any(k in w.title.lower() for k in cls.WINDOW_TITLE_KEYWORDS):
                        return True
            except Exception:
                pass
        return False

    @classmethod
    def find_antigravity_window(cls) -> Optional[int]:
        """Returns the HWND of the primary Antigravity or Demo window."""
        try:
            user32 = ctypes.windll.user32
            found_hwnds = []

            def enum_proc(hwnd, lParam):
                if user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title_lower = buf.value.lower()
                        if any(k in title_lower for k in cls.WINDOW_TITLE_KEYWORDS):
                            if "autoselect-commander launcher" not in title_lower:
                                found_hwnds.append(hwnd)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
            if found_hwnds:
                return found_hwnds[0]
        except Exception:
            pass

        if gw is not None:
            try:
                for w in gw.getAllWindows():
                    if w.title and any(k in w.title.lower() for k in cls.WINDOW_TITLE_KEYWORDS):
                        if hasattr(w, "_hWnd"):
                            return w._hWnd
            except Exception:
                pass
        return None

    @classmethod
    def is_minimized(cls, hwnd: int) -> bool:
        if not hwnd:
            return False
        try:
            return bool(ctypes.windll.user32.IsIconic(hwnd))
        except Exception:
            return False

    @classmethod
    def is_foreground(cls, hwnd: int) -> bool:
        if not hwnd:
            return False
        try:
            return ctypes.windll.user32.GetForegroundWindow() == hwnd
        except Exception:
            return False

    @classmethod
    def bring_to_foreground(cls, hwnd: int) -> bool:
        """Brings window to foreground without moving the mouse."""
        if not hwnd:
            return False
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            else:
                user32.ShowWindow(hwnd, 5)  # SW_SHOW

            cur_thread = kernel32.GetCurrentThreadId()
            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0

            if fg_thread and fg_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fg_thread, True)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.AttachThreadInput(cur_thread, fg_thread, False)
            else:
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)

            time.sleep(0.15)
            return True
        except Exception:
            return False

    @classmethod
    def check_and_foreground(cls) -> Tuple[bool, str, Optional[int]]:
        """
        Verifies if Antigravity is open/running and brings it to the foreground if minimized or in background.
        Returns: (is_ready, message, hwnd)
        """
        proc_running = cls.is_process_running()
        hwnd = cls.find_antigravity_window()

        if not proc_running and not hwnd:
            return False, "एंटी-ग्रैविटी अभी ओपन नहीं है (Antigravity is currently not open)", None

        if hwnd:
            if cls.is_minimized(hwnd):
                cls.bring_to_foreground(hwnd)
                return True, "Antigravity minimized window restored to foreground.", hwnd
            elif not cls.is_foreground(hwnd):
                cls.bring_to_foreground(hwnd)
                return True, "Antigravity background window brought to foreground.", hwnd
            else:
                return True, "Antigravity active in foreground.", hwnd

        return True, "Antigravity process is active.", None


# =============================================================================
# 2. Configuration Manager
# =============================================================================
@dataclass
class Config:
    countdown_seconds: int = 10
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
    submit_keywords: Tuple[str, ...] = (
        "Submit",
        "पुष्टि करें",
        "Confirm",
        "Proceed",
        "Submit / पुष्टि करें",
        "जारी रखें",
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
                        countdown_seconds=int(data.get("countdown_seconds", 10)),
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
                        submit_keywords=tuple(data.get("submit_keywords", cls.submit_keywords)),
                        detection_mode=str(data.get("detection_mode", "auto")),
                    )
            except Exception as e:
                print(f"\033[93m[WARN] Failed to parse config.json ({e}). Using default settings.\033[0m")
        return cls()


# =============================================================================
# 3. Detection Result Data Structure
# =============================================================================
@dataclass
class DetectionResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    source: str  # 'WindowsOcr', 'UIAutomation', 'Vision', or 'LayoutInference'
    label: str

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


# =============================================================================
# 4. Windows Native WinRT OCR Detection Engine (Fast, Font-Invariant)
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

    def scan_image(
        self,
        img: Image.Image,
        offset_x: int = 0,
        offset_y: int = 0,
        keywords: Optional[Tuple[str, ...]] = None,
        min_y: int = 0,
    ) -> Optional[DetectionResult]:
        """Runs OCR on a PIL Image and matches against target keywords with fuzzy tolerance."""
        if not self.is_available() or img is None:
            return None

        kw_list = keywords if keywords is not None else self.target_keywords
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
                for kw in kw_list:
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
                        matched_words = []
                        for word in line.words:
                            w_clean = word.text.lower().strip("()[] ")
                            if kw_clean in w_clean or difflib.SequenceMatcher(None, w_clean, kw_clean).ratio() >= 0.70:
                                matched_words.append(word)

                        if matched_words:
                            min_x = min(w.bounding_rect.x for w in matched_words)
                            w_min_y = min(w.bounding_rect.y for w in matched_words)
                            max_x = max(w.bounding_rect.x + w.bounding_rect.width for w in matched_words)
                            max_y = max(w.bounding_rect.y + w.bounding_rect.height for w in matched_words)

                            actual_y = int(w_min_y + offset_y)
                            if min_y > 0 and actual_y < min_y:
                                continue

                            return DetectionResult(
                                x=int(min_x + offset_x),
                                y=actual_y,
                                width=int(max_x - min_x),
                                height=int(max_y - w_min_y),
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
# 5. Windows UIAutomation Detection Engine (Fast, DPI-Invariant)
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

    def find_by_keywords(self, keywords: Tuple[str, ...]) -> Optional[DetectionResult]:
        """Searches UIA tree specifically for elements matching given keywords (e.g. Submit button)."""
        if auto is None:
            return None
        try:
            fg_win = auto.GetForegroundControl()
            if fg_win:
                match = self._find_in_tree_for_keywords(fg_win, keywords)
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
                            label=match.Name or "Submit",
                        )
        except Exception:
            pass
        return None

    def _find_in_tree(self, parent_control):
        """Recursively checks controls for target keyword matches with depth limit."""
        return self._find_in_tree_for_keywords(parent_control, self.target_keywords)

    def _find_in_tree_for_keywords(self, parent_control, keywords: Tuple[str, ...]):
        try:
            ctrl_name = parent_control.Name or ""
            for kw in keywords:
                if kw.lower() in ctrl_name.lower():
                    return parent_control

            # Depth limit to keep inspection under 40ms
            for child in parent_control.GetChildren()[:30]:
                name = child.Name or ""
                for kw in keywords:
                    if kw.lower() in name.lower():
                        return child
                for grandchild in child.GetChildren()[:20]:
                    gname = grandchild.Name or ""
                    for kw in keywords:
                        if kw.lower() in gname.lower():
                            return grandchild
        except Exception:
            pass
        return None


# =============================================================================
# 6. Computer Vision / Multi-Scale Multi-Theme Template Matching Engine
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
# 7. Multi-Engine Detection Orchestrator
# =============================================================================
class MultiEngineDetector:
    """Coordinates Windows Native OCR, UIAutomation, and Vision Detection."""

    def __init__(self, config: Config):
        self.config = config
        self.ocr_detector = WindowsOcrDetector(config.target_keywords, ocr_enabled=config.ocr_enabled)
        self.uia_detector = UIAutomationDetector(config.window_title_filter, config.target_keywords)
        self.vision_detector = VisionDetector(target_keywords=config.target_keywords)

    def detect(self) -> Optional[DetectionResult]:
        """Detects the (Recommended) option modal on screen."""
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

    def detect_submit_button(self, option_result: Optional[DetectionResult] = None) -> Optional[DetectionResult]:
        """
        Detects the 'Submit / पुष्टि करें' button on the active Antigravity modal.
        Uses UIA -> OCR -> Layout Inference fallback.
        """
        # 1. UIAutomation scan
        if self.config.detection_mode in ("auto", "uia"):
            res = self.uia_detector.find_by_keywords(self.config.submit_keywords)
            if res:
                return res

        # 2. Windows Native OCR scan
        if self.config.detection_mode in ("auto", "ocr"):
            if self.ocr_detector.is_available() and ImageGrab is not None:
                try:
                    screen_img = ImageGrab.grab()
                    min_y = (option_result.y + option_result.height) if option_result else 0
                    res = self.ocr_detector.scan_image(
                        screen_img,
                        offset_x=0,
                        offset_y=0,
                        keywords=self.config.submit_keywords,
                        min_y=min_y,
                    )
                    if res:
                        return res
                except Exception:
                    pass

        # 3. Layout Inference Fallback: Standard Antigravity modal places Submit ~65px below option
        if option_result:
            return DetectionResult(
                x=option_result.x,
                y=option_result.y + option_result.height + 65,
                width=min(option_result.width, 160),
                height=38,
                confidence=0.85,
                source="LayoutInference",
                label="Submit / पुष्टि करें",
            )

        return None


# Backward-compatibility alias
DualModeDetector = MultiEngineDetector


# =============================================================================
# 8. Floating On-Screen HUD Overlay (Tkinter Top-Most Window)
# =============================================================================
class FloatingHUD:
    """Always-on-top semi-transparent floating on-screen countdown HUD."""

    def __init__(self, alpha: float = 0.92):
        self.alpha = alpha
        self.root = None
        self.master = None
        self.lbl_title = None
        self.lbl_status = None
        self.total_seconds = 10.0
        self.is_visible = False

    def show(self, total_seconds: float, label: str, master=None):
        """Displays the floating HUD at the top center of the primary display."""
        try:
            import tkinter as tk
            self.total_seconds = float(total_seconds)
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
            w, h = 620, 58
            x = (sw - w) // 2
            y = 20
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.configure(bg="#181825", highlightbackground="#89B4FA", highlightthickness=2)

            clean_label = label.replace("\n", " ")
            if len(clean_label) > 42:
                clean_label = clean_label[:39] + "..."

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

            if remaining > 6.0:
                color = "#A6E3A1"  # Mint Green
            elif remaining > 3.0:
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

    def update_step(self, step_title: str, step_detail: str, color: str = "#89B4FA"):
        """Displays real-time multi-step progress in the HUD."""
        if not self.is_visible or not self.root:
            return
        try:
            self.lbl_title.config(text=step_title, fg=color)
            self.lbl_status.config(text=step_detail, fg="#CDD6F4")
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

    def flash_success(self, title: str = "✅ AUTO-SELECTED & SUBMITTED SUCCESSFULLY", detail: str = "Form submitted! Agent unblocked and resuming autonomously."):
        """Flashes green notification indicating success."""
        if not self.is_visible or not self.root:
            return
        try:
            self.root.configure(highlightbackground="#A6E3A1")
            self.lbl_title.config(text=title, fg="#A6E3A1")
            self.lbl_status.config(text=detail, fg="#A6E3A1")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1.2)
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
# 9. Smooth Human-Like Mouse Controller with Firm Click
# =============================================================================
class MouseController:
    """Dispatches human-like cubic easing cursor motion and natural clicks."""

    def __init__(self, glide_duration: float = 0.8, failsafe_enabled: bool = True):
        self.glide_duration = glide_duration
        if pyautogui:
            pyautogui.FAILSAFE = failsafe_enabled

    def firm_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Firm mouse down + dwell + up ensuring 100% reliable click registration on Web/Electron/Native."""
        if not pyautogui:
            return
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            time.sleep(0.06)
            pyautogui.mouseDown()
            time.sleep(0.08)  # 80ms press duration guarantees OS and Chromium register click
            pyautogui.mouseUp()
            time.sleep(0.06)
        except Exception:
            pass

    def glide_and_click(self, target_x: int, target_y: int, check_interrupted_fn=None) -> bool:
        """Glides cursor smoothly and executes a firm click at the target coordinate."""
        if not pyautogui:
            return False

        try:
            # Add minor random offset (+-2 px) for human-like natural landing
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
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

            # Firm click with dwell to guarantee button/option triggers
            self.firm_click()
            return True
        except Exception as e:
            print(f"\033[91m[ERROR] Mouse controller exception: {e}\033[0m")
            return False


# =============================================================================
# 10. Real-Time ANSI Terminal Dashboard
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
 {cls.GREEN}● Countdown:{cls.RESET} {config.countdown_seconds}s Timeout (2-Step)       {cls.GREEN}● Floating HUD:{cls.RESET} {'Enabled (Top-Most)' if config.floating_hud_enabled else 'Disabled'}
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
        color = cls.GREEN if remaining > 6 else (cls.YELLOW if remaining > 3 else cls.RED)
        sys.stdout.write(
            f"{cls.CLEAR_LINE}{color}[COUNTDOWN]{cls.RESET} [{bar}] {cls.BOLD}{remaining:4.1f}s{cls.RESET} remaining | Target: ({cx}, {cy}) | {cls.YELLOW}Move mouse to cancel{cls.RESET}"
        )
        sys.stdout.flush()

    @classmethod
    def render_interrupted(cls, distance: float, threshold: float):
        print(f"\n{cls.RED}{cls.BOLD}[FAIL-SAFE TRIGGERED]{cls.RESET} Human mouse movement detected ({distance:.1f}px > {threshold}px)!")
        print(f"{cls.YELLOW}➜ Yielded full control back to developer. Entering cooldown suppression.{cls.RESET}\n")

    @classmethod
    def render_clicking(cls, step: int, total_steps: int, label: str, x: int, y: int):
        print(f"\n{cls.CYAN}{cls.BOLD}[ACTION STEP {step}/{total_steps}]{cls.RESET} Gliding cursor smoothly to {label} at ({x}, {y}) and clicking...")

    @classmethod
    def render_completed(cls):
        print(f"{cls.GREEN}{cls.BOLD}[SUCCESS]{cls.RESET} 2-Step Flow complete! Option selected & form submitted. Agent unblocked.\n")

    @classmethod
    def render_cooldown(cls, seconds_left: int):
        sys.stdout.write(f"{cls.CLEAR_LINE}{cls.YELLOW}[COOLDOWN]{cls.RESET} Resuming scan in {seconds_left}s...")
        sys.stdout.flush()


# =============================================================================
# 11. Main Engine Orchestrator
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
        last_not_open_log = 0.0

        while self.is_running:
            try:
                # -------------------------------------------------------------
                # State 1: SCANNING
                # -------------------------------------------------------------
                if self.current_state == "SCANNING":
                    tick += 1

                    # Check Antigravity process and window state
                    is_ready, msg, hwnd = AntigravityWindowManager.check_and_foreground()

                    if not is_ready:
                        now = time.time()
                        if now - last_not_open_log >= 5.0:
                            print(f"\n{TerminalDashboard.YELLOW}[ANTIGRAVITY]{TerminalDashboard.RESET} {msg}")
                            last_not_open_log = now
                        time.sleep(self.config.check_interval_ms / 1000.0)
                        continue

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

            if self.config.floating_hud_enabled:
                self.hud.update_step("⏱️ Step 1/2: Auto-Selecting Option 1...", "Gliding to (Recommended) option...", "#89B4FA")

            success_step1 = self.mouse_ctrl.glide_and_click(
                target_cx,
                target_cy,
                check_interrupted_fn=self._check_mouse_interrupted,
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

                if self.config.floating_hud_enabled:
                    self.hud.update_step("⏱️ Step 2/2: Confirming Submission...", "Gliding to Submit button...", "#A6E3A1")

                success_step2 = self.mouse_ctrl.glide_and_click(
                    sub_cx,
                    sub_cy,
                    check_interrupted_fn=self._check_mouse_interrupted,
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
                TerminalDashboard.render_completed()
                if self.config.floating_hud_enabled:
                    self.hud.flash_success()
                self.current_state = "COOLDOWN"


# =============================================================================
# 12. Built-In Interactive Live Visual Simulator (--test / --simulate / --demo)
# =============================================================================
def launch_simulator(countdown_seconds: float = 10.0):
    """
    Spawns mock Antigravity modal, floating HUD, and physically glides mouse in a full 2-step flow:
    Step 1: Glide to Option 1 (Recommended) -> Firm click (Option 1 highlights & selects).
    Step 2: Glide to Submit button -> Firm click (Submit activates with chime & confirmation).
    """
    try:
        import tkinter as tk
    except ImportError:
        print("[ERROR] Tkinter is required for simulator mode.")
        return

    print("\n\033[96m[SIMULATION MODE] Launching mock Antigravity Decision Modal & Floating HUD (2-Step Flow)...\033[0m")
    root = tk.Tk()
    root.title("Antigravity - Interactive Decision Modal (Live Demo)")
    root.geometry("700x460+300+180")
    root.configure(bg="#1E1E2E")
    root.attributes("-topmost", True)

    # Ensure window is visible and active in foreground without moving mouse
    root.update_idletasks()
    try:
        hwnd = root.winfo_id()
        top_hwnd = ctypes.windll.user32.GetParent(hwnd) or hwnd
        AntigravityWindowManager.bring_to_foreground(top_hwnd)
    except Exception:
        pass

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
        wraplength=620,
        justify="left",
    )
    desc.pack(pady=4)

    # Variable to track selected option (Step 1)
    selected_option = tk.StringVar(value="")

    # Option 1 Container Frame
    opt1_frame = tk.Frame(root, bg="#313244", highlightbackground="#45475A", highlightthickness=1)
    opt1_frame.pack(pady=8, fill="x", padx=40)

    radio1_lbl = tk.Label(opt1_frame, text="○", font=("Segoe UI", 14), fg="#BAC2DE", bg="#313244")
    radio1_lbl.pack(side="left", padx=(12, 6), pady=8)

    opt1_text_lbl = tk.Label(
        opt1_frame,
        text="Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना",
        font=("Segoe UI", 11, "bold"),
        fg="#A6E3A1",
        bg="#313244",
        cursor="hand2",
    )
    opt1_text_lbl.pack(side="left", pady=8, fill="x", expand=True, anchor="w")

    # Option 2 Container Frame
    opt2_frame = tk.Frame(root, bg="#313244", highlightbackground="#45475A", highlightthickness=1)
    opt2_frame.pack(pady=4, fill="x", padx=40)

    radio2_lbl = tk.Label(opt2_frame, text="○", font=("Segoe UI", 14), fg="#BAC2DE", bg="#313244")
    radio2_lbl.pack(side="left", padx=(12, 6), pady=6)

    opt2_text_lbl = tk.Label(
        opt2_frame,
        text="Option 2: नहीं, अभी रहने दो क्योंकि टेस्टिंग पेंडिंग है",
        font=("Segoe UI", 10),
        fg="#BAC2DE",
        bg="#313244",
        cursor="hand2",
    )
    opt2_text_lbl.pack(side="left", pady=6, fill="x", expand=True, anchor="w")

    # Selection handlers
    def select_option_1():
        selected_option.set("option_1")
        radio1_lbl.config(text="●", fg="#A6E3A1", bg="#263b36")
        opt1_frame.config(bg="#263b36", highlightbackground="#A6E3A1", highlightthickness=2)
        opt1_text_lbl.config(bg="#263b36", fg="#A6E3A1")

        radio2_lbl.config(text="○", fg="#BAC2DE", bg="#313244")
        opt2_frame.config(bg="#313244", highlightbackground="#45475A", highlightthickness=1)
        opt2_text_lbl.config(bg="#313244", fg="#BAC2DE")

        status_lbl.config(
            text="Step 1/2 Complete: Option 1 Selected! Moving to Submit button...",
            fg="#A6E3A1",
            font=("Segoe UI", 10, "bold"),
        )
        submit_btn.config(state="normal", bg="#89B4FA", fg="#11111B")

    def select_option_2():
        selected_option.set("option_2")
        radio2_lbl.config(text="●", fg="#F9E2AF", bg="#3c3836")
        opt2_frame.config(bg="#3c3836", highlightbackground="#F9E2AF", highlightthickness=2)
        opt2_text_lbl.config(bg="#3c3836", fg="#F9E2AF")

        radio1_lbl.config(text="○", fg="#BAC2DE", bg="#313244")
        opt1_frame.config(bg="#313244", highlightbackground="#45475A", highlightthickness=1)
        opt1_text_lbl.config(bg="#313244", fg="#A6E3A1")

        status_lbl.config(text="Option 2 selected manually by developer.", fg="#F9E2AF")
        submit_btn.config(state="normal", bg="#89B4FA", fg="#11111B")

    opt1_frame.bind("<Button-1>", lambda e: select_option_1())
    opt1_text_lbl.bind("<Button-1>", lambda e: select_option_1())
    radio1_lbl.bind("<Button-1>", lambda e: select_option_1())

    opt2_frame.bind("<Button-1>", lambda e: select_option_2())
    opt2_text_lbl.bind("<Button-1>", lambda e: select_option_2())
    radio2_lbl.bind("<Button-1>", lambda e: select_option_2())

    # Step 2: Submit Button at bottom
    def on_submit_clicked():
        if not selected_option.get():
            status_lbl.config(text="⚠️ Please select an option first!", fg="#F38BA8")
            return
        submit_btn.config(text="✅ Submitted / पुष्टि हो गई!", bg="#A6E3A1", fg="#11111B")
        status_lbl.config(
            text="🎉 Step 2/2 Complete: Form Submitted! Agent unblocked and resuming autonomously.",
            fg="#A6E3A1",
            font=("Segoe UI", 11, "bold"),
        )
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        root.after(1800, root.destroy)

    submit_frame = tk.Frame(root, bg="#1E1E2E")
    submit_frame.pack(pady=12)

    submit_btn = tk.Button(
        submit_frame,
        text="🚀 Submit / पुष्टि करें",
        font=("Segoe UI", 11, "bold"),
        bg="#45475A",
        fg="#BAC2DE",
        activebackground="#A6E3A1",
        activeforeground="#11111B",
        relief="raised",
        bd=2,
        padx=24,
        pady=8,
        cursor="hand2",
        command=on_submit_clicked,
    )
    submit_btn.pack()

    status_lbl = tk.Label(
        root,
        text="AutoSelect-Commander active. 10-second countdown in progress...",
        font=("Segoe UI", 9, "italic"),
        fg="#9399B2",
        bg="#1E1E2E",
        pady=6,
    )
    status_lbl.pack()

    # Floating HUD overlay initialized to configured countdown duration
    hud = FloatingHUD(alpha=0.92)
    countdown_duration = float(countdown_seconds)
    hud.show(countdown_duration, "Option 1: (Recommended) GitHub", master=root)

    start_time = time.time()
    initial_mouse = pyautogui.position() if pyautogui else (0, 0)
    cancelled = [False]
    mouse_ctrl = MouseController(glide_duration=0.8, failsafe_enabled=True)

    def sim_tick():
        if cancelled[0]:
            return

        # Auto-foregrounding check during countdown
        try:
            if root.state() == "iconic":
                root.deiconify()
                root.lift()
        except Exception:
            pass

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
            # -------------------------------------------------------------
            # STEP 1: Glide to Option 1 and Firm Click
            # -------------------------------------------------------------
            hud.update_step("⏱️ Step 1/2: Auto-Selecting Option 1...", "Gliding cursor smoothly to (Recommended)...", "#89B4FA")
            status_lbl.config(text="[STEP 1/2] Gliding cursor to Option 1 (Recommended)...", fg="#89B4FA")
            root.update_idletasks()
            opt1_frame.update_idletasks()

            o1_x = opt1_frame.winfo_rootx() + opt1_frame.winfo_width() // 2
            o1_y = opt1_frame.winfo_rooty() + opt1_frame.winfo_height() // 2

            def check_cancel():
                return cancelled[0]

            success_step1 = mouse_ctrl.glide_and_click(o1_x, o1_y, check_interrupted_fn=check_cancel)
            if not success_step1:
                hud.flash_cancelled()
                return

            select_option_1()
            root.update()

            # Small natural dwell between Step 1 and Step 2
            time.sleep(0.35)

            # -------------------------------------------------------------
            # STEP 2: Glide to Submit Button and Firm Click
            # -------------------------------------------------------------
            hud.update_step("⏱️ Step 2/2: Confirming Submission...", "Gliding cursor smoothly to Submit button...", "#A6E3A1")
            status_lbl.config(text="[STEP 2/2] Gliding cursor to Submit / पुष्टि करें...", fg="#A6E3A1")
            root.update_idletasks()
            submit_btn.update_idletasks()

            sb_x = submit_btn.winfo_rootx() + submit_btn.winfo_width() // 2
            sb_y = submit_btn.winfo_rooty() + submit_btn.winfo_height() // 2

            success_step2 = mouse_ctrl.glide_and_click(sb_x, sb_y, check_interrupted_fn=check_cancel)
            if success_step2:
                hud.flash_success("✅ 2-STEP AUTO-SELECTION & SUBMISSION COMPLETE!", "Form submitted! Agent unblocked and resuming autonomously.")
                on_submit_clicked()
            else:
                hud.flash_cancelled()
            return

        root.after(50, sim_tick)

    root.after(200, sim_tick)
    root.mainloop()


# =============================================================================
# 13. Screen & Window Diagnostics Probe (--diagnostics)
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

    # 2. Antigravity Process & Window Status
    print("\n[2] ANTIGRAVITY PROCESS & WINDOW STATUS")
    is_proc = AntigravityWindowManager.is_process_running()
    hwnd = AntigravityWindowManager.find_antigravity_window()
    print(f"  • Process Active     : {is_proc}")
    print(f"  • Window Handle      : {hwnd if hwnd else 'None'}")
    if hwnd:
        is_min = AntigravityWindowManager.is_minimized(hwnd)
        is_fg = AntigravityWindowManager.is_foreground(hwnd)
        print(f"  • Minimized (Iconic) : {is_min}")
        print(f"  • Is Foreground      : {is_fg}")
    else:
        print("  • Notice             : 'एंटी-ग्रैविटी अभी ओपन नहीं है (Antigravity is currently not open)'")

    # 3. Windows Native OCR Status
    print("\n[3] WINDOWS WINRT OCR STATUS")
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

    # 4. Visible Windows Probe
    print("\n[4] VISIBLE WINDOWS PROBE")
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

    # 5. OCR Live Screen Text Probe
    print("\n[5] OCR LIVE SCREEN TEXT PROBE")
    if ocr_det.is_available() and ImageGrab is not None:
        try:
            print("  • Capturing desktop surface for OCR text extraction...")
            screen_img = ImageGrab.grab()
            buf = io.BytesIO()
            screen_img.save(buf, format="PNG")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, ocr_det._recognize_async(buf.getvalue()))
                try:
                    ocr_res = future.result(timeout=4.0)
                except concurrent.futures.TimeoutError:
                    print("  • OCR Screen Grab Notice: Recognition timed out after 4.0s.")
                    ocr_res = None
            if ocr_res and ocr_res.lines:
                print(f"  • Lines Extracted    : {len(ocr_res.lines)}")
                print("  • Sample Detected Lines (first 10):")
                for line in ocr_res.lines[:10]:
                    print(f"    - \"{line.text}\"")

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
    else:
        print("  • OCR probe skipped (OCR or ImageGrab unavailable).")

    # 6. UIAutomation Tree Probe
    print("\n[6] UIAUTOMATION TREE PROBE")
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
# 14. CLI Entry Point
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="AutoSelect-Commander: Visual Mouse Automation for Antigravity"
    )
    parser.add_argument(
        "--test",
        "--simulate",
        "--demo",
        dest="test",
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
        help="Override countdown duration in seconds (default: 10s)",
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
        launch_simulator(cfg.countdown_seconds)
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
