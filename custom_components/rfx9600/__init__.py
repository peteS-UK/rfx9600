"""The emotiva component."""

import logging

from homeassistant import config_entries, core
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST, CONF_NAME

from .rfx9600 import RFX9600

from .const import DOMAIN, CONF_RELAY_1, CONF_RELAY_2, CONF_RELAY_3, CONF_RELAY_4

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH]


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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        # rfx9600 = hass.data[DOMAIN][entry.entry_id]["rfx9600"]
        # await rfx9600.async_udp_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
