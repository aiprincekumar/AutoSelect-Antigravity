## [unreleased]

### 🚀 Features

- *(core)* Initial release of AutoSelect-Commander visual mouse automation tool
- *(core)* Implement 10s countdown, reliable firm click, 2-step submit flow, and Antigravity auto-foregrounding
- *(ocr)* Enhance disabled Submit and Skip button detection with contrast boost and bracketed matching
- *(navigation)* Implement Step 0 (?) chat badge navigation, purge demo code into standalone files, streamline production run.bat

### 🐛 Bug Fixes

- *(core)* Overhaul detection engine, add floating HUD overlay and interactive launcher menu
- *(runner)* Wrap diagnostics OCR probe in ThreadPoolExecutor with timeout and sanitize run.bat
- *(detection,demo)* Mask console window in OCR and enable demo mode target window click override
- *(win32,detector)* Restore minimized Antigravity window and require submit button to eliminate chat false positives

### 📚 Documentation

- *(changelog)* Generate initial CHANGELOG.md via git-cliff
- *(changelog)* Update CHANGELOG.md via git-cliff

### 🚜 Refactor

- *(architecture)* Decompose into modular auto_commander package, fix Antigravity window tracking and click safety

### ⚙️ Miscellaneous Tasks

- *(encoding)* Apply UTF-8 BOM to README.md and CHANGELOG.md
