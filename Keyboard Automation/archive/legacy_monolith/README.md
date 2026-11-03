# Legacy Monolithic Automation Archive
======================================

This directory contains the original monolithic automation script and screen-coordinate configuration that preceded the modular 5-step Clean Architecture pipeline:

1. **`activating_grill_me.py`**:
   - Original monolithic 57KB orchestrator combining transcript parsing, screen coordinate calculation, window focus, PyAutoGUI clicks, and Enter dispatch into a single script.
   - Superseded by the modular architecture:
     - Step 0: `step_0_antigravity_detector/`
     - Step 1: `step_1_chat_identifier/`
     - Step 2: `step_2_chat_and_focus/`
     - Step 3: `step_3_select_the_recommendation/`
     - Step 4: `step_4_reporting/`
     - Master Hub: `Complete Automation/`
     - Shared Engine: `core_engine/`

2. **`config.json`**:
   - Original fixed 1920x1080 pixel coordinates for the legacy monolith.
   - Superseded by dynamic DOM/CDP and Win32 element detection, with configurable pipeline settings now residing in `Complete Automation/config.json`.
