# -*- coding: utf-8 -*-
"""
Windows 10/11 WinRT Native OCR Detection Engine.
Fast, font-invariant, zero-training text extraction using Windows.Media.Ocr.
"""

import asyncio
import concurrent.futures
import difflib
import io
from typing import Optional, Tuple

try:
    from PIL import Image, ImageGrab, ImageDraw
except ImportError:
    Image = ImageGrab = ImageDraw = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import winsdk.windows.media.ocr as win_ocr
    import winsdk.windows.graphics.imaging as win_imaging
    import winsdk.windows.storage.streams as win_streams
    WINSDK_OCR_AVAILABLE = True
except ImportError:
    win_ocr = win_imaging = win_streams = None
    WINSDK_OCR_AVAILABLE = False

from auto_commander.detectors.base import BaseDetector
from auto_commander.models import DetectionResult
from auto_commander.platform.win32_window import AntigravityWindowManager


class WindowsOcrDetector(BaseDetector):
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
        img: "Image.Image",
        offset_x: int = 0,
        offset_y: int = 0,
        keywords: Optional[Tuple[str, ...]] = None,
        min_y: int = 0,
        mask_console: bool = True,
    ) -> Optional[DetectionResult]:
        """Runs OCR on a PIL Image and matches against target keywords with fuzzy tolerance."""
        if not self.is_available() or img is None:
            return None

        kw_list = keywords if keywords is not None else self.target_keywords
        try:
            # Mask out console window if it intersects the image region
            console_rect = AntigravityWindowManager.get_console_window_rect() if mask_console else None
            working_img = img
            if console_rect and ImageDraw is not None:
                rel_x1 = max(0, console_rect.left - offset_x)
                rel_y1 = max(0, console_rect.top - offset_y)
                rel_x2 = min(img.width, console_rect.right - offset_x)
                rel_y2 = min(img.height, console_rect.bottom - offset_y)
                if rel_x2 > rel_x1 and rel_y2 > rel_y1:
                    working_img = img.copy()
                    draw = ImageDraw.Draw(working_img)
                    draw.rectangle([rel_x1, rel_y1, rel_x2, rel_y2], fill=(0, 0, 0))

            buf = io.BytesIO()
            working_img.save(buf, format="PNG")
            image_bytes = buf.getvalue()

            # Execute WinRT async OCR inside a clean worker thread (MTA apartment) with timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self._recognize_async(image_bytes))
                result = future.result(timeout=3.5)

            if not result or not result.lines:
                return None

            for line in result.lines:
                line_lower = line.text.lower()
                line_words_clean = [w.text.lower().strip("()[]:., ") for w in line.words]

                # Check line level matching first
                for kw in kw_list:
                    kw_lower = kw.lower()
                    kw_clean = kw_lower.strip("()[] ")
                    if not kw_clean:
                        continue

                    kw_tokens = [t.strip("()[]:., ") for t in kw_lower.split() if t.strip("()[]:., ")]

                    # Match logic: substring, token matching, or fuzzy word matching
                    has_match = (kw_clean in line_lower)
                    if not has_match and kw_tokens:
                        if all(any(token in wc or wc in token for wc in line_words_clean) for token in kw_tokens):
                            has_match = True
                    if not has_match:
                        for wc in line_words_clean:
                            if kw_clean in wc or (len(kw_clean) >= 4 and difflib.SequenceMatcher(None, wc, kw_clean).ratio() >= 0.75):
                                has_match = True
                                break

                    if has_match:
                        matched_words = []
                        target_tokens = set(kw_tokens) if kw_tokens else {kw_clean}
                        for word in line.words:
                            wc = word.text.lower().strip("()[]:., ")
                            if any(token in wc or wc in token or (len(token) >= 4 and difflib.SequenceMatcher(None, wc, token).ratio() >= 0.70) for token in target_tokens):
                                matched_words.append(word)

                        words_to_measure = matched_words if matched_words else list(line.words)

                        if words_to_measure:
                            min_x = min(w.bounding_rect.x for w in words_to_measure)
                            w_min_y = min(w.bounding_rect.y for w in words_to_measure)
                            max_x = max(w.bounding_rect.x + w.bounding_rect.width for w in words_to_measure)
                            max_y = max(w.bounding_rect.y + w.bounding_rect.height for w in words_to_measure)

                            actual_x = int(min_x + offset_x)
                            actual_y = int(w_min_y + offset_y)
                            actual_w = int(max_x - min_x)
                            actual_h = int(max_y - w_min_y)

                            if min_y > 0 and actual_y < min_y:
                                continue

                            # Console boundary filter: never return detection inside console window
                            if console_rect:
                                if console_rect.contains(actual_x, actual_y) or console_rect.contains(
                                    actual_x + actual_w // 2, actual_y + actual_h // 2
                                ):
                                    continue

                            return DetectionResult(
                                x=actual_x,
                                y=actual_y,
                                width=actual_w,
                                height=actual_h,
                                confidence=0.98,
                                source="WindowsOcr",
                                label=kw,
                            )
        except Exception:
            return None
        return None

    def scan_decision_modal_on_image(
        self,
        img: "Image.Image",
        offset_x: int = 0,
        offset_y: int = 0,
        target_keywords: Optional[Tuple[str, ...]] = None,
        submit_keywords: Optional[Tuple[str, ...]] = None,
        require_submit: bool = True,
        mask_console: bool = True,
    ) -> Optional[Tuple[DetectionResult, Optional[DetectionResult]]]:
        """
        Scans an image for an interactive decision modal containing BOTH an option
        candidate and a corresponding Submit button.
        Plain chat text without a Submit button will return None when require_submit is True.
        """
        if not self.is_available() or img is None:
            return None

        opt_kw_list = target_keywords if target_keywords is not None else self.target_keywords
        sub_kw_list = submit_keywords if submit_keywords is not None else (
            "Submit", "पुष्टि करें", "Confirm", "Proceed", "Submit / पुष्टि करें", "जारी रखें", "Continue", "Select"
        )

        try:
            console_rect = AntigravityWindowManager.get_console_window_rect() if mask_console else None
            working_img = img
            if console_rect and ImageDraw is not None:
                rel_x1 = max(0, console_rect.left - offset_x)
                rel_y1 = max(0, console_rect.top - offset_y)
                rel_x2 = min(img.width, console_rect.right - offset_x)
                rel_y2 = min(img.height, console_rect.bottom - offset_y)
                if rel_x2 > rel_x1 and rel_y2 > rel_y1:
                    working_img = img.copy()
                    draw = ImageDraw.Draw(working_img)
                    draw.rectangle([rel_x1, rel_y1, rel_x2, rel_y2], fill=(0, 0, 0))

            buf = io.BytesIO()
            working_img.save(buf, format="PNG")
            image_bytes = buf.getvalue()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self._recognize_async(image_bytes))
                result = future.result(timeout=3.5)

            if not result or not result.lines:
                return None

            option_candidates: list[DetectionResult] = []
            submit_candidates: list[DetectionResult] = []

            for line in result.lines:
                line_text = line.text.strip()
                line_lower = line_text.lower()
                line_words_clean = [w.text.lower().strip("()[]:., ") for w in line.words]

                # Check for Submit / Confirm button
                # Button lines are concise (not long conversational sentences)
                if 1 <= len(line.words) <= 6 and len(line_text) <= 40:
                    for skw in sub_kw_list:
                        skw_clean = skw.lower().strip("()[] ")
                        if not skw_clean:
                            continue
                        sub_match = False
                        if skw_clean in line_lower:
                            sub_match = True
                        elif any(skw_clean == wc or (len(skw_clean) >= 4 and difflib.SequenceMatcher(None, wc, skw_clean).ratio() >= 0.80) for wc in line_words_clean):
                            sub_match = True

                        if sub_match and line.words:
                            min_x = min(w.bounding_rect.x for w in line.words)
                            w_min_y = min(w.bounding_rect.y for w in line.words)
                            max_x = max(w.bounding_rect.x + w.bounding_rect.width for w in line.words)
                            max_y = max(w.bounding_rect.y + w.bounding_rect.height for w in line.words)

                            act_x = int(min_x + offset_x)
                            act_y = int(w_min_y + offset_y)
                            act_w = int(max_x - min_x)
                            act_h = int(max_y - w_min_y)

                            if console_rect and (console_rect.contains(act_x, act_y) or console_rect.contains(act_x + act_w // 2, act_y + act_h // 2)):
                                continue

                            submit_candidates.append(DetectionResult(
                                x=act_x,
                                y=act_y,
                                width=act_w,
                                height=act_h,
                                confidence=0.98,
                                source="WindowsOcr",
                                label=skw,
                            ))
                            break

                # Check for Option candidate
                for okw in opt_kw_list:
                    okw_lower = okw.lower()
                    okw_clean = okw_lower.strip("()[] ")
                    if not okw_clean:
                        continue
                    okw_tokens = [t.strip("()[]:., ") for t in okw_lower.split() if t.strip("()[]:., ")]

                    has_opt_match = (okw_clean in line_lower)
                    if not has_opt_match and okw_tokens:
                        if all(any(token in wc or wc in token for wc in line_words_clean) for token in okw_tokens):
                            has_opt_match = True
                    if not has_opt_match:
                        for wc in line_words_clean:
                            if okw_clean in wc or (len(okw_clean) >= 4 and difflib.SequenceMatcher(None, wc, okw_clean).ratio() >= 0.75):
                                has_opt_match = True
                                break

                    if has_opt_match and line.words:
                        matched_words = []
                        target_tokens = set(okw_tokens) if okw_tokens else {okw_clean}
                        for word in line.words:
                            wc = word.text.lower().strip("()[]:., ")
                            if any(token in wc or wc in token or (len(token) >= 4 and difflib.SequenceMatcher(None, wc, token).ratio() >= 0.70) for token in target_tokens):
                                matched_words.append(word)

                        words_to_measure = matched_words if matched_words else list(line.words)
                        if words_to_measure:
                            min_x = min(w.bounding_rect.x for w in words_to_measure)
                            w_min_y = min(w.bounding_rect.y for w in words_to_measure)
                            max_x = max(w.bounding_rect.x + w.bounding_rect.width for w in words_to_measure)
                            max_y = max(w.bounding_rect.y + w.bounding_rect.height for w in words_to_measure)

                            act_x = int(min_x + offset_x)
                            act_y = int(w_min_y + offset_y)
                            act_w = int(max_x - min_x)
                            act_h = int(max_y - w_min_y)

                            if console_rect and (console_rect.contains(act_x, act_y) or console_rect.contains(act_x + act_w // 2, act_y + act_h // 2)):
                                continue

                            option_candidates.append(DetectionResult(
                                x=act_x,
                                y=act_y,
                                width=act_w,
                                height=act_h,
                                confidence=0.98,
                                source="WindowsOcr",
                                label=okw,
                            ))
                            break

            # Pair Option candidates with corresponding Submit button
            for opt in option_candidates:
                # Find submit button located below option within the modal/card area
                matching_subs = [
                    sub for sub in submit_candidates
                    if (sub.y >= opt.y - 15) and (sub.y - opt.y <= 650) and (abs(sub.x - opt.x) <= 600)
                ]
                if matching_subs:
                    matching_subs.sort(key=lambda s: s.y - opt.y)
                    return (opt, matching_subs[0])
                elif not require_submit:
                    return (opt, None)

        except Exception:
            return None

        return None

    def scan_decision_modal(
        self,
        target_hwnd: Optional[int] = None,
        target_keywords: Optional[Tuple[str, ...]] = None,
        submit_keywords: Optional[Tuple[str, ...]] = None,
        require_submit: bool = True,
    ) -> Optional[Tuple[DetectionResult, Optional[DetectionResult]]]:
        """
        Scans target window, active window, and screen for an interactive decision modal
        with verified Option AND Submit button.
        """
        if not self.is_available() or ImageGrab is None:
            return None

        AntigravityWindowManager.attach_to_input_desktop()

        # Strategy 0: Direct scan on target window bounds
        if target_hwnd:
            try:
                target_rect = AntigravityWindowManager.get_window_rect(target_hwnd)
                if target_rect and target_rect.width > 100 and target_rect.height > 80:
                    sw = user32.GetSystemMetrics(0) if user32 else 1920
                    sh = user32.GetSystemMetrics(1) if user32 else 1080
                    x1 = max(0, min(target_rect.left, sw - 1))
                    y1 = max(0, min(target_rect.top, sh - 1))
                    x2 = max(x1 + 10, min(target_rect.right, sw))
                    y2 = max(y1 + 10, min(target_rect.bottom, sh))

                    win_img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    res = self.scan_decision_modal_on_image(
                        win_img,
                        offset_x=x1,
                        offset_y=y1,
                        target_keywords=target_keywords,
                        submit_keywords=submit_keywords,
                        require_submit=require_submit,
                    )
                    if res:
                        return res
            except Exception:
                pass

        # Strategy 1: Active foreground window
        try:
            if gw is not None:
                active_win = gw.getActiveWindow()
                if active_win and active_win.width > 100 and active_win.height > 80:
                    sw = user32.GetSystemMetrics(0) if user32 else 1920
                    sh = user32.GetSystemMetrics(1) if user32 else 1080
                    x1 = max(0, min(active_win.left, sw - 1))
                    y1 = max(0, min(active_win.top, sh - 1))
                    x2 = max(x1 + 10, min(active_win.right, sw))
                    y2 = max(y1 + 10, min(active_win.bottom, sh))

                    win_img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    res = self.scan_decision_modal_on_image(
                        win_img,
                        offset_x=x1,
                        offset_y=y1,
                        target_keywords=target_keywords,
                        submit_keywords=submit_keywords,
                        require_submit=require_submit,
                    )
                    if res:
                        return res
        except Exception:
            pass

        # Strategy 2: Full screen screenshot scan
        try:
            screen_img = ImageGrab.grab()
            return self.scan_decision_modal_on_image(
                screen_img,
                offset_x=0,
                offset_y=0,
                target_keywords=target_keywords,
                submit_keywords=submit_keywords,
                require_submit=require_submit,
            )
        except Exception:
            return None

    def scan(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """Scans target window first, then foreground window, then full screen if needed."""
        if not self.is_available() or ImageGrab is None:
            return None

        AntigravityWindowManager.attach_to_input_desktop()

        # Strategy 0: Direct scan of target window bounds if provided
        if target_hwnd:
            try:
                target_rect = AntigravityWindowManager.get_window_rect(target_hwnd)
                if target_rect and target_rect.width > 100 and target_rect.height > 80:
                    sw = user32.GetSystemMetrics(0) if user32 else 1920
                    sh = user32.GetSystemMetrics(1) if user32 else 1080
                    x1 = max(0, min(target_rect.left, sw - 1))
                    y1 = max(0, min(target_rect.top, sh - 1))
                    x2 = max(x1 + 10, min(target_rect.right, sw))
                    y2 = max(y1 + 10, min(target_rect.bottom, sh))

                    bbox = (x1, y1, x2, y2)
                    win_img = ImageGrab.grab(bbox=bbox)
                    res = self.scan_image(win_img, offset_x=bbox[0], offset_y=bbox[1])
                    if res:
                        return res
            except Exception:
                pass

        # Strategy 1: Fast scan on active foreground window
        try:
            if gw is not None:
                active_win = gw.getActiveWindow()
                if active_win and active_win.width > 100 and active_win.height > 80:
                    sw = user32.GetSystemMetrics(0) if user32 else 1920
                    sh = user32.GetSystemMetrics(1) if user32 else 1080
                    x1 = max(0, min(active_win.left, sw - 1))
                    y1 = max(0, min(active_win.top, sh - 1))
                    x2 = max(x1 + 10, min(active_win.right, sw))
                    y2 = max(y1 + 10, min(active_win.bottom, sh))

                    bbox = (x1, y1, x2, y2)
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
