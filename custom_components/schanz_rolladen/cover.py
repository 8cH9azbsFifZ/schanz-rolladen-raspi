from __future__ import annotations

from dataclasses import replace
import logging
import time
from datetime import timedelta

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

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
    DEFAULT_UPDATE_INTERVAL,
)
from .minicul_transport import MiniculTransport, MiniculTransportError
from .movement import ACTION_SEND_CLOSE, ACTION_SEND_OPEN, MovementModel
from .serial_discovery import guess_minicul_device
from .validation import validate_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    merged = dict(entry.data)
    merged.update(entry.options)
    config = validate_config(merged)
    if config.auto_detect_device:
        detected = await hass.async_add_executor_job(guess_minicul_device)
        if detected:
            config = replace(config, device=detected)
    async_add_entities([SchanzRolladenCover(config)])


class SchanzRolladenCover(CoverEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, config):
        self._attr_name = config.name
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        self._command_open = config.command_open
        self._command_close = config.command_close
        self._update_interval = config.update_interval or DEFAULT_UPDATE_INTERVAL
        self._available = True
        self._transport = MiniculTransport(
            device=config.device,
            baudrate=config.baudrate,
            command_prefix=config.transport_prefix,
            command_suffix=config.transport_suffix,
        )
        self._model = MovementModel(time_open=config.time_open, time_close=config.time_close)
        self._unsub_tick = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_position = last_state.attributes.get("current_position")
            if isinstance(restored_position, (int, float)):
                self._model.set_position_percent(restored_position)

        self._model.last_time = time.monotonic()
        self._unsub_tick = async_track_time_interval(
            self.hass,
            self._handle_tick,
            timedelta(seconds=self._update_interval),
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None
        await self.hass.async_add_executor_job(self._transport.close)
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        return self._available

    @property
    def current_cover_position(self) -> int:
        return self._model.current_position_percent()

    @property
    def is_closed(self) -> bool:
        return self._model.position >= 1.0

    @property
    def is_closing(self) -> bool:
        return self._model.moving_close

    @property
    def is_opening(self) -> bool:
        return self._model.moving_open

    async def async_open_cover(self, **kwargs) -> None:
        self._model.command_open(time.monotonic(), target_position=0.0)
        await self._send_payload(self._command_open)
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs) -> None:
        self._model.command_close(time.monotonic(), target_position=1.0)
        await self._send_payload(self._command_close)
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs) -> None:
        requested = kwargs.get(ATTR_POSITION)
        if requested is None:
            return

        target = float(requested) / 100.0
        action = self._model.command_to_position(time.monotonic(), target)
        if action == ACTION_SEND_OPEN:
            await self._send_payload(self._command_open)
        elif action == ACTION_SEND_CLOSE:
            await self._send_payload(self._command_close)

        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs) -> None:
        action = self._model.stop()
        if action == ACTION_SEND_OPEN:
            await self._send_payload(self._command_open)
        elif action == ACTION_SEND_CLOSE:
            await self._send_payload(self._command_close)
        self.async_write_ha_state()

    async def _handle_tick(self, _now) -> None:
        action = self._model.tick(time.monotonic())
        if action == ACTION_SEND_OPEN:
            await self._send_payload(self._command_open)
        elif action == ACTION_SEND_CLOSE:
            await self._send_payload(self._command_close)
        self.async_write_ha_state()

    async def _send_payload(self, payload) -> None:
        try:
            await self.hass.async_add_executor_job(self._transport.send_payload, payload)
            self._available = True
        except MiniculTransportError as exc:
            self._available = False
            _LOGGER.error("Failed to send Minicul command: %s", exc)
