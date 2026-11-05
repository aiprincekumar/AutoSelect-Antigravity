#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Chrome DevTools Protocol (CDP) Helper Subsystem
===============================================
Workspace: AutoSelect-Commander \ Keyboard Automation
Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)

Provides zero-dependency RFC 6455 WebSocket client to communicate with Antigravity
IDE/Electron internal Chrome DevTools instance for 100% precision questionnaire DOM
inspection, option selection, and continuation submission.
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
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("Step3KeyboardAutomation.CDPHelper")


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
            self.port = self._read_devtools_port()
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

        # Masked client frame header (RFC 6455)
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

    # =========================================================================
    # High-Level Antigravity Questionnaire Automation Helpers
    # =========================================================================
    def ensure_chat_active(self, conversation_id: str) -> bool:
        """Ensures the specified conversation is active and loaded in view."""
        if not conversation_id:
            return False
        js = f"""
        (() => {{
            if (window.location.href.includes("{conversation_id}")) {{
                return true;
            }}
            const link = document.querySelector('a[href*="{conversation_id}"]');
            if (link) {{
                link.scrollIntoView({{ block: 'center' }});
                link.click();
                const opts = {{ bubbles: true, cancelable: true, view: window, buttons: 1 }};
                link.dispatchEvent(new PointerEvent('pointerdown', opts));
                link.dispatchEvent(new MouseEvent('mousedown', opts));
                link.dispatchEvent(new PointerEvent('pointerup', opts));
                link.dispatchEvent(new MouseEvent('mouseup', opts));
                link.dispatchEvent(new MouseEvent('click', opts));
                return true;
            }}
            return false;
        }})()
        """
        ok = self.eval_js(js)
        if ok:
            time.sleep(0.5)
        return bool(ok)

    def get_questionnaire_status(self) -> Dict[str, Any]:
        """
        Returns live inspection of the questionnaire widget currently on screen.
        Handles both Single-Question (N=1) and Multi-Question (N=2, 3, 4, 5... N) seamlessly.
        """
        js = """
        (() => {
            const card = document.querySelector('[data-testid="interaction-takeover-card"]')
                      || document.querySelector('[data-testid="ask-question-header-text"]')?.closest('div.border')
                      || document.querySelector('[data-testid="ask-question-header-text"]')?.parentElement?.parentElement;

            let continueBtn = document.querySelector('[data-testid="interaction-continue-button"]')
                           || document.querySelector('[data-testid="interaction-submit-button"]');
            if (!continueBtn) {
                continueBtn = Array.from(document.querySelectorAll('button')).find(b => {
                    const t = (b.innerText || '').trim();
                    return (t.includes('Continue') || t.includes('Submit')) && !t.includes('Skip');
                });
            }

            const skipBtn = document.querySelector('[data-testid="interaction-skip-button"]');
            const headerText = document.querySelector('[data-testid="ask-question-header-text"]');

            let labels = Array.from(document.querySelectorAll('[data-testid="ask-question-option"]'));
            if (labels.length === 0) {
                labels = Array.from(document.querySelectorAll('label[for*="ask-opt"]'));
            }
            if (labels.length === 0) {
                labels = Array.from(document.querySelectorAll('input[type="radio"][id*="ask-opt"]'));
            }

            let currentQ = 1;
            let totalQ = 1;
            const fullText = (headerText ? headerText.innerText + ' ' : '') + (card ? card.innerText + ' ' : '') + document.body.innerText;
            const match = fullText.match(/\\b([1-9]\\d*)\\s*(?:of|\\/)\\s*([1-9]\\d*)\\b/i)
                       || fullText.match(/\\[.*?\\b([1-9]\\d*)\\s*(?:of|\\/)\\s*([1-9]\\d*)\\b.*?\\]/i);
            if (match) {
                currentQ = parseInt(match[1]);
                totalQ = parseInt(match[2]);
            } else if (labels.length > 0) {
                currentQ = 1;
                totalQ = 1;
            }

            const hasCard = !!card || !!continueBtn || !!skipBtn || labels.length > 0;
            const btnDisabled = continueBtn ? (continueBtn.disabled || continueBtn.classList.contains('pointer-events-none')) : null;
            const btnText = continueBtn ? continueBtn.innerText.replace(/\\n/g, ' ').trim() : null;

            const inputs = Array.from(document.querySelectorAll('input[type="radio"][id*="ask-opt"]'));
            const hasChecked = inputs.some(i => i.checked);

            return {
                has_card: hasCard,
                current_question: currentQ,
                total_questions: totalQ,
                question_text: headerText ? headerText.innerText.trim().slice(0, 100) : null,
                options_count: labels.length,
                has_checked_option: hasChecked,
                continue_btn_text: btnText,
                continue_btn_disabled: btnDisabled
            };
        })()
        """
        res = self.eval_js(js)
        return res if isinstance(res, dict) else {
            "has_card": False,
            "current_question": 1,
            "total_questions": 1,
            "has_checked_option": False,
            "continue_btn_disabled": None
        }

    def select_option(self, option_index: int = 1) -> bool:
        """
        Selects the specified 1-based option index in the visible questionnaire.
        Dispatches click, pointer events, and change event to update React state immediately.
        """
        opt_idx = max(0, option_index - 1)
        js = f"""
        (() => {{
            let options = Array.from(document.querySelectorAll('[data-testid="ask-question-option"]'));
            if (options.length === 0) {{
                options = Array.from(document.querySelectorAll('label[for*="ask-opt"]'));
            }}
            if (options.length === 0) {{
                options = Array.from(document.querySelectorAll('input[type="radio"][id*="ask-opt"]'));
            }}

            if (options.length > {opt_idx}) {{
                const target = options[{opt_idx}];
                target.scrollIntoView({{ block: 'nearest' }});

                // Find associated radio input
                let input = null;
                if (target.tagName === 'INPUT') {{
                    input = target;
                }} else {{
                    input = target.querySelector('input') || document.getElementById(target.getAttribute('for'));
                }}

                if (input) {{
                    input.checked = true;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}

                target.click();
                const opts = {{ bubbles: true, cancelable: true, view: window, buttons: 1 }};
                target.dispatchEvent(new PointerEvent('pointerdown', opts));
                target.dispatchEvent(new MouseEvent('mousedown', opts));
                target.dispatchEvent(new PointerEvent('pointerup', opts));
                target.dispatchEvent(new MouseEvent('mouseup', opts));
                target.dispatchEvent(new MouseEvent('click', opts));
                return true;
            }}
            return false;
        }})()
        """
        return bool(self.eval_js(js))

    def click_continue_or_submit(self) -> bool:
        """
        Clicks the Continue / Submit confirmation button on the questionnaire.
        Synthesizes standard click + pointer events for React Radix/button handlers.
        """
        js = """
        (() => {
            let btn = document.querySelector('[data-testid="interaction-continue-button"]')
                   || document.querySelector('[data-testid="interaction-submit-button"]');
            if (!btn) {
                btn = Array.from(document.querySelectorAll('button')).find(b => {
                    const t = (b.innerText || '').trim();
                    return (t.includes('Continue') || t.includes('Submit')) && !t.includes('Skip');
                });
            }

            if (btn && !btn.disabled && !btn.classList.contains('pointer-events-none')) {
                btn.scrollIntoView({ block: 'nearest' });
                btn.click();
                const opts = { bubbles: true, cancelable: true, view: window, buttons: 1 };
                btn.dispatchEvent(new PointerEvent('pointerdown', opts));
                btn.dispatchEvent(new MouseEvent('mousedown', opts));
                btn.dispatchEvent(new PointerEvent('pointerup', opts));
                btn.dispatchEvent(new MouseEvent('mouseup', opts));
                btn.dispatchEvent(new MouseEvent('click', opts));
                return true;
            }
            return false;
        })()
        """
        return bool(self.eval_js(js))

    def wait_for_question(self, expected_question: int = 1, timeout: float = 3.0) -> bool:
        """Polls until the expected question number or card options are active in the DOM."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = self.get_questionnaire_status()
            if st.get("has_card") and st.get("options_count", 0) > 0:
                total_q = st.get("total_questions", 1)
                curr_q = st.get("current_question", 1)
                if total_q == 1 or curr_q == expected_question:
                    return True
            time.sleep(0.1)
        return False

    def wait_for_button_enabled(self, timeout: float = 2.5) -> bool:
        """Polls until Continue/Submit button is found and no longer disabled."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = self.get_questionnaire_status()
            disabled = st.get("continue_btn_disabled")
            if disabled is False:
                return True
            time.sleep(0.08)
        return False

    def wait_for_advance_or_close(self, previous_question: int, is_last: bool, timeout: float = 3.5) -> bool:
        """
        Waits for UI wizard to transition after clicking Continue or Submit.
        If is_last: waits for card to disappear.
        If not is_last: waits for current_question to increment.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = self.get_questionnaire_status()
            if is_last:
                if not st.get("has_card"):
                    return True
            else:
                curr_q = st.get("current_question", 1)
                if curr_q > previous_question:
                    return True
            time.sleep(0.1)
        return True
