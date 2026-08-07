import unittest

from custom_components.schanz_rolladen.minicul_transport import (
    MiniculTransport,
    MiniculTransportError,
)


class FakeSerial:
    def __init__(self, device, baudrate, timeout=None, write_timeout=None):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.writes = []
        self.is_open = True
        self.flush_count = 0

    def write(self, data):
        self.writes.append(data)

    def flush(self):
        self.flush_count += 1

    def close(self):
        self.is_open = False


class OpeningErrorSerial:
    def __call__(self, *args, **kwargs):
        raise OSError("cannot open")


class FailingWriteSerial(FakeSerial):
    def write(self, data):
        raise OSError("write failed")


class MiniculTransportTests(unittest.TestCase):
    def test_sends_payload_with_prefix_and_suffix(self):
        holder = {}

        def serial_factory(*args, **kwargs):
            conn = FakeSerial(*args, **kwargs)
            holder["conn"] = conn
            return conn

        transport = MiniculTransport(
            device="/dev/ttyUSB0",
            baudrate=57600,
            command_prefix="sendMsg ",
            command_suffix="\n",
            serial_factory=serial_factory,
        )

        transport.send_payload("P46#TEST#R10")
        self.assertEqual(holder["conn"].writes, [b"sendMsg P46#TEST#R10\n"])
        self.assertEqual(holder["conn"].flush_count, 1)

    def test_open_error_raises_transport_error(self):
        transport = MiniculTransport(
            device="/dev/ttyUSB0",
            baudrate=57600,
            serial_factory=OpeningErrorSerial(),
        )

        with self.assertRaises(MiniculTransportError):
            transport.send_payload("P46#TEST#R10")

    def test_write_error_closes_connection_and_raises(self):
        conn = FailingWriteSerial("/dev/ttyUSB0", 57600)

        def serial_factory(*_args, **_kwargs):
            return conn

        transport = MiniculTransport(
            device="/dev/ttyUSB0",
            baudrate=57600,
            serial_factory=serial_factory,
        )

        with self.assertRaises(MiniculTransportError):
            transport.send_payload("P46#TEST#R10")
        self.assertFalse(conn.is_open)

    def test_reconnects_after_failed_write(self):
        fail_conn = FailingWriteSerial("/dev/ttyUSB0", 57600)
        ok_conn = FakeSerial("/dev/ttyUSB0", 57600)
        calls = {"count": 0}

        def serial_factory(*_args, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                return fail_conn
            return ok_conn

        transport = MiniculTransport(
            device="/dev/ttyUSB0",
            baudrate=57600,
            serial_factory=serial_factory,
        )

        with self.assertRaises(MiniculTransportError):
            transport.send_payload("P46#FAIL#R10")

        transport.send_payload("P46#OK#R10")
        self.assertEqual(ok_conn.writes, [b"sendMsg P46#OK#R10\n"])


if __name__ == "__main__":
    unittest.main()
