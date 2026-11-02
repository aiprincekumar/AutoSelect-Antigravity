# 📦 Grill Me Keyboard Automation Archive Snapshot

> **Archive Location:** `Keyboard Automation/archive/`  
> **Source Directory:** `Keyboard Automation/`  
> **Archive Snapshot Version:** `v1.1.0-modular-verified` (Post CHG-012/CHG-013 Enterprise Modularization)  
> **Snapshot Timestamp:** `2026-11-02 07:15:00 IST`  
> **Author & Maintainer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Integrity Status:** VERIFIED (100% Bit-for-Bit SHA-256 Match with Live Production Package)  

---

## 🎯 1. Purpose & Snapshot Description

This directory contains an immutable, verified archive copy of the complete **Grill Me Keyboard Automation Suite** in its enterprise modular architecture.

It preserves the exact tested and certified state of the automation engine following the modular refactoring and verification of **CHG-012** & **CHG-013**. It contains both the modular package `keyboard_automation/` and the backward-compatible entrypoint `grill_me_automation.py`, ensuring that this snapshot serves as a 100% self-contained, runnable, and verified point-in-time restore point and independent fallback runner.

---

## 📋 2. Archived File Inventory & Verification Hashes

All 11 files in this archive match the certified working production files bit-for-bit:

| Filename / Path | Type | Size (Bytes) | SHA-256 Verification Hash |
| :--- | :--- | :--- | :--- |
| [`grill_me_automation.py`](./grill_me_automation.py) | Backward-Compatible Facade / CLI | 3,446 | `334329CF264C3A7F5CF9D610BE2ED635656D6D4F56BAB2FCE0440CB389B1E8DB` |
| [`keyboard_automation/__init__.py`](./keyboard_automation/__init__.py) | Package Entry & Public Exports | 3,364 | `617C5853DC9EB032051CC6571CCA478A776EDF0CB67580886063398CB56A3F35` |
| [`keyboard_automation/automator.py`](./keyboard_automation/automator.py) | Core Orchestrator Class | 12,609 | `5FDED1249941C6F2A86B9E0C5A5FDD820D916A4CFAFA8E45A6ACC9C7E082F211` |
| [`keyboard_automation/cli.py`](./keyboard_automation/cli.py) | CLI Argument Parsing Subsystem | 6,109 | `7C51589ACA8FC56E2158E09A9B750DACD84E9D2C2A1941F417149BBAF5EB4D23` |
| [`keyboard_automation/constants.py`](./keyboard_automation/constants.py) | Virtual Keys & Configuration Defaults | 1,990 | `336B98133753D8191D4AA155DB7336243B59609CB462343ED91BC910431EB40A` |
| [`keyboard_automation/input_injector.py`](./keyboard_automation/input_injector.py) | Native Keystroke Injection Subsystem | 4,101 | `0F6B02E316A4C8C6D438734A118B1FCA2AE5E27FBA1460D4E498FDC68588F7B0` |
| [`keyboard_automation/win32_api.py`](./keyboard_automation/win32_api.py) | Win32 ctypes Structures & Signatures | 8,586 | `805468491093658E449E8777BE53AF6C1792FE03A78998234A97C78596B8FF74` |
| [`keyboard_automation/window_manager.py`](./keyboard_automation/window_manager.py) | Window Scoring, Maximizing & Focus | 21,678 | `BD58026C8CB9DE13AB45B6B5CB63727F4C756F8E0E2D6752D84D12BA19A1806A` |
| [`run_grill_me.bat`](./run_grill_me.bat) | 1-Click Windows Batch Runner | 2,474 | `87A31A16FC5EB45ECD9EE46FFA3B4EF4A0DFB54CA5360584CD304EB22ED72AA9` |
| [`run_grill_me.ps1`](./run_grill_me.ps1) | PowerShell Script Runner | 4,538 | `368BBF382FA9D536E562CD0888A0DD63004C5BB2B6945E760B6F9AFDDD0F33C4` |
| [`requirements.txt`](./requirements.txt) | Dependency Manifest | 366 | `CF36C187D77903709FD6719B4A72794F296F3892E5CDCDC78281DF6AA315C1DE` |
| [`README.md`](./README.md) | Archive Documentation | (This file) | Self-documenting snapshot manifest |

---

## 🛡️ 3. Certified Capabilities & Features Preserved

1. **Enterprise Modular Architecture:**
   - Decoupled into `constants`, `win32_api`, `window_manager`, `input_injector`, `automator`, and `cli`.
   - Backward-compatible facade preserves 100% drop-in compatibility for all legacy callers and tests.
2. **Antigravity 2.0 Priority Process Targeting:**
   - Scans Win32 top-level windows prioritizing `antigravity.exe` (+1000 score).
   - Resolves native executable paths via `QueryFullProcessImageNameW`.
3. **Strict Web Browser Disqualification:**
   - Explicitly rejects `chrome.exe`, `msedge.exe`, `firefox.exe`, `brave.exe`, `opera.exe`, `vivaldi.exe`, `iexplore.exe`, `safari.exe` with a disqualifying score of `-9999`.
4. **Automated Window Management:**
   - Un-minimizes (`SW_RESTORE`) if Antigravity is minimized.
   - Maximize-to-Full-Screen (`SW_MAXIMIZE`) if not maximized.
   - Foreground lock bypass via synthetic `Alt` signal and `AttachThreadInput`.
5. **Pre-Execution Safety Gatekeeper:**
   - Inspects the active foreground window immediately prior to keystroke dispatch; if a browser is detected, keystroke injection immediately aborts to protect user tabs.
6. **Zero-Dependency Native Execution:**
   - Built with pure standard library `ctypes` accessing Windows Win32 APIs (`user32.dll`, `kernel32.dll`).

---

## 🚀 4. How to Run Directly from Archive

The archived scripts are completely self-contained and can be executed directly from within this archive directory:

### 1-Click Batch Execution:
```cmd
cd "Keyboard Automation\archive"
run_grill_me.bat
```

### PowerShell Runner:
```powershell
cd "Keyboard Automation\archive"
.\run_grill_me.ps1
```

### Python Direct Execution:
```cmd
cd "Keyboard Automation\archive"
python grill_me_automation.py --dry-run --no-countdown
```

---

## 🔄 5. Restore Runbook

To restore the main working directory from this archive:
```powershell
Copy-Item -Path "Keyboard Automation\archive\*" -Destination "Keyboard Automation\" -Exclude "README.md" -Recurse -Force
```
This restores all modular automation scripts and packages to the parent folder without overwriting the parent `README.md`.
