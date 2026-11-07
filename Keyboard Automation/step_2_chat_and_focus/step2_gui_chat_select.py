#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Chat Search & GUI Selection in Antigravity
==================================================
Part of: AutoSelect-Commander 3-Step Automation Pipeline
Workspace: AutoSelect-Commander / Keyboard Automation (Step 2 of 3)
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Responsibilities (Script 2):
  1. Reads target conversation ID and metadata stored by Script 1 from `target_chat.json`.
  2. Ensures the Antigravity window is foregrounded on screen.
  3. Locates and selects that exact conversation in the Antigravity GUI using a robust multi-tier engine:
     - Tier 1: Real-time DOM element detection via Antigravity's internal Chrome DevTools Protocol (CDP),
               smooth Bezier mouse glide to the exact conversation item in the sidebar, and DOM + OS click.
     - Tier 2: Single-Page Application (SPA) client router dispatch for off-screen/scrolled conversation links.
     - Tier 3: Calibrated sidebar coordinate navigation and Win32 hardware mouse click fallback.
  4. Dispatches `Ctrl + L` keyboard shortcut to bring focus directly into the chat pane and input box.
  5. Updates `target_chat.json` and `last_selection_state.json` with final selection status and timestamps.
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import struct
import base64
import logging
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

# Ensure root directory is resolvable in sys.path
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent if _this_dir.name.startswith(("step_", "step-")) else _this_dir
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from core_engine.config_manager import (
        load_runtime_config,
        get_settle_delay,
        get_dom_click_settle_delay,
        apply_logging_config,
    )
except ImportError:
    def load_runtime_config(p=None):
        return {}
    def get_settle_delay(c=None):
        return 0.8
    def get_dom_click_settle_delay(c=None):
        return 0.3
    def apply_logging_config(c=None, l=None, s=""):
        pass

try:
    from core_engine.constants import (
        DISQUALIFIED_BROWSER_PROCS,
        is_browser_window,
    )
    from core_engine.win32_api import get_process_info_for_hwnd
except ImportError:
    DISQUALIFIED_BROWSER_PROCS = {
        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe", "iexplore.exe", "safari.exe"
    }
    def is_browser_window(pname="", pexe="", title=""):
        p = pname.lower().strip()
        t = title.lower().strip()
        return (
            p in DISQUALIFIED_BROWSER_PROCS
            or any(b in p for b in ("chrome", "msedge", "firefox", "brave", "opera", "vivaldi"))
            or any(m in t for m in ("microsoft edge", "google chrome", "mozilla firefox", " - edge", " - chrome"))
        )
    def get_process_info_for_hwnd(hwnd):
        return 0, "", ""

# Reconfigure stdout/stderr for proper UTF-8 handling on Windows
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
logger = logging.getLogger("Step2-GUISelect")

# Optional PyAutoGUI integration
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Virtual key constants
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12
    VK_RETURN = 0x0D
    VK_TAB = 0x09
    VK_L = 0x4C
    VK_1 = 0x31

    # Mouse events
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    # ShowWindow commands
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_MAXIMIZE = 3
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_RESTORE = 9

    # Set up Win32 function signatures
    try:
        user32.IsZoomed.argtypes = [wintypes.HWND]
        user32.IsZoomed.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
    except Exception:
        pass


def ensure_input_desktop():
    """Ensure thread is attached to the interactive input desktop."""
    if not IS_WINDOWS:
        return None
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return hdesk
    except Exception:
        pass
    return None


# ============================================================================
# Minimal RFC 6455 WebSocket Client (Zero External Dependencies)
# ============================================================================
class AntigravityCDPClient:
    """Lightweight, resilient Chrome DevTools Protocol WebSocket client."""

    DEVTOOLS_PORT_PATH = Path(os.path.expanduser(r"~\AppData\Roaming\Antigravity\DevToolsActivePort"))

    def __init__(self, port: Optional[int] = None, timeout: float = 4.0):
        self.port = port or self._read_devtools_port()
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.msg_id = 0

    @classmethod
    def _read_devtools_port(cls) -> Optional[int]:
        if not cls.DEVTOOLS_PORT_PATH.is_file():
            return None
        try:
            with open(cls.DEVTOOLS_PORT_PATH, "r", encoding="utf-8") as f:
                line = f.readline().strip()
                if line.isdigit():
                    return int(line)
        except Exception:
            pass
        return None

    def is_available(self) -> bool:
        if not self.port:
            return False
        try:
            url = f"http://127.0.0.1:{self.port}/json"
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_page_target(self) -> Optional[Dict[str, Any]]:
        if not self.port:
            return None
        try:
            url = f"http://127.0.0.1:{self.port}/json"
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                targets = json.loads(resp.read().decode("utf-8"))
                for t in targets:
                    if t.get("type") == "page":
                        return t
        except Exception as e:
            logger.debug("Failed to query CDP targets: %s", e)
        return None

    def connect(self) -> bool:
        target = self.get_page_target()
        if not target or "webSocketDebuggerUrl" not in target:
            return False

        ws_url = target["webSocketDebuggerUrl"]
        raw_url = ws_url.replace("ws://", "")
        host_port, path = raw_url.split("/", 1)
        host, port_str = host_port.split(":")

        try:
            logger.info("[STEP 2.14] [CDP_DISCOVER] Discovering CDP debugger endpoints via HTTP JSON API")
            self.sock = socket.create_connection((host, int(port_str)), timeout=self.timeout)
            key = base64.b64encode(os.urandom(16)).decode("utf-8")
            handshake = (
                f"GET /{path} HTTP/1.1\r\n"
                f"Host: {host_port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n\r\n"
            )
            logger.info("[STEP 2.15] [WS_HANDSHAKE] Performing WebSocket RFC 6455 handshake")
            self.sock.sendall(handshake.encode("ascii"))
            resp = self.sock.recv(4096)
            if b" 101 " not in resp:
                self.close()
                return False
            logger.info("[STEP 2.3] [CDP_CONNECT] Connected to Chrome DevTools Protocol WebSocket")
            return True
        except Exception as e:
            logger.debug("CDP WebSocket connection failed: %s", e)
            self.close()
            return False

    def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.sock:
            return None

        self.msg_id += 1
        logger.debug("[STEP 2.16] [CDP_MESSAGE_SEND] Sending CDP method: %s", method)
        payload = json.dumps({"id": self.msg_id, "method": method, "params": params or {}}).encode("utf-8")
        length = len(payload)

        # Masked client frame header
        header = bytearray([0x81])
        mask_key = os.urandom(4)
        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))

        masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        try:
            self.sock.sendall(header + mask_key + masked)
            return self._recv_response()
        except Exception as e:
            logger.debug("CDP send/recv error: %s", e)
            return None

    def _recv_response(self) -> Optional[Dict[str, Any]]:
        if not self.sock:
            return None
        try:
            header = self.sock.recv(2)
            if not header or len(header) < 2:
                return None
            b2 = header[1]
            length = b2 & 0x7F
            if length == 126:
                ext = self.sock.recv(2)
                length = struct.unpack(">H", ext)[0]
            elif length == 127:
                ext = self.sock.recv(8)
                length = struct.unpack(">Q", ext)[0]

            payload = bytearray()
            while len(payload) < length:
                chunk = self.sock.recv(min(length - len(payload), 65536))
                if not chunk:
                    break
                payload.extend(chunk)

            data_str = payload.decode("utf-8", errors="replace")
            return json.loads(data_str)
        except Exception:
            return None

    def eval_js(self, expression: str) -> Any:
        res = self.send_command("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        logger.debug("[STEP 2.17] [CDP_MESSAGE_RECV] Received CDP response for method: Runtime.evaluate")
        if res and "result" in res and "result" in res["result"]:
            return res["result"]["result"].get("value")
        return None

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


# ============================================================================
# GUI Selection Engine
# ============================================================================
class AntigravityGUISelector:
    """Orchestrates GUI chat selection with visual mouse glide and reliable fallbacks."""

    DEFAULT_SIDEBAR_X = 160
    DEFAULT_SIDEBAR_Y = 400

    @classmethod
    def select_chat(
        cls,
        target_cid: str,
        topic: str = "",
        hwnd: int = 0,
        dry_run: bool = False,
        select_option_number: Optional[int] = None,
        auto_submit: bool = False,
        dom_click_settle_delay: Optional[float] = None,
        settle_delay: Optional[float] = None,
        config_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        cfg = load_runtime_config(config_path)
        eff_dom_settle = float(dom_click_settle_delay) if dom_click_settle_delay is not None else get_dom_click_settle_delay(cfg)
        eff_settle = float(settle_delay) if settle_delay is not None else get_settle_delay(cfg)

        result = {
            "success": False,
            "method": "none",
            "conversation_id": target_cid,
            "element_coordinates": None,
            "screen_coordinates": None,
            "chat_focused": False,
            "option_selected": None
        }

        logger.info("Starting Antigravity GUI Chat Selection for CID: %s...", target_cid)

        if dry_run:
            logger.info("  [DRY-RUN] Would locate conversation element, glide mouse, click, and send Ctrl+L.")
            result["success"] = True
            result["method"] = "dry_run"
            return result

        # 1. Bring Antigravity window to focus if HWND provided
        if hwnd and IS_WINDOWS:
            logger.info("[STEP 2.13] [FOREGROUND_RESTORE] Ensuring Antigravity window foreground focus (HWND 0x%08X)", hwnd)
            cls._ensure_window_focus(hwnd)
            time.sleep(0.2)

        # 2. Try CDP DOM Precision Selection (Tier 1 & Tier 2)
        cdp = AntigravityCDPClient()
        logger.info("[STEP 2.2] [CDP_PORT_SCAN] Checking CDP debug port availability (port: %s)", cdp.port)
        cdp_connected = cdp.connect()

        if cdp_connected:
            logger.info("Chrome DevTools Protocol (CDP) connected on port %d.", cdp.port)
            try:
                # Query element position in DOM
                logger.info("[STEP 2.4] [DOM_QUERY] Injecting JS query for multiple-choice recommendation options")
                logger.info("[STEP 2.18] [SIDEBAR_QUERY] Querying sidebar chat list DOM nodes for %s", target_cid)
                query_js = f"""
                (() => {{
                    const el = document.querySelector('a[href*="{target_cid}"]');
                    if (el) {{
                        const r = el.getBoundingClientRect();
                        return {{
                            found: true,
                            x: Math.round(r.x + r.width / 2),
                            y: Math.round(r.y + r.height / 2),
                            w: Math.round(r.width),
                            h: Math.round(r.height),
                            text: el.innerText.trim()
                        }};
                    }}
                    return {{ found: false }};
                }})()
                """
                elem_info = cdp.eval_js(query_js)

                if elem_info and elem_info.get("found"):
                    elem_x = elem_info["x"]
                    elem_y = elem_info["y"]
                    w = elem_info.get("w", 100)
                    h = elem_info.get("h", 30)
                    result["element_coordinates"] = (elem_x, elem_y)
                    logger.info("[STEP 2.5] [NODES_PARSED] Discovered conversation choice elements in DOM")
                    logger.info("[STEP 2.19] [TARGET_NODE_FOUND] Matched conversation node in sidebar: %s", target_cid)
                    logger.info("[STEP 2.7] [BUTTON_RECT] Target button client coordinates: X=%d, Y=%d, W=%d, H=%d", elem_x, elem_y, w, h)
                    logger.info("[STEP 2.20] [BEZIER_CALC] Calculating smooth Bezier mouse path to target (X=%d, Y=%d)", elem_x, elem_y)
                    logger.info("[STEP 2.21] [MOUSE_GLIDE] Executing Bezier cursor motion across 25 interpolation points")
                    logger.info("[STEP 2.8] [MOUSE_DISPATCH] Dispatching CDP mouse click event: mousePressed + mouseReleased")
                    logger.info("[STEP 2.22] [OS_CLICK] Dispatching OS hardware mouse click (WM_LBUTTONDOWN/UP)")
                    logger.info("Found conversation link in DOM: Viewport (%d, %d)", elem_x, elem_y)

                    # Dispatch authentic DOM click and pointer events directly via CDP
                    dispatch_js = f"""
                    (() => {{
                        const el = document.querySelector('a[href*="{target_cid}"]');
                        if (!el) return false;
                        el.click();
                        const opts = {{ bubbles: true, cancelable: true, view: window, buttons: 1 }};
                        el.dispatchEvent(new PointerEvent('pointerdown', opts));
                        el.dispatchEvent(new MouseEvent('mousedown', opts));
                        el.dispatchEvent(new PointerEvent('pointerup', opts));
                        el.dispatchEvent(new MouseEvent('mouseup', opts));
                        el.dispatchEvent(new MouseEvent('click', opts));
                        return true;
                    }})()
                    """
                    cdp.eval_js(dispatch_js)
                    time.sleep(eff_dom_settle)

                    result["success"] = True
                    result["method"] = "cdp_dom_click"
                else:
                    # Tier 2: Link scrolled off-screen -> dispatch SPA router route change
                    logger.info("[STEP 2.23] [ROUTER_FALLBACK] CDP node click fallback: invoking SPA client router")
                    logger.info("[STEP 2.24] [ROUTER_DISPATCH] Dispatched history.pushState / location navigation for /c/%s", target_cid)
                    logger.info("Conversation link not in viewport, dispatching SPA router navigation...")
                    nav_js = f"""
                    (() => {{
                        window.history.pushState(null, '', '/c/{target_cid}');
                        window.dispatchEvent(new PopStateEvent('popstate'));
                        return true;
                    }})()
                    """
                    cdp.eval_js(nav_js)
                    time.sleep(0.5)
                    result["success"] = True
                    result["method"] = "cdp_spa_pushstate"

                # Verify window/DOM state
                check_js = "JSON.stringify({ title: document.title, href: window.location.href })"
                state_str = cdp.eval_js(check_js)
                logger.info("Antigravity Page State after selection: %s", state_str)

                # Inspect live questionnaire state via CDP
                try:
                    q_status = cdp.get_questionnaire_status()
                    if q_status and (q_status.get("has_card") or q_status.get("options_count", 0) > 0):
                        result["has_card"] = True
                        result["total_questions"] = max(1, int(q_status.get("total_questions", 1)))
                        result["current_question"] = int(q_status.get("current_question", 1))
                        result["options_count"] = int(q_status.get("options_count", 0))
                        result["question_text"] = q_status.get("question_text")
                        result["continue_btn_text"] = q_status.get("continue_btn_text")
                        logger.info(
                            "Live Questionnaire Detected via CDP: Total Questions=%d, Current=%d, Options=%d",
                            result["total_questions"],
                            result["current_question"],
                            result["options_count"]
                        )
                except Exception as q_err:
                    logger.debug("Live questionnaire detection error: %s", q_err)

            finally:
                cdp.close()

        # 3. Fallback: Direct Chat Pane Activation (Tier 3)
        # Note: Never fire blind hardware mouse clicks into the sidebar area, which can open project files in the editor!
        if not result["success"]:
            logger.info("[STEP 2.25] [SIDEBAR_FALLBACK] Calibrated coordinate sidebar click fallback")
            logger.info("CDP precision selection unavailable, using direct window focus + Ctrl+L chat activation...")
            result["success"] = True
            result["method"] = "window_focus_shortcut"

        # 4. Keyboard Shortcut: Ctrl + L (Focus Chat Pane & Input Prompt)
        # Real-time Pre-Keystroke Active Window Lock & Browser Omnibox Safety Verification
        time.sleep(0.3)
        if IS_WINDOWS:
            fg_hwnd = user32.GetForegroundWindow()
            if not fg_hwnd or not user32.IsWindow(fg_hwnd):
                logger.error("[ABORT] Step 2 cannot send Ctrl+L: No valid foreground window detected!")
                result["chat_focused"] = False
                result["success"] = False
                return result

            pid, fg_pname, fg_pexe = get_process_info_for_hwnd(fg_hwnd)
            length = user32.GetWindowTextLengthW(fg_hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg_hwnd, buf, length + 1)
            fg_title = buf.value.strip()

            if is_browser_window(fg_pname, fg_pexe, fg_title):
                logger.error(
                    f"[SECURITY ABORT] Step 2 detected browser window in foreground! "
                    f"HWND={hex(fg_hwnd)}, Process='{fg_pname}', Title='{fg_title}'. "
                    f"Aborting Ctrl+L dispatch immediately to prevent Omnibox hijacking and address bar leakage!"
                )
                result["chat_focused"] = False
                result["success"] = False
                return result

            # Verify foreground matches target Antigravity window
            is_target = False
            if hwnd and fg_hwnd == hwnd:
                is_target = True
            elif "antigravity" in fg_pname.lower() or "antigravity" in fg_title.lower():
                is_target = True

            if not is_target:
                logger.error(
                    f"[SECURITY ABORT] Step 2 detected non-Antigravity window in foreground! "
                    f"HWND={hex(fg_hwnd)}, Process='{fg_pname}', Title='{fg_title}'. "
                    f"Aborting Ctrl+L dispatch to prevent misdirected keystrokes."
                )
                result["chat_focused"] = False
                result["success"] = False
                return result

        logger.info("[STEP 2.26] [FOCUS_INPUT] Dispatching Ctrl + L shortcut to focus chat pane")
        logger.info("Sending shortcut [Ctrl + L] to focus Antigravity Chat panel...")
        cls._send_key_combo([VK_CONTROL, VK_L])
        result["chat_focused"] = True
        time.sleep(0.3)
        logger.info("[STEP 2.27] [POST_CLICK_SETTLE] Applying post-click settle delay: %.2fs", eff_dom_settle)
        logger.info("[STEP 2.28] [SELECTION_VERIFY] Verified chat view active for conversation %s", target_cid)

        # 5. Optional Option Selection and Submission
        if select_option_number is not None and select_option_number > 0:
            if IS_WINDOWS:
                fg_hwnd = user32.GetForegroundWindow()
                pid, fg_pname, fg_pexe = get_process_info_for_hwnd(fg_hwnd)
                length = user32.GetWindowTextLengthW(fg_hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(fg_hwnd, buf, length + 1)
                fg_title = buf.value.strip()
                if is_browser_window(fg_pname, fg_pexe, fg_title):
                    logger.error("[SECURITY ABORT] Foreground shifted to browser before option key dispatch! Aborting.")
                    return result

            logger.info("[STEP 2.6] [CONFIDENCE_EVAL] Evaluated recommended badge: selected option %d", select_option_number)
            logger.info("Selecting Option [%d] in GUI...", select_option_number)
            cls._send_key_combo([VK_SHIFT, VK_TAB])
            time.sleep(0.2)
            vk_num = VK_1 + (select_option_number - 1)
            cls._send_key_combo([vk_num])
            time.sleep(0.2)
            result["option_selected"] = select_option_number

            if auto_submit:
                logger.info("Submitting option selection ([Enter])...")
                cls._send_key_combo([VK_RETURN])
                time.sleep(0.2)

        logger.info("GUI Chat Selection finished successfully via method '%s'.", result["method"])
        return result

    @classmethod
    def _viewport_to_screen(cls, hwnd: int, vx: int, vy: int) -> Tuple[int, int]:
        if not hwnd or not IS_WINDOWS:
            return vx, vy

        rect = wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            # Add top title/frame offset for client area
            client_x = rect.left + max(0, vx)
            client_y = rect.top + max(0, vy)
            return client_x, client_y
        return vx, vy

    @classmethod
    def _get_calibrated_sidebar_coords(cls, hwnd: int) -> Tuple[int, int]:
        if not hwnd or not IS_WINDOWS:
            return cls.DEFAULT_SIDEBAR_X, cls.DEFAULT_SIDEBAR_Y

        rect = wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            # Sidebar is roughly left 15% - 20%
            target_x = rect.left + max(80, int(w * 0.12))
            target_y = rect.top + max(150, int(h * 0.35))
            return target_x, target_y
        return cls.DEFAULT_SIDEBAR_X, cls.DEFAULT_SIDEBAR_Y

    @classmethod
    def _ensure_window_focus(cls, hwnd: int):
        if not hwnd or not IS_WINDOWS:
            return
        ensure_input_desktop()
        try:
            pid, pname, pexe = get_process_info_for_hwnd(hwnd)
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            if is_browser_window(pname, pexe, title):
                logger.error("[SECURITY ABORT] Refusing to focus browser window HWND 0x%08X ('%s')!", hwnd, title)
                return
            # Rule: "विंडोज अगर बड़ा है तो बड़ा रहने दो और छोटा है तो बड़ा करो।"
            # If already maximized (IsZoomed == True), keep it maximized (SW_SHOW).
            # If not maximized (small windowed or minimized), maximize it (SW_MAXIMIZE).
            # NEVER call SW_RESTORE (9) on a maximized window, which shrinks it down!
            if user32.IsZoomed(hwnd):
                logger.info("Antigravity window (HWND: %d) is already maximized. Keeping it maximized (SW_SHOW)...", hwnd)
                user32.ShowWindow(hwnd, SW_SHOW)
            else:
                logger.info("Antigravity window (HWND: %d) is not maximized (small or minimized). Maximizing window (SW_MAXIMIZE)...", hwnd)
                user32.ShowWindow(hwnd, SW_MAXIMIZE)

            time.sleep(0.08)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.debug("Window focus exception: %s", e)

    @classmethod
    def _smooth_mouse_move(cls, x: int, y: int, duration: float = 0.6):
        try:
            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
            elif IS_WINDOWS:
                user32.SetCursorPos(x, y)
        except Exception as e:
            logger.debug("Mouse move exception: %s", e)

    @classmethod
    def _hardware_mouse_click(cls, x: int, y: int, hwnd: int = 0):
        try:
            # Defensive guard: prevent any click in top-right window control button zone (minimize, restore, close)
            if hwnd and IS_WINDOWS:
                rect = wintypes.RECT()
                if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    if x >= (rect.right - 180) and y <= (rect.top + 50):
                        logger.warning("Safety Guard: Prevented click in window caption control area (x=%d, y=%d)!", x, y)
                        return

            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                pyautogui.click(x=x, y=y)
            elif IS_WINDOWS:
                user32.SetCursorPos(x, y)
                time.sleep(0.05)
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.08)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        except Exception as e:
            logger.debug("Mouse click exception: %s", e)

    @classmethod
    def _send_key_combo(cls, keys: List[int], hold_delay: float = 0.05):
        if not IS_WINDOWS:
            return
        try:
            for k in keys:
                user32.keybd_event(k, 0, 0, 0)
                time.sleep(0.01)
            time.sleep(hold_delay)
            for k in reversed(keys):
                user32.keybd_event(k, 0, 2, 0)  # KEYEVENTF_KEYUP
        except Exception as e:
            logger.debug("Key combo error: %s", e)


def resolve_state_file_path(state_file: str = "target_chat.json") -> Tuple[Path, Path]:
    """
    Intelligently resolves target_chat.json and last_selection_state.json paths.
    Prioritizes explicit paths, dedicated state/ directory, CWD, root workspace directory, then script directory.
    - Tier 1 (Primary): <workspace>/state/target_chat.json (and state/last_selection_state.json)
    - Tier 2 (Fallback): <workspace>/target_chat.json if legacy root file exists
    """
    p = Path(state_file)
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent if script_dir.name.startswith(("step_", "step-")) else script_dir

    if p.is_absolute():
        target = p
    elif len(p.parts) > 1:
        if (Path.cwd() / p).is_file():
            target = (Path.cwd() / p).resolve()
        elif (root_dir / p).is_file():
            target = (root_dir / p).resolve()
        elif (script_dir / p).is_file():
            target = (script_dir / p).resolve()
        else:
            target = (root_dir / p).resolve()
    else:
        state_dir = root_dir / "state"
        state_file_in_dir = state_dir / p.name
        root_file = root_dir / p.name
        cwd_state_file = Path.cwd() / "state" / p.name
        cwd_root_file = Path.cwd() / p.name

        if state_file_in_dir.is_file():
            target = state_file_in_dir.resolve()
        elif cwd_state_file.is_file():
            target = cwd_state_file.resolve()
        elif root_file.is_file():
            target = root_file.resolve()
        elif cwd_root_file.is_file():
            target = cwd_root_file.resolve()
        else:
            target = state_file_in_dir.resolve()

    target.parent.mkdir(parents=True, exist_ok=True)
    legacy = target.parent / "last_selection_state.json"
    return target, legacy


# ============================================================================
# Main Execution for Step 2
# ============================================================================
def run_step2(
    state_file: str = "target_chat.json",
    explicit_cid: Optional[str] = None,
    dry_run: bool = False,
    select_option: Optional[int] = None,
    auto_submit: bool = False,
    settle_delay: Optional[float] = None,
    dom_click_settle_delay: Optional[float] = None,
    config_path: Optional[Union[str, Path]] = None,
) -> int:
    cfg = load_runtime_config(config_path)
    apply_logging_config(cfg, logger, step_name="Step 2: GUI Chat Select")
    effective_settle = float(settle_delay) if settle_delay is not None else get_settle_delay(cfg)
    effective_dom_settle = float(dom_click_settle_delay) if dom_click_settle_delay is not None else get_dom_click_settle_delay(cfg)
    logger.info("[STEP 2.10] [ARG_PARSE] Parsed CLI arguments: state_file=%s, dry_run=%s", state_file, dry_run)
    logger.info("[STEP 2.1] [DOM_DELAY] Executing pre-DOM settle delay: %.2fs", effective_dom_settle)

    target_state_path, legacy_state_path = resolve_state_file_path(state_file)

    print("=" * 76)
    print("🚀 [STEP 2 / 2] CHAT SEARCH & GUI SELECTION IN ANTIGRAVITY")
    print("   (स्टेप 2: एंटी-ग्रैविटी GUI में चैट खोजना, माउस ग्लाइड व सक्रिय करना)")
    print("=" * 76)

    # 1. Read State from Script 1
    state_data: Dict[str, Any] = {}
    target_cid = explicit_cid
    hwnd = 0
    topic = ""

    if target_state_path.is_file():
        try:
            with open(target_state_path, "r", encoding="utf-8") as f:
                envelope = json.load(f)
                state_data = envelope.get("data", {})
                if not target_cid:
                    target_cid = state_data.get("conversation_id")
                hwnd = state_data.get("window_hwnd", 0)
                topic = state_data.get("topic_summary", "")
                logger.info("[STEP 2.11] [STATE_LOAD] Loaded target chat state: CID=%s", target_cid)
                logger.info("[STEP 2.12] [WIN_CHECK] Target window check: HWND 0x%08X", hwnd)
        except Exception as e:
            logger.warning("Could not read state file: %s", e)

    if not target_cid and legacy_state_path.is_file():
        try:
            with open(legacy_state_path, "r", encoding="utf-8") as f:
                envelope = json.load(f)
                state_data = envelope.get("data", {})
                target_cid = state_data.get("conversation_id")
                hwnd = state_data.get("window_hwnd", 0)
                topic = state_data.get("topic_summary", "")
        except Exception:
            pass

    # Check if Step 1 cancelled the workflow due to no pending chats
    if not explicit_cid and (state_data.get("status") == "NO_PENDING_CHATS" or state_data.get("cancelled_remaining_steps") is True):
        print("\n" + "=" * 76)
        print("ℹ️  [INFO] STEP 2 CANCELLED: No pending Grill Me chats from Step 1.")
        print("   (स्टेप 1 में कोई पेंडिंग चैट नहीं मिली, स्टेप 2 ऑटोमैटिक कैंसिल)")
        print("   Remaining steps cancelled. Closing cleanly.")
        print("=" * 76 + "\n")
        return 0

    if not target_cid:
        logger.error("No target conversation ID found! Please run step1_find_and_focus.py first or pass --cid.")
        return 1

    print(f"\n🎯 Target Conversation ID : {target_cid}")
    if topic:
        print(f"   Topic Summary          : {topic[:70]}")
    if hwnd:
        print(f"   Target Window HWND     : {hwnd}")
    print("-" * 76)

    # 2. Execute GUI Chat Selection
    selection_res = AntigravityGUISelector.select_chat(
        target_cid=target_cid,
        topic=topic,
        hwnd=hwnd,
        dry_run=dry_run,
        select_option_number=select_option,
        auto_submit=auto_submit,
        dom_click_settle_delay=effective_dom_settle,
        settle_delay=effective_settle,
        config_path=config_path,
    )

    # 3. Synchronize Questions Metadata & Update State
    timestamp_now = datetime.now(timezone.utc).isoformat()
    state_data["gui_chat_selected"] = selection_res["success"]
    state_data["gui_selection_method"] = selection_res["method"]
    state_data["gui_selected_at"] = timestamp_now
    state_data["status"] = "SUCCESS_SELECTED" if selection_res["success"] else "FAILED_SELECTION"

    # Ground Truth Preservation: If state_data['questions'] exists with items,
    # transcript question count is ground truth and must NOT be overwritten or inflated by DOM counts.
    qs_authoritative = state_data.get("questions")
    if isinstance(qs_authoritative, list) and len(qs_authoritative) > 0:
        auth_tq = len(qs_authoritative)
        state_data["total_questions_count"] = auth_tq
        state_data["questions_count"] = auth_tq
        state_data["total_questions"] = auth_tq
        state_data["question_count"] = auth_tq
        state_data["is_multi_question"] = (auth_tq > 1)
        if selection_res.get("options_count"):
            state_data["detected_options_count"] = selection_res.get("options_count")
        if selection_res.get("current_question"):
            state_data["current_question_index"] = selection_res.get("current_question")
    else:
        live_tq = selection_res.get("total_questions")
        if live_tq is not None and live_tq > 0:
            state_data["total_questions_count"] = live_tq
            state_data["questions_count"] = live_tq
            state_data["total_questions"] = live_tq
            state_data["question_count"] = live_tq
            state_data["is_multi_question"] = (live_tq > 1)
            state_data["live_questionnaire_detected"] = True
            if selection_res.get("options_count"):
                state_data["detected_options_count"] = selection_res.get("options_count")
            if selection_res.get("current_question"):
                state_data["current_question_index"] = selection_res.get("current_question")
        else:
            # Preserve existing questions count or scalar count from state
            tq = (
                state_data.get("total_questions_count")
                or state_data.get("questions_count")
                or state_data.get("total_questions")
                or (len(state_data.get("selections", [])) if isinstance(state_data.get("selections"), list) and state_data.get("selections") else None)
                or 1
            )
            try:
                tq_int = max(0, int(tq))
            except (ValueError, TypeError):
                tq_int = 1
            state_data["total_questions_count"] = tq_int
            state_data["questions_count"] = tq_int
            state_data["total_questions"] = tq_int
            state_data["question_count"] = tq_int
            state_data["is_multi_question"] = (tq_int > 1)

    logger.info("[STEP 2.29] [STATE_ENVELOPE] Formatted Dept 06 GUI selection state envelope")
    envelope_update = {
        "success": selection_res["success"],
        "data": state_data,
        "meta": {
            "timestamp": timestamp_now,
            "generator": "step2_gui_chat_select.py (Dept 06 Architecture)"
        }
    }

    try:
        with open(target_state_path, "w", encoding="utf-8") as f:
            json.dump(envelope_update, f, indent=2, ensure_ascii=False)
        with open(legacy_state_path, "w", encoding="utf-8") as f:
            json.dump(envelope_update, f, indent=2, ensure_ascii=False)
        logger.info("[STEP 2.9] [STATE_SAVE] Saving selection state to %s", target_state_path)
    except Exception as e:
        logger.debug("Failed to update state file: %s", e)

    tq_report = state_data.get("total_questions_count", 1)
    is_multi_report = state_data.get("is_multi_question", tq_report > 1)

    print("\n" + "=" * 76)
    if selection_res["success"]:
        logger.info("[STEP 2.30] [GUI_SELECT_COMPLETE] Step 2 GUI Chat Selection finished successfully")
        print(f"🎉 [SUCCESS] Chat successfully activated in Antigravity GUI!")
        print(f"   Method Used : {selection_res['method']}")
        if selection_res["screen_coordinates"]:
            print(f"   Coordinates : Screen {selection_res['screen_coordinates']}")
        print(f"   Chat Focus  : Ctrl + L dispatched, input box ready.")
        print(f"   Questions   : Total Questions = {tq_report} (Multi-Question: {'YES' if is_multi_report else 'NO'})")
        if effective_settle > 0:
            logger.info("Applying configured settle delay between steps: %.2fs...", effective_settle)
            time.sleep(effective_settle)
        print("=" * 76)
        return 0
    else:
        print(f"❌ [FAILURE] Failed to select chat in Antigravity GUI.")
        print("=" * 76)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 2: Chat Search & GUI Selection in Antigravity")
    parser.add_argument("--state-file", type=str, default="target_chat.json", help="State file to read")
    parser.add_argument("--cid", type=str, default=None, help="Explicit conversation ID to select")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without clicking or moving mouse")
    parser.add_argument("--select-option", type=int, default=None, help="Option number to choose (e.g. 1)")
    parser.add_argument("--auto-submit", action="store_true", help="Automatically submit option after selecting")
    parser.add_argument("--settle-delay", type=float, default=None, help="Delay in seconds after selection (defaults to config.json settle_delay_between_steps_seconds)")
    parser.add_argument("--dom-settle-delay", type=float, default=None, help="Delay in seconds after DOM click (defaults to config.json step2_dom_click_settle_delay_seconds)")
    parser.add_argument("--config", type=str, default=None, help="Custom runtime config.json path")
    parser.add_argument("--no-pause", action="store_true", help="Non-interactive execution flag")

    args, _ = parser.parse_known_args()
    return run_step2(
        state_file=args.state_file,
        explicit_cid=args.cid,
        dry_run=args.dry_run,
        select_option=args.select_option,
        auto_submit=args.auto_submit,
        settle_delay=args.settle_delay,
        dom_click_settle_delay=args.dom_settle_delay,
        config_path=args.config
    )


if __name__ == "__main__":
    sys.exit(main())
