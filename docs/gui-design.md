# GUI Design Specification

## Overview

The Telegram Signal Extractor desktop application provides a user-friendly interface for monitoring signal extraction in real-time, with background operation capability via system tray integration.

## Design Principles

1. **Simplicity**: Clean, uncluttered interface focusing on essential information
2. **Visibility**: Clear status indicators showing system health at a glance
3. **Accessibility**: Important functions within 1-2 clicks
4. **Responsiveness**: UI remains responsive during background processing
5. **Non-intrusive**: Runs in background without demanding attention

## Application Windows

### 1. Main Window

The primary interface showing system status and recent activity.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Telegram Signal Extractor                            [_] [□] [X]         │
├─────────────────────────────────────────────────────────────────────────┤
│ File    Settings    View    Help                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Status: ● Connected    │   Uptime: 02:34:15   │   Signals: 47      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────┬─────────────────────────────────────────────┤
│ CHANNELS & METRICS        │ RECENT SIGNALS                              │
│                           │                                             │
│ ┌─ Monitored Channels ─┐ │ ┌─────────────────────────────────────────┐ │
│ │                       │ │ │ Time    Chan.  Symbol  Dir   Entry     │ │
│ │ ● Nick Alpha Trader   │ │ ├─────────────────────────────────────────┤ │
│ │   Last: 2 min ago     │ │ │ 16:34  Nick   XAUUSD  SELL  4746.50    │ │
│ │   Signals: 28         │ │ │ 16:32  Gary   XAUUSD  BUY   4930       │ │
│ │                       │ │ │ 16:25  Nick   XAUUSD  SELL  4742       │ │
│ │ ● Gary Gold Legacy    │ │ │ 16:18  Gary   XAUUSD  BUY   4926       │ │
│ │   Last: 5 min ago     │ │ │ 16:12  Nick   XAUUSD  SELL  4750       │ │
│ │   Signals: 19         │ │ │ ...                                     │ │
│ │                       │ │ │                                         │ │
│ │ [+ Add Channel]       │ │ │ (Double-click row to see details)      │ │
│ └───────────────────────┘ │ └─────────────────────────────────────────┘ │
│                           │                                             │
│ ┌─ System Metrics ─────┐ │ [ View All ]  [ Export CSV ]  [ Clear ]    │
│ │                       │ │                                             │
│ │ Messages: 1,234       │ │                                             │
│ │ Extracted: 47         │ ├─────────────────────────────────────────────┤
│ │ Errors: 3             │ │ ACTIVITY LOG                                │
│ │ Success: 94.0%        │ │                                             │
│ │                       │ │ ┌─────────────────────────────────────────┐ │
│ │ Last Error:           │ │ │ 16:34:12  New signal extracted          │ │
│ │   5 min ago           │ │ │ 16:32:05  Message processed             │ │
│ │                       │ │ │ 16:30:00  Connection healthy             │ │
│ │ [View Error Log]      │ │ │ 16:25:33  Signal saved to CSV           │ │
│ └───────────────────────┘ │ │ 16:18:44  New signal extracted          │ │
│                           │ └─────────────────────────────────────────┘ │
│ ┌─ Actions ────────────┐ │                                             │
│ │ [  Start/Stop  ]      │ │                                             │
│ │ [   Settings   ]      │ │                                             │
│ │ [ Open CSV File]      │ │                                             │
│ └───────────────────────┘ │                                             │
├───────────────────────────┴─────────────────────────────────────────────┤
│ Monitoring 2 channels  |  Last update: 16:34:15  |  CSV: signals.csv   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Components

**Status Bar (Top)**
- Connection indicator: ● Green (Connected), ● Yellow (Warning), ● Red (Error), ● Gray (Stopped)
- Uptime counter (HH:MM:SS)
- Total signals extracted (today or session)

**Left Panel: Channels & Metrics**
- **Channel List**:
  - Each channel shows:
    - Status indicator (● Green = active)
    - Channel name
    - Time since last message
    - Number of signals extracted
  - "+ Add Channel" button
  - Click channel to view details

- **System Metrics**:
  - Messages received counter
  - Signals extracted counter
  - Errors counter
  - Success rate percentage
  - Last error timestamp
  - "View Error Log" button

- **Action Buttons**:
  - Start/Stop Monitoring toggle
  - Settings (opens Settings dialog)
  - Open CSV File (opens in Excel/default app)

**Center/Right Panel: Signals & Activity**
- **Recent Signals Table**:
  - Shows last 20 signals
  - Columns: Time, Channel, Symbol, Direction, Entry, SL, TPs
  - Double-click row opens Signal Details dialog
  - Auto-scrolls to show newest
  - Buttons: "View All", "Export CSV", "Clear"

- **Activity Log**:
  - Real-time event stream
  - Shows processing activity
  - Auto-scrolls
  - Color-coded by event type

**Bottom Status Bar**
- Current operation status
- Last update timestamp
- Output CSV file path

### 2. System Tray

The application can be minimized to system tray for background operation.

#### Tray Icon States

```
Normal Tray Icon:
  ● Green  = Connected and running normally
  ● Yellow = Warning (connection issues, high error rate)
  ● Red    = Critical error or disconnected
  ● Gray   = Stopped/Not monitoring

Animation (optional):
  Pulse or spin during active signal extraction
```

#### Context Menu

```
┌────────────────────────────────────┐
│ ● Telegram Signal Extractor        │  ← Status indicator
├────────────────────────────────────┤
│ Show Window                        │  ← Restore main window
│ ────────────────────────────       │
│ Recent Signals                  ▶  │  ← Submenu
│ ────────────────────────────       │
│ ✓ Monitoring (Click to stop)      │  ← Toggle
│ ────────────────────────────       │
│ Open Logs Folder                   │
│ Open Output CSV                    │
│ ────────────────────────────       │
│ Settings...                        │
│ About...                           │
│ ────────────────────────────       │
│ Exit                               │  ← Close application
└────────────────────────────────────┘
```

**Recent Signals Submenu:**
```
┌────────────────────────────────────┐
│ 16:34 - XAUUSD SELL @ 4746.50     │
│ 16:32 - XAUUSD BUY @ 4930         │
│ 16:25 - XAUUSD SELL @ 4742        │
│ ────────────────────────────       │
│ Show All...                        │
└────────────────────────────────────┘
```

### 3. Settings Dialog

Multi-tab configuration interface.

```
┌───────────────────────────────────────────────────────────┐
│ Settings                                     [?] [X]       │
├───────────────────────────────────────────────────────────┤
│ ┌─────────────┬───────────────────────────────────────┐   │
│ │ Telegram    │ TELEGRAM CONFIGURATION                │   │
│ │ Channels    │                                       │   │
│ │ Extraction  │ API Credentials:                      │   │
│ │ Output      │   API ID:      [38958887________]     │   │
│ │ GUI         │   API Hash:    [********************] │   │
│ │             │   Phone:       [+1234567890________]  │   │
│ │             │                                       │   │
│ │             │ Session:                              │   │
│ │             │   Status: ● Connected                 │   │
│ │             │   [Reconnect]  [Clear Session]        │   │
│ │             │                                       │   │
│ │             │ ☐ Remember credentials                │   │
│ │             │                                       │   │
│ └─────────────┴───────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────┤
│                             [Apply] [OK] [Cancel]         │
└───────────────────────────────────────────────────────────┘
```

#### Tab 1: Telegram
- API ID input field
- API Hash input field (masked)
- Phone number input
- Connection status
- Reconnect button
- Clear session button
- Remember credentials checkbox

#### Tab 2: Channels
```
│ CHANNEL MANAGEMENT                                        │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐  │
│ │ ☑ nickalphatrader                     [Edit] [Remove] │
│ │   https://t.me/nickalphatrader                       │
│ │                                                       │
│ │ ☑ GaryGoldLegacy                      [Edit] [Remove] │
│ │   https://t.me/GaryGoldLegacy                        │
│ └─────────────────────────────────────────────────────┘  │
│                                                           │
│ [+ Add Channel]                                           │
│                                                           │
│ Add Channel URL or Username:                              │
│ [_____________________________________________] [Add]      │
```

#### Tab 3: Extraction
```
│ EXTRACTION SETTINGS                                       │
│                                                           │
│ Minimum Confidence: [0.75_____] (0.0 - 1.0)              │
│   Signals below this threshold will be logged as errors  │
│                                                           │
│ Validation:                                               │
│   ☑ Validate price logic (SL/TP relative to entry)      │
│   ☑ Check symbol against allowed list                   │
│   ☐ Detect duplicate signals                            │
│                                                           │
│ Allowed Symbols:                                          │
│   [XAUUSD, EURUSD, GBPUSD, BTCUSD_________________]      │
```

#### Tab 4: Output
```
│ OUTPUT CONFIGURATION                                      │
│                                                           │
│ CSV File:                                                 │
│   [C:\...\output\signals.csv___________] [Browse]        │
│                                                           │
│ Error Log:                                                │
│   [C:\...\logs\extraction_errors.jsonl_] [Browse]        │
│                                                           │
│ System Log:                                               │
│   [C:\...\logs\system.log_____________] [Browse]         │
│                                                           │
│ CSV Options:                                              │
│   Encoding: [UTF-8 ▼]                                    │
│   ☑ Append to existing file                              │
│   Max file size: [10_] MB (0 = unlimited)                │
```

#### Tab 5: GUI
```
│ GUI PREFERENCES                                           │
│                                                           │
│ Appearance:                                               │
│   Theme: [● Light  ○ Dark  ○ System]                     │
│                                                           │
│ Notifications:                                            │
│   ☑ Enable desktop notifications                         │
│   ☑ New signals extracted                                │
│   ☑ Errors and warnings                                  │
│   ☐ Play sound on notification                           │
│                                                           │
│ Behavior:                                                 │
│   ☑ Minimize to tray on close                            │
│   ☑ Start minimized                                      │
│   ☑ Start with Windows                                   │
│   Refresh interval: [1000_] ms                           │
│                                                           │
│ Window:                                                   │
│   ☑ Remember window size and position                    │
│   [Reset to Default Size]                                │
```

### 4. Signal Details Dialog

Shows complete information about a selected signal.

```
┌───────────────────────────────────────────────────────────┐
│ Signal Details                                   [X]      │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ Message Information:                                      │
│   Channel:    nickalphatrader                            │
│   Timestamp:  2026-01-24 16:34:12                        │
│   Message ID: 12345                                      │
│                                                           │
│ Trading Signal:                                           │
│   Symbol:         XAUUSD (Gold)                          │
│   Direction:      SELL                                   │
│   Entry Range:    4746.50 - 4750.50                      │
│   Stop Loss:      4752.50                                │
│   Take Profit 1:  4730.00                                │
│   Take Profit 2:  4720.00                                │
│                                                           │
│ Extraction Info:                                          │
│   Confidence:     100%                                   │
│   Extracted At:   2026-01-24 16:34:12                    │
│   Status:         ✓ Valid                                │
│                                                           │
│ Raw Message:                                              │
│ ┌─────────────────────────────────────────────────────┐  │
│ │ GOLD SELL                                           │  │
│ │                                                     │  │
│ │ Gold sell now @4746.50-4750.50                      │  │
│ │                                                     │  │
│ │ sl: 4752.50                                         │  │
│ │                                                     │  │
│ │ tp1: 4730                                           │  │
│ │ tp2: 4720                                           │  │
│ └─────────────────────────────────────────────────────┘  │
│                                                           │
│                      [Copy to Clipboard] [Close]         │
└───────────────────────────────────────────────────────────┘
```

### 5. Error Log Viewer

Displays extraction failures for review.

```
┌─────────────────────────────────────────────────────────────┐
│ Extraction Error Log                              [_] [X]   │
├─────────────────────────────────────────────────────────────┤
│ Filters: [All Channels ▼] [Last 7 days ▼]  [Refresh]       │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │Time      Channel    Reason              [Actions]       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │16:20:05  Nick      Low confidence       [View] [Retry]  │ │
│ │15:45:22  Gary      Missing SL           [View] [Retry]  │ │
│ │14:30:11  Nick      Invalid format       [View] [Mark]   │ │
│ │...                                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Selected Error Details:                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Channel: nickalphatrader                                │ │
│ │ Time: 16:20:05                                          │ │
│ │ Reason: Confidence score (0.65) below threshold (0.75)  │ │
│ │                                                         │ │
│ │ Message:                                                │ │
│ │ Gold might go down around 4750 area...                 │ │
│ │                                                         │ │
│ │ Extracted Fields:                                       │ │
│ │   Symbol: XAUUSD ✓                                      │ │
│ │   Direction: SELL ? (uncertain)                         │ │
│ │   Entry: 4750 ✓                                         │ │
│ │   SL: (missing)                                         │ │
│ │   TP: (missing)                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Actions:                                                    │
│ [Retry Extraction] [Mark as Reviewed] [Export Selected]    │
│                                            [Close]          │
└─────────────────────────────────────────────────────────────┘
```

### 6. First-Run Setup Wizard

Guides users through initial configuration.

```
┌───────────────────────────────────────────────────────────┐
│ Telegram Signal Extractor - Setup Wizard        [?] [X]  │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    Welcome!                         │ │
│  │                                                     │ │
│  │   This wizard will help you configure              │ │
│  │   the Telegram Signal Extractor.                   │ │
│  │                                                     │ │
│  │   You will need:                                    │ │
│  │   • Telegram API credentials                       │ │
│  │   • Access to signal channels                      │ │
│  │   • Phone number for authentication                │ │
│  │                                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  Step 1 of 4: Telegram API Setup                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                           │
│                          [< Back]  [Next >]  [Cancel]    │
└───────────────────────────────────────────────────────────┘
```

**Wizard Steps:**
1. Welcome
2. Telegram API credentials
3. Phone authentication (with code input)
4. Add channels
5. Set output paths
6. Finish (start monitoring)

### 7. Notifications

Desktop notifications appear in Windows notification area.

```
┌─────────────────────────────────────────┐
│  [📊]  New Signal Extracted             │
│                                         │
│  XAUUSD SELL @ 4746.50-4750.50         │
│  SL: 4752.50  TPs: 4730, 4720          │
│                                         │
│  From: nickalphatrader                 │
│  ────────────────────────────────────  │
│  Telegram Signal Extractor             │
└─────────────────────────────────────────┘
```

**Notification Types:**
- New Signal Extracted (green)
- Extraction Error (yellow)
- Connection Lost (red)
- Connection Restored (green)

## Color Scheme

### Light Theme
- Background: #FFFFFF
- Panel Background: #F5F5F5
- Text: #212121
- Success: #4CAF50 (Green)
- Warning: #FFC107 (Amber)
- Error: #F44336 (Red)
- Info: #2196F3 (Blue)
- Disabled: #9E9E9E (Gray)

### Dark Theme (Optional)
- Background: #1E1E1E
- Panel Background: #2D2D2D
- Text: #E0E0E0
- Success: #66BB6A
- Warning: #FFD54F
- Error: #EF5350
- Info: #42A5F5
- Disabled: #757575

## Icons

### Required Icons
- Application icon (16x16, 32x32, 48x48, 256x256)
- Tray icons (16x16 in 4 colors: green, yellow, red, gray)
- Start button icon
- Stop button icon
- Settings gear icon
- Add (+) icon
- Remove (×) icon
- Refresh icon
- Export icon
- Notification icons

### Icon Sources
- Qt built-in icons
- QtAwesome font icons
- Custom PNG/SVG icons

## Responsive Behavior

### Minimum Window Size
- Width: 800px
- Height: 600px

### Window States
- Normal: Full layout as shown
- Minimized: To taskbar (standard Windows behavior)
- Minimized to Tray: Hidden from taskbar
- Maximized: All panels expand proportionally

### Panel Resizing
- Left panel: Fixed width (250px)
- Center/Right panels: Expandable
- Splitter between panels allows resizing

## Accessibility

- Keyboard shortcuts for common actions
- Tab navigation through all controls
- Screen reader compatible labels
- High contrast mode support
- Configurable font sizes (future)

## Performance Considerations

- Update signals table max once per second (avoid flooding)
- Activity log max 100 entries (auto-trim oldest)
- Error log paginated (show 50 at a time)
- Lazy load signal details (only when opened)
- Background worker in separate thread (non-blocking UI)

## Platform-Specific Features

### Windows Integration
- Native window decorations
- System tray (Windows notification area)
- Windows notifications (Action Center)
- File associations (.csv opens in Excel)
- Startup folder shortcut

### Future Enhancements
- macOS support (menu bar extra)
- Linux support (system tray via Qt)
- Cross-platform packaging

## User Experience Flow

### First Launch
1. User starts application
2. Setup wizard appears
3. User enters Telegram credentials
4. Phone authentication (code input)
5. User adds channels
6. Configuration saved
7. Main window appears
8. Monitoring starts automatically

### Daily Use
1. Application runs in tray
2. Notifications appear when signals extracted
3. User can click tray icon to view recent signals
4. User can open main window for detailed view
5. Application runs 24/7 in background

### Error Handling
1. Extraction error occurs
2. Error notification (optional)
3. Error logged to viewer
4. User can review and retry
5. System continues monitoring

## Implementation Notes

### Technology Stack
- **Framework**: PySide6 (Qt for Python)
- **Threading**: QThread for background work
- **Async**: asyncio for Telegram client (in worker thread)
- **Signals**: Qt Signals/Slots for thread-safe communication
- **Styling**: QSS (Qt Style Sheets) for theming
- **Notifications**: QSystemTrayIcon.showMessage()

### Project Structure
```
src/gui/
├── __init__.py
├── app.py                 # Application entry point
├── main_window.py         # Main window implementation
├── system_tray.py         # Tray icon and menu
├── settings_dialog.py     # Settings multi-tab dialog
├── signal_details.py      # Signal details dialog
├── error_log_viewer.py    # Error log viewer
├── setup_wizard.py        # First-run wizard
├── controller.py          # App controller (coordinates GUI + backend)
├── worker.py              # Background worker thread
├── notifications.py       # Notification manager
├── widgets/               # Custom widgets
│   ├── channel_widget.py
│   ├── metrics_widget.py
│   ├── signal_table.py
│   └── activity_log.py
└── resources/             # Icons, styles, etc.
    ├── icons/
    ├── styles.qss
    └── resources.qrc
```

## Testing Checklist

- [ ] Window opens and displays correctly
- [ ] All buttons and controls respond
- [ ] Minimize to tray works
- [ ] Restore from tray works
- [ ] Tray icon updates based on status
- [ ] Tray context menu functions work
- [ ] Settings save and load correctly
- [ ] Signals display in real-time
- [ ] Error log viewer shows errors
- [ ] Notifications appear correctly
- [ ] Start/stop monitoring works
- [ ] Thread communication is stable
- [ ] No UI freezing during processing
- [ ] Application closes cleanly
- [ ] Auto-start works
- [ ] All dialogs open and close properly

## Future Enhancements

- Dark mode theme
- Customizable dashboard layouts
- Charts and analytics
- Signal filtering and search
- Export to multiple formats
- Web dashboard (optional)
- Mobile notifications (via web service)
- Multi-language support
- Voice notifications (text-to-speech)
