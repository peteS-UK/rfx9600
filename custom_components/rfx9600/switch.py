
from __future__ import annotations

import logging

from .const import DOMAIN

from .rfx9600 import RFX9600

import voluptuous as vol

from homeassistant import config_entries, core

from homeassistant.components.switch import (
	PLATFORM_SCHEMA,
	SwitchEntity
	)

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
	config_validation as cv,
	discovery_flow,
	entity_platform,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.start import async_at_start

_LOGGER = logging.getLogger(__name__)

from .const import (
	DOMAIN,
	CONF_RELAY_1,
	CONF_RELAY_2,
	CONF_RELAY_3,
	CONF_RELAY_4,
	DEFAULT_NAME
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{vol.Optional(CONF_RELAY_1, default="Relay 1"): cv.string,
	vol.Optional(CONF_RELAY_2, default="Relay 2"): cv.string,
	vol.Optional(CONF_RELAY_3, default="Relay 3"): cv.string,
	vol.Optional(CONF_RELAY_4, default="Relay 4"): cv.string,
	vol.Required(CONF_HOST): cv.string, 
	vol.Optional(CONF_NAME): cv.string
}
)

PARALLEL_UPDATES = 1

from datetime import timedelta

SCAN_INTERVAL = timedelta(seconds=300)

async def async_setup_entry(
	hass: core.HomeAssistant,
	config_entry: config_entries.ConfigEntry,
	async_add_entities,
) -> None:

	config = hass.data[DOMAIN][config_entry.entry_id]

	rfx9600 = config["rfx9600"]
	
	relays = []

	for port in range(1,5):
		port_name = "relay_"+str(port)
		relays.append(RFX9600Device(rfx9600, rfx9600._port_name[port-1], port, hass))

	async_add_entities(relays)

class RFX9600Device(SwitchEntity):
	# Representation of a RFX9600

	def __init__(self, device, port_name, port_number, hass):

		self._device = device
		self._port_name = port_name
		self._port_number = port_number
		# self._udp_stream = device._udp_stream
		self._hass = hass
		self._entity_id = "switch.rfx9600_relay_" + str(port_number)
		self._unique_id = "rfx9600_relay_"+str(port_number)

	async def async_added_to_hass(self):
		#await self._device.async_udp_connect()
		
		await self._device.async_update(self._port_number)

	async def async_will_remove_from_hass(self) -> None:
		pass
		#await self._device.async_udp_disconnect()


	should_poll = True

	@property
	def should_poll(self):
		return True



	@property
	def name(self):
		return self._port_name

	@property
	def has_entity_name(self):
		return True

	@property
	def device_info(self) -> DeviceInfo:
		"""Return the device info."""
		return DeviceInfo(
			identifiers={
				# Serial numbers are unique identifiers within a specific domain
				(DOMAIN, self._device._name)
			},
			name=self._device._name,
			manufacturer='Philips',
			model="RFX9600")

	@property
	def unique_id(self):
		return self._unique_id
		
	@property
	def entity_id(self):
		return self._entity_id
	
	@entity_id.setter
	def entity_id(self, entity_id):
		self._entity_id = entity_id

	@property
	def is_on(self):
		return self._device.state

	async def async_turn_on(self, **kwargs):
		await self._device.async_turn_on(self._port_number)
		self._device.state = True
		self.async_schedule_update_ha_state(force_refresh=False)

	async def async_turn_off(self, **kwargs):
		await self._device.async_turn_off(self._port_number)
		self._device.state = False
		self.async_schedule_update_ha_state(force_refresh=False)

	async def async_update(self):
		await self._device.async_update(self._port_number)
