#!/usr/bin/env python3
"""Copy-Cat ADB Controller.

Provides modular, safe, and optional Android Debug Bridge (ADB) automation
for app reconnaissance, screen capturing, flow testing, and device interaction.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime


class ADBError(Exception):
    """Base exception for ADB controller errors."""
    pass


class ADBNotFoundError(ADBError):
    """Raised when the ADB binary cannot be located."""
    pass


class DeviceNotFoundError(ADBError):
    """Raised when no connected Android device is found."""
    pass


class DeviceUnauthorizedError(ADBError):
    """Raised when the connected Android device is unauthorized."""
    pass


class ADBController:
    """Controller for Android Debug Bridge interactions."""

    COMMON_ADB_PATHS = [
        # Windows paths
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
        os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb.exe"),
        r"C:\Android\platform-tools\adb.exe",
        r"C:\platform-tools\adb.exe",
        # Unix paths
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
        "/usr/bin/adb",
        "/usr/local/bin/adb",
    ]

    KEY_CODES = {
        "back": 4,
        "home": 3,
        "recents": 187,
        "app_switch": 187,
        "power": 26,
        "volume_up": 24,
        "volume_down": 25,
        "enter": 66,
        "tab": 61,
        "space": 62,
        "delete": 67,
        "backspace": 67,
        "escape": 111,
    }

    def __init__(self, adb_path=None, serial=None):
        self.adb_path = adb_path or self.find_adb()
        self.serial = serial

    @classmethod
    def find_adb(cls):
        """Locate adb executable on the system."""
        # 1. Check PATH
        path = shutil.which("adb")
        if path and os.path.isfile(path):
            return os.path.abspath(path)

        # 2. Check known standard locations
        for candidate in cls.COMMON_ADB_PATHS:
            if candidate and os.path.isfile(candidate):
                return os.path.abspath(candidate)

        return None

    def is_available(self):
        """Check if ADB binary is found and executable."""
        if not self.adb_path:
            self.adb_path = self.find_adb()
        return bool(self.adb_path and os.path.isfile(self.adb_path))

    def _build_cmd(self, args, target_device=True):
        """Build full command array with optional serial targeting."""
        if not self.adb_path:
            raise ADBNotFoundError(
                "ADB executable not found. Please install Android Platform-Tools or set PATH."
            )
        cmd = [self.adb_path]
        if target_device and self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return cmd

    def run_cmd(self, args, target_device=True, check=True, text=True, timeout=30):
        """Execute an ADB command and return stdout/stderr."""
        cmd = self._build_cmd(args, target_device=target_device)
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=text,
                timeout=timeout,
                check=False
            )
            if check and res.returncode != 0:
                err_msg = res.stderr.strip() if text else str(res.stderr)
                raise ADBError(f"ADB command failed ({res.returncode}): {' '.join(cmd)}\n{err_msg}")
            return res
        except subprocess.TimeoutExpired as exc:
            raise ADBError(f"ADB command timed out after {timeout}s: {' '.join(cmd)}") from exc
        except OSError as exc:
            raise ADBError(f"Failed to execute ADB command: {exc}") from exc

    def get_version(self):
        """Return ADB version string and details."""
        res = self.run_cmd(["version"], target_device=False)
        output = res.stdout.strip()
        version_match = re.search(r"Android Debug Bridge version ([\d.]+)", output)
        return {
            "installed": True,
            "path": self.adb_path,
            "version": version_match.group(1) if version_match else "unknown",
            "raw": output
        }

    def list_devices(self):
        """List all connected Android devices with status."""
        res = self.run_cmd(["devices", "-l"], target_device=False)
        lines = res.stdout.strip().splitlines()
        devices = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]
            extra = {}
            for item in parts[2:]:
                if ":" in item:
                    k, v = item.split(":", 1)
                    extra[k] = v
            devices.append({
                "serial": serial,
                "state": state,
                "product": extra.get("product", ""),
                "model": extra.get("model", ""),
                "device": extra.get("device", ""),
                "transport_id": extra.get("transport_id", "")
            })
        return devices

    def select_active_device(self):
        """Determine and validate the active device serial."""
        devices = self.list_devices()
        if not devices:
            raise DeviceNotFoundError(
                "No Android devices connected. Please connect a phone via USB and enable USB Debugging."
            )

        if self.serial:
            matched = [d for d in devices if d["serial"] == self.serial]
            if not matched:
                raise DeviceNotFoundError(f"Specified device with serial '{self.serial}' not found.")
            target = matched[0]
        else:
            ready = [d for d in devices if d["state"] == "device"]
            if ready:
                target = ready[0]
                self.serial = target["serial"]
            else:
                target = devices[0]
                self.serial = target["serial"]

        if target["state"] == "unauthorized":
            raise DeviceUnauthorizedError(
                f"Device '{target['serial']}' is unauthorized. Check your phone screen and tap 'Allow USB debugging'."
            )
        if target["state"] == "offline":
            raise ADBError(
                f"Device '{target['serial']}' is offline. Please reconnect the USB cable or restart adb."
            )

        return target

    def get_device_info(self):
        """Retrieve detailed hardware, OS, and display properties of device."""
        self.select_active_device()

        def get_prop(prop_name):
            r = self.run_cmd(["shell", "getprop", prop_name])
            return r.stdout.strip()

        manufacturer = get_prop("ro.product.manufacturer")
        model = get_prop("ro.product.model")
        brand = get_prop("ro.product.brand")
        android_version = get_prop("ro.build.version.release")
        sdk_version = get_prop("ro.build.version.sdk")

        # Resolution
        size_res = self.run_cmd(["shell", "wm", "size"])
        size_match = re.search(r"(?:Physical size|size):\s*(\d+x\d+)", size_res.stdout)
        resolution = size_match.group(1) if size_match else "unknown"

        # Density
        density_res = self.run_cmd(["shell", "wm", "density"])
        density_match = re.search(r"(?:Physical density|density):\s*(\d+)", density_res.stdout)
        density = density_match.group(1) if density_match else "unknown"

        return {
            "serial": self.serial,
            "manufacturer": manufacturer,
            "brand": brand,
            "model": model,
            "android_version": android_version,
            "sdk_level": sdk_version,
            "screen_resolution": resolution,
            "screen_density": density
        }

    def take_screenshot(self, output_path=None):
        """Capture screenshot from device and save locally."""
        self.select_active_device()

        if not output_path:
            os.makedirs("replica/screens", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("replica", "screens", f"screen_{ts}.png")
        else:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

        abs_out = os.path.abspath(output_path)

        # Method 1: exec-out screencap -p (fastest direct binary stream)
        res = self.run_cmd(["exec-out", "screencap", "-p"], text=False, check=False)
        png_data = res.stdout

        # Verify PNG header (\x89PNG\r\n\x1a\n)
        if res.returncode == 0 and len(png_data) > 8 and png_data.startswith(b"\x89PNG\r\n\x1a\n"):
            with open(abs_out, "wb") as f:
                f.write(png_data)
            return abs_out

        # Method 2: fallback to sdcard write + pull
        remote_temp = "/sdcard/copycat_temp_screencap.png"
        self.run_cmd(["shell", "screencap", "-p", remote_temp])
        self.run_cmd(["pull", remote_temp, abs_out])
        self.run_cmd(["shell", "rm", remote_temp], check=False)
        return abs_out

    def launch_app(self, package_name):
        """Launch an application given its package name."""
        self.select_active_device()
        # Use monkey tool to launch default launcher activity without needing to know activity name
        cmd = ["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
        res = self.run_cmd(cmd)
        success = "Events injected: 1" in res.stdout or res.returncode == 0
        return {
            "package": package_name,
            "success": success,
            "output": res.stdout.strip()
        }

    def close_app(self, package_name):
        """Force-stop an application."""
        self.select_active_device()
        res = self.run_cmd(["shell", "am", "force-stop", package_name])
        return {
            "package": package_name,
            "closed": True,
            "output": res.stdout.strip()
        }

    def tap(self, x, y):
        """Tap screen coordinates (x, y)."""
        self.select_active_device()
        res = self.run_cmd(["shell", "input", "tap", str(int(x)), str(int(y))])
        return {"action": "tap", "x": int(x), "y": int(y), "success": res.returncode == 0}

    def swipe(self, x1, y1, x2, y2, duration_ms=300):
        """Perform swipe from (x1, y1) to (x2, y2)."""
        self.select_active_device()
        res = self.run_cmd([
            "shell", "input", "swipe",
            str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))
        ])
        return {
            "action": "swipe",
            "from": (int(x1), int(y1)),
            "to": (int(x2), int(y2)),
            "duration_ms": int(duration_ms),
            "success": res.returncode == 0
        }

    def scroll(self, direction="down", distance=600):
        """Scroll page up or down."""
        info = self.get_device_info()
        res_str = info.get("screen_resolution", "1080x2400")
        try:
            w_str, h_str = res_str.split("x")
            width, height = int(w_str), int(h_str)
        except Exception:
            width, height = 1080, 2400

        center_x = width // 2
        center_y = height // 2
        dist = int(distance)

        if direction.lower() == "down":
            # Scrolling down means swiping finger upwards
            start_y = min(height - 100, center_y + (dist // 2))
            end_y = max(100, start_y - dist)
        else:
            # Scrolling up means swiping finger downwards
            start_y = max(100, center_y - (dist // 2))
            end_y = min(height - 100, start_y + dist)

        return self.swipe(center_x, start_y, center_x, end_y, duration_ms=350)

    def key_event(self, key_name_or_code):
        """Send navigation or hardware key event."""
        self.select_active_device()
        key_str = str(key_name_or_code).strip().lower()
        if key_str in self.KEY_CODES:
            code = self.KEY_CODES[key_str]
        else:
            try:
                code = int(key_str)
            except ValueError:
                raise ADBError(
                    f"Unknown key '{key_name_or_code}'. Supported: {', '.join(sorted(self.KEY_CODES.keys()))}"
                )

        res = self.run_cmd(["shell", "input", "keyevent", str(code)])
        return {"action": "keyevent", "key": key_name_or_code, "keycode": code, "success": res.returncode == 0}

    def input_text(self, text):
        """Type text into focused input field."""
        self.select_active_device()
        # Escape special characters for shell input text
        # Spaces need %s
        escaped = ""
        for ch in str(text):
            if ch == " ":
                escaped += "%s"
            elif ch in r'\"\'&$<>()|;#*?~`':
                escaped += f"\\{ch}"
            else:
                escaped += ch

        res = self.run_cmd(["shell", "input", "text", escaped])
        return {"action": "text", "text": text, "success": res.returncode == 0}


def create_parser():
    """Create command line parser."""
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--json", action="store_true", help="Format output as JSON.")

    parser = argparse.ArgumentParser(
        description="Copy-Cat ADB Controller: Safe, modular Android automation for app reconnaissance and testing.",
        parents=[shared]
    )
    parser.add_argument("--serial", "-s", help="Target specific device serial number.")
    parser.add_argument("--adb-path", help="Explicit path to adb binary.")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    subparsers.add_parser("version", help="Check ADB installation and version.", parents=[shared])
    subparsers.add_parser("devices", help="List connected Android devices.", parents=[shared])
    subparsers.add_parser("info", help="Retrieve device model, OS, and screen specs.", parents=[shared])

    p_shot = subparsers.add_parser("screenshot", help="Capture screen and save locally.", parents=[shared])
    p_shot.add_argument("--output", "-o", help="Target output file path (PNG).")

    p_tap = subparsers.add_parser("tap", help="Tap screen coordinates.", parents=[shared])
    p_tap.add_argument("x", type=int, help="X coordinate.")
    p_tap.add_argument("y", type=int, help="Y coordinate.")

    p_swipe = subparsers.add_parser("swipe", help="Swipe between coordinates.", parents=[shared])
    p_swipe.add_argument("x1", type=int, help="Start X.")
    p_swipe.add_argument("y1", type=int, help="Start Y.")
    p_swipe.add_argument("x2", type=int, help="End X.")
    p_swipe.add_argument("y2", type=int, help="End Y.")
    p_swipe.add_argument("--duration", type=int, default=300, help="Duration in milliseconds.")

    p_scroll = subparsers.add_parser("scroll", help="Scroll screen up or down.", parents=[shared])
    p_scroll.add_argument("direction", choices=["up", "down"], default="down", nargs="?")
    p_scroll.add_argument("--distance", type=int, default=600, help="Scroll distance in pixels.")

    p_key = subparsers.add_parser("key", help="Press navigation or system button.", parents=[shared])
    p_key.add_argument("button", help="Button name (back, home, recents, power, enter) or keycode.")

    p_text = subparsers.add_parser("text", help="Type text into focused element.", parents=[shared])
    p_text.add_argument("content", help="Text string to type.")

    p_launch = subparsers.add_parser("launch", help="Launch app by package name.", parents=[shared])
    p_launch.add_argument("package", help="Android package name (e.g. com.example.app).")

    p_close = subparsers.add_parser("close", help="Close app by package name.", parents=[shared])
    p_close.add_argument("package", help="Android package name to force-stop.")

    return parser


def main():
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    controller = ADBController(adb_path=args.adb_path, serial=args.serial)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "version":
            res = controller.get_version()
        elif args.command == "devices":
            res = controller.list_devices()
        elif args.command == "info":
            res = controller.get_device_info()
        elif args.command == "screenshot":
            path = controller.take_screenshot(args.output)
            res = {"screenshot": path, "success": True}
        elif args.command == "tap":
            res = controller.tap(args.x, args.y)
        elif args.command == "swipe":
            res = controller.swipe(args.x1, args.y1, args.x2, args.y2, args.duration)
        elif args.command == "scroll":
            res = controller.scroll(args.direction, args.distance)
        elif args.command == "key":
            res = controller.key_event(args.button)
        elif args.command == "text":
            res = controller.input_text(args.content)
        elif args.command == "launch":
            res = controller.launch_app(args.package)
        elif args.command == "close":
            res = controller.close_app(args.package)
        else:
            parser.print_help()
            sys.exit(1)

        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if isinstance(res, dict):
                for k, v in res.items():
                    print(f"{k}: {v}")
            elif isinstance(res, list):
                if not res:
                    print("No devices found.")
                for item in res:
                    print(item)
            else:
                print(res)

    except ADBError as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "success": False}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
