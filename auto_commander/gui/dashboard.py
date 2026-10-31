# -*- coding: utf-8 -*-
"""
Terminal Dashboard & ANSI Interactive Progress Visualizer.
"""

import sys
from auto_commander.config import Config
from auto_commander.detectors.ocr_detector import WINSDK_OCR_AVAILABLE
from auto_commander.models import DetectionResult


class TerminalDashboard:
    """Renders ANSI colored banner, status updates, and interactive countdown bar."""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[2K\r"

    @classmethod
    def print_banner(cls, config: Config):
        ocr_status = "WinRT OCR Active" if WINSDK_OCR_AVAILABLE else "OCR Disabled/Not Installed"
        banner = f"""
{cls.CYAN}{cls.BOLD}╔══════════════════════════════════════════════════════════════════════════════╗
║                   AutoSelect-Commander for Antigravity                       ║
║        Visual Mouse Automation & Autonomous [Recommended Option] Selector    ║
╚══════════════════════════════════════════════════════════════════════════════╝{cls.RESET}
 {cls.GREEN}● Status:{cls.RESET} Active Daemon Running       {cls.GREEN}● Failsafe:{cls.RESET} Instant Mouse Movement (> {config.mouse_interruption_threshold_px}px)
 {cls.GREEN}● Countdown:{cls.RESET} {config.countdown_seconds}s Timeout (2-Step)       {cls.GREEN}● Floating HUD:{cls.RESET} {'Enabled (Top-Most)' if config.floating_hud_enabled else 'Disabled'}
 {cls.GREEN}● Engines:{cls.RESET} Multi (OCR + UIA + Vision)  {cls.GREEN}● WinRT OCR:{cls.RESET} {ocr_status}
 {cls.YELLOW}● Emergency Abort:{cls.RESET} Shake/Move Mouse, Press 'Q' or ESC, or Move to Screen Corner
────────────────────────────────────────────────────────────────────────────────
"""
        print(banner)

    @classmethod
    def render_scanning(cls, tick: int):
        dots = "." * ((tick % 3) + 1)
        dots_padded = dots.ljust(4)
        sys.stdout.write(f"{cls.CLEAR_LINE}{cls.CYAN}[SCANNING]{cls.RESET} Monitoring screen for Antigravity decision modals{dots_padded}")
        sys.stdout.flush()

    @classmethod
    def render_detected(cls, result: DetectionResult):
        cx, cy = result.center
        clean_label = result.label.replace("(Recommended)", "[Recommended Option]").replace("Recommended", "[Recommended Option]")
        print(f"\n{cls.GREEN}{cls.BOLD}[MODAL DETECTED]{cls.RESET} Engine: {cls.MAGENTA}{result.source}{cls.RESET} | Target: '{clean_label}' at ({cx}, {cy})")

    @classmethod
    def render_countdown(cls, remaining: float, total: float, result: DetectionResult):
        cx, cy = result.center
        bar_length = 30
        pct = max(0.0, min(1.0, remaining / total))
        filled = int(bar_length * pct)
        bar = "█" * filled + "░" * (bar_length - filled)
        color = cls.GREEN if remaining > 6 else (cls.YELLOW if remaining > 3 else cls.RED)
        sys.stdout.write(
            f"{cls.CLEAR_LINE}{color}[COUNTDOWN]{cls.RESET} [{bar}] {cls.BOLD}{remaining:4.1f}s{cls.RESET} remaining | Target: ({cx}, {cy}) | {cls.YELLOW}Move mouse to cancel{cls.RESET}"
        )
        sys.stdout.flush()

    @classmethod
    def render_interrupted(cls, distance: float, threshold: float):
        print(f"\n{cls.RED}{cls.BOLD}[FAIL-SAFE TRIGGERED]{cls.RESET} Human mouse movement detected ({distance:.1f}px > {threshold}px)!")
        print(f"{cls.YELLOW}➜ Yielded full control back to developer. Entering cooldown suppression.{cls.RESET}\n")

    @classmethod
    def render_clicking(cls, step: int, total_steps: int, label: str, x: int, y: int):
        clean_label = label.replace("(Recommended)", "[Recommended Option]").replace("Recommended", "[Recommended Option]")
        print(f"\n{cls.CYAN}{cls.BOLD}[ACTION STEP {step}/{total_steps}]{cls.RESET} Gliding cursor smoothly to {clean_label} at ({x}, {y}) and clicking...")

    @classmethod
    def render_completed(cls):
        print(f"{cls.GREEN}{cls.BOLD}[SUCCESS]{cls.RESET} 2-Step Flow complete! Option selected & form submitted. Agent unblocked.\n")

    @classmethod
    def render_cooldown(cls, seconds_left: int):
        sys.stdout.write(f"{cls.CLEAR_LINE}{cls.YELLOW}[COOLDOWN]{cls.RESET} Resuming scan in {seconds_left}s...")
        sys.stdout.flush()
