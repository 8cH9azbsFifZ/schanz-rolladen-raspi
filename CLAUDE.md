# CLAUDE.md

## Project Overview

**schanz-rolladen-raspi** is a Raspberry Pi-based home automation controller for Schanz roller shutters (Siral EL4F motors) using 433 MHz RF signals. It provides an MQTT interface compatible with Home Assistant and OpenHAB.

**Architecture**: A Python service bridges MQTT commands to FHEM (home automation server), which drives a minicul CC1101 USB 433 MHz transceiver via the SIGNALduino module. An alternative relais-based GPIO mode exists for direct button emulation.

## Repository Structure

```
src/
  rollershutter.py      # Main application - single Rollershutter class
  health_check.py       # Docker health check (verifies FHEM/sigduino connection)
  requirements.txt      # Python deps: paho-mqtt, fhem, RPi.GPIO
doc/
  example_configurations/  # Docker Compose, Home Assistant, OpenHAB configs
  experiments/             # Reverse engineering docs (RF protocol, SDR, USB relais)
  mqtt/                    # MQTT dashboard setup
  img/                     # Hardware photos
Dockerfile              # Python 3.11 based container
.github/workflows/docker.yml  # CI: multi-arch Docker image build & push
```

## Tech Stack

- **Language**: Python 3.11
- **Dependencies**: `paho-mqtt`, `fhem`, `RPi.GPIO`
- **Container**: Docker with multi-arch builds (amd64, arm64, arm/v6)
- **Registry**: ghcr.io (GitHub Container Registry)
- **Protocol**: MQTT for external control, HTTP to FHEM for RF commands

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
```

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
| `PIN_BCM_UP` | `23` | GPIO pin for open (relais mode) |
| `PIN_BCM_DOWN` | `24` | GPIO pin for close (relais mode) |
| `SIMULATION` | unset | Set to enable simulation mode |
| `USERELAIS` | unset | Set to enable relais mode |

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
- **RF commands**: Protocol 46 tristate encoding via SIGNALduino - open: `P46#111010101110001010#R10`, close: `P46#111010101110001000#R10`.
- **Stop mechanism**: Sends the opposite direction command to halt movement (close to stop opening, open to stop closing).

## Code Conventions

- Private methods/attributes use `_prefix`
- Logging via Python `logging` module at DEBUG level
- Environment variable names: `UPPERCASE_SNAKE_CASE`
- Constructor parameters use mixed case (e.g., `MQTThostname`, `FHEMhostname`, `TimeOpen`)
- No type annotations in existing code
- No formal linter or formatter configured

## CI/CD

GitHub Actions workflow (`.github/workflows/docker.yml`):
- **Triggers**: Push to `master`/`main`/`dev`, version tags (`v*`), PRs to `main`/`dev`
- **Builds**: Multi-platform Docker images via Buildx (amd64, arm64, arm/v6)
- **Pushes to**: GitHub Container Registry (ghcr.io)
- **Tagging**: Semantic versioning from git tags, SHA, `latest` for main branch

## Known Issues / Technical Debt

- Several `FIXME` comments in `rollershutter.py` (lines 6, 20, 70-72, 228, 257, 263)
- `USEFHEM`, `SIMULATION`, `USERELAIS` env vars are not properly parsed as booleans (hardcoded to defaults)
- SIGNALduino device path (`/dev/ttyUSB0`) and hardware type are hardcoded
- Close command occasionally stops working until original physical remote is pressed (line 228)
- `RPi.GPIO` import is unconditional, breaking non-Raspberry Pi environments
- No unit tests or integration tests
- License: AGPLv3

## Hardware Requirements

- Raspberry Pi (any model, including Pi Zero)
- minicul CC1101 USB 433 MHz transceiver (at `/dev/ttyUSB0`)
- FHEM server with SIGNALduino firmware
- MQTT broker (e.g., Mosquitto)
- Optional: GPIO relay module for physical button emulation
