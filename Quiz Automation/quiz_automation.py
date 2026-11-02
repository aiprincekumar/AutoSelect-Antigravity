#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quiz Keyboard Automation Subsystem
==================================
Workspace: AutoSelect-Commander
Target: Antigravity 2.0 Interactive Prompt / Multi-Question Quiz Mode

Executes a deterministic multi-question shortcut loop based on the detected
question count (N questions).

Keystroke Loop Algorithm:
For q = 1 to N:
  - Ctrl + L    : Focus chat prompt input
  - Shift + Tab : Shift focus backward into radio option group
  - 1           : Select Option 1 (or configured option for that question)
  - If q == N   : Press Enter (Submit batch response)
  - If q < N    : SUPPRESS ENTER! Settle delay and advance to question q+1

Zero External Dependencies:
Pure Python 3 standard library + Windows ctypes SendInput with scancode mapping.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Safe stdout configuration for Windows consoles
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
logger = logging.getLogger("QuizAutomation")

IS_WINDOWS = sys.platform == "win32"
DEFAULT_TARGET_WINDOW = "Antigravity,Antigravity 2.0,Harness,AutoSelect-Commander"

# Virtual Key Codes
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12       # Alt
VK_RETURN = 0x0D     # Enter
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

SW_RESTORE = 9
SW_MAXIMIZE = 3
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040
ASFW_ANY = -1

INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

DISQUALIFIED_BROWSER_PROCS = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "vivaldi.exe",
}

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

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

    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.MapVirtualKeyW.restype = wintypes.UINT
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.restype = wintypes.BOOL
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL
    user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWPLACEMENT)]
    user32.GetWindowPlacement.restype = wintypes.BOOL
    user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
    user32.AllowSetForegroundWindow.restype = wintypes.BOOL


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


def send_key_event(vk_code: int, key_up: bool = False, use_scancode: bool = True) -> bool:
    """Send a single key press or release event via SendInput."""
    if not IS_WINDOWS:
        return False

    scan = user32.MapVirtualKeyW(vk_code, 0)
    dw_flags = KEYEVENTF_KEYUP if key_up else KEYEVENTF_KEYDOWN
    if use_scancode and scan != 0:
        dw_flags |= KEYEVENTF_SCANCODE

    ki = KEYBDINPUT(
        wVk=vk_code,
        wScan=scan,
        dwFlags=dw_flags,
        time=0,
        dwExtraInfo=None,
    )
    inp = INPUT(type=INPUT_KEYBOARD, union=_INPUT_UNION(ki=ki))
    res = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    return res == 1


def send_single_key(vk_code: int, hold_delay: float = 0.05) -> bool:
    """Press and release a single key with dwell delay."""
    if not IS_WINDOWS:
        return False
    send_key_event(vk_code, key_up=False)
    time.sleep(hold_delay)
    send_key_event(vk_code, key_up=True)
    return True


def send_key_combo(vk_codes: List[int], hold_delay: float = 0.05) -> bool:
    """Press a sequence of keys down in order, wait, and release in reverse order."""
    if not IS_WINDOWS:
        return False
    for vk in vk_codes:
        send_key_event(vk, key_up=False)
        time.sleep(0.01)

    time.sleep(hold_delay)

    for vk in reversed(vk_codes):
        send_key_event(vk, key_up=True)
        time.sleep(0.01)
    return True


def find_target_window(target_string: str) -> Optional[Tuple[int, str]]:
    """Scan and select target window matching comma-separated token list."""
    if not IS_WINDOWS:
        return None

    candidates = []
    target_tokens = [t.strip().lower() for t in target_string.split(",") if t.strip()]
    current_pid = kernel32.GetCurrentProcessId()

    def enum_proc(hwnd, lparam):
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip()

        if not title:
            return True

        lp_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
        if lp_pid.value == current_pid:
            return True

        title_lower = title.lower()
        for token in target_tokens:
            if token in title_lower:
                candidates.append((hwnd, title))
                break

        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    cb = WNDENUMPROC(enum_proc)
    user32.EnumWindows(cb, 0)

    if candidates:
        return candidates[0]
    return None


def get_active_window_title() -> str:
    """Get the window title of the current foreground window."""
    if not IS_WINDOWS:
        return "<Non-Windows OS>"
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "<No Active Window>"
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return "<Untitled Window>"
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value


def get_process_name_for_hwnd(hwnd: int) -> str:
    """Get the executable process name for a given HWND."""
    if not IS_WINDOWS or not hwnd:
        return "unknown"
    lp_pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
    pid = lp_pid.value
    if pid == 0:
        return "unknown"

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h_proc:
        return "unknown"

    try:
        buf_size = wintypes.DWORD(260)
        buf = ctypes.create_unicode_buffer(260)
        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(buf_size)):
            return Path(buf.value).name.lower()
    finally:
        kernel32.CloseHandle(h_proc)

    return "unknown"


def restore_and_focus_window(hwnd: int, maximize: bool = True) -> bool:
    """
    Restore (if minimized), optionally maximize, and focus target window
    using robust Win32 thread attachment and Alt-pulse bypass.
    """
    if not IS_WINDOWS or not hwnd:
        return False

    # 1. Restore if minimized
    if user32.IsIconic(hwnd):
        logger.info(f"Window is minimized. Restoring (SW_RESTORE)...")
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.15)

    # 2. Maximize if requested
    if maximize:
        wp = WINDOWPLACEMENT()
        wp.length = ctypes.sizeof(WINDOWPLACEMENT)
        if user32.GetWindowPlacement(hwnd, ctypes.byref(wp)):
            if wp.showCmd != SW_MAXIMIZE:
                logger.info("Maximizing window to full screen (SW_MAXIMIZE)...")
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                time.sleep(0.15)

    # 3. Focus Bypass
    fg_hwnd = user32.GetForegroundWindow()
    if fg_hwnd != hwnd:
        fg_pid = wintypes.DWORD()
        fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(fg_pid))
        cur_tid = kernel32.GetCurrentThreadId()

        attached = False
        if fg_tid != 0 and fg_tid != cur_tid:
            attached = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))

        try:
            # Pulse Alt key to grant SetForegroundWindow permission
            send_key_event(VK_MENU, key_up=False)
            send_key_event(VK_MENU, key_up=True)
            user32.AllowSetForegroundWindow(ASFW_ANY)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            if attached:
                user32.AttachThreadInput(cur_tid, fg_tid, False)

    return True


class QuizAutomator:
    """
    Multi-question shortcut automation engine.
    """

    def __init__(
        self,
        questions: int = 1,
        options: Optional[List[str]] = None,
        dry_run: bool = False,
        skip_enter: bool = False,
        step_delay: float = 0.35,
        hold_delay: float = 0.05,
        settle_delay: float = 0.50,
        target_window: str = DEFAULT_TARGET_WINDOW,
        auto_focus: bool = True,
        auto_maximize: bool = True
    ):
        self.questions = max(1, questions)
        self.dry_run = dry_run
        self.skip_enter = skip_enter
        self.step_delay = max(0.05, step_delay)
        self.hold_delay = max(0.01, hold_delay)
        self.settle_delay = max(0.0, settle_delay)
        self.target_window = target_window
        self.auto_focus = auto_focus
        self.auto_maximize = auto_maximize

        # Resolve options list for all questions
        raw_options = options or ["1"]
        if len(raw_options) == 1 and self.questions > 1:
            self.options = raw_options * self.questions
        elif len(raw_options) < self.questions:
            self.options = raw_options + ["1"] * (self.questions - len(raw_options))
        else:
            self.options = raw_options[:self.questions]

    @classmethod
    def load_question_count_from_file(cls, filepath: Optional[str] = None) -> int:
        """
        Locate and load detected question count from question_count.json.
        Searches candidate locations if specific path not given.
        """
        if filepath:
            p = Path(filepath)
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        count = int(data.get("question_count", 1))
                        if count >= 1:
                            logger.info(f"[CONFIG] Read question count={count} from explicit file: {p.resolve()}")
                            return count
                except Exception as e:
                    logger.warning(f"Failed to read explicit file {p}: {e}")
            else:
                logger.warning(f"[CONFIG] Explicit file not found: {p.resolve()}")
            return 1

        # Search candidate locations if no explicit file was provided
        candidate_paths = [
            Path("question_count.json"),
            Path("Question Detection/question_count.json"),
            Path("../Question Detection/question_count.json"),
            Path(__file__).resolve().parent / "question_count.json",
            Path(__file__).resolve().parent.parent / "question_count.json",
            Path(__file__).resolve().parent.parent / "Question Detection" / "question_count.json",
        ]

        for p in candidate_paths:
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        count = int(data.get("question_count", 1))
                        if count >= 1:
                            logger.info(f"[CONFIG] Read question count={count} from: {p.resolve()}")
                            return count
                except Exception as e:
                    logger.warning(f"Failed to read {p}: {e}")

        logger.info("[CONFIG] No valid question_count.json found. Defaulting to 1 question.")
        return 1

    def prepare_window(self) -> bool:
        """Find and prepare target window (restore, maximize, focus)."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Simulating window preparation for: '{self.target_window}'")
            return True

        target_info = find_target_window(self.target_window)
        if not target_info:
            logger.warning(f"Target window matching '{self.target_window}' not found. Continuing with active window...")
            return False

        hwnd, title = target_info
        logger.info(f"Target window identified: HWND=0x{hwnd:x}, Title='{title}'")

        if self.auto_focus:
            restore_and_focus_window(hwnd, maximize=self.auto_maximize)
            time.sleep(self.settle_delay)

        # Check safety: Disqualify external browser processes
        fg_hwnd = user32.GetForegroundWindow() if IS_WINDOWS else 0
        proc_name = get_process_name_for_hwnd(fg_hwnd)
        if proc_name in DISQUALIFIED_BROWSER_PROCS:
            logger.error(
                f"[SAFETY ABORT] Active window belongs to external browser '{proc_name}'. "
                f"Halting automation to prevent unexpected browser keystrokes."
            )
            return False

        return True

    def _execute_keystroke(self, label: str, action_fn, simulation_msg: str):
        """Execute keystroke action with dry-run support and step delay."""
        logger.info(f"  --> {label}")
        if self.dry_run:
            logger.info(f"      [DRY-RUN] {simulation_msg}")
        else:
            action_fn()
        time.sleep(self.step_delay)

    def execute(self) -> bool:
        """
        Execute the multi-question keystroke loop:
        For q = 1 to N:
          1. Ctrl + L (focus input)
          2. Shift + Tab (reverse tab to option)
          3. Option Key (e.g. '1')
          4. If q == N: Enter (Submit)
             If q < N: SUPPRESS ENTER! Settle pause and advance.
        """
        logger.info("=" * 68)
        logger.info(f"  [*] INITIATING QUIZ AUTOMATION LOOP: {self.questions} QUESTION(S)")
        logger.info(f"  [*] Option Choices: {self.options}")
        logger.info(f"  [*] Dry Run Mode:   {self.dry_run}")
        logger.info("=" * 68)

        # Window preparation
        self.prepare_window()

        active_title = get_active_window_title()
        logger.info(f"Active Foreground Window: '{active_title}'")

        for q_idx in range(1, self.questions + 1):
            opt = self.options[q_idx - 1]
            is_last = (q_idx == self.questions)

            logger.info(f"\n[QUESTION {q_idx}/{self.questions}] (Selected Option: '{opt}')")

            # Step A: Focus chat input
            self._execute_keystroke(
                f"[Q{q_idx}] Step 1: Press [Ctrl + L] (Focus chat prompt input)",
                lambda: send_key_combo([VK_CONTROL, VK_L], hold_delay=self.hold_delay),
                "Send Key Combo: Ctrl + L"
            )

            # Step B: Reverse tab to option
            self._execute_keystroke(
                f"[Q{q_idx}] Step 2: Press [Shift + Tab] (Move backward to options)",
                lambda: send_key_combo([VK_SHIFT, VK_TAB], hold_delay=self.hold_delay),
                "Send Key Combo: Shift + Tab"
            )

            # Step C: Select option
            vk_opt = get_option_vk(opt)
            self._execute_keystroke(
                f"[Q{q_idx}] Step 3: Press [{opt}] (Select Option {opt})",
                lambda: send_single_key(vk_opt, hold_delay=self.hold_delay),
                f"Send Single Key: '{opt}' (VK=0x{vk_opt:02X})"
            )

            # Step D: Enter Gate
            if is_last:
                if not self.skip_enter:
                    self._execute_keystroke(
                        f"[Q{q_idx}] Step 4: Press [Enter] (Submit ALL answers on final question)",
                        lambda: send_single_key(VK_RETURN, hold_delay=self.hold_delay),
                        "Send Single Key: Enter (VK_RETURN)"
                    )
                else:
                    logger.info(f"[Q{q_idx}] Step 4: [SKIPPED ENTER] Enter suppressed per --skip-enter flag.")
            else:
                logger.info(
                    f"[Q{q_idx}] Step 4: [SUPPRESS ENTER] Intermediate question {q_idx}/{self.questions} complete. "
                    f"Advancing to Question {q_idx + 1}..."
                )
                time.sleep(self.settle_delay)

        logger.info("\n" + "=" * 68)
        logger.info("  [SUCCESS] Multi-question automation loop completed successfully!")
        logger.info("=" * 68 + "\n")
        return True


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for Quiz Automation."""
    parser = argparse.ArgumentParser(
        description="Antigravity 2.0 Quiz Automation - Multi-question shortcut sequence execution",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-q", "--questions",
        type=str,
        default="auto",
        help="Number of questions (integer e.g. 1, 2, 3 or 'auto' to read question_count.json)"
    )
    parser.add_argument(
        "-o", "--options",
        type=str,
        default="1",
        help="Comma-separated option keys per question (e.g. '1' or '1,2,1')"
    )
    parser.add_argument(
        "-i", "--input-file",
        type=str,
        default=None,
        help="Path to question_count.json to read count from"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate keystroke execution without physically sending events"
    )
    parser.add_argument(
        "--skip-enter",
        action="store_true",
        help="Do not press Enter even on the final question"
    )
    parser.add_argument(
        "-t", "--target",
        type=str,
        default=DEFAULT_TARGET_WINDOW,
        help="Target window title/process tokens (comma-separated)"
    )
    parser.add_argument(
        "--no-maximize",
        action="store_true",
        help="Do not automatically maximize the target window"
    )
    parser.add_argument(
        "--no-focus",
        action="store_true",
        help="Do not bring target window to foreground"
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.35,
        help="Delay in seconds between keystroke steps"
    )
    parser.add_argument(
        "--hold-delay",
        type=float,
        default=0.05,
        help="Duration key is held down in seconds"
    )
    parser.add_argument(
        "--settle-delay",
        type=float,
        default=0.50,
        help="Delay in seconds between questions for UI settling"
    )
    parser.add_argument(
        "-c", "--countdown",
        type=int,
        default=0,
        help="Countdown in seconds before beginning automation"
    )

    return parser.parse_args()


def main() -> int:
    """CLI Entrypoint."""
    args = parse_arguments()

    # Determine question count
    if str(args.questions).lower() == "auto":
        q_count = QuizAutomator.load_question_count_from_file(args.input_file)
    else:
        try:
            q_count = int(args.questions)
        except ValueError:
            logger.error(f"Invalid --questions value '{args.questions}'. Expected integer or 'auto'.")
            return 1

    # Parse options
    options_list = [opt.strip() for opt in args.options.split(",") if opt.strip()]

    # Countdown if requested
    if args.countdown > 0:
        logger.info(f"Starting in {args.countdown} seconds (switch to Antigravity if desired)...")
        for s in range(args.countdown, 0, -1):
            print(f"  Launching in {s}s...", end="\r", flush=True)
            time.sleep(1.0)
        print(" " * 30, end="\r", flush=True)

    automator = QuizAutomator(
        questions=q_count,
        options=options_list,
        dry_run=args.dry_run,
        skip_enter=args.skip_enter,
        step_delay=args.step_delay,
        hold_delay=args.hold_delay,
        settle_delay=args.settle_delay,
        target_window=args.target,
        auto_focus=not args.no_focus,
        auto_maximize=not args.no_maximize
    )

    success = automator.execute()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
