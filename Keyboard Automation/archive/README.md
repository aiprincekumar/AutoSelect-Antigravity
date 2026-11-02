# 📦 Grill Me Keyboard Automation Archive Snapshot

> **Archive Location:** `Keyboard Automation/archive/`  
> **Source Directory:** `Keyboard Automation/`  
> **Archive Snapshot Version:** `v1.0.0-verified` (Post CHG-011 / Commit `ffa5036`)  
> **Snapshot Timestamp:** `2026-11-02 05:25:00 IST`  
> **Author & Maintainer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)  
> **Integrity Status:** VERIFIED (100% Bit-for-Bit SHA-256 Match)  

---

## 🎯 1. Purpose & Snapshot Description

This directory contains an immutable, verified archive copy of the complete **Grill Me Keyboard Automation Suite**.

It preserves the exact tested and certified state of the automation engine following the resolution of **CHG-011** (Browser Disqualification & Native Antigravity 2.0 Process Targeting). This ensures that if the working files in the parent folder are ever modified, refactored, or corrupted, this snapshot serves as a 100% verified point-in-time restore point and independent fallback runner.

---

## 📋 2. Archived File Inventory & Verification Hashes

All files in this archive match the certified working files bit-for-bit:

| Filename | Type | Size (Bytes) | SHA-256 Verification Hash |
| :--- | :--- | :--- | :--- |
| [`grill_me_automation.py`](./grill_me_automation.py) | Python Core Engine | 53,743 | `63852CF8CC5B6491C38BF89EE501469694C3FB04F2EFB8DF9CDBE41E4CC1349D` |
| [`run_grill_me.bat`](./run_grill_me.bat) | 1-Click Windows Batch | 2,474 | `87A31A16FC5EB45ECD9EE46FFA3B4EF4A0DFB54CA5360584CD304EB22ED72AA9` |
| [`run_grill_me.ps1`](./run_grill_me.ps1) | PowerShell Runner | 4,538 | `368BBF382FA9D536E562CD0888A0DD63004C5BB2B6945E760B6F9AFDDD0F33C4` |
| [`requirements.txt`](./requirements.txt) | Dependency Manifest | 366 | `CF36C187D77903709FD6719B4A72794F296F3892E5CDCDC78281DF6AA315C1DE` |
| [`README.md`](./README.md) | Archive Documentation | (This file) | Self-documenting snapshot manifest |

---

## 🛡️ 3. Certified Capabilities & Features Preserved

1. **Antigravity 2.0 Priority Process Targeting:**
   - Scans Win32 top-level windows prioritizing `antigravity.exe` (+1000 score).
   - Resolves native executable paths via `QueryFullProcessImageNameW`.
2. **Strict Web Browser Disqualification:**
   - Explicitly rejects `chrome.exe`, `msedge.exe`, `firefox.exe`, `brave.exe`, `opera.exe`, `vivaldi.exe`, `iexplore.exe`, `safari.exe` with a disqualifying score of `-9999`.
3. **Automated Window Management:**
   - Un-minimizes (`SW_RESTORE`) if Antigravity is minimized.
   - Maximize-to-Full-Screen (`SW_MAXIMIZE`) if not maximized.
   - Foreground lock bypass via synthetic `Alt` signal and `AttachThreadInput`.
4. **Pre-Execution Safety Gatekeeper:**
   - Inspects the active foreground window immediately prior to keystroke dispatch; if a browser is detected, keystroke injection immediately aborts to protect user tabs.
5. **Zero-Dependency Native Execution:**
   - Built with pure standard library `ctypes` accessing Windows Win32 APIs (`user32.dll`, `kernel32.dll`).

---

## 🚀 4. How to Run Directly from Archive

The archived scripts are fully self-contained and can be executed directly from this archive folder:

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
python grill_me_automation.py
```

---

## 🔄 5. Restore Runbook

To restore the main working directory from this archive:
```powershell
Copy-Item -Path "Keyboard Automation\archive\*" -Destination "Keyboard Automation\" -Exclude "README.md" -Force
```
This restores all automation scripts to the parent folder without overwriting the parent `README.md`.
