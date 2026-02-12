# CLAUDE.md

## Project Overview

**schanz-rolladen-raspi** is a Raspberry Pi-based home automation controller for Schanz roller shutters (Siral EL4F motors) using 433 MHz RF signals. It provides an MQTT interface compatible with Home Assistant and OpenHAB.

**Architecture**: A Python service bridges MQTT commands to FHEM (home automation server), which drives a minicul CC1101 USB 433 MHz transceiver via the SIGNALduino module. An alternative relais-based GPIO mode exists for direct button emulation.

## Repository Structure

```
src/
  rollershutter.py         # Main application - single Rollershutter class (~273 lines)
  health_check.py          # Docker health check (instantiates Rollershutter, checks sigduino)
  requirements.txt         # Python deps: paho-mqtt, fhem, RPi.GPIO
doc/
  example_configurations/  # Docker Compose, Home Assistant, OpenHAB configs
    docker-compose.yml     #   FHEM-based setup (primary)
    relais/docker-compose.yml  # Relais-based setup (alternative)
    homeassistant-config.yaml  # Home Assistant MQTT cover config
    openhab.things         #   OpenHAB MQTT things
    openhab.items          #   OpenHAB MQTT items
  experiments/             # Reverse engineering docs (RF protocol, SDR, USB relais)
  mqtt/                    # MQTT dashboard setup (Mosquitto + UI)
  img/                     # Hardware photos
Dockerfile                 # Python 3.11 based container
.github/workflows/docker.yml  # CI: multi-arch Docker image build & push
LICENSE                    # GPLv3
```

## Tech Stack

- **Language**: Python 3.11
- **Dependencies**: `paho-mqtt`, `fhem`, `RPi.GPIO`
- **Container**: Docker with multi-arch builds (amd64, arm64, arm/v6)
- **Registry**: ghcr.io (GitHub Container Registry)
- **Protocol**: MQTT for external control, HTTP to FHEM for RF commands
- **License**: GPLv3

## Building & Running

```bash
# Build Docker image
docker build -t schanz-rolladen-mqtt .

# Run with Docker Compose (see doc/example_configurations/docker-compose.yml)
docker compose up

# Test with mosquitto CLI
mosquitto_pub -h <host> -t rollershutter/control/Test1 -m Open
mosquitto_pub -h <host> -t rollershutter/control/Test1 -m Close
mosquitto_pub -h <host> -t rollershutter/control/Test1 -m Stop
mosquitto_pub -h <host> -t rollershutter/control_position/Test1 -m 50

# Subscribe to state updates
mosquitto_sub -h <host> -t rollershutter/Test1/state
mosquitto_sub -h <host> -t rollershutter/Test1/percentage
```

**Docker Compose** runs two services: the `schanz-rolladen-mqtt` container (this project) and a `fhem` container (ghcr.io/fhem/fhem-docker). The FHEM container needs privileged mode and access to `/dev/ttyUSB0`. The rollershutter service waits for FHEM to be healthy before starting (`depends_on: condition: service_healthy`).

There is no formal test suite. The only test file is `doc/experiments/testing/test_connection_fhem.py` (manual FHEM connectivity check).

## Configuration

All configuration is via environment variables (defaults in Dockerfile):

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_HOST` | `t20` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `FHEM_HOST` | `minicul-raspi` | FHEM server hostname |
| `FHEM_PORT` | `8083` | FHEM HTTP port |
| `TIME_OPEN` | `53` | Seconds for full open travel |
| `TIME_CLOSE` | `53` | Seconds for full close travel |
| `ROLLERSHUTTER_NAME` | `Test1` | Name used in MQTT topics |
| `PIN_BCM_UP` | `23` | GPIO BCM pin for open (relais mode) |
| `PIN_BCM_DOWN` | `24` | GPIO BCM pin for close (relais mode) |
| `SIMULATION` | unset | Set to any value to enable simulation mode (see caveat below) |
| `USEFHEM` | n/a | **Currently ignored** - hardcoded to `True` in `__main__` |
| `USERELAIS` | n/a | **Currently ignored** - hardcoded to `False` in `__main__` |

**Caveat**: `SIMULATION`, `USEFHEM`, and `USERELAIS` are not properly parsed as booleans. `SIMULATION` uses `os.getenv()` so any non-empty string (including `"False"`) is truthy. `USEFHEM` is hardcoded to `True` and `USERELAIS` to `False` at line 271, ignoring the env vars entirely. This is tracked by FIXME comments in the code.

## MQTT Topics

| Direction | Topic | Values |
|-----------|-------|--------|
| Command | `rollershutter/control/{name}` | `Open`, `Close`, `Stop` |
| Command | `rollershutter/control_position/{name}` | `0`-`100` |
| State (published) | `rollershutter/{name}/state` | `open`, `closed`, `opening`, `closing`, `stopped` |
| State (published) | `rollershutter/{name}/percentage` | `0`-`100` |

Convention: 0% = fully open, 100% = fully closed.

## Key Code Concepts

- **Single class architecture**: `Rollershutter` in `src/rollershutter.py` handles everything - MQTT, FHEM, GPIO, position tracking.
- **Position tracking**: Internal range is `[0.0, 1.0]`, external (MQTT) is `[0, 100]`. Position is estimated using velocity * elapsed time.
- **Velocity model**: `velocity = 1.0 / travel_time_seconds`. Open and close speeds are independent.
- **RF commands**: Protocol 46 tristate encoding via SIGNALduino - open: `P46#111010101110001010#R10` (data: EAE28), close: `P46#111010101110001000#R10` (data: EAE20).
- **Stop mechanism**: Sends the opposite direction command to halt movement (close to stop opening, open to stop closing).
- **Core loop**: `_core_loop()` runs an infinite loop calling `mqtt.Client.loop()` with a 10ms sampling rate (`_samplingrate = 0.01`), then recalculates position. Note: the inline comment on line 209 incorrectly says "100ms" but the actual value is 10ms.
- **Health check**: `health_check.py` instantiates a full `Rollershutter` object (connecting to both FHEM and MQTT), then calls `_check_connection_sigduino_fhem()` to verify the sigduino device exists in FHEM. Returns exit code 0 on success, 1 on failure.
- **Relais mode**: Alternative to FHEM/RF - simulates physical button presses via GPIO relay. Press duration is 0.5 seconds (`_sw_press_duration`). Note: the inline comment on line 40 incorrectly says "1 second" but the actual value is 0.5s.

## Code Conventions

- Private methods/attributes use `_prefix`
- Public methods use `PascalCase` (e.g., `Open()`, `Close()`, `Stop()`, `SetPercent()`)
- `Name` is the only public attribute on `Rollershutter`
- Logging via Python `logging` module at DEBUG level
- Log format: `Rollershutter(%(threadName)-10s) %(message)s`
- Environment variable names: `UPPERCASE_SNAKE_CASE`
- Constructor parameters use inconsistent casing (e.g., `MQTThostname`, `FHEMhostname`, `TimeOpen` vs. `mqtt_port`, `fhem_port`)
- No type annotations in existing code
- No formal linter or formatter configured

## CI/CD

GitHub Actions workflow (`.github/workflows/docker.yml`):
- **Triggers**: Push to `master`/`main`/`dev`, version tags (`v*`), PRs to `main`/`dev`
- **Builds**: Multi-platform Docker images via Buildx (amd64, arm64, arm/v6)
- **Pushes to**: GitHub Container Registry (ghcr.io)
- **Tagging**: Semantic versioning from git tags, SHA, `latest` for main branch
- **Note**: Uses older action versions (checkout@v3, setup-qemu-action@v2, build-push-action@v4)

## Known Issues / Technical Debt

- **FIXME comments** in `rollershutter.py`:
  - Line 6: `RPi.GPIO` import is unconditional, breaking non-Raspberry Pi environments
  - Line 20: Unclear comment about FHEM usage
  - Line 70: Should check `_use_fhem` instead of `_simulation` for sigduino setup
  - Lines 71-72: SIGNALduino device path (`/dev/ttyUSB0@57600`) and hardware type (`miniculCC1101`) are hardcoded
  - Line 228: Close command occasionally stops working until original physical remote is pressed
  - Line 257: `USEFHEM` env var is commented out, hardcoded to `True`
  - Lines 263-264: `SIMULATION` and `USERELAIS` env vars lack proper boolean parsing and defaults
- **Env vars `UseFhem` and `UseRelais` ignored at runtime**: Line 271 passes `UseFhem=True, UseRelais=False` directly, ignoring the parsed env vars `vUSEFHEM` and `vUSERELAIS`
- **GPIO pin mapping inconsistency**: Code uses BCM 23 = Up, BCM 24 = Down; but `doc/experiments/usb/README.md` documents BCM 23 = Down, BCM 24 = Up (reversed)
- **Comment/code mismatches**: `_sw_press_duration = .5` has comment "1 second" (line 40); `_samplingrate = 0.01` has comment "100ms" (line 209)
- **No unit tests or integration tests**
- **Docker Compose** example uses old format `version: '2.3'`

## Hardware Requirements

- Raspberry Pi (any model, including Pi Zero)
- minicul CC1101 USB 433 MHz transceiver (at `/dev/ttyUSB0`, 57600 baud)
- FHEM server with SIGNALduino firmware (runs as separate Docker container)
- MQTT broker (e.g., Mosquitto)
- Optional: GPIO relay module for physical button emulation (BCM pins 23/24)
