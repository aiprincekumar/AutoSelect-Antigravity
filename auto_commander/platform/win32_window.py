# -*- coding: utf-8 -*-
"""
Win32 window detection, self-exclusion filtering, and safe foreground activation.
"""

import ctypes
from ctypes import wintypes
import os
import sys
import time
from typing import List, Optional, Set, Tuple

from auto_commander.models import Rect

# Ensure Win32 types
user32 = ctypes.windll.user32 if sys.platform == "win32" else None
kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]


if user32:
    user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
    user32.SetThreadDesktop.restype = wintypes.BOOL
    user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWPLACEMENT)]
    user32.GetWindowPlacement.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindowAsync.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND

# Shell and system processes that must NEVER be targeted or brought to foreground
BLACK_LISTED_PROCESS_NAMES = {
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
    "conhost.exe",
    "wt.exe",
    "windowsterminal.exe",
    "explorer.exe",
    "python.exe",
    "pythonw.exe",
}

# Substrings that must NEVER match as real Antigravity IDE (applied to non-Antigravity windows)
EXCLUDED_WINDOW_TITLE_KEYWORDS = {
    "command prompt",
    "windows powershell",
    "file explorer",
}


class AntigravityWindowManager:
    """
    Win32 Window Manager dedicated to locating, verifying, and safely foregrounding
    the true Antigravity IDE process and window, with strict self-exclusion to prevent
    targeting cmd.exe, PowerShell, File Explorer, or itself.
    """

    PROCESS_NAMES = ("antigravity.exe", "antigravity")

    @classmethod
    def attach_to_input_desktop(cls) -> bool:
        """
        Attaches the current thread to the interactive user desktop (WinSta0\\Default).
        Crucial when running from background sessions, subagents, or elevated harnesses.
        """
        if not user32:
            return False
        try:
            h_input = user32.OpenInputDesktop(0, False, 0x01FF)
            if h_input:
                user32.SetThreadDesktop(h_input)
                return True
        except Exception:
            pass
        return False

    @classmethod
    def get_own_process_family_pids(cls) -> Set[int]:
        """
        Retrieves own PID and immediate console/shell parent PIDs (e.g. cmd.exe, wt.exe, python.exe)
        so they can never be targeted or confused with Antigravity.
        NEVER blacklists Antigravity itself even if Antigravity launched the sub-shell.
        """
        pids = {os.getpid()}
        if not kernel32:
            return pids

        try:
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
                parent_map = {}
                name_map = {}
                has_next = kernel32.Process32FirstW(h_snap, ctypes.byref(pe))
                while has_next:
                    parent_map[pe.th32ProcessID] = pe.th32ParentProcessID
                    name_map[pe.th32ProcessID] = pe.szExeFile.lower()
                    has_next = kernel32.Process32NextW(h_snap, ctypes.byref(pe))
                kernel32.CloseHandle(h_snap)

                curr = os.getpid()
                depth = 0
                while curr in parent_map and depth < 6:
                    curr = parent_map[curr]
                    exe_name = name_map.get(curr, "")
                    # NEVER blacklist Antigravity IDE itself!
                    if any(target in exe_name for target in cls.PROCESS_NAMES):
                        break
                    # Only blacklist shells and script interpreters
                    if exe_name in BLACK_LISTED_PROCESS_NAMES:
                        pids.add(curr)
                    depth += 1
        except Exception:
            pass
        return pids

    @classmethod
    def get_process_image_path(cls, pid: int) -> Tuple[str, str]:
        """Returns (process_name, full_executable_path) for a given PID."""
        if not kernel32 or not pid:
            return "", ""
        try:
            h_proc = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not h_proc:
                return "", ""
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                full_path = buf.value
                name = os.path.basename(full_path).lower()
                kernel32.CloseHandle(h_proc)
                return name, full_path
            kernel32.CloseHandle(h_proc)
        except Exception:
            pass
        return "", ""

    @classmethod
    def is_process_running(cls) -> bool:
        """Checks if the Antigravity IDE executable is running in the Windows process table."""
        if not kernel32:
            return False
        try:
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
                return found
        except Exception:
            pass
        return False

    @classmethod
    def find_antigravity_window(cls, title_filter: str = "") -> Optional[int]:
        """
        Locates the exact HWND for Antigravity IDE window.
        Strictly excludes cmd.exe, PowerShell, File Explorer, and own processes.
        """
        if not user32:
            return None

        h_input = None
        try:
            h_input = user32.OpenInputDesktop(0, False, 0x01FF)
            if h_input:
                user32.SetThreadDesktop(h_input)
        except Exception:
            h_input = None

        blacklisted_pids = cls.get_own_process_family_pids()
        matched_hwnds: List[Tuple[int, int]] = []  # (priority, hwnd)

        def enum_cb(hwnd, lparam):
            if not (user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd)):
                return 1

            # Get PID
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in blacklisted_pids:
                return 1

            # Get process image name
            pname, _ = cls.get_process_image_path(pid.value)
            if pname in BLACK_LISTED_PROCESS_NAMES:
                return 1

            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            title = ""
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
            title_lower = title.lower()

            # Get window class
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            cls_name = class_buf.value

            # Get window rect
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top

            # Production Antigravity IDE detection
            is_antigravity_proc = any(target in pname for target in cls.PROCESS_NAMES)

            # Enforce self-exclusion on title (only for non-Antigravity processes)
            if not is_antigravity_proc and any(k in title_lower for k in EXCLUDED_WINDOW_TITLE_KEYWORDS):
                return 1
            if is_antigravity_proc:
                is_iconic = bool(user32.IsIconic(hwnd))

                # For minimized windows, rect from GetWindowRect is (-32000, -32000) with small dims (~160x30).
                # Retrieve normal restored dimensions via GetWindowPlacement
                normal_w = width
                normal_h = height
                if is_iconic:
                    wp = WINDOWPLACEMENT()
                    wp.length = ctypes.sizeof(WINDOWPLACEMENT)
                    if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                        normal_w = wp.rcNormalPosition.right - wp.rcNormalPosition.left
                        normal_h = wp.rcNormalPosition.bottom - wp.rcNormalPosition.top

                # Check minimum size: either current dimensions or normal placement if iconic
                if (width >= 300 and height >= 200) or (is_iconic and (normal_w >= 300 and normal_h >= 200 or normal_w == 0)):
                    priority = 50
                    # Electron top-level window class
                    if cls_name == "Chrome_WidgetWin_1":
                        priority += 20
                    # If window is visible and not minimized, higher priority
                    if user32.IsWindowVisible(hwnd) and not is_iconic:
                        priority += 10
                    elif is_iconic:
                        priority += 8  # Prioritize minimized top-level Antigravity window
                    matched_hwnds.append((priority, hwnd))
                    return 1

            # Title filter fallback (if specified and not blacklisted)
            if title_filter and title_filter.lower() in title_lower and ((width >= 300 and height >= 200) or user32.IsIconic(hwnd)):
                matched_hwnds.append((30, hwnd))

            return 1

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb_func = WNDENUMPROC(enum_cb)
        if h_input:
            user32.EnumDesktopWindows.argtypes = [wintypes.HANDLE, WNDENUMPROC, wintypes.LPARAM]
            user32.EnumDesktopWindows(h_input, cb_func, 0)
        else:
            user32.EnumWindows(cb_func, 0)

        if matched_hwnds:
            matched_hwnds.sort(key=lambda item: item[0], reverse=True)
            return matched_hwnds[0][1]

        return None

    @classmethod
    def is_minimized(cls, hwnd: int) -> bool:
        """Returns True if the window is currently minimized (iconic)."""
        if not hwnd or not user32:
            return False
        try:
            return bool(user32.IsIconic(hwnd))
        except Exception:
            return False

    @classmethod
    def is_foreground(cls, hwnd: int) -> bool:
        """Returns True if the window is currently in the active foreground."""
        if not hwnd or not user32:
            return False
        try:
            return user32.GetForegroundWindow() == hwnd
        except Exception:
            return False

    @classmethod
    def get_window_rect(cls, hwnd: int) -> Optional[Rect]:
        """Returns the bounding Rect of a window."""
        if not hwnd or not user32:
            return None
        try:
            rect = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return Rect(
                    x=rect.left,
                    y=rect.top,
                    width=rect.right - rect.left,
                    height=rect.bottom - rect.top,
                )
        except Exception:
            pass
        return None

    @classmethod
    def get_console_hwnd(cls) -> Optional[int]:
        """Returns the HWND of own console window."""
        if not kernel32:
            return None
        try:
            h = kernel32.GetConsoleWindow()
            return h if h else None
        except Exception:
            return None

    @classmethod
    def is_console_foreground(cls) -> bool:
        """Returns True if own console window is currently the active foreground window."""
        h_console = cls.get_console_hwnd()
        if not h_console or not user32:
            return False
        try:
            return user32.GetForegroundWindow() == h_console
        except Exception:
            return False

    @classmethod
    def minimize_console(cls) -> bool:
        """Minimizes the console window so it does not obstruct Antigravity."""
        h_console = cls.get_console_hwnd()
        if h_console and user32:
            try:
                return bool(user32.ShowWindow(h_console, 6))  # SW_MINIMIZE = 6
            except Exception:
                pass
        return False

    @classmethod
    def get_window_at_point(cls, x: int, y: int) -> Optional[int]:
        """Returns the root top-level HWND containing screen coordinate (x, y)."""
        if not user32:
            return None
        try:
            pt = wintypes.POINT(x, y)
            hwnd_at_pt = user32.WindowFromPoint(pt)
            if hwnd_at_pt:
                GA_ROOT = 2
                root_hwnd = user32.GetAncestor(hwnd_at_pt, GA_ROOT)
                return root_hwnd or hwnd_at_pt
        except Exception:
            pass
        return None

    @classmethod
    def get_console_window_rect(cls) -> Optional[Rect]:
        """Returns the bounding Rect of own console/terminal window to prevent self-clicks."""
        h_console = cls.get_console_hwnd()
        if h_console and user32 and user32.IsWindowVisible(h_console):
            return cls.get_window_rect(h_console)
        return None

    @classmethod
    def validate_click_target(
        cls,
        x: int,
        y: int,
        target_hwnd: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Validates that click coordinates:
        1. Fall strictly inside the target window's bounding box if target_hwnd is provided.
        2. Do NOT fall inside own console window when the console window is active/foreground.
           If target_hwnd is provided and in foreground (or brought to foreground), console
           overlap is allowed since the click will land on the target window covering the console.
        """
        h_console = cls.get_console_hwnd()
        fg_hwnd = user32.GetForegroundWindow() if user32 else None

        # If own console is currently in foreground and a target_hwnd is given,
        # automatically bring target_hwnd to the foreground so clicks land on Antigravity.
        if target_hwnd and h_console and fg_hwnd == h_console:
            cls.bring_to_foreground(target_hwnd)
            fg_hwnd = user32.GetForegroundWindow() if user32 else None

        target_rect = cls.get_window_rect(target_hwnd) if target_hwnd else None

        # Check target window boundary if provided
        if target_hwnd and target_rect:
            if not target_rect.contains(x, y):
                return (
                    False,
                    f"Click at ({x}, {y}) is outside target window bounds "
                    f"({target_rect.left},{target_rect.top} {target_rect.width}x{target_rect.height})! Blocked for safety.",
                )

            # Check if target_hwnd is in the foreground or directly under the cursor
            is_target_fg = cls.is_foreground(target_hwnd)
            is_target_at_pt = False
            root_at_pt = cls.get_window_at_point(x, y)
            if root_at_pt and (root_at_pt == target_hwnd):
                is_target_at_pt = True

            # If target_hwnd is in the foreground (or under cursor) and target_rect contains (x, y):
            # The click lands safely on Antigravity; DO NOT block on console_rect!
            if is_target_fg or is_target_at_pt or (h_console is None) or (fg_hwnd is not None and fg_hwnd != h_console):
                return True, "Click target coordinate valid (target window is foreground)."

        # Check console boundary for self-click prevention
        console_rect = cls.get_console_window_rect()
        if console_rect and console_rect.contains(x, y):
            # Only block if the console window itself is the foreground window,
            # or if no target_hwnd was specified.
            if not target_hwnd or cls.is_console_foreground() or (fg_hwnd and fg_hwnd == h_console):
                return (
                    False,
                    f"Click at ({x}, {y}) falls inside console window! Blocked to prevent self-clicking.",
                )

        return True, "Click target coordinate valid."

    @classmethod
    def bring_to_foreground(cls, hwnd: int) -> bool:
        """
        Safely brings ONLY the target window to the foreground.
        NEVER minimizes or touches other windows.
        If minimized, restores using WINDOWPLACEMENT to preserve maximized state (SW_MAXIMIZE or SW_RESTORE).
        """
        if not hwnd or not user32 or not kernel32:
            return False
        try:
            cls.attach_to_input_desktop()

            # Restore minimized window using WINDOWPLACEMENT to preserve maximized state
            if user32.IsIconic(hwnd):
                wp = WINDOWPLACEMENT()
                wp.length = ctypes.sizeof(WINDOWPLACEMENT)
                was_maximized = False
                if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
                    # WPF_RESTORETOMAXIMIZED = 0x0002
                    # SW_SHOWMAXIMIZED = 3
                    if (wp.flags & 0x0002) or wp.showCmd == 3:
                        was_maximized = True

                cmd = 3 if was_maximized else 9  # SW_MAXIMIZE=3, SW_RESTORE=9
                user32.ShowWindow(hwnd, cmd)
                user32.ShowWindowAsync(hwnd, cmd)
            else:
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                user32.ShowWindowAsync(hwnd, 5)

            # Unlock foreground lock via null Alt key tap
            VK_MENU = 0x12
            KEYEVENTF_KEYUP = 0x0002
            try:
                user32.keybd_event(VK_MENU, 0, 0, 0)
                user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

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
    def check_and_foreground(cls, title_filter: str = "") -> Tuple[bool, str, Optional[int]]:
        """
        Verifies if Antigravity is open/running and brings it to foreground if minimized or in background.
        Returns: (is_ready, message, hwnd)
        """
        proc_running = cls.is_process_running()
        hwnd = cls.find_antigravity_window(title_filter=title_filter)

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
                cls.attach_to_input_desktop()
                return True, "Antigravity active in foreground.", hwnd

        if proc_running:
            return True, "Antigravity process is active.", None

        return False, "Target window not found.", None
