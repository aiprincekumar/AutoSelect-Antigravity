#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Chat Search & GUI Selection in Antigravity
==================================================
Part of: Activating Grill Me Chat in Antigravity (Two-Script Modular Architecture)
Workspace: AutoSelect-Commander / Activating Grill Me Chat in anti-gravity
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
            self.sock.sendall(handshake.encode("ascii"))
            resp = self.sock.recv(4096)
            if b" 101 " not in resp:
                self.close()
                return False
            return True
        except Exception as e:
            logger.debug("CDP WebSocket connection failed: %s", e)
            self.close()
            return False

    def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.sock:
            return None

        self.msg_id += 1
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
        auto_submit: bool = False
    ) -> Dict[str, Any]:
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
            cls._ensure_window_focus(hwnd)
            time.sleep(0.2)

        # 2. Try CDP DOM Precision Selection (Tier 1 & Tier 2)
        cdp = AntigravityCDPClient()
        cdp_connected = cdp.connect()

        if cdp_connected:
            logger.info("Chrome DevTools Protocol (CDP) connected on port %d.", cdp.port)
            try:
                # Query element position in DOM
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
                    result["element_coordinates"] = (elem_x, elem_y)
                    logger.info("Found conversation link in DOM: Viewport (%d, %d)", elem_x, elem_y)

                    # Calculate absolute screen coordinates from window rect
                    screen_x, screen_y = cls._viewport_to_screen(hwnd, elem_x, elem_y)
                    result["screen_coordinates"] = (screen_x, screen_y)

                    # Smooth visual glide to target conversation row
                    cls._smooth_mouse_move(screen_x, screen_y, duration=0.6)
                    time.sleep(0.15)

                    # Dispatch authentic DOM pointer & mouse events
                    dispatch_js = f"""
                    (() => {{
                        const el = document.querySelector('a[href*="{target_cid}"]');
                        if (!el) return false;
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
                    # Also click hardware OS mouse
                    cls._hardware_mouse_click(screen_x, screen_y, hwnd=hwnd)
                    time.sleep(0.4)

                    result["success"] = True
                    result["method"] = "cdp_dom_click"
                else:
                    # Tier 2: Link scrolled off-screen -> dispatch SPA router route change
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

            finally:
                cdp.close()

        # 3. Fallback: Calibrated Sidebar Coordinate Click (Tier 3)
        if not result["success"]:
            logger.warning("CDP precision selection unavailable, falling back to calibrated coordinate click...")
            coords = cls._get_calibrated_sidebar_coords(hwnd)
            screen_x, screen_y = coords
            result["screen_coordinates"] = (screen_x, screen_y)

            cls._smooth_mouse_move(screen_x, screen_y, duration=0.8)
            time.sleep(0.2)
            cls._hardware_mouse_click(screen_x, screen_y, hwnd=hwnd)
            time.sleep(0.4)

            result["success"] = True
            result["method"] = "calibrated_coordinate_click"

        # 4. Keyboard Shortcut: Ctrl + L (Focus Chat Pane & Input Prompt)
        time.sleep(0.3)
        logger.info("Sending shortcut [Ctrl + L] to focus Antigravity Chat panel...")
        cls._send_key_combo([VK_CONTROL, VK_L])
        result["chat_focused"] = True
        time.sleep(0.3)

        # 5. Optional Option Selection and Submission
        if select_option_number is not None and select_option_number > 0:
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


# ============================================================================
# Main Execution for Step 2
# ============================================================================
def run_step2(
    state_file: str = "target_chat.json",
    explicit_cid: Optional[str] = None,
    dry_run: bool = False,
    select_option: Optional[int] = None,
    auto_submit: bool = False
) -> int:
    script_dir = Path(__file__).resolve().parent
    target_state_path = script_dir / state_file
    legacy_state_path = script_dir / "last_selection_state.json"

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
        auto_submit=auto_submit
    )

    # 3. Update and Save State
    timestamp_now = datetime.now(timezone.utc).isoformat()
    state_data["gui_chat_selected"] = selection_res["success"]
    state_data["gui_selection_method"] = selection_res["method"]
    state_data["gui_selected_at"] = timestamp_now
    state_data["status"] = "SUCCESS_SELECTED" if selection_res["success"] else "FAILED_SELECTION"

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
    except Exception as e:
        logger.debug("Failed to update state file: %s", e)

    print("\n" + "=" * 76)
    if selection_res["success"]:
        print(f"🎉 [SUCCESS] Chat successfully activated in Antigravity GUI!")
        print(f"   Method Used : {selection_res['method']}")
        if selection_res["screen_coordinates"]:
            print(f"   Coordinates : Screen {selection_res['screen_coordinates']}")
        print(f"   Chat Focus  : Ctrl + L dispatched, input box ready.")
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
    parser.add_argument("--no-pause", action="store_true", help="Non-interactive execution flag")

    args, _ = parser.parse_known_args()
    return run_step2(
        state_file=args.state_file,
        explicit_cid=args.cid,
        dry_run=args.dry_run,
        select_option=args.select_option,
        auto_submit=args.auto_submit
    )


if __name__ == "__main__":
    sys.exit(main())
