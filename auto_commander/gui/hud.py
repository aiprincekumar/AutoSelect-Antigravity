# -*- coding: utf-8 -*-
"""
Floating On-Screen HUD Overlay (Tkinter Top-Most Window).
Provides a non-intrusive semi-transparent progress countdown and fail-safe notice.
"""

import time
from typing import Optional


class FloatingHUD:
    """Always-on-top semi-transparent floating on-screen countdown HUD."""

    def __init__(self, alpha: float = 0.92):
        self.alpha = alpha
        self.root = None
        self.master = None
        self.lbl_title = None
        self.lbl_status = None
        self.total_seconds = 10.0
        self.is_visible = False

    def show(self, total_seconds: float, label: str, master=None):
        """Displays the floating HUD at the top center of the primary display."""
        try:
            import tkinter as tk
            self.total_seconds = float(total_seconds)
            self.master = master

            if master is not None:
                self.root = tk.Toplevel(master)
            else:
                self.root = tk.Tk()

            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            try:
                self.root.attributes("-alpha", self.alpha)
            except Exception:
                pass

            # Center at top of screen
            sw = self.root.winfo_screenwidth()
            w, h = 620, 58
            x = (sw - w) // 2
            y = 20
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.configure(bg="#181825", highlightbackground="#89B4FA", highlightthickness=2)

            clean_label = label.replace("\n", " ")
            if len(clean_label) > 42:
                clean_label = clean_label[:39] + "..."

            self.lbl_title = tk.Label(
                self.root,
                text=f"⏱️ AutoSelect-Commander | Auto-Selecting: {clean_label}",
                fg="#89B4FA",
                bg="#181825",
                font=("Segoe UI", 10, "bold"),
            )
            self.lbl_title.pack(pady=(4, 2))

            self.lbl_status = tk.Label(
                self.root,
                text="[████████████████████] Initializing...",
                fg="#A6E3A1",
                bg="#181825",
                font=("Consolas", 10, "bold"),
            )
            self.lbl_status.pack()

            self.root.update_idletasks()
            self.root.update()
            self.is_visible = True
        except Exception:
            self.is_visible = False
            self.root = None

    def update_countdown(self, remaining: float):
        """Updates the countdown bar and seconds remaining."""
        if not self.is_visible or not self.root:
            return
        try:
            pct = max(0.0, min(1.0, remaining / self.total_seconds))
            bar_len = 22
            filled = int(bar_len * pct)
            bar = "█" * filled + "░" * (bar_len - filled)

            if remaining > (self.total_seconds * 0.6):
                color = "#A6E3A1"  # Mint Green
            elif remaining > (self.total_seconds * 0.3):
                color = "#F9E2AF"  # Warm Yellow
            else:
                color = "#F38BA8"  # Soft Red

            self.lbl_status.config(
                text=f"[{bar}] {remaining:4.1f}s remaining | Move mouse to cancel",
                fg=color,
            )
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def update_step(self, step_title: str, step_detail: str, color: str = "#89B4FA"):
        """Displays real-time multi-step progress in the HUD."""
        if not self.is_visible or not self.root:
            return
        try:
            self.lbl_title.config(text=step_title, fg=color)
            self.lbl_status.config(text=step_detail, fg="#CDD6F4")
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def flash_cancelled(self):
        """Flashes red notification indicating human took over."""
        if not self.is_visible or not self.root:
            return
        try:
            self.root.configure(highlightbackground="#F38BA8")
            self.lbl_title.config(text="⚠️ INTERRUPTED — Developer Control Restored", fg="#F38BA8")
            self.lbl_status.config(text="Auto-selection aborted. Returning to monitoring.", fg="#CDD6F4")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1.0)
        except Exception:
            pass
        finally:
            self.close()

    def flash_success(
        self,
        title: str = "✅ AUTO-SELECTED & SUBMITTED SUCCESSFULLY",
        detail: str = "Form submitted! Agent unblocked and resuming autonomously.",
    ):
        """Flashes green notification indicating success."""
        if not self.is_visible or not self.root:
            return
        try:
            self.root.configure(highlightbackground="#A6E3A1")
            self.lbl_title.config(text=title, fg="#A6E3A1")
            self.lbl_status.config(text=detail, fg="#A6E3A1")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1.2)
        except Exception:
            pass
        finally:
            self.close()

    def close(self):
        """Closes and destroys the HUD window safely."""
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
        self.is_visible = False
