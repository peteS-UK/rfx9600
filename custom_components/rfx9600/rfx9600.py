
import logging

import socket

from lxml import etree

import asyncio

import asyncio_datagram

import time

import sys

# Third byte is a sequence number
# third from last is off/on
# fourth from last is relay number
RELAY_COMMAND = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x63\x00\x00\x06\x00\x00\x00\x00")

# fourth from last is relay number
RELAY_TOGGLE = bytearray(b"\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x64\x00\x00\x05\x00\x00\x00\x00")

# fourth from last is relay number
RELAY_QUERY = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x65\x00\x00\x05\x00\x00\x00\x00")

_LOGGER = logging.getLogger(__name__)

class RFX9600(object):
	def __init__(self, ip, name):

		self._ip = ip
		self._name = name
		self._port = 65442
		self._port_name = []
		self.state = False
		self._seq = 0

	async def async_udp_connect(self):

		_stream = None
		try:
			_stream = await asyncio_datagram.connect((self._ip, self._port))
		except IOError as e:
			_LOGGER.critical("Cannot connect command socket %d: %s", e.errno, e.strerror)
		except:
			_LOGGER.critical("Unknown error on command socket connection %s", sys.exc_info()[0])
		return _stream

	async def async_udp_disconnect(self, _stream):
		try:
			_stream.close()
		except IOError as e:
			_LOGGER.critical("Cannot disconnect from command socket %d: %s", e.errno, e.strerror)
		except:
			_LOGGER.critical("Unknown error on command socket disconnection %s", sys.exc_info()[0])

	async def async_turn_on(self, port_number):

		command = RELAY_COMMAND
		command[-4] = port_number - 1
		command[-3] = 1


		if self._seq == 16777215:
			self._seq = 0
		else:
			self._seq = self._seq+1

		_LOGGER.debug("Turn On relay_%d with seq %d", port_number, self._seq)

		_seq_bytes = self._seq.to_bytes(3)
		command[0] = _seq_bytes[0]
		command[1] = _seq_bytes[1]
		command[2] = _seq_bytes[2]
		
		await self._async_send_command(bytes(command), port_number,  self._seq)





	async def async_turn_off(self, port_number):


		command = RELAY_COMMAND
		
		command[-4] = port_number - 1
		command[-3] = 0


		if self._seq == 16777215:
			self._seq = 0
		else:
			self._seq = self._seq+1

		_LOGGER.debug("Turn Off relay_%d with seq %d", port_number, self._seq)

		_seq_bytes = self._seq.to_bytes(3)
		command[0] = _seq_bytes[0]
		command[1] = _seq_bytes[1]
		command[2] = _seq_bytes[2]

		await self._async_send_command(bytes(command), port_number, self._seq)



	async def async_update(self, port_number):

		command = RELAY_QUERY
		command[-4] = port_number - 1

		if self._seq == 16777215:
			self._seq = 0
		else:
			self._seq = self._seq+1

		_LOGGER.debug("Calling update for relay_%d with seq %d", port_number, self._seq)

		_seq_bytes = self._seq.to_bytes(3)
		command[0] = _seq_bytes[0]
		command[1] = _seq_bytes[1]
		command[2] = _seq_bytes[2]
		
		await self._async_send_command(bytes(command), port_number, self._seq, True)

		if self._resp:
			if self._resp[12] == 0:
				_LOGGER.debug("Setting state to False for port number %d", port_number)
				self.state = False
			if self._resp[12] == 1:
				_LOGGER.debug("Setting state to True for port number %d", port_number)
				self.state = True



	async def _async_send_command(self, command, port_number, _seq, ack = False):

		_stream = await self.async_udp_connect()

		if not _stream:
			return

		await _stream.send(command)

#		try: 
#			await _stream.send(command)
#		except IOError as e:
#			_LOGGER.critical("Cannot send to command socket %d: %s", e.errno, e.strerror)
#		except:
#			_LOGGER.critical("Unknown error on command socket send %s", sys.exc_info()[0])

		if ack:
			try:
				_data, remote_addr = await asyncio.wait_for(_stream.recv(), timeout=0.2)
				await asyncio.sleep(0.1)
				_resp, remote_addr = await asyncio.wait_for(_stream.recv(), timeout=0.2)
			except:
				_LOGGER.debug("No query response received for port %d, seq %d",port_number, _seq )
				self._resp = None
				return
			
			if (_resp[0] == command [0] and _resp[1] == command [1] 
	   				and _resp[2] == command [2] and _resp[3] == 64):
					_LOGGER.debug("Query response received for port %d, seq %d",port_number, _seq)
					self._resp = _resp

		await self.async_udp_disconnect(_stream)
		
