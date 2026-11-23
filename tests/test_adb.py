import json
import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from adb.adb_controller import (
    ADBController,
    ADBError,
    ADBNotFoundError,
    DeviceNotFoundError,
    DeviceUnauthorizedError,
    create_parser,
)


class TestADBController(unittest.TestCase):
    def setUp(self):
        self.controller = ADBController(adb_path="/mock/bin/adb", serial="test_device_123")

    def test_find_adb_fallback(self):
        with patch("shutil.which", return_value=None):
            with patch("os.path.isfile", return_value=False):
                controller = ADBController()
                self.assertFalse(controller.is_available())

    def test_find_adb_in_path(self):
        with patch("shutil.which", return_value="/usr/bin/adb"):
            with patch("os.path.isfile", return_value=True):
                path = ADBController.find_adb()
                self.assertIsNotNone(path)

    @patch("subprocess.run")
    def test_get_version(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Android Debug Bridge version 1.0.41\nVersion 37.0.1-15733141\n",
            stderr=""
        )
        ver = self.controller.get_version()
        self.assertTrue(ver["installed"])
        self.assertEqual(ver["version"], "1.0.41")

    @patch("subprocess.run")
    def test_list_devices_parsing(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "List of devices attached\n"
                "emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1\n"
                "R58M123456            unauthorized transport_id:2\n"
            ),
            stderr=""
        )
        devices = self.controller.list_devices()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["serial"], "emulator-5554")
        self.assertEqual(devices[0]["state"], "device")
        self.assertEqual(devices[0]["model"], "sdk_gphone64_arm64")
        self.assertEqual(devices[1]["serial"], "R58M123456")
        self.assertEqual(devices[1]["state"], "unauthorized")

    @patch("subprocess.run")
    def test_select_active_device_unauthorized(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\nPHONE123   unauthorized\n",
            stderr=""
        )
        ctrl = ADBController(adb_path="/mock/adb", serial="PHONE123")
        with self.assertRaises(DeviceUnauthorizedError):
            ctrl.select_active_device()

    @patch("subprocess.run")
    def test_select_active_device_empty(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n\n",
            stderr=""
        )
        ctrl = ADBController(adb_path="/mock/adb")
        with self.assertRaises(DeviceNotFoundError):
            ctrl.select_active_device()

    @patch("subprocess.run")
    def test_get_device_info(self, mock_run):
        def side_effect(cmd, **kwargs):
            if "devices" in cmd:
                return MagicMock(returncode=0, stdout="List of devices attached\nTEST1  device\n", stderr="")
            if "ro.product.manufacturer" in cmd:
                return MagicMock(returncode=0, stdout="Google\n", stderr="")
            if "ro.product.model" in cmd:
                return MagicMock(returncode=0, stdout="Pixel 8 Pro\n", stderr="")
            if "ro.product.brand" in cmd:
                return MagicMock(returncode=0, stdout="google\n", stderr="")
            if "ro.build.version.release" in cmd:
                return MagicMock(returncode=0, stdout="14\n", stderr="")
            if "ro.build.version.sdk" in cmd:
                return MagicMock(returncode=0, stdout="34\n", stderr="")
            if "wm" in cmd and "size" in cmd:
                return MagicMock(returncode=0, stdout="Physical size: 1344x2992\n", stderr="")
            if "wm" in cmd and "density" in cmd:
                return MagicMock(returncode=0, stdout="Physical density: 480\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect
        ctrl = ADBController(adb_path="/mock/adb", serial="TEST1")
        info = ctrl.get_device_info()
        self.assertEqual(info["manufacturer"], "Google")
        self.assertEqual(info["model"], "Pixel 8 Pro")
        self.assertEqual(info["android_version"], "14")
        self.assertEqual(info["screen_resolution"], "1344x2992")
        self.assertEqual(info["screen_density"], "480")

    @patch("subprocess.run")
    def test_interactions(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\nTEST1  device\n",
            stderr=""
        )
        ctrl = ADBController(adb_path="/mock/adb", serial="TEST1")

        # Tap
        tap_res = ctrl.tap(100, 200)
        self.assertTrue(tap_res["success"])
        self.assertEqual(tap_res["x"], 100)

        # Swipe
        swipe_res = ctrl.swipe(100, 200, 100, 600, duration_ms=400)
        self.assertTrue(swipe_res["success"])

        # Key event
        key_res = ctrl.key_event("back")
        self.assertTrue(key_res["success"])
        self.assertEqual(key_res["keycode"], 4)

        # Input text
        text_res = ctrl.input_text("hello world")
        self.assertTrue(text_res["success"])

        # Launch app
        launch_res = ctrl.launch_app("com.example.app")
        self.assertTrue(launch_res["success"])

        # Close app
        close_res = ctrl.close_app("com.example.app")
        self.assertTrue(close_res["closed"])

    def test_parser_options(self):
        parser = create_parser()
        args = parser.parse_args(["tap", "150", "250", "--json"])
        self.assertEqual(args.command, "tap")
        self.assertEqual(args.x, 150)
        self.assertEqual(args.y, 250)
        self.assertTrue(args.json)


if __name__ == "__main__":
    unittest.main()
