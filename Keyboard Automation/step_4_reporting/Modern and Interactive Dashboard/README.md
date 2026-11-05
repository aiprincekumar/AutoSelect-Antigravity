# Modern and Interactive Dashboard
==========================================

> **Subsystem:** Next-Generation Visual Telemetry & Real-Time Orchestration Dashboard  
> **Location:** `step_4_reporting/Modern and Interactive Dashboard/`  
> **Standard:** Department 04 (UI/UX Design System), Department 05 (Frontend Architecture) & Department 06 (Backend & API Engineering)  
> **Developer:** Atul Verma (`aiprincekumar` / `aiprincekumar010100@gmail.com`)

---

## ⚡ Overview & Key Innovations

The **Modern and Interactive Dashboard** is an upgraded, high-performance telemetry and control dashboard engineered for the `AutoSelect-Commander` autonomous automation suite. It elevates the visual hierarchy, micro-interactions, ergonomics, and real-time observability to modern SaaS standards (Linear/Vercel/Datadog grade) with zero external CSS or JavaScript dependencies.

---

## 🚀 Key Features & Enhancements

1. **Header Dual-Cluster Architecture**:
   - **System Health Cluster**: Dedicated indicators for Control Server Bridge (`🟢 Server Port 8501`), Engine Activity (`⚪ Inactive`, `🟡 Paused`, `🟢 Active`), and Runtime Mode (`⚡ Production` / `🧪 Test`).
   - **Action Control Cluster**: Prominent Automation Toggle button (`▶️ Start` / `⏹️ Stop`), Console Logs trigger, Theme toggle, Sound chime toggle, and 1-Click Classic Dashboard switcher (`🏛️ Classic View`).

2. **Live Pulse Ticker Strip**:
   - A real-time execution ribbon situated directly below the header.
   - Animated glowing green beacon (`● LIVE TELEMETRY`), live daemon status message, and digital precision clock.

3. **Slide-Up Live Console Logs Drawer**:
   - Slides up smoothly from the bottom via `[📟 Logs]` button or keyboard shortcut `L`.
   - Real-time stream from `complete_automation.log` via `/api/logs/tail?lines=80` (polled every 2.5s).
   - Line numbers, syntax coloring for `[INFO]`, `[WARNING]`, `[ERROR]`, auto-scroll toggle, and clear terminal button.

4. **Visual Hierarchy for 8 Key Performance Indicators (KPIs)**:
   - **Row 1 (North Star Hero Cards)**:
     - `Total Questions Answered`: 2.5rem display typography, indigo-violet gradient border, ambient glow, count-up animation (0 ➔ 21).
     - `Total Completed Pipeline Runs`: Emerald gradient border, ambient glow, count-up animation (0 ➔ 6).
   - **Row 2 (Operational Efficiency Metrics)**:
     - 6 responsive secondary cards: Runtime, Distinct Chats, Avg Latency, Question Density, Avg Depth, Resolution Speed.

5. **Context-Aware Filter Toolbar & Active Dismiss Chips**:
   - Automatically visible on `Overview` and `Chats` tabs; smoothly hidden on `Mode Switch` and `Config` tabs.
   - Quick Presets: All Time, Today, Yesterday, Last 7 Days, Fast Runs (<20s), Deep Runs (>40s).
   - Dismissible active filter chips (`[Preset: All Time ✕]`) for instant 1-click filter clearing.

6. **Interactive Floating SVG Tooltips**:
   - Hovering over any SVG chart data element (Distribution bars, Latency trend points, Topic donut slices, Velocity bars) displays an elegant floating card with exact values, timestamps, and run IDs.

7. **Questions Tab (Supercharged Q&A Ledger)**:
   - **1-Click "Copy Q&A" Button**: Copies the question, all options, and selected answer to clipboard with an emerald toast notification (`✅ Question & answer copied to clipboard!`).
   - **Visual Badging**: Solid emerald badge for `✓ Selected` and cyan badge for `⭐ Recommended`.
   - Real-time instant search input.

8. **Mode Switch Tab (Interactive Visual Diff)**:
   - Interactive side-by-side cards for Production and Test modes.
   - Parameter difference matrix highlighting timing and safety impact.
   - 1-Click switch with live persistence to `config.json`.

9. **Config Tab Ergonomics**:
   - Real-time search filter for settings.
   - Floating "Unsaved Changes" dock at the bottom: `⚠️ Unsaved changes — [Discard] [Save to config.json]`.

10. **Built-in Web Audio API Synthesizer (Zero Audio Files)**:
    - High-tech rising 2-tone chord on Start.
    - Calming falling 2-tone chord on Stop.
    - Crisp blip on Copy Q&A.
    - Muteable via `🔔` button or keyboard shortcut `M` (persisted in `localStorage`).

11. **Keyboard Shortcuts HUD Modal**:
    - Press `?` to view all shortcuts:
      - `1` - `5`: Switch tabs (Overview, Chats, Questions, Mode, Config)
      - `/`: Focus search input
      - `L`: Open/close live console logs drawer
      - `T`: Toggle light/dark theme
      - `M`: Toggle audio chimes
      - `Esc`: Close open drawers and modals

---

## 🏃 How to Run

### Option 1: 1-Click Launcher (Batch)
Double-click `run_modern_dashboard.bat` or run:
```powershell
.\run_modern_dashboard.bat
```

### Option 2: Via Local Control Server (Port 8501)
If `dashboard_server.py` is running:
- **Modern Dashboard:** `http://127.0.0.1:8501/` or `http://127.0.0.1:8501/modern`
- **Classic Dashboard:** `http://127.0.0.1:8501/classic`

### Option 3: Regenerate from Fresh Data
Run the generator script anytime new automation data arrives:
```powershell
python "step_4_reporting\Modern and Interactive Dashboard\generate_modern_dashboard.py"
```
