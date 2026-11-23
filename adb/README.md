# Copy-Cat ADB Integration Extension

Optional, modular Android Debug Bridge (ADB) integration for Copy-Cat. Enables live app reconnaissance, automated screenshot capture, flow verification, and user interaction testing directly on connected Android hardware.

## Features

- **Device Diagnostics**: Automatically locates `adb` and queries device model, manufacturer, brand, Android OS release, SDK API level, display resolution, and screen density.
- **Visual Capture**: Takes high-resolution screenshots directly from the device and stores them inside `replica/screens/` for visual diffing and UI inspection.
- **Clean App Flow Exploration**: Launches apps by package name via the Android launcher intent and closes them cleanly without requiring root access.
- **Input & Gesture Control**: Supports tapping coordinates, swiping, vertical scrolling, typing text, and hardware/navigation buttons (Back, Home, Recents, Power, Enter).
- **Graceful Error Handling**: Detects disconnected devices, offline states, and unauthorized debugging permissions with clear recovery instructions.
- **Agent and Script Friendly**: Full CLI with `--json` output format for seamless consumption by Antigravity or custom automation scripts.

## Safety and Security Standards

This extension strictly adheres to responsible automation principles:

1. **No Root Required**: Operates entirely within standard Android developer shell capabilities.
2. **Security Intact**: Does not bypass lockscreens, biometric security, or Android OS permission models.
3. **Privacy First**: Does not inspect private personal data, contacts, messages, or unapproved directories.
4. **No Silent Changes**: Does not silently install, uninstall, or tamper with system packages.
5. **Clean Room Verification**: Screenshots captured are stored in `replica/screens/` as reference for reverse-engineering layout metrics, never embedded into production code.

## Quick Start

### 1. Verify ADB and Connected Devices

Check ADB version:
```bash
python adb/adb_controller.py version
```

List connected devices:
```bash
python adb/adb_controller.py devices
```

Inspect hardware and display properties:
```bash
python adb/adb_controller.py info
```

### 2. Capture Reference Screenshots for Reconnaissance

Capture the current screen and save to `replica/screens/`:
```bash
python adb/adb_controller.py screenshot
```

Or specify a custom destination path:
```bash
python adb/adb_controller.py screenshot --output replica/screens/login_screen.png
```

### 3. Launch and Control Applications

Launch an application by its package name:
```bash
python adb/adb_controller.py launch com.example.targetapp
```

Tap a button or UI element at coordinates (X, Y):
```bash
python adb/adb_controller.py tap 540 1200
```

Scroll down to view more content:
```bash
python adb/adb_controller.py scroll down
```

Scroll up:
```bash
python adb/adb_controller.py scroll up
```

Swipe with custom coordinates and duration (ms):
```bash
python adb/adb_controller.py swipe 540 1600 540 400 --duration 300
```

Type text into a focused input field:
```bash
python adb/adb_controller.py text "hello@example.com"
```

Press system buttons:
```bash
python adb/adb_controller.py key back
python adb/adb_controller.py key home
python adb/adb_controller.py key recents
```

Close the app when testing is finished:
```bash
python adb/adb_controller.py close com.example.targetapp
```

### 4. JSON Output for Automated Tooling

Every command supports `--json`:
```bash
python adb/adb_controller.py info --json
```

Example JSON response:
```json
{
  "serial": "R58M123456",
  "manufacturer": "Samsung",
  "brand": "samsung",
  "model": "SM-S918B",
  "android_version": "14",
  "sdk_level": "34",
  "screen_resolution": "1440x3088",
  "screen_density": "500"
}
```

## Python API

You can also import and use `ADBController` in your own Python scripts:

```python
from adb.adb_controller import ADBController

controller = ADBController()

# Check availability
if controller.is_available():
    # Retrieve device info
    info = controller.get_device_info()
    print("Connected Device:", info["manufacturer"], info["model"])

    # Capture screen
    path = controller.take_screenshot("replica/screens/dashboard.png")
    print("Screenshot saved to:", path)

    # Perform navigation
    controller.tap(500, 1000)
    controller.input_text("Search query")
    controller.key_event("enter")
```
