class MiniculTransportError(Exception):
    pass


def _default_serial_factory():
    import serial

    return serial.Serial


class MiniculTransport:
    def __init__(
        self,
        device,
        baudrate,
        command_prefix="sendMsg ",
        command_suffix="\n",
        timeout=1.0,
        write_timeout=1.0,
        serial_factory=None,
    ):
        self._device = device
        self._baudrate = int(baudrate)
        self._command_prefix = command_prefix
        self._command_suffix = command_suffix
        self._timeout = timeout
        self._write_timeout = write_timeout
        self._serial_factory = serial_factory or _default_serial_factory()
        self._serial_conn = None

    def close(self):
        if self._serial_conn is not None:
            try:
                self._serial_conn.close()
            finally:
                self._serial_conn = None

    def send_payload(self, payload):
        wire = f"{self._command_prefix}{payload}{self._command_suffix}"
        encoded = wire.encode("ascii")
        try:
            serial_conn = self._ensure_connection()
            serial_conn.write(encoded)
            if hasattr(serial_conn, "flush"):
                serial_conn.flush()
        except Exception as exc:
            self.close()
            raise MiniculTransportError(f"failed to send payload '{payload}'") from exc

    def _ensure_connection(self):
        if self._serial_conn is not None and getattr(self._serial_conn, "is_open", True):
            return self._serial_conn

        try:
            self._serial_conn = self._serial_factory(
                self._device,
                self._baudrate,
                timeout=self._timeout,
                write_timeout=self._write_timeout,
            )
            return self._serial_conn
        except Exception as exc:
            self._serial_conn = None
            raise MiniculTransportError(f"failed to open serial device '{self._device}'") from exc

