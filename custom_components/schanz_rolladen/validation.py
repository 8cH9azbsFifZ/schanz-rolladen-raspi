from dataclasses import dataclass

from .const import (
    CONF_BAUDRATE,
    CONF_COMMAND_CLOSE,
    CONF_COMMAND_OPEN,
    CONF_DEVICE,
    CONF_NAME,
    CONF_TIME_CLOSE,
    CONF_TIME_OPEN,
    CONF_TRANSPORT_PREFIX,
    CONF_TRANSPORT_SUFFIX,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BAUDRATE,
    DEFAULT_COMMAND_CLOSE,
    DEFAULT_COMMAND_OPEN,
    DEFAULT_DEVICE,
    DEFAULT_NAME,
    DEFAULT_TIME_CLOSE,
    DEFAULT_TIME_OPEN,
    DEFAULT_TRANSPORT_PREFIX,
    DEFAULT_TRANSPORT_SUFFIX,
    DEFAULT_UPDATE_INTERVAL,
)


@dataclass(frozen=True)
class IntegrationConfig:
    name: str
    device: str
    baudrate: int
    time_open: float
    time_close: float
    command_open: str
    command_close: str
    transport_prefix: str
    transport_suffix: str
    update_interval: float


def _non_empty_text(value, field_name):
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


def _positive_number(value, field_name):
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if numeric <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return numeric


def _positive_int(value, field_name):
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if numeric <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return numeric


def validate_config(config_input):
    merged = {
        CONF_NAME: DEFAULT_NAME,
        CONF_DEVICE: DEFAULT_DEVICE,
        CONF_BAUDRATE: DEFAULT_BAUDRATE,
        CONF_TIME_OPEN: DEFAULT_TIME_OPEN,
        CONF_TIME_CLOSE: DEFAULT_TIME_CLOSE,
        CONF_COMMAND_OPEN: DEFAULT_COMMAND_OPEN,
        CONF_COMMAND_CLOSE: DEFAULT_COMMAND_CLOSE,
        CONF_TRANSPORT_PREFIX: DEFAULT_TRANSPORT_PREFIX,
        CONF_TRANSPORT_SUFFIX: DEFAULT_TRANSPORT_SUFFIX,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    }
    merged.update(config_input or {})

    return IntegrationConfig(
        name=_non_empty_text(merged[CONF_NAME], CONF_NAME),
        device=_non_empty_text(merged[CONF_DEVICE], CONF_DEVICE),
        baudrate=_positive_int(merged[CONF_BAUDRATE], CONF_BAUDRATE),
        time_open=_positive_number(merged[CONF_TIME_OPEN], CONF_TIME_OPEN),
        time_close=_positive_number(merged[CONF_TIME_CLOSE], CONF_TIME_CLOSE),
        command_open=_non_empty_text(merged[CONF_COMMAND_OPEN], CONF_COMMAND_OPEN),
        command_close=_non_empty_text(merged[CONF_COMMAND_CLOSE], CONF_COMMAND_CLOSE),
        transport_prefix=str(merged[CONF_TRANSPORT_PREFIX]),
        transport_suffix=str(merged[CONF_TRANSPORT_SUFFIX]),
        update_interval=_positive_number(merged[CONF_UPDATE_INTERVAL], CONF_UPDATE_INTERVAL),
    )

