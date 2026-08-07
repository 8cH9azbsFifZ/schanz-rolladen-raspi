import unittest

from custom_components.schanz_rolladen.serial_discovery import choose_minicul_device


class SerialDiscoveryTests(unittest.TestCase):
    def test_prefers_by_id_ch340_device(self):
        ports = [
            {
                "device": "/dev/ttyUSB0",
                "description": "USB Serial",
                "hwid": "USB VID:PID=1A86:7523",
            },
            {
                "device": "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
                "description": "USB Serial",
                "hwid": "USB VID:PID=1A86:7523",
            },
        ]
        self.assertEqual(
            choose_minicul_device(ports),
            "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
        )

    def test_returns_none_without_match(self):
        ports = [{"device": "/dev/ttyS0", "description": "UART"}]
        self.assertIsNone(choose_minicul_device(ports))

    def test_prefers_vid_pid_match_over_generic_usb_serial(self):
        ports = [
            {
                "device": "/dev/ttyUSB0",
                "description": "USB Serial Adapter",
                "hwid": "USB VID:PID=0403:6001",
                "vid": 0x0403,
                "pid": 0x6001,
            },
            {
                "device": "/dev/ttyUSB1",
                "description": "USB Serial",
                "hwid": "USB VID:PID=1A86:7523",
                "vid": 0x1A86,
                "pid": 0x7523,
            },
        ]
        self.assertEqual(choose_minicul_device(ports), "/dev/ttyUSB1")


if __name__ == "__main__":
    unittest.main()
