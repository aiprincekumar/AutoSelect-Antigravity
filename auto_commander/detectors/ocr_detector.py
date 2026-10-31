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

    def scan(self, target_hwnd: Optional[int] = None) -> Optional[DetectionResult]:
        """Scans target window first, then foreground window, then full screen if needed."""
        if not self.is_available() or ImageGrab is None:
            return None

        # Strategy 0: Direct scan of target window bounds if provided
        if target_hwnd:
            try:
                target_rect = AntigravityWindowManager.get_window_rect(target_hwnd)
                if target_rect and target_rect.width > 100 and target_rect.height > 80:
                    bbox = (
                        max(0, target_rect.left),
                        max(0, target_rect.top),
                        max(0, target_rect.right),
                        max(0, target_rect.bottom),
                    )
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
