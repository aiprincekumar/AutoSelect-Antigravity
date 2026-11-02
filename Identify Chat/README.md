# ⚠️ Notice: Migrated to Keyboard Automation

> **Migration Status:** COMPLETED  
> **Destination Folder:** [`../Keyboard Automation/`](file:///c:/Users/Atul%20Verma/Desktop/AutoSelect-Commander/Keyboard%20Automation/)  
> **Date:** 2026-11-03  

---

## 📌 Architecture Consolidation Notice

All scripts, runners, and configuration for **Step 1 (Scan & Focus)** and **Step 2 (GUI Chat Select)** have been moved and consolidated into the **`Keyboard Automation`** directory.

The automation pipeline now runs entirely from `Keyboard Automation` as a unified 3-step pipeline:

- **Step 1:** `step1_find_and_focus.py` (Scan brain transcripts, focus window, save `target_chat.json`)
- **Step 2:** `step2_gui_chat_select.py` (CDP/DOM chat selection and focus)
- **Step 3:** `step3_keyboard_automation.py` (Keystroke automation, dynamic multi-question scaling, and submission)

### 🚀 Unified Launchers in `Keyboard Automation`:
- `run_all_steps.bat` / `run_activating_grill_me_with_automation.bat`: Complete Step 1 -> Step 2 -> Step 3 Pipeline
- `run_step1.bat` / `run_step1_find_and_focus.bat`: Step 1 Standalone
- `run_step2.bat` / `run_step2_gui_chat_select.bat`: Step 2 Standalone
- `run_step3.bat` / `run_step3_keyboard_automation.bat`: Step 3 Standalone
