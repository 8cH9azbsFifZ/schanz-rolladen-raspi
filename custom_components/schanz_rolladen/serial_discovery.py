def _port_attr(port, name):
    value = getattr(port, name, None)
    if value is None and isinstance(port, dict):
        value = port.get(name)
    return value


def _score_port(port):
    device = (_port_attr(port, "device") or "").lower()
    description = (_port_attr(port, "description") or "").lower()
    hwid = (_port_attr(port, "hwid") or "").lower()
    manufacturer = (_port_attr(port, "manufacturer") or "").lower()
    product = (_port_attr(port, "product") or "").lower()
    vid = _port_attr(port, "vid")
    pid = _port_attr(port, "pid")

    score = 0
    if device.startswith("/dev/serial/by-id/"):
        score += 60
    if "1a86" in device or "1a86" in hwid:
        score += 50
    if "7523" in hwid:
        score += 50
    if vid == 0x1A86 and pid == 0x7523:
        score += 80
    if "ch340" in description or "ch340" in product:
        score += 40
    if "usb serial" in description or "usb serial" in product:
        score += 20
    if "qinheng" in manufacturer or "wch" in manufacturer:
        score += 20
    if device.startswith("/dev/ttyusb") or device.startswith("/dev/cu.usb"):
        score += 10
    return score


def choose_minicul_device(ports):
    best_device = None
    best_score = 0
    for port in ports:
        device = _port_attr(port, "device")
        if not device:
            continue
        score = _score_port(port)
        if score > best_score:
            best_score = score
            best_device = device
    return best_device


def guess_minicul_device():
    from serial.tools import list_ports

    return choose_minicul_device(list_ports.comports())

