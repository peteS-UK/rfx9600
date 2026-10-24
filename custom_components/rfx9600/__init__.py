"""The emotiva component."""

import logging

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .rfx9600 import RFX9600

from .const import (
    CONF_BAUD_RATE,
    CONF_COMMAND,
    CONF_DATA_BITS,
    CONF_DURATION_MS,
    CONF_PARITY,
    CONF_PORT,
    CONF_RELAY_1,
    CONF_RELAY_2,
    CONF_RELAY_3,
    CONF_RELAY_4,
    CONF_REPEAT_COUNT,
    CONF_STOP_BITS,
    DOMAIN,
    SERVICE_SEND_RS232,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH]

RS232_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COMMAND): cv.string,
        vol.Required(CONF_PORT): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
        vol.Required(CONF_BAUD_RATE): vol.All(
            vol.Coerce(int),
            vol.In([2400, 4800, 9600, 14400, 19200, 28800, 31250, 38400, 57600, 115200]),
        ),
        vol.Required(CONF_STOP_BITS): vol.All(
            vol.Coerce(float), vol.In([1.0, 1.5, 2.0])
        ),
        vol.Required(CONF_PARITY): vol.All(
            cv.string, vol.Lower, vol.In(["none", "even", "odd", "mark", "space"])
        ),
        vol.Required(CONF_DATA_BITS): vol.All(
            vol.Coerce(int), vol.In([5, 6, 7, 8])
        ),
        vol.Optional(CONF_DURATION_MS, default=500): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_REPEAT_COUNT, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=255)
        ),
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    rfx9600 = RFX9600(hass_data[CONF_HOST], hass_data[CONF_NAME])

    # await rfx9600.async_udp_connect()

    rfx9600._port_name.append(hass_data[CONF_RELAY_1])
    rfx9600._port_name.append(hass_data[CONF_RELAY_2])
    rfx9600._port_name.append(hass_data[CONF_RELAY_3])
    rfx9600._port_name.append(hass_data[CONF_RELAY_4])

    hass_data["rfx9600"] = rfx9600

    hass.data[DOMAIN][entry.entry_id] = hass_data

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_RS232):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_RS232,
            _build_send_rs232_service_handler(hass),
            schema=RS232_SERVICE_SCHEMA,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _build_send_rs232_service_handler(hass: core.HomeAssistant):
    async def _async_send_rs232(call: core.ServiceCall) -> None:
        all_entries = hass.data.get(DOMAIN, {})

        if len(all_entries) != 1:
            raise HomeAssistantError(
                "Exactly one RFX9600 entry must be configured for send_rs232"
            )

        selected_entry = next(iter(all_entries.values()))
        await selected_entry["rfx9600"].async_send_rs232(
            command_string=call.data[CONF_COMMAND],
            port_number=call.data[CONF_PORT],
            baud_rate=call.data[CONF_BAUD_RATE],
            stop_bits=call.data[CONF_STOP_BITS],
            parity=call.data[CONF_PARITY],
            data_bits=call.data[CONF_DATA_BITS],
            duration_ms=call.data[CONF_DURATION_MS],
            repeat_count=call.data[CONF_REPEAT_COUNT],
        )

    return _async_send_rs232


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        # rfx9600 = hass.data[DOMAIN][entry.entry_id]["rfx9600"]
        # await rfx9600.async_udp_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_SEND_RS232):
            hass.services.async_remove(DOMAIN, SERVICE_SEND_RS232)

    return unload_ok
