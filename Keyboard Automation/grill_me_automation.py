#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grill Me Automation - Hybrid Keyboard & Focus Automation Suite
=============================================================
Workspace: AutoSelect-Commander
Target: Antigravity / IDE / Browser / Terminal Chat Window
Workflow:
  1. User triggers automation script (via CLI, .bat, or .ps1).
  2. Countdown timer runs (default 5s) allowing user to switch to or click the target chat window.
  3. Script detects and logs the active foreground window.
  4. Script executes the sequence:
     [Step 1] Ctrl + L    -> Focus chat input prompt
     [Step 2] Shift + Tab -> Move focus backward to option buttons
     [Step 3] 1           -> Select Option 1 (or configured option)
     [Step 4] Enter       -> Submit / confirm selection
  5. Provides clean terminal logs, error recovery, and optional loop/repeat support.

Supports zero external dependencies via native Windows ctypes (SendInput / keybd_event)
with automatic fallback/interop for PyAutoGUI if installed.
"""

import os
import sys
import time
import argparse
import logging
from typing import Optional, List, Tuple

# Safe stdout encoding configuration for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger("GrillMeAutomation")

# ============================================================================
# Windows Native ctypes Input Simulation Engine (Zero Dependency)
# ============================================================================
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Virtual-Key codes
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_RETURN = 0x0D
    VK_TAB = 0x09
    VK_L = 0x4C
    VK_0 = 0x30
    VK_1 = 0x31
    VK_2 = 0x32
    VK_3 = 0x33
    VK_4 = 0x34
    VK_5 = 0x35
    VK_6 = 0x36
    VK_7 = 0x37
    VK_8 = 0x38
    VK_9 = 0x39
    VK_MENU = 0x12  # Alt key (used for OS foreground lock release)

    # ShowWindow commands
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_MAXIMIZE = 3
    SW_SHOWNOACTIVATE = 4
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_SHOWMINNOACTIVE = 7
    SW_SHOWNA = 8
    SW_RESTORE = 9
    SW_SHOWDEFAULT = 10

    # RECT structure for window geometry
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    # SendInput constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_EXTENDEDKEY = 0x0001

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", wintypes.DWORD),
            ("union", _INPUT_UNION),
        ]

    # Function prototypes
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.MapVirtualKeyW.restype = wintypes.UINT

    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL

    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.IsZoomed.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.restype = wintypes.BOOL

    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL

    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND

    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL

    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL

    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    kernel32.GetConsoleWindow.argtypes = []
    kernel32.GetConsoleWindow.restype = wintypes.HWND

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL

    def get_active_window_title() -> str:
        """Get the title of the current foreground active window."""
        try:
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "<No Active Window>"
            buf = ctypes.create_unicode_buffer(512)
            length = user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip() if length > 0 else f"<Window hwnd: {hex(hwnd)}>"
            return title
        except Exception as e:
            return f"<Detection Error: {e}>"

    def _send_key_event(vk_code: int, key_up: bool = False, use_scancode: bool = True) -> bool:
        """Send a single key press or release event via SendInput."""
        try:
            scan = user32.MapVirtualKeyW(vk_code, 0)
            flags = KEYEVENTF_KEYUP if key_up else KEYEVENTF_KEYDOWN
            if use_scancode and scan:
                flags |= KEYEVENTF_SCANCODE

            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = 0 if (use_scancode and scan) else vk_code
            inp.union.ki.wScan = scan if use_scancode else 0
            inp.union.ki.dwFlags = flags
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None

            res = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            if res != 1:
                # Fallback to keybd_event if SendInput failed
                flags_legacy = KEYEVENTF_KEYUP if key_up else 0
                user32.keybd_event(vk_code, scan, flags_legacy, 0)
            return True
        except Exception as ex:
            logger.warning(f"Fallback keybd_event on error: {ex}")
            try:
                flags_legacy = KEYEVENTF_KEYUP if key_up else 0
                user32.keybd_event(vk_code, 0, flags_legacy, 0)
                return True
            except Exception as ex2:
                logger.error(f"Failed to send key event vk={vk_code}: {ex2}")
                return False

    def send_key_combo(keys: List[int], hold_delay: float = 0.05) -> bool:
        """Press down a sequence of keys, hold briefly, then release in reverse order."""
        # Press all keys in order
        for key in keys:
            _send_key_event(key, key_up=False)
            time.sleep(0.01)
        time.sleep(hold_delay)
        # Release all keys in reverse order
        for key in reversed(keys):
            _send_key_event(key, key_up=True)
            time.sleep(0.01)
        return True

    def send_single_key(key: int, hold_delay: float = 0.05) -> bool:
        """Press and release a single key."""
        return send_key_combo([key], hold_delay=hold_delay)

    # ------------------------------------------------------------------------
    # Window Auto-Targeting, Geometry, and Focus Subsystem (Win32)
    # ------------------------------------------------------------------------
    def get_window_info(hwnd: int) -> dict:
        """Retrieve comprehensive window state, visibility, and geometry info."""
        if not hwnd or not user32.IsWindow(hwnd):
            return {"hwnd": hwnd, "title": "", "exists": False, "visible": False, "minimized": False, "maximized": False, "rect": (0, 0, 0, 0), "width": 0, "height": 0}
        try:
            visible = bool(user32.IsWindowVisible(hwnd))
            iconic = bool(user32.IsIconic(hwnd))
            zoomed = bool(user32.IsZoomed(hwnd))
            buf = ctypes.create_unicode_buffer(512)
            length = user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip() if length > 0 else ""
            rect = RECT()
            rect_ok = bool(user32.GetWindowRect(hwnd, ctypes.byref(rect)))
            return {
                "hwnd": hwnd,
                "title": title,
                "exists": True,
                "visible": visible,
                "minimized": iconic,
                "maximized": zoomed,
                "rect": (rect.left, rect.top, rect.right, rect.bottom) if rect_ok else (0, 0, 0, 0),
                "width": (rect.right - rect.left) if rect_ok else 0,
                "height": (rect.bottom - rect.top) if rect_ok else 0,
            }
        except Exception as e:
            return {"hwnd": hwnd, "title": "", "exists": False, "visible": False, "minimized": False, "maximized": False, "rect": (0, 0, 0, 0), "width": 0, "height": 0, "error": str(e)}

    def find_windows_by_title(keywords: List[str], exclude_console: bool = True) -> List[Tuple[int, str]]:
        """
        Enumerate all visible top-level windows whose title contains any keyword (case-insensitive).
        Safeguarded to exclude the runner's own console window.
        """
        matches: List[Tuple[int, str]] = []
        console_hwnd = kernel32.GetConsoleWindow() if exclude_console else 0

        def enum_cb(hwnd, lparam):
            if exclude_console and console_hwnd and hwnd == console_hwnd:
                return True
            try:
                if user32.IsWindowVisible(hwnd):
                    buf = ctypes.create_unicode_buffer(512)
                    length = user32.GetWindowTextW(hwnd, buf, 512)
                    if length > 0:
                        title = buf.value.strip()
                        title_lower = title.lower()
                        for kw in keywords:
                            if kw.lower() in title_lower:
                                matches.append((hwnd, title))
                                break
            except Exception:
                pass
            return True

        cb = WNDENUMPROC(enum_cb)
        user32.EnumWindows(cb, 0)
        return matches

    def select_target_window(target_keyword: str, exclude_terms: Optional[List[str]] = None) -> Optional[Tuple[int, str]]:
        """
        Search and score visible top-level windows to identify the best match for the target keyword.
        Prioritizes exact/strong matches and de-prioritizes terminal/runner windows.
        """
        keywords = [target_keyword] if target_keyword else ["Antigravity", "antigravity"]
        candidates = find_windows_by_title(keywords, exclude_console=True)
        if not candidates:
            return None

        default_excludes = ["grill_me", "run_grill_me", "test_grill_me", "powershell", "cmd.exe"]
        excludes = default_excludes + (exclude_terms or [])

        scored: List[Tuple[int, int, str]] = []  # (score, hwnd, title)
        kw_primary = target_keyword.lower() if target_keyword else "antigravity"

        for hwnd, title in candidates:
            t_low = title.lower()
            score = 0
            if t_low == kw_primary:
                score += 100
            elif t_low.startswith(kw_primary):
                score += 80
            elif kw_primary in t_low:
                score += 50

            # Penalize if it contains runner/terminal terms and the keyword isn't specifically that runner
            for ex in excludes:
                if ex.lower() in t_low and kw_primary not in ex.lower():
                    score -= 40

            # Prefer non-iconic and already zoomed windows
            try:
                if not user32.IsIconic(hwnd):
                    score += 10
                if user32.IsZoomed(hwnd):
                    score += 5
            except Exception:
                pass

            scored.append((score, hwnd, title))

        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] > 0:
            return (scored[0][1], scored[0][2])
        return candidates[0] if candidates else None

    def ensure_window_on_screen(
        hwnd: int,
        auto_maximize: bool = True,
        auto_focus: bool = True,
        settle_delay: float = 0.5
    ) -> bool:
        """
        Ensures the target window is restored if minimized, maximized to full-screen
        (if requested), and brought to foreground focus with verified geometry.
        """
        if not hwnd or not user32.IsWindow(hwnd):
            logger.error(f"Invalid window handle: {hex(hwnd) if hwnd else '0'}")
            return False

        info = get_window_info(hwnd)
        logger.info(f"Target Window Found: '{info['title']}' (HWND: {hex(hwnd)})")
        logger.info(f"Initial State: Minimized={'YES' if info['minimized'] else 'NO'}, Maximized={'YES' if info['maximized'] else 'NO'}, Dimensions={info['width']}x{info['height']}")

        try:
            # Step 1: Check if minimized. If minimized, restore window.
            if info['minimized']:
                logger.info("Target window is minimized. Restoring window state...")
                user32.ShowWindow(hwnd, SW_RESTORE)
                time.sleep(0.08)

            # Step 2: Check if maximized. If not maximized and auto_maximize requested, maximize.
            if auto_maximize:
                if not user32.IsZoomed(hwnd):
                    logger.info("Target window is not maximized. Maximizing to full screen...")
                    user32.ShowWindow(hwnd, SW_MAXIMIZE)
                    time.sleep(0.08)
                else:
                    logger.info("Target window is already maximized.")
            else:
                if not user32.IsWindowVisible(hwnd) or info['minimized']:
                    user32.ShowWindow(hwnd, SW_SHOW)
                    time.sleep(0.05)

            # Step 3: Bring to Foreground & Focus
            if auto_focus:
                fg_hwnd = user32.GetForegroundWindow()
                if fg_hwnd != hwnd:
                    logger.info("Bringing target window to foreground focus...")
                    cur_thread_id = kernel32.GetCurrentThreadId()
                    fg_thread_id = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
                    target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)

                    attached_fg = False
                    attached_target = False
                    if fg_thread_id and fg_thread_id != cur_thread_id:
                        attached_fg = bool(user32.AttachThreadInput(cur_thread_id, fg_thread_id, True))
                    if target_thread_id and target_thread_id != cur_thread_id:
                        attached_target = bool(user32.AttachThreadInput(cur_thread_id, target_thread_id, True))

                    try:
                        # Windows Foreground Lock Bypass: Simulate Alt keystroke
                        _send_key_event(VK_MENU, key_up=False)
                        _send_key_event(VK_MENU, key_up=True)

                        user32.ShowWindow(hwnd, SW_SHOW)
                        user32.BringWindowToTop(hwnd)
                        user32.SetForegroundWindow(hwnd)
                        user32.SetFocus(hwnd)
                    finally:
                        if attached_fg:
                            user32.AttachThreadInput(cur_thread_id, fg_thread_id, False)
                        if attached_target:
                            user32.AttachThreadInput(cur_thread_id, target_thread_id, False)

            # Step 4: Settling delay for UI rendering
            if settle_delay > 0:
                time.sleep(settle_delay)

            # Step 5: Post-condition verification
            post_info = get_window_info(hwnd)
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
    # Non-Windows fallback (informational)
    def get_active_window_title() -> str:
        return "<Platform Not Windows>"

    def send_key_combo(keys: List[int], hold_delay: float = 0.05) -> bool:
        logger.error("Native ctypes SendInput is only supported on Windows.")
        return False

    def send_single_key(key: int, hold_delay: float = 0.05) -> bool:
        logger.error("Native ctypes SendInput is only supported on Windows.")
        return False

    def get_window_info(hwnd: int) -> dict:
        return {"hwnd": hwnd, "title": "<Non-Windows>", "exists": False, "visible": False, "minimized": False, "maximized": False, "rect": (0, 0, 0, 0), "width": 0, "height": 0}

    def find_windows_by_title(keywords: List[str], exclude_console: bool = True) -> List[Tuple[int, str]]:
        return []

    def select_target_window(target_keyword: str, exclude_terms: Optional[List[str]] = None) -> Optional[Tuple[int, str]]:
        return None

    def ensure_window_on_screen(hwnd: int, auto_maximize: bool = True, auto_focus: bool = True, settle_delay: float = 0.5) -> bool:
        return False

# ============================================================================
# Optional PyAutoGUI Engine
# ============================================================================
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None

# ============================================================================
# Key Mapping Helpers
# ============================================================================
def get_option_vk(option_char: str) -> int:
    """Map string option ('1', '2', etc.) to Virtual Key code."""
    opt = str(option_char).strip().lower()
    if opt == "1":
        return VK_1
    elif opt == "2":
        return VK_2
    elif opt == "3":
        return VK_3
    elif opt == "4":
        return VK_4
    elif opt == "5":
        return VK_5
    elif opt == "6":
        return VK_6
    elif opt == "7":
        return VK_7
    elif opt == "8":
        return VK_8
    elif opt == "9":
        return VK_9
    elif opt == "0":
        return VK_0
    elif len(opt) == 1 and opt.isalpha():
        return ord(opt.upper())
    return VK_1


# ============================================================================
# Automation Sequence Runner
# ============================================================================
class GrillMeAutomator:
    """
    Automates the 'Grill Me' keyboard selection sequence with intelligent window auto-targeting:
    1. Scan & identify target window (e.g. Antigravity)
    2. Check minimized state -> Restore window
    3. Check maximized state -> Maximize to full screen
    4. Robust foreground focus bypass & geometry verification
    5. Settle delay (default 500ms) for UI rendering
    6. Execute sequence:
       - Ctrl + L    -> Focus chat input
       - Shift + Tab -> Shift focus to option select buttons
       - Option key  -> Select option (default '1')
       - Enter       -> Submit confirmation
    """

    def __init__(
        self,
        engine: str = "auto",
        step_delay: float = 0.35,
        hold_delay: float = 0.05,
        option: str = "1",
        skip_ctrl_l: bool = False,
        skip_enter: bool = False,
        dry_run: bool = False,
        target_window: str = "Antigravity",
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
        self.target_window = target_window
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
        Locates target window by title keyword, restores if minimized,
        maximizes to full screen (if requested), and sets foreground focus.
        """
        if not IS_WINDOWS:
            logger.info("Window auto-focus/maximize is only available on Windows.")
            return False

        if not self.auto_focus and not self.auto_maximize:
            logger.info("Window auto-focus and auto-maximize are disabled by user configuration.")
            return True

        logger.info(f"Scanning for target window matching keyword: '{self.target_window}'...")
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
        logger.info(f"[+] Target window detected: '{title}' (HWND: {hex(hwnd)})")

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
                # Truncate title if too long
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


# ============================================================================
# CLI Entry Point
# ============================================================================
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Grill Me Keyboard Automation Suite for Antigravity & Chat Interfaces.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-t", "--target-window",
        type=str,
        default="Antigravity",
        help="Keyword to identify target window (e.g. 'Antigravity') for auto-focus/maximize."
    )
    parser.add_argument(
        "--auto-focus",
        dest="auto_focus",
        action="store_true",
        default=True,
        help="Automatically bring target window to foreground before injection (default: True)."
    )
    parser.add_argument(
        "--no-auto-focus",
        dest="auto_focus",
        action="store_false",
        help="Disable automatic foreground window focusing."
    )
    parser.add_argument(
        "--auto-maximize",
        dest="auto_maximize",
        action="store_true",
        default=True,
        help="Automatically restore and maximize target window to full screen (default: True)."
    )
    parser.add_argument(
        "--no-auto-maximize",
        dest="auto_maximize",
        action="store_false",
        help="Disable automatic window maximization."
    )
    parser.add_argument(
        "--settle-delay",
        type=float,
        default=0.5,
        help="Delay in seconds after window focus/maximize to allow UI rendering to settle."
    )
    parser.add_argument(
        "-c", "--countdown",
        type=int,
        default=5,
        help="Seconds of countdown to focus the target chat window before keystrokes are sent."
    )
    parser.add_argument(
        "-d", "--step-delay",
        type=float,
        default=0.35,
        help="Delay in seconds between keystroke steps (e.g. 0.35 = 350ms)."
    )
    parser.add_argument(
        "--hold-delay",
        type=float,
        default=0.05,
        help="Duration in seconds keys are held down before releasing."
    )
    parser.add_argument(
        "-o", "--option",
        type=str,
        default="1",
        help="The option number or character to choose (default: 1)."
    )
    parser.add_argument(
        "--skip-ctrl-l",
        action="store_true",
        help="Skip sending Ctrl + L (if chat input is already focused)."
    )
    parser.add_argument(
        "--skip-enter",
        action="store_true",
        help="Skip sending Enter (leaves selection active without auto-submitting)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without sending actual keyboard events."
    )
    parser.add_argument(
        "-e", "--engine",
        choices=["auto", "ctypes", "pyautogui"],
        default="auto",
        help="Input simulation engine to use."
    )
    parser.add_argument(
        "-r", "--repeat",
        type=int,
        default=1,
        help="Number of times to run the sequence."
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=2.0,
        help="Interval between repeats in seconds."
    )
    parser.add_argument(
        "--no-countdown",
        action="store_true",
        help="Execute immediately without countdown."
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("\n" + "=" * 65)
    print("      [*] AutoSelect-Commander: Grill Me Keyboard Automation")
    print("=" * 65)
    print(f" Target Window: '{args.target_window}' (Focus: {args.auto_focus}, Maximize: {args.auto_maximize})")
    print(f" Engine      : {args.engine.upper()} (Zero-dependency ctypes: {IS_WINDOWS})")
    print(f" Sequence    : {'Ctrl+L -> ' if not args.skip_ctrl_l else ''}Shift+Tab -> Option '{args.option}' -> {'Enter' if not args.skip_enter else '[No Enter]'}")
    print(f" Step Delay  : {int(args.step_delay * 1000)}ms | Settle Delay: {int(args.settle_delay * 1000)}ms")
    print(f" Mode        : {'DRY RUN (Simulated)' if args.dry_run else 'ACTIVE INJECTION'}")
    print("=" * 65 + "\n")

    automator = GrillMeAutomator(
        engine=args.engine,
        step_delay=args.step_delay,
        hold_delay=args.hold_delay,
        option=args.option,
        skip_ctrl_l=args.skip_ctrl_l,
        skip_enter=args.skip_enter,
        dry_run=args.dry_run,
        target_window=args.target_window,
        auto_focus=args.auto_focus,
        auto_maximize=args.auto_maximize,
        settle_delay=args.settle_delay,
    )

    if not args.no_countdown and args.countdown > 0:
        automator.run_countdown(seconds=args.countdown)

    total_runs = max(1, args.repeat)
    success_count = 0

    for iteration in range(1, total_runs + 1):
        if total_runs > 1:
            print(f"\n--- Iteration {iteration} of {total_runs} ---")
        
        ok = automator.execute()
        if ok:
            success_count += 1

        if iteration < total_runs and args.interval > 0:
            logger.info(f"Waiting {args.interval}s before next iteration...")
            time.sleep(args.interval)

    print("\n" + "=" * 65)
    print(f"  [+] Execution Finished: {success_count}/{total_runs} runs successful.")
    print("=" * 65 + "\n")

    return 0 if success_count == total_runs else 1


if __name__ == "__main__":
    sys.exit(main())
