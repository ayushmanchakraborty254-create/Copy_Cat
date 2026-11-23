---
name: copycat-adb
description: >-
  Connects to and interacts with an Android device or emulator via Android Debug
  Bridge (ADB). Use when the user wants to inspect a connected Android phone, capture
  screenshots for app reverse-engineering, launch apps, send taps or swipes, type
  text, scroll pages, or test mobile app flows on real hardware in Copy-Cat.
---

# copycat-adb

Controls a connected Android phone or emulator using Android Debug Bridge (ADB)
to capture reference screens, inspect device specifications, and execute user flows.

Designed to assist:
- **`copycat-recon`**: Capture reference screenshots directly from a live app on your phone.
- **`copycat-test`**: Drive mobile app interaction flows (tap, scroll, text entry, navigation).

Helper script:
`python adb/adb_controller.py <command>`

All commands support the `--json` flag for machine-readable output.

## Safety Guidelines

1. **Clean-room reference only**: Screenshots are saved to `replica/screens/` as layout references and are never included in the shippable clone.
2. **Standard permissions**: No root access or device modifications.
3. **No privacy leaks**: Do not dump personal user data, accounts, contacts, or messages.
4. **Explicit actions**: Confirm before launching unknown or destructive actions.

## Step 1: Check Connection and Device Info

Verify ADB is installed and a device is connected:

```bash
python adb/adb_controller.py version
python adb/adb_controller.py devices
```

If unauthorized, ask the user to unlock the phone and tap "Allow USB debugging".

Query device specifications (model, Android version, resolution, density):

```bash
python adb/adb_controller.py info
```

## Step 2: Capture Screenshots for Reconnaissance

When reverse-engineering an app, capture the active screen:

```bash
python adb/adb_controller.py screenshot --output replica/screens/screen_name.png
```

Captured screenshots can immediately be analyzed for layout, colors, typography,
and component hierarchy to populate `replica/recon.md` and `replica/features.csv`.

## Step 3: Mobile Flow Navigation and Testing

Interact with the app under test:

- **Launch application**:
  ```bash
  python adb/adb_controller.py launch com.example.package
  ```

- **Tap coordinate**:
  ```bash
  python adb/adb_controller.py tap <X> <Y>
  ```

- **Scroll down or up**:
  ```bash
  python adb/adb_controller.py scroll down
  python adb/adb_controller.py scroll up
  ```

- **Swipe**:
  ```bash
  python adb/adb_controller.py swipe <X1> <Y1> <X2> <Y2> --duration 300
  ```

- **Type text**:
  ```bash
  python adb/adb_controller.py text "Sample input text"
  ```

- **Hardware and navigation buttons**:
  ```bash
  python adb/adb_controller.py key back
  python adb/adb_controller.py key home
  python adb/adb_controller.py key recents
  ```

- **Close application**:
  ```bash
  python adb/adb_controller.py close com.example.package
  ```
