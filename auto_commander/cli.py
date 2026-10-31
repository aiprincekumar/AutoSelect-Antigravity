# -*- coding: utf-8 -*-
"""
Command-line interface and argument parsing for AutoSelect-Commander.
"""

import argparse
import ctypes
import sys

from auto_commander.config import Config
from auto_commander.core.diagnostics import run_diagnostics
from auto_commander.core.engine import AutoCommanderEngine
from auto_commander.gui.simulator import launch_simulator


def configure_windows_environment():
    """Initializes UTF-8 encoding, High-DPI awareness, and ANSI console mode on Windows."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        try:
            kernel32 = ctypes.windll.kernel32
            h_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_out, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            pass


def main():
    """CLI Entry Point."""
    configure_windows_environment()

    parser = argparse.ArgumentParser(
        description="AutoSelect-Commander: Visual Mouse Automation for Antigravity"
    )
    parser.add_argument(
        "--test",
        "--simulate",
        "--demo",
        dest="test",
        action="store_true",
        help="Launch interactive simulation window for instant visual end-to-end verification",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Run deep screen, window, and OCR text diagnostics probe",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to custom config.json file (default: config.json)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "ocr", "uia", "vision"],
        default=None,
        help="Override detection mode: 'auto', 'ocr', 'uia', or 'vision'",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Override countdown duration in seconds (default: 10s)",
    )
    args = parser.parse_args()

    # Load configuration
    cfg = Config.load(args.config)
    if args.mode:
        cfg.detection_mode = args.mode
    if args.timeout:
        cfg.countdown_seconds = args.timeout

    if args.diagnostics:
        run_diagnostics(cfg)
        return

    if args.test:
        launch_simulator(cfg.countdown_seconds)
        return

    # Initialize and run engine
    engine = AutoCommanderEngine(cfg)
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n\033[93m[EXIT] Stopped by user.\033[0m")
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
