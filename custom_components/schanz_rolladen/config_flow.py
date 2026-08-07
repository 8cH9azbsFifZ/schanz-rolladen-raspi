import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

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
    DOMAIN,
)
from .validation import validate_config


def _user_schema(defaults):
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_DEVICE, default=defaults.get(CONF_DEVICE, DEFAULT_DEVICE)): str,
            vol.Required(CONF_BAUDRATE, default=defaults.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)): int,
            vol.Required(CONF_TIME_OPEN, default=defaults.get(CONF_TIME_OPEN, DEFAULT_TIME_OPEN)): vol.Coerce(float),
            vol.Required(CONF_TIME_CLOSE, default=defaults.get(CONF_TIME_CLOSE, DEFAULT_TIME_CLOSE)): vol.Coerce(float),
            vol.Required(CONF_UPDATE_INTERVAL, default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): vol.Coerce(float),
            vol.Required(CONF_COMMAND_OPEN, default=defaults.get(CONF_COMMAND_OPEN, DEFAULT_COMMAND_OPEN)): str,
            vol.Required(CONF_COMMAND_CLOSE, default=defaults.get(CONF_COMMAND_CLOSE, DEFAULT_COMMAND_CLOSE)): str,
            vol.Required(CONF_TRANSPORT_PREFIX, default=defaults.get(CONF_TRANSPORT_PREFIX, DEFAULT_TRANSPORT_PREFIX)): str,
            vol.Required(CONF_TRANSPORT_SUFFIX, default=defaults.get(CONF_TRANSPORT_SUFFIX, DEFAULT_TRANSPORT_SUFFIX)): str,
        }
    )


class SchanzRolladenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                config = validate_config(user_input)
            except ValueError:
                errors["base"] = "invalid_config"
            else:
                return self.async_create_entry(
                    title=config.name,
                    data={
                        CONF_NAME: config.name,
                        CONF_DEVICE: config.device,
                        CONF_BAUDRATE: config.baudrate,
                        CONF_TIME_OPEN: config.time_open,
                        CONF_TIME_CLOSE: config.time_close,
                        CONF_COMMAND_OPEN: config.command_open,
                        CONF_COMMAND_CLOSE: config.command_close,
                        CONF_TRANSPORT_PREFIX: config.transport_prefix,
                        CONF_TRANSPORT_SUFFIX: config.transport_suffix,
                        CONF_UPDATE_INTERVAL: config.update_interval,
                    },
                )

        return self.async_show_form(step_id="user", data_schema=_user_schema(user_input or {}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SchanzRolladenOptionsFlow(config_entry)


class SchanzRolladenOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        merged_defaults = dict(self._config_entry.data)
        merged_defaults.update(self._config_entry.options)

        if user_input is not None:
            try:
                config = validate_config(user_input)
            except ValueError:
                errors["base"] = "invalid_config"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_NAME: config.name,
                        CONF_DEVICE: config.device,
                        CONF_BAUDRATE: config.baudrate,
                        CONF_TIME_OPEN: config.time_open,
                        CONF_TIME_CLOSE: config.time_close,
                        CONF_COMMAND_OPEN: config.command_open,
                        CONF_COMMAND_CLOSE: config.command_close,
                        CONF_TRANSPORT_PREFIX: config.transport_prefix,
                        CONF_TRANSPORT_SUFFIX: config.transport_suffix,
                        CONF_UPDATE_INTERVAL: config.update_interval,
                    },
                )

        return self.async_show_form(step_id="init", data_schema=_user_schema(merged_defaults), errors=errors)

