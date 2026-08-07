# OpenSpec: Native Home Assistant integration for Schanz shutters via Minicul (without FHEM)

## 1. Scope
This spec defines a Home Assistant custom integration (`schanz_rolladen`) that controls Schanz/Siral EL4F shutters directly through a Minicul USB transceiver.  
FHEM is out of runtime scope for this integration.

## 2. Functional requirements
1. The integration must expose a `cover` entity with:
   - open
   - close
   - stop
   - set position (0..100, where 0=open and 100=closed)
2. The integration must estimate current position from elapsed time and configured full-travel durations.
3. The integration must support different open and close durations.
4. Commands must be sent over USB serial using configurable device path and baudrate.
5. Transport failures must be surfaced in logs and entity availability/state updates.
6. Integration setup must be possible via config flow (UI).

## 3. Non-goals for iteration 1
1. RF receive/decode from the shutter remote.
2. Multi-device auto-discovery.
3. Generic framework for arbitrary RF protocols.

## 4. Protocol contract
1. Default command payloads:
   - open: `P46#111010101110001010#R10`
   - close: `P46#111010101110001000#R10`
2. Stop behavior:
   - while opening: send close payload once
   - while closing: send open payload once
3. Outbound wire format:
   - command line = `<prefix><payload><suffix>`
   - defaults:
     - prefix: `sendMsg `
     - suffix: `\n`
4. All protocol strings must be configurable in options flow.

## 5. Configuration contract
Required config:
1. name
2. serial device path
3. baudrate
4. full travel time open (seconds)
5. full travel time close (seconds)

Optional config:
1. command open
2. command close
3. transport prefix
4. transport suffix
5. update interval (seconds)

## 6. State model
1. Internal position is float in range [0.0, 1.0].
2. External position is integer [0, 100].
3. Entity states:
   - `opening`
   - `closing`
   - `open`
   - `closed`
   - `stopped` (mapped to a non-moving state with last known position)
4. Position updates must be clamped at bounds and target.

## 7. Error handling
1. Serial open/write errors must not be swallowed.
2. Serial transport must attempt reconnect on next command after failure.
3. Invalid configuration values must be rejected by config/option flow validation.

## 8. Test contract (iteration 1 gate)
Mandatory test gates before merge:
1. Logic tests for movement/position/state transitions.
2. Transport tests with mocked serial backend.
3. Config flow and entity behavior tests (without hardware).

Hardware-in-the-loop on Home Assistant Green + Minicul is recommended as a dedicated follow-up gate.
