# GUI Application Guide

## Overview

The Telegram Signal Extractor now includes a complete **Desktop GUI Application** built with PySide6 (Qt for Python). The GUI provides a user-friendly interface for monitoring signal extraction in real-time, with background operation capability via system tray integration.

**Phase 6 Status**: ✅ **Complete and Functional**

---

## Quick Start

### Launch the GUI

**Option 1: Windows Batch File**
```bash
run_gui.bat
```

**Option 2: Python Script**
```bash
python run_gui.py
```

**Option 3: Direct Module**
```bash
python -m src.gui.app
```

---

## Main Window

### Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Telegram Signal Extractor                         [_] [□] [X]   │
├─────────────────────────────────────────────────────────────────┤
│ File    Settings    View    Help                                │
├─────────────────────────────────────────────────────────────────┤
│ Status: ● Connected  |  Uptime: 02:34:15  |  Signals: 47        │
├──────────────────────┬──────────────────────────────────────────┤
│ CHANNELS & METRICS   │ RECENT SIGNALS                           │
│                      │                                          │
│ Monitored Channels   │ Time   Chan.  Symbol  Dir   Entry       │
│ ● nickalphatrader    │ 16:34  Nick   XAUUSD  SELL  4746.50     │
│ ● GaryGoldLegacy     │ 16:32  Gary   XAUUSD  BUY   4930        │
│                      │ ...                                      │
│ System Metrics       │                                          │
│ Messages: 1,234      │ ACTIVITY LOG                             │
│ Extracted: 47        │ 16:34:12  New signal extracted           │
│ Errors: 3            │ 16:32:05  Message processed              │
│ Success: 94.0%       │ 16:30:00  Connection healthy             │
│                      │                                          │
│ [Start/Stop]         │                                          │
│ [Settings]           │                                          │
│ [Open CSV]           │                                          │
└──────────────────────┴──────────────────────────────────────────┘
```

### Components

#### Top Status Bar
- **Connection Indicator**:
  - ● Green = Connected and running
  - ● Orange = Warning/Connecting
  - ● Red = Error
  - ● Gray = Stopped
- **Uptime Counter**: Shows how long the application has been running (HH:MM:SS)
- **Signal Count**: Total signals extracted in current session

#### Left Panel: Channels & Metrics

**Monitored Channels:**
- Shows all configured channels from config.yaml
- ● Green dot = Channel active
- Last message time
- Signal count per channel

**System Metrics:**
- Messages processed count
- Signals extracted count
- Errors count
- Success rate percentage (color-coded)

**Action Buttons:**
- **Start/Stop Monitoring**: Toggle signal extraction on/off
- **Settings**: Open settings dialog
- **Open CSV**: Open signals.csv in default application (Excel)

#### Right Panel: Signals & Activity

**Recent Signals Table:**
- Last 50 signals displayed
- Columns: Time, Channel, Symbol, Direction, Entry, SL, TP1
- Color-coded directions (BUY=Green, SELL=Red)
- Double-click row to view full signal details (coming soon)
- Auto-scrolls to show newest signals

**Activity Log:**
- Real-time event stream
- Color-coded by type:
  - Blue = Info
  - Green = Success
  - Orange = Warning
  - Red = Error
  - Gray = Debug
- Auto-scrolls and auto-trims (max 100 entries)

#### Bottom Status Bar
- Current operation status
- CSV output file path

---

## System Tray Integration

### Minimize to Tray

When you close the main window, the application minimizes to the system tray instead of exiting. This allows it to run silently in the background while continuing to monitor channels.

### Tray Icon States

- **● Green**: Connected and running normally
- **● Orange**: Warning (connection issues)
- **● Red**: Critical error or disconnected
- **● Gray**: Stopped/Not monitoring

### Tray Context Menu

Right-click the tray icon to access:

```
● Telegram Signal Extractor
─────────────────────────
Show Window
─────────────────────────
Recent Signals            ▶
─────────────────────────
Start/Stop Monitoring
─────────────────────────
Open Logs Folder
Open Output CSV
─────────────────────────
Settings...
About...
─────────────────────────
Exit
```

### Desktop Notifications

When enabled, the application shows desktop notifications for:
- New signals extracted
- Errors and warnings
- Connection status changes

---

## Menu Bar

### File Menu
- **Open CSV File**: Opens output/signals.csv in Excel or default CSV viewer
- **Open Logs Folder**: Opens the logs/ directory
- **Exit**: Closes the application completely

### Settings Menu
- **Preferences**: Opens the Settings dialog

### View Menu
- **Refresh**: Refreshes all displays
- **Clear Activity Log**: Clears the activity log

### Help Menu
- **About**: Shows application information
- **Documentation**: Opens README.md

---

## Settings Dialog

### Telegram Tab
- API ID, API Hash, Phone number
- Session status
- Reconnect and Clear Session buttons

### Channels Tab
- Information about managing channels
- Link to edit config.yaml

### Extraction Tab
- Minimum Confidence threshold (0.0 - 1.0)
- Controls signal extraction sensitivity

### Output Tab
- CSV file path
- Error log path
- System log path
- Browse buttons to change paths

### GUI Tab
- Enable/disable desktop notifications
- Notification preferences (signals, errors)
- Minimize to tray on close
- Start minimized

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F5 | Refresh view |
| Ctrl+S | Open Settings |
| Ctrl+Q | Quit application |
| Ctrl+O | Open CSV file |

---

## Features

### ✅ Implemented in Phase 6

1. **Main Window with Dashboard**
   - Real-time status indicators
   - Channel monitoring display
   - System metrics
   - Signal table with recent extractions
   - Activity log

2. **System Tray Integration**
   - Minimize to tray
   - Status indicator icon
   - Context menu
   - Restore window

3. **Background Worker Thread**
   - Runs Telegram monitoring in separate thread
   - Qt Signals/Slots for thread-safe communication
   - Non-blocking UI

4. **Settings Dialog**
   - Multi-tab configuration
   - Telegram credentials
   - Extraction settings
   - Output paths
   - GUI preferences

5. **Desktop Notifications**
   - New signal alerts
   - Error notifications
   - Connection status

6. **Real-time Updates**
   - Signal table updates automatically
   - Metrics refresh every second
   - Activity log streams events

---

## Technical Architecture

### Component Structure

```
src/gui/
├── app.py                    # Application entry point
├── main_window.py            # Main window implementation
├── system_tray.py            # System tray icon & menu
├── worker.py                 # Background worker thread
├── controller.py             # App controller (GUI ↔ Backend)
├── settings_dialog.py        # Settings dialog
└── widgets/
    ├── channel_widget.py     # Channel list widget
    ├── metrics_widget.py     # Metrics display widget
    ├── signal_table.py       # Signal table widget
    └── activity_log.py       # Activity log widget
```

### Threading Model

- **Main Thread**: Qt GUI event loop (UI updates, user interactions)
- **Worker Thread**: Asyncio event loop (Telegram monitoring, signal extraction)
- **Communication**: Qt Signals/Slots (thread-safe)

### Signals

Worker Thread → GUI:
- `status_changed`: Connection status updates
- `signal_extracted`: New signal data
- `error_occurred`: Error messages
- `message_received`: Message processing events
- `stats_updated`: Statistics updates
- `log_message`: Log entries

---

## Troubleshooting

### GUI Won't Start

**Error: "No module named 'PySide6'"**
```bash
pip install -r requirements.txt
```

**Error: "Config file not found"**
```bash
# Make sure you're in the project root
cd c:\Projects\nmasuki\TellegramSignals
```

### GUI Freezes

- The GUI should never freeze - background work runs in separate thread
- If it freezes, check logs/system.log for errors
- Restart the application

### Tray Icon Not Showing

- Windows: Check notification area settings
- Make sure system tray is enabled in GUI preferences

### Notifications Not Appearing

- Check Windows notification settings
- Enable notifications in GUI Settings → GUI tab
- Make sure "Focus Assist" is not blocking notifications

### Can't Connect to Telegram

- Verify credentials in Settings → Telegram tab
- Check .env file has correct API ID, API Hash, and Phone
- Try "Clear Session" and reconnect
- Check logs/system.log for detailed error messages

---

## Comparison: Console vs. GUI

| Feature | Console App | GUI App |
|---------|------------|---------|
| **Interface** | Terminal/Command line | Desktop Window |
| **Status Visibility** | Log messages only | Visual indicators, real-time dashboard |
| **Background Operation** | Requires terminal open | Runs in system tray |
| **Signal Viewing** | Check CSV file manually | Live table in UI |
| **Configuration** | Edit .env and config.yaml | Settings dialog (partial) |
| **Monitoring** | Log files | Activity log + notifications |
| **User Friendliness** | Technical users | All users |

**Both applications use the same backend** - they just have different interfaces.

---

## Next Steps

### To Use the GUI

1. Launch with `run_gui.bat` or `python run_gui.py`
2. Wait for connection (status bar shows "Connected")
3. Monitor the signal table for new extractions
4. Check activity log for detailed events
5. Minimize to tray to run in background
6. Right-click tray icon to access quick actions

### To Use Console App

```bash
python src/main.py
```

The console app continues to work as before.

---

## Known Limitations

1. **Settings Dialog**: Changes require restart to take effect (full implementation would update config dynamically)
2. **Channel Management**: Must edit config.yaml manually (GUI editing coming in future)
3. **Signal Details**: Double-click signal for details not yet implemented
4. **Error Log Viewer**: Separate window for errors not yet implemented
5. **First-Run Wizard**: Manual setup required (wizard coming in future)

---

## Future Enhancements

Possible improvements for future phases:

- [ ] Dark mode theme
- [ ] Signal details dialog
- [ ] Error log viewer window
- [ ] Dynamic channel management (add/remove via GUI)
- [ ] Charts and analytics
- [ ] Export to multiple formats
- [ ] First-run setup wizard
- [ ] Signal filtering and search
- [ ] Custom dashboard layouts

---

## Files Created in Phase 6

### Core GUI Files
- src/gui/app.py
- src/gui/main_window.py
- src/gui/system_tray.py
- src/gui/worker.py
- src/gui/controller.py
- src/gui/settings_dialog.py

### Widget Files
- src/gui/widgets/channel_widget.py
- src/gui/widgets/metrics_widget.py
- src/gui/widgets/signal_table.py
- src/gui/widgets/activity_log.py

### Launch Scripts
- run_gui.py (Python launcher)
- run_gui.bat (Windows batch file)

### Documentation
- GUI_GUIDE.md (this file)

---

## Support

If you encounter issues:

1. Check [logs/system.log](logs/system.log) for errors
2. Review [TESTING.md](TESTING.md) troubleshooting section
3. Verify configuration in [config/config.yaml](config/config.yaml)
4. Ensure .env has correct credentials

---

**Version**: 1.0
**Phase**: 6 Complete (Desktop GUI)
**Status**: Production Ready
**Date**: 2026-01-24

---

**Congratulations!** You now have a fully functional desktop GUI for the Telegram Signal Extractor. 🎉
