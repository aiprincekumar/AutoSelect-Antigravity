# -*- coding: utf-8 -*-
"""
High-Fidelity Interactive Decision Simulator (--demo / --simulate / --test).
Spawns a mock Antigravity decision card, renders the floating HUD overlay,
and demonstrates the 2-step autonomous selection workflow with physical mouse glide.
"""

import ctypes
import math
import time

try:
    import pyautogui
except ImportError:
    pyautogui = None

from auto_commander.gui.hud import FloatingHUD
from auto_commander.platform.mouse_ctrl import MouseController
from auto_commander.platform.win32_window import AntigravityWindowManager


def launch_simulator(countdown_seconds: float = 10.0):
    """
    Spawns mock Antigravity modal, floating HUD, and physically glides mouse in a full 2-step flow:
    Step 1: Glide to Option 1 (Recommended) -> Firm click (Option 1 highlights & selects).
    Step 2: Glide to Submit button -> Firm click (Submit activates with chime & confirmation).
    """
    try:
        import tkinter as tk
    except ImportError:
        print("[ERROR] Tkinter is required for simulator mode.")
        return

    print("\n\033[96m[SIMULATION MODE] Launching mock Antigravity Decision Modal & Floating HUD (2-Step Flow)...\033[0m")
    root = tk.Tk()
    root.title("Antigravity - Interactive Decision Modal (Live Demo)")
    root.update_idletasks()

    # Position demo window nicely centered on screen
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w, win_h = 700, 460
    pos_x = max(0, (screen_w - win_w) // 2)
    pos_y = max(0, (screen_h - win_h) // 2)
    root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
    root.configure(bg="#1E1E2E")
    root.attributes("-topmost", True)

    root.update_idletasks()
    sim_hwnd = None
    try:
        raw_hwnd = root.winfo_id()
        # GA_ROOT = 2 retrieves the root window handle for the specified window
        sim_hwnd = ctypes.windll.user32.GetAncestor(raw_hwnd, 2) or ctypes.windll.user32.GetParent(raw_hwnd) or raw_hwnd
        AntigravityWindowManager.bring_to_foreground(sim_hwnd)
    except Exception:
        pass

    header = tk.Label(
        root,
        text="Interactive Pair-Programming Decision Required",
        font=("Segoe UI", 13, "bold"),
        fg="#89B4FA",
        bg="#1E1E2E",
        pady=10,
    )
    header.pack()

    desc = tk.Label(
        root,
        text="Task complete. Would you like to push the committed changes to GitHub online repository?",
        font=("Segoe UI", 10),
        fg="#CDD6F4",
        bg="#1E1E2E",
        wraplength=620,
        justify="left",
    )
    desc.pack(pady=4)

    # Variable to track selected option (Step 1)
    selected_option = tk.StringVar(value="")

    # Option 1 Container Frame
    opt1_frame = tk.Frame(root, bg="#313244", highlightbackground="#45475A", highlightthickness=1)
    opt1_frame.pack(pady=8, fill="x", padx=40)

    radio1_lbl = tk.Label(opt1_frame, text="○", font=("Segoe UI", 14), fg="#BAC2DE", bg="#313244")
    radio1_lbl.pack(side="left", padx=(12, 6), pady=8)

    opt1_text_lbl = tk.Label(
        opt1_frame,
        text="Option 1: (Recommended) GitHub पर कमिट चेंजेस पुश करना",
        font=("Segoe UI", 11, "bold"),
        fg="#A6E3A1",
        bg="#313244",
        cursor="hand2",
    )
    opt1_text_lbl.pack(side="left", pady=8, fill="x", expand=True, anchor="w")

    # Option 2 Container Frame
    opt2_frame = tk.Frame(root, bg="#313244", highlightbackground="#45475A", highlightthickness=1)
    opt2_frame.pack(pady=4, fill="x", padx=40)

    radio2_lbl = tk.Label(opt2_frame, text="○", font=("Segoe UI", 14), fg="#BAC2DE", bg="#313244")
    radio2_lbl.pack(side="left", padx=(12, 6), pady=6)

    opt2_text_lbl = tk.Label(
        opt2_frame,
        text="Option 2: नहीं, अभी रहने दो क्योंकि टेस्टिंग पेंडिंग है",
        font=("Segoe UI", 10),
        fg="#BAC2DE",
        bg="#313244",
        cursor="hand2",
    )
    opt2_text_lbl.pack(side="left", pady=6, fill="x", expand=True, anchor="w")

    # Selection handlers
    def select_option_1():
        selected_option.set("option_1")
        radio1_lbl.config(text="●", fg="#A6E3A1", bg="#263b36")
        opt1_frame.config(bg="#263b36", highlightbackground="#A6E3A1", highlightthickness=2)
        opt1_text_lbl.config(bg="#263b36", fg="#A6E3A1")

        radio2_lbl.config(text="○", fg="#BAC2DE", bg="#313244")
        opt2_frame.config(bg="#313244", highlightbackground="#45475A", highlightthickness=1)
        opt2_text_lbl.config(bg="#313244", fg="#BAC2DE")

        status_lbl.config(
            text="Step 1/2 Complete: Option 1 Selected! Moving to Submit button...",
            fg="#A6E3A1",
            font=("Segoe UI", 10, "bold"),
        )
        submit_btn.config(state="normal", bg="#89B4FA", fg="#11111B")

    def select_option_2():
        selected_option.set("option_2")
        radio2_lbl.config(text="●", fg="#F9E2AF", bg="#3c3836")
        opt2_frame.config(bg="#3c3836", highlightbackground="#F9E2AF", highlightthickness=2)
        opt2_text_lbl.config(bg="#3c3836", fg="#F9E2AF")

        radio1_lbl.config(text="○", fg="#BAC2DE", bg="#313244")
        opt1_frame.config(bg="#313244", highlightbackground="#45475A", highlightthickness=1)
        opt1_text_lbl.config(bg="#313244", fg="#A6E3A1")

        status_lbl.config(text="Option 2 selected manually by developer.", fg="#F9E2AF")
        submit_btn.config(state="normal", bg="#89B4FA", fg="#11111B")

    opt1_frame.bind("<Button-1>", lambda e: select_option_1())
    opt1_text_lbl.bind("<Button-1>", lambda e: select_option_1())
    radio1_lbl.bind("<Button-1>", lambda e: select_option_1())

    opt2_frame.bind("<Button-1>", lambda e: select_option_2())
    opt2_text_lbl.bind("<Button-1>", lambda e: select_option_2())
    radio2_lbl.bind("<Button-1>", lambda e: select_option_2())

    # Step 2: Submit Button at bottom
    def on_submit_clicked():
        if not selected_option.get():
            status_lbl.config(text="⚠️ Please select an option first!", fg="#F38BA8")
            return
        submit_btn.config(text="✅ Submitted / पुष्टि हो गई!", bg="#A6E3A1", fg="#11111B")
        status_lbl.config(
            text="🎉 Step 2/2 Complete: Form Submitted! Agent unblocked and resuming autonomously.",
            fg="#A6E3A1",
            font=("Segoe UI", 11, "bold"),
        )
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        root.after(1800, root.destroy)

    submit_frame = tk.Frame(root, bg="#1E1E2E")
    submit_frame.pack(pady=12)

    submit_btn = tk.Button(
        submit_frame,
        text="🚀 Submit / पुष्टि करें",
        font=("Segoe UI", 11, "bold"),
        bg="#45475A",
        fg="#BAC2DE",
        activebackground="#A6E3A1",
        activeforeground="#11111B",
        relief="raised",
        bd=2,
        padx=24,
        pady=8,
        cursor="hand2",
        command=on_submit_clicked,
    )
    submit_btn.pack()

    status_lbl = tk.Label(
        root,
        text="AutoSelect-Commander active. Countdown in progress...",
        font=("Segoe UI", 9, "italic"),
        fg="#9399B2",
        bg="#1E1E2E",
        pady=6,
    )
    status_lbl.pack()

    # Floating HUD overlay initialized to configured countdown duration
    hud = FloatingHUD(alpha=0.92)
    countdown_duration = float(countdown_seconds)
    hud.show(countdown_duration, "Option 1: [Recommended Option] GitHub", master=root)

    start_time = time.time()
    initial_mouse = [None]
    cancelled = [False]
    mouse_ctrl = MouseController(glide_duration=0.8, failsafe_enabled=True)

    def sim_tick():
        if cancelled[0]:
            return

        # Auto-foregrounding check during countdown
        try:
            if root.state() == "iconic":
                root.deiconify()
                root.lift()
        except Exception:
            pass

        # Capture initial mouse position on first tick when window is shown and countdown starts
        if pyautogui and initial_mouse[0] is None:
            initial_mouse[0] = pyautogui.position()

        elapsed = time.time() - start_time
        remaining = max(0.0, countdown_duration - elapsed)

        # Check for user mouse movement fail-safe
        if pyautogui and initial_mouse[0] is not None:
            curr_pos = pyautogui.position()
            dist = math.hypot(curr_pos[0] - initial_mouse[0][0], curr_pos[1] - initial_mouse[0][1])
            if dist > 15:
                cancelled[0] = True
                hud.flash_cancelled()
                status_lbl.config(
                    text=f"⚠️ Auto-selection CANCELLED! Human mouse movement detected ({dist:.1f}px).",
                    fg="#F38BA8",
                    font=("Segoe UI", 10, "bold"),
                )
                return

        hud.update_countdown(remaining)

        if remaining <= 0:
            # -------------------------------------------------------------
            # STEP 1: Glide to Option 1 and Firm Click
            # -------------------------------------------------------------
            hud.update_step("⏱️ Step 1/2: Auto-Selecting Option 1...", "Gliding cursor smoothly to [Recommended Option]...", "#89B4FA")
            status_lbl.config(text="[STEP 1/2] Gliding cursor to Option 1 [Recommended Option]...", fg="#89B4FA")
            root.update_idletasks()
            opt1_frame.update_idletasks()

            o1_x = opt1_frame.winfo_rootx() + opt1_frame.winfo_width() // 2
            o1_y = opt1_frame.winfo_rooty() + opt1_frame.winfo_height() // 2

            def check_cancel():
                return cancelled[0]

            success_step1 = mouse_ctrl.glide_and_click(
                o1_x,
                o1_y,
                check_interrupted_fn=check_cancel,
                target_hwnd=sim_hwnd,
                is_demo=True,
            )
            if not success_step1:
                hud.flash_cancelled()
                return

            select_option_1()
            root.update()

            # Small natural dwell between Step 1 and Step 2
            time.sleep(0.35)

            # -------------------------------------------------------------
            # STEP 2: Glide to Submit Button and Firm Click
            # -------------------------------------------------------------
            hud.update_step("⏱️ Step 2/2: Confirming Submission...", "Gliding cursor smoothly to Submit button...", "#A6E3A1")
            status_lbl.config(text="[STEP 2/2] Gliding cursor to Submit / पुष्टि करें...", fg="#A6E3A1")
            root.update_idletasks()
            submit_btn.update_idletasks()

            sb_x = submit_btn.winfo_rootx() + submit_btn.winfo_width() // 2
            sb_y = submit_btn.winfo_rooty() + submit_btn.winfo_height() // 2

            success_step2 = mouse_ctrl.glide_and_click(
                sb_x,
                sb_y,
                check_interrupted_fn=check_cancel,
                target_hwnd=sim_hwnd,
                is_demo=True,
            )
            if success_step2:
                hud.flash_success("✅ 2-STEP AUTO-SELECTION & SUBMISSION COMPLETE!", "Form submitted! Agent unblocked and resuming autonomously.")
                on_submit_clicked()
            else:
                hud.flash_cancelled()
            return

        root.after(50, sim_tick)

    root.after(200, sim_tick)
    root.mainloop()
