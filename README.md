# CPU Temperature Widget

A polished, lightweight Windows desktop widget that displays your CPU temperature in real-time with a beautiful translucent overlay.

![Widget Preview](https://via.placeholder.com/200x80/1e1e2e/cdd6f4?text=CPU:+52°C)

## Download

**[Download Latest Installer (Windows)](https://github.com/jaifar530/cpu-temp-widget/releases/latest)**

Just download and run `CPUTempWidget_Setup_1.1.0.exe` - no Python or command line needed!

## Features

- **Floating Widget**: Translucent, frameless overlay that stays on top of other windows
- **Real-time Monitoring**: Live CPU temperature updates with configurable refresh rate
- **Warning Alerts**: Text turns red when temperature exceeds threshold (default: 70°C)
- **HOT Indicator**: Pulsing "HOT" label appears after sustained high temperature
- **System Tray Integration**: Easy access from the notification area
- **Draggable**: Click and drag to reposition anywhere on screen
- **Position Memory**: Remembers its position between restarts
- **Lock Mode**: Lock position with click-through for zero interference
- **Multi-Monitor Support**: Works across multiple displays with DPI awareness

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| UI Framework | PyQt6 | Native look, excellent transparency/frameless support |
| Hardware Monitor | LibreHardwareMonitor + WMI | Most reliable Windows CPU temp source |
| Config Storage | JSON file in AppData | Simple, human-readable |
| Packaging | PyInstaller + Inno Setup | Single portable .exe with Windows installer |

## Installation

### Option 1: Run from Source

1. **Install Python 3.10+** from [python.org](https://www.python.org/downloads/)

2. **Clone or download** this repository

3. **Install dependencies**:
   ```bash
   cd cpu_temp_widget
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

### Option 2: Build Portable Executable

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the executable**:
   ```bash
   python build.py
   ```

3. **Find the executable** in `dist/CPUTempWidget.exe`

## How to Use

### Widget Controls

| Action | Result |
|--------|--------|
| **Left-click + Drag** | Move widget to new position |
| **Right-click** | Open context menu |

### Right-click Menu

- **Lock Position**: Prevents accidental dragging and enables click-through mode
- **Settings...**: Open the settings dialog
- **Exit**: Close the application

### System Tray

The app runs in the system tray (notification area) next to the clock.

| Action | Result |
|--------|--------|
| **Left-click tray icon** | Toggle widget visibility |
| **Right-click tray icon** | Open tray menu |

### Tray Menu

- **Show Widget**: Toggle widget on/off
- **Settings...**: Open settings dialog
- **Start with Windows**: Enable/disable auto-start
- **Exit**: Close the application completely

### Settings

Access settings from the widget right-click menu or tray menu:

| Setting | Description | Default |
|---------|-------------|---------|
| **Warning Threshold** | Temperature (°C) that triggers warning colors | 70°C |
| **Update Interval** | How often to refresh temperature | 1 second |
| **Text Size** | Widget text size (Small/Medium/Large) | Medium |
| **Transparency** | Background opacity (30%-90%) | 60% |
| **Always on Top** | Keep widget above other windows | On |
| **Start with Windows** | Launch automatically at startup | Off |
| **Reset Position** | Move widget back to default position | - |

## Administrator Privileges

**For accurate CPU temperature readings, run as Administrator.**

The app uses LibreHardwareMonitor to read hardware sensors, which requires elevated privileges on Windows. Without administrator rights:
- The app will still run
- Temperature may show as `--°C` or use simulated values
- A notification will appear on first run

### Running as Administrator

1. **From executable**: Right-click `CPUTempWidget.exe` → "Run as administrator"
2. **From source**: Run your terminal as Administrator, then `python main.py`

### Auto-start with Admin Rights

To start with Windows as Administrator:
1. Create a shortcut to the executable
2. Right-click shortcut → Properties → Shortcut tab → Advanced
3. Check "Run as administrator"
4. Place shortcut in Startup folder (`Win+R` → `shell:startup`)

## Temperature Color Guide

| State | Color | Meaning |
|-------|-------|---------|
| Normal | White/Light gray | Temperature below threshold |
| Warning | Red | Temperature at or above threshold |
| HOT (pulsing) | Red + indicator | High temp for 5+ seconds |
| Error | `--°C` with ⚠ icon | Unable to read temperature |

## Configuration Location

Settings are stored in:
```
%APPDATA%\CPUTempWidget\config.json
```

You can manually edit this file or delete it to reset all settings.

## Troubleshooting

### Widget shows `--°C`

- **Solution**: Run as Administrator for accurate readings
- **Alternative**: The app will use simulated values for demo purposes

### Widget disappeared

- **Solution**: Click the system tray icon or use tray menu → Show Widget
- **Alternative**: Delete config file to reset position

### Can't drag the widget

- **Solution**: The widget might be locked. Right-click → uncheck "Lock Position"

### High CPU usage

- **Solution**: Increase the update interval in Settings (try 2 seconds)

### Widget not saving position

- **Solution**: Check if `%APPDATA%\CPUTempWidget\` folder is writable
- **Alternative**: Run as Administrator

## Technical Details

- **Language**: Python 3.10+
- **UI Framework**: PyQt6
- **Hardware Access**: LibreHardwareMonitor (via pythonnet)
- **Config Format**: JSON

## Files Structure

```
cpu_temp_widget/
├── main.py              # Application entry point
├── widget.py            # Floating widget window
├── tray.py              # System tray icon
├── settings_dialog.py   # Settings window
├── temp_monitor.py      # Temperature monitoring thread
├── config.py            # Configuration management
├── build.py             # Build script
├── build.spec           # PyInstaller specification
├── requirements.txt     # Python dependencies
├── resources/
│   ├── styles.qss       # Qt stylesheet
│   └── icon_data.py     # Embedded icon data
└── README.md            # This file
```

## License

Copyright (c) 2024 Virtual Platforms LLC. All rights reserved.

## Support

For issues or feature requests, please open an issue on the project repository.
