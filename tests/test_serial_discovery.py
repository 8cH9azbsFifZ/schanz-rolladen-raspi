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


if __name__ == "__main__":
    unittest.main()

