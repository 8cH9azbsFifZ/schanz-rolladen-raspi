import unittest

from custom_components.schanz_rolladen.validation import validate_config


class ValidateConfigTests(unittest.TestCase):
    def test_defaults_are_applied(self):
        config = validate_config({})
        self.assertEqual(config.name, "Schanz Rolladen")
        self.assertEqual(config.device, "/dev/ttyUSB0")
        self.assertEqual(config.baudrate, 57600)

    def test_invalid_empty_name_raises(self):
        with self.assertRaises(ValueError):
            validate_config({"name": "  "})

    def test_invalid_time_raises(self):
        with self.assertRaises(ValueError):
            validate_config({"time_open": 0})


if __name__ == "__main__":
    unittest.main()

