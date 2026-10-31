# -*- coding: utf-8 -*-
"""
Screen, window, OCR, and accessibility diagnostic probe (--diagnostics).
"""

import asyncio
import ctypes
from ctypes import wintypes
import io
import sys

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import uiautomation as auto
except ImportError:
    auto = None

try:
    import winsdk.windows.media.ocr as win_ocr
except ImportError:
    win_ocr = None

from auto_commander.config import Config
from auto_commander.detectors.ocr_detector import WindowsOcrDetector, WINSDK_OCR_AVAILABLE
from auto_commander.platform.win32_window import AntigravityWindowManager


def run_diagnostics(config: Config):
    """Deep screen, window, and text diagnostic probe."""
    print("=" * 80)
    print("           AutoSelect-Commander Screen & Window Diagnostics")
    print("=" * 80)

    # Ensure thread desktop attachment
    AntigravityWindowManager.attach_to_input_desktop()

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
    hwnd = AntigravityWindowManager.find_antigravity_window(title_filter=config.window_title_filter)
    print(f"  • Process Active     : {is_proc}")
    print(f"  • Window Handle      : {hwnd if hwnd else 'None'}")
    if hwnd:
        is_min = AntigravityWindowManager.is_minimized(hwnd)
        is_fg = AntigravityWindowManager.is_foreground(hwnd)
        rect = AntigravityWindowManager.get_window_rect(hwnd)
        print(f"  • Minimized (Iconic) : {is_min}")
        print(f"  • Is Foreground      : {is_fg}")
        if rect:
            print(f"  • Window Rect        : ({rect.x}, {rect.y}, {rect.width}x{rect.height})")
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
    top_windows = []
    try:
        user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
        if user32:
            h_input = user32.OpenInputDesktop(0, False, 0x01FF)
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_vis(h, l):
                if user32.IsWindowVisible(h):
                    length = user32.GetWindowTextLengthW(h)
                    if length > 0:
                        b = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(h, b, length + 1)
                        rect = ctypes.wintypes.RECT()
                        user32.GetWindowRect(h, ctypes.byref(rect))
                        w = rect.right - rect.left
                        h_dim = rect.bottom - rect.top
                        if w > 50 and h_dim > 50:
                            top_windows.append((b.value, rect.left, rect.top, w, h_dim))
                return True
            cb_v = WNDENUMPROC(enum_vis)
            if h_input:
                user32.EnumDesktopWindows.argtypes = [ctypes.wintypes.HANDLE, WNDENUMPROC, ctypes.wintypes.LPARAM]
                user32.EnumDesktopWindows(h_input, cb_v, 0)
            else:
                user32.EnumWindows(cb_v, 0)
    except Exception:
        pass

    if top_windows:
        print(f"  • Total Titled Windows : {len(top_windows)}")
        for idx, (t, l, top_pos, w, h) in enumerate(top_windows[:8], 1):
            clean_t = t[:50].replace("\n", " ")
            print(f"    [{idx}] \"{clean_t}\" ({w}x{h} at {l},{top_pos})")
    elif gw is not None:
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
            print(f"  • pygetwindow fallback notice: {e}")
    else:
        print("  • Window enumeration not available.")

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
            else:
                print("  • OCR Screen Grab Notice: No text lines extracted on current frame.")
        except Exception as e:
            print(f"  • OCR Screen Grab Exception: {e}")

    # 6. UIAutomation Tree Probe
    print("\n[6] UIAUTOMATION TREE PROBE")
    if auto is not None:
        try:
            root_ctrl = auto.GetRootControl()
            fg_ctrl = auto.GetForegroundControl()
            print(f"  • Root UIA Control   : {root_ctrl.Name if root_ctrl else 'None'} ({len(root_ctrl.GetChildren()) if root_ctrl else 0} children)")
            print(f"  • Foreground Control : {fg_ctrl.Name if fg_ctrl else 'None'}")
        except Exception as e:
            print(f"  • UIA probe exception: {e}")
    else:
        print("  • uiautomation not available.")

    print("\n" + "=" * 80)
    print("Diagnostics complete.")
    print("=" * 80)
