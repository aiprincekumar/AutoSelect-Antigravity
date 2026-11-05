#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Manager Subsystem
========================
Discovers, scores, restores, maximizes, and focuses application windows.
Includes Antigravity 2.0 targeting heuristics, browser disqualification,
and Windows 10/11 foreground focus lock bypass.
"""

import os
import sys
import time
import logging
from typing import Optional, List, Tuple, Dict, Any

from .constants import (
    IS_WINDOWS,
    VK_MENU,
    VK_ESCAPE,
    SW_RESTORE,
    SW_MAXIMIZE,
    SW_SHOW,
    HWND_TOPMOST,
    HWND_NOTOPMOST,
    SWP_NOSIZE,
    SWP_NOMOVE,
    SWP_SHOWWINDOW,
    ASFW_ANY,
    DISQUALIFIED_BROWSER_PROCS,
    BLACK_LISTED_SHELL_PROCS,
    DEFAULT_TARGET_WINDOW,
)
from .win32_api import (
    ensure_input_desktop,
    get_process_info_for_hwnd,
    get_active_window_title,
)
from .input_injector import _send_key_event

logger = logging.getLogger("GrillMeAutomation.WindowManager")

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    from .win32_api import user32, kernel32, WINDOWPLACEMENT, WNDENUMPROC

    def get_window_info(hwnd: int) -> dict:
        """Retrieve comprehensive window state, visibility, process info, and geometry info."""
        if not hwnd or not user32.IsWindow(hwnd):
            return {
                "hwnd": hwnd,
                "title": "",
                "class": "",
                "process_name": "",
                "process_exe": "",
                "pid": 0,
                "exists": False,
                "visible": False,
                "minimized": False,
                "maximized": False,
                "rect": (0, 0, 0, 0),
                "width": 0,
                "height": 0
            }
        try:
            ensure_input_desktop()
            visible = bool(user32.IsWindowVisible(hwnd))
            iconic = bool(user32.IsIconic(hwnd))
            zoomed = bool(user32.IsZoomed(hwnd))
            buf = ctypes.create_unicode_buffer(512)
            length = user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip() if length > 0 else ""

            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            cls_name = cls_buf.value.strip()

            pid, pname, pexe = get_process_info_for_hwnd(hwnd)

            rect = wintypes.RECT()
            rect_ok = bool(user32.GetWindowRect(hwnd, ctypes.byref(rect)))

            # If minimized, GetWindowRect returns (-32000, -32000). Check WINDOWPLACEMENT for restored size
            width = (rect.right - rect.left) if rect_ok else 0
            height = (rect.bottom - rect.top) if rect_ok else 0
            if iconic or (rect_ok and rect.left <= -30000):
                wp = WINDOWPLACEMENT()
                wp.length = ctypes.sizeof(WINDOWPLACEMENT)
                if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                    width = wp.rcNormalPosition.right - wp.rcNormalPosition.left
                    height = wp.rcNormalPosition.bottom - wp.rcNormalPosition.top

            return {
                "hwnd": hwnd,
                "title": title,
                "class": cls_name,
                "process_name": pname,
                "process_exe": pexe,
                "pid": pid,
                "exists": True,
                "visible": visible,
                "minimized": iconic,
                "maximized": zoomed,
                "rect": (rect.left, rect.top, rect.right, rect.bottom) if rect_ok else (0, 0, 0, 0),
                "width": width,
                "height": height,
            }
        except Exception as e:
            return {
                "hwnd": hwnd,
                "title": "",
                "class": "",
                "process_name": "",
                "process_exe": "",
                "pid": 0,
                "exists": False,
                "visible": False,
                "minimized": False,
                "maximized": False,
                "rect": (0, 0, 0, 0),
                "width": 0,
                "height": 0,
                "error": str(e)
            }

    def find_all_candidate_windows() -> List[dict]:
        """
        Enumerate all top-level candidate windows on active desktop,
        capturing title, class name, process info, visibility, iconic/zoomed state, and rect.
        """
        if not IS_WINDOWS:
            return []

        hdesk = ensure_input_desktop()
        console_hwnd = kernel32.GetConsoleWindow()
        candidates: List[dict] = []

        def enum_cb(hwnd, lparam):
            if console_hwnd and hwnd == console_hwnd:
                return True
            try:
                if not user32.IsWindow(hwnd):
                    return True

                visible = bool(user32.IsWindowVisible(hwnd))
                iconic = bool(user32.IsIconic(hwnd))
                zoomed = bool(user32.IsZoomed(hwnd))

                # Length check
                length = user32.GetWindowTextLengthW(hwnd)
                title = ""
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()

                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                cls_name = cls_buf.value.strip()

                pid, pname, pexe = get_process_info_for_hwnd(hwnd)

                rect = wintypes.RECT()
                rect_ok = bool(user32.GetWindowRect(hwnd, ctypes.byref(rect)))
                w = (rect.right - rect.left) if rect_ok else 0
                h = (rect.bottom - rect.top) if rect_ok else 0

                # Include if titled or if matching Antigravity/Electron class
                p_lower = pname.lower()
                is_antigravity = "antigravity" in p_lower or "electron" in p_lower
                if (title or (is_antigravity and cls_name == "Chrome_WidgetWin_1")) and (visible or iconic):
                    candidates.append({
                        "hwnd": hwnd,
                        "title": title,
                        "class": cls_name,
                        "pid": pid,
                        "process_name": pname,
                        "process_exe": pexe,
                        "visible": visible,
                        "minimized": iconic,
                        "maximized": zoomed,
                        "width": w,
                        "height": h,
                        "rect": (rect.left, rect.top, rect.right, rect.bottom) if rect_ok else (0, 0, 0, 0),
                    })
            except Exception:
                pass
            return True

        cb = WNDENUMPROC(enum_cb)
        if hdesk:
            try:
                user32.EnumDesktopWindows(hdesk, cb, 0)
            finally:
                try:
                    user32.CloseDesktop(hdesk)
                except Exception:
                    pass
        else:
            user32.EnumWindows(cb, 0)

        return candidates

    def find_windows_by_title(keywords: List[str], exclude_console: bool = True) -> List[Tuple[int, str]]:
        """
        Enumerate all visible top-level windows whose title contains any keyword (case-insensitive).
        Maintained for backward compatibility.
        """
        matches: List[Tuple[int, str]] = []
        candidates = find_all_candidate_windows()
        for c in candidates:
            t_lower = c["title"].lower()
            for kw in keywords:
                if kw.lower() in t_lower:
                    matches.append((c["hwnd"], c["title"]))
                    break
        return matches

    def select_target_window(
        target_keyword: str = DEFAULT_TARGET_WINDOW,
        exclude_terms: Optional[List[str]] = None
    ) -> Optional[Tuple[int, str]]:
        """
        Search and score candidate windows to identify the best match for Antigravity 2.0 Harness,
        IDE, or chat interfaces.

        Supports multi-keyword comma-separated strings (e.g. "Antigravity,Harness,AutoSelect-Commander"),
        process executable matching ('Antigravity.exe'), class inspection ('Chrome_WidgetWin_1'),
        and title matching.
        """
        # Parse multi-keywords
        raw_kws = target_keyword.replace("|", ",").split(",") if target_keyword else ["Antigravity"]
        keywords = [k.strip() for k in raw_kws if k.strip()]
        if not keywords:
            keywords = ["Antigravity", "Antigravity 2.0", "Harness", "AutoSelect-Commander"]

        candidates = find_all_candidate_windows()
        if not candidates:
            return None

        console_hwnd = kernel32.GetConsoleWindow()
        blacklisted_procs = {
            "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe", "wt.exe",
            "python.exe", "pythonw.exe", "explorer.exe"
        }
        blacklisted_titles = [
            "grill_me", "run_grill_me", "test_grill_me", "powershell", "cmd.exe",
            "run_all_steps", "run_step1", "run_step2", "run_step3"
        ]
        excludes = blacklisted_titles + (exclude_terms or [])

        # Distinguish between default search vs user-specified custom filter
        default_set = {"antigravity", "antigravity 2.0", "harness", "autoselect-commander"}
        is_custom_filter = not any(k.lower() in default_set for k in keywords)

        # Check if the user explicitly requested a web browser by name
        user_explicitly_requested_browser = any(
            any(browser in kw.lower() for browser in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "iexplore"))
            for kw in keywords
        )

        scored: List[Tuple[int, int, str, dict]] = []  # (score, hwnd, title, candidate_dict)

        for c in candidates:
            hwnd = c["hwnd"]
            title = c["title"]
            t_lower = title.lower()
            pname = c["process_name"]
            p_lower = pname.lower()
            cls_name = c["class"]
            pexe = c["process_exe"].lower()
            pexe_base = os.path.basename(pexe).lower() if pexe else ""

            if console_hwnd and hwnd == console_hwnd:
                continue

            # 1. Strict Browser Disqualification
            is_browser = (
                p_lower in DISQUALIFIED_BROWSER_PROCS
                or pexe_base in DISQUALIFIED_BROWSER_PROCS
                or any(b in p_lower for b in ("chrome", "msedge", "firefox", "brave", "opera", "vivaldi"))
            )
            if is_browser and not user_explicitly_requested_browser:
                # Strictly reject / disqualify any web browser
                continue

            # 2. Check shell blacklist
            is_blacklisted_proc = p_lower in BLACK_LISTED_SHELL_PROCS
            kw_mentions_proc = any(kw.lower() in p_lower for kw in keywords)
            if is_blacklisted_proc and not kw_mentions_proc:
                continue

            # Check if keyword matches process or title
            kw_matches_proc = any(kw.lower() in p_lower or (pexe and kw.lower() in pexe) for kw in keywords)
            kw_matches_title = any(kw.lower() in t_lower for kw in keywords)

            # If user specified a specific custom filter, require a match
            if is_custom_filter and not (kw_matches_proc or kw_matches_title):
                continue

            score = 0

            # 1. Antigravity 2.0 Harness Process Signature (Highest Priority: +1000)
            is_antigravity_proc = (
                "antigravity.exe" in p_lower
                or p_lower == "antigravity"
                or "antigravity" in pexe
            )
            if is_antigravity_proc:
                score += 1000
                if cls_name == "Chrome_WidgetWin_1":
                    score += 100
                if c["minimized"] or (c["width"] >= 400 and c["height"] >= 300):
                    score += 50
            elif "electron" in p_lower or "electron" in pexe:
                score += 200
                if cls_name == "Chrome_WidgetWin_1":
                    score += 50

            # 2. Keyword matching against process name or executable path
            for kw in keywords:
                kw_l = kw.lower()
                if kw_l in p_lower or (pexe and kw_l in pexe):
                    score += 70
                    break

            # 3. Keyword matching against window title
            for kw in keywords:
                kw_l = kw.lower()
                if kw_l == t_lower:
                    score += 100
                elif t_lower.startswith(kw_l):
                    score += 80
                elif kw_l in t_lower:
                    score += 50

            # 4. Window Class weighting - ONLY for verified Antigravity or Electron apps!
            # Never assign points for Chrome_WidgetWin_1 to arbitrary or unverified windows.
            if is_antigravity_proc and cls_name == "Chrome_WidgetWin_1":
                score += 20

            # 5. Visibility and layout bonuses
            if c["visible"]:
                score += 15
            if c["maximized"]:
                score += 10
            elif not c["minimized"] and c["width"] >= 600 and c["height"] >= 400:
                score += 10

            # 6. Exclusions and runner penalties
            for ex in excludes:
                if ex.lower() in t_lower and not any(kw.lower() in ex.lower() for kw in keywords):
                    score -= 50

            # Absolute disqualification for web browsers unless explicitly requested
            if is_browser and not user_explicitly_requested_browser:
                score = -9999

            if score > 0:
                scored.append((score, hwnd, title, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] > 0:
            top_score, top_hwnd, top_title, top_c = scored[0]
            proc_name = top_c.get("process_name", "")
            pid = top_c.get("pid", 0)
            cls_name = top_c.get("class", "")

            logger.info(
                f"Selected Window: HWND={hex(top_hwnd)}, Process={proc_name} (PID={pid}), "
                f"Title='{top_title}', Class={cls_name} [Score: {top_score}]"
            )

            # Defensive verification: Ensure candidate is NEVER a browser
            if proc_name.lower() in DISQUALIFIED_BROWSER_PROCS and not user_explicitly_requested_browser:
                logger.error(f"[SECURITY ALERT] Candidate is browser '{proc_name}'. Rejected!")
                return None

            return (top_hwnd, top_title)
        return None

    def ensure_window_on_screen(
        hwnd: int,
        auto_maximize: bool = True,
        auto_focus: bool = True,
        settle_delay: float = 0.5
    ) -> bool:
        """
        Ensures the target window is restored if minimized, maximized to full-screen
        (if requested), and brought to foreground focus with verified geometry.
        Incorporates Windows 10/11 foreground lock bypass, thread input attachment,
        Z-order bumping, and Electron window refresh.
        """
        if not hwnd or not user32.IsWindow(hwnd):
            logger.error(f"Invalid window handle: {hex(hwnd) if hwnd else '0'}")
            return False

        ensure_input_desktop()
        info = get_window_info(hwnd)
        logger.info(
            f"Target Window Found: '{info['title']}' (HWND: {hex(hwnd)}) | "
            f"Process: {info['process_name']} (PID: {info['pid']}) | Class: {info['class']}"
        )
        logger.info(
            f"Initial State: Minimized={'YES' if info['minimized'] else 'NO'}, "
            f"Maximized={'YES' if info['maximized'] else 'NO'}, Dimensions={info['width']}x{info['height']}"
        )

        try:
            # Unlock Windows OS foreground lock
            try:
                user32.AllowSetForegroundWindow(ASFW_ANY)
            except Exception:
                pass

            # Step 1: Un-minimize / restore if minimized (iconic)
            if user32.IsIconic(hwnd) or info["minimized"]:
                logger.info("Target window is minimized. Restoring window state (SW_RESTORE)...")
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.ShowWindowAsync(hwnd, SW_RESTORE)
                try:
                    user32.OpenIcon(hwnd)
                except Exception:
                    pass
                time.sleep(0.08)

            # Step 2: Maximize to full screen if requested
            if auto_maximize:
                if not user32.IsZoomed(hwnd):
                    logger.info("Target window is not maximized. Maximizing to full screen (SW_MAXIMIZE)...")
                    user32.ShowWindow(hwnd, SW_MAXIMIZE)
                    user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
                    time.sleep(0.08)
                else:
                    logger.info("Target window is already maximized.")
            else:
                if not user32.IsWindowVisible(hwnd) or info["minimized"]:
                    user32.ShowWindow(hwnd, SW_SHOW)
                    user32.ShowWindowAsync(hwnd, SW_SHOW)
                    time.sleep(0.05)

            # Step 3: Bring to Foreground & Force Focus with OS lock release
            if auto_focus:
                fg_hwnd = user32.GetForegroundWindow()
                if fg_hwnd != hwnd:
                    logger.info("Engaging force-focus & foreground lock bypass...")
                    cur_thread = kernel32.GetCurrentThreadId()
                    fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
                    target_thread = user32.GetWindowThreadProcessId(hwnd, None)

                    attached_fg = False
                    attached_target = False
                    if fg_thread and fg_thread != cur_thread:
                        attached_fg = bool(user32.AttachThreadInput(cur_thread, fg_thread, True))
                    if target_thread and target_thread != cur_thread:
                        attached_target = bool(user32.AttachThreadInput(cur_thread, target_thread, True))

                    try:
                        # Z-Order bump to force window to topmost layer then restore
                        user32.SetWindowPos(
                            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                        )
                        user32.SetWindowPos(
                            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                        )

                        user32.BringWindowToTop(hwnd)
                        user32.SetForegroundWindow(hwnd)
                        if hasattr(user32, "SwitchToThisWindow"):
                            user32.SwitchToThisWindow(hwnd, True)
                        user32.SetActiveWindow(hwnd)
                        user32.SetFocus(hwnd)

                        # Dismiss any accidentally activated application menu bar (e.g. Electron Alt trap)
                        # to guarantee window menu / Close button is never focused
                        _send_key_event(VK_ESCAPE, key_up=False)
                        _send_key_event(VK_ESCAPE, key_up=True)
                    finally:
                        if attached_fg:
                            user32.AttachThreadInput(cur_thread, fg_thread, False)
                        if attached_target:
                            user32.AttachThreadInput(cur_thread, target_thread, False)

            # Step 4: Settle delay for UI rendering
            if settle_delay > 0:
                time.sleep(settle_delay)

            # Step 5: Post-condition verification & retry loop
            post_info = get_window_info(hwnd)
            curr_fg = user32.GetForegroundWindow()
            is_fg = (curr_fg == hwnd)

            # If not foreground, execute secondary pulse
            if auto_focus and not is_fg:
                logger.info("Secondary focus pulse...")
                user32.SetForegroundWindow(hwnd)
                if hasattr(user32, "SwitchToThisWindow"):
                    user32.SwitchToThisWindow(hwnd, True)
                time.sleep(0.1)
                curr_fg = user32.GetForegroundWindow()
                is_fg = (curr_fg == hwnd)

            logger.info(
                f"[VERIFIED] Window On Screen: Foreground={'YES' if is_fg else 'NO'}, "
                f"Maximized={'YES' if post_info['maximized'] else 'NO'}, "
                f"Bounds=[{post_info['rect'][0]},{post_info['rect'][1]},{post_info['rect'][2]},{post_info['rect'][3]}] "
                f"({post_info['width']}x{post_info['height']})"
            )
            return True
        except Exception as e:
            logger.error(f"Error while positioning/focusing window {hex(hwnd)}: {e}")
            return False

else:
    # Non-Windows stubs
    def get_window_info(hwnd: int) -> dict:
        return {
            "hwnd": hwnd,
            "title": "<Non-Windows>",
            "class": "",
            "process_name": "",
            "process_exe": "",
            "pid": 0,
            "exists": False,
            "visible": False,
            "minimized": False,
            "maximized": False,
            "rect": (0, 0, 0, 0),
            "width": 0,
            "height": 0
        }

    def find_all_candidate_windows() -> List[dict]:
        return []

    def find_windows_by_title(keywords: List[str], exclude_console: bool = True) -> List[Tuple[int, str]]:
        return []

    def select_target_window(target_keyword: str = "", exclude_terms: Optional[List[str]] = None) -> Optional[Tuple[int, str]]:
        return None

    def ensure_window_on_screen(hwnd: int, auto_maximize: bool = True, auto_focus: bool = True, settle_delay: float = 0.5) -> bool:
        return False
