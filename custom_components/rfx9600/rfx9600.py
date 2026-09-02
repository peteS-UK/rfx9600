import logging

import asyncio
import codecs

import asyncio_datagram

import sys

# Third byte is a sequence number
# third from last is off/on
# fourth from last is relay number
RELAY_COMMAND = bytearray(
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x63\x00\x00\x06\x00\x00\x00\x00"
)

# fourth from last is relay number
RELAY_TOGGLE = bytearray(
    b"\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x64\x00\x00\x05\x00\x00\x00\x00"
)

# fourth from last is relay number
RELAY_QUERY = bytearray(
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x65\x00\x00\x05\x00\x00\x00\x00"
)

_LOGGER = logging.getLogger(__name__)


class RFX9600(object):
    def __init__(self, ip, name):
        self._ip = ip
        self._name = name
        self._port = 65442
        self._port_name = []
        self.state = False
        self._seq = 0

    def _next_sequence(self):
        if self._seq == 16777215:
            self._seq = 0
        else:
            self._seq = self._seq + 1
        return self._seq

    def _set_sequence(self, command):
        _seq_bytes = self._seq.to_bytes(3)
        command[0] = _seq_bytes[0]
        command[1] = _seq_bytes[1]
        command[2] = _seq_bytes[2]

    async def async_udp_connect(self):
        _stream = None
        try:
            _stream = await asyncio_datagram.connect((self._ip, self._port))
        except IOError as e:
            _LOGGER.critical(
                "Cannot connect command socket %d: %s", e.errno, e.strerror
            )
        except Exception:
            _LOGGER.critical(
                "Unknown error on command socket connection %s", sys.exc_info()[0]
            )
        return _stream

    async def async_udp_disconnect(self, _stream):
        try:
            _stream.close()
        except IOError as e:
            _LOGGER.critical(
                "Cannot disconnect from command socket %d: %s", e.errno, e.strerror
            )
        except Exception:
            _LOGGER.critical(
                "Unknown error on command socket disconnection %s", sys.exc_info()[0]
            )

    async def async_turn_on(self, port_number):
        command = RELAY_COMMAND
        command[-4] = port_number - 1
        command[-3] = 1

        self._next_sequence()

        _LOGGER.debug("Turn On relay_%d with seq %d", port_number, self._seq)

        self._set_sequence(command)

        await self._async_send_command(bytes(command), port_number, self._seq)

    async def async_turn_off(self, port_number):
        command = RELAY_COMMAND

        command[-4] = port_number - 1
        command[-3] = 0

        self._next_sequence()

        _LOGGER.debug("Turn Off relay_%d with seq %d", port_number, self._seq)

        self._set_sequence(command)

        await self._async_send_command(bytes(command), port_number, self._seq)

    async def async_update(self, port_number):
        command = RELAY_QUERY
        command[-4] = port_number - 1

        self._next_sequence()

        _LOGGER.debug("Calling update for relay_%d with seq %d", port_number, self._seq)

        self._set_sequence(command)

        await self._async_send_command(bytes(command), port_number, self._seq, True)

        if self._resp:
            if self._resp[12] == 0:
                _LOGGER.debug("Setting state to False for port number %d", port_number)
                self.state = False
            if self._resp[12] == 1:
                _LOGGER.debug("Setting state to True for port number %d", port_number)
                self.state = True

    async def async_send_rs232(
        self,
        command_string,
        port_number,
        baud_rate,
        stop_bits,
        parity,
        data_bits,
        duration_ms=500,
        repeat_count=1,
    ):
        baud_lookup = {
            2400: 0x2,
            4800: 0x3,
            9600: 0x4,
            14400: 0x5,
            19200: 0x6,
            28800: 0x7,
            31250: 0x8,
            38400: 0x9,
            57600: 0xA,
            115200: 0xB,
        }
        stop_bits_lookup = {1: 0x0, 1.5: 0x2, 2: 0x4}
        parity_lookup = {
            "none": 0x0,
            "even": 0x8,
            "odd": 0x10,
            "mark": 0x18,
            "space": 0x20,
        }
        data_bits_lookup = {5: 0x00, 6: 0x40, 7: 0x80, 8: 0xC0}

        baud_code = baud_lookup[baud_rate]
        stop_code = stop_bits_lookup[stop_bits]
        parity_code = parity_lookup[parity]
        data_bits_code = data_bits_lookup[data_bits]

        port_baud = ((port_number - 1) << 4) | baud_code
        rs232_flags = stop_code + parity_code + data_bits_code

        decoded_command = codecs.decode(command_string, "unicode_escape")
        command_bytes = decoded_command.encode("ascii")
        if len(command_bytes) > 236:
            raise ValueError("RS232 command is too long (maximum 236 bytes)")

        payload = bytearray()
        payload.append(port_baud)
        payload.append(rs232_flags)
        payload.extend(duration_ms.to_bytes(2, byteorder="big", signed=False))
        payload.extend(b"\x00\x00\x00\x00\x00\x00\x00")
        payload.append(repeat_count)
        payload.extend(command_bytes)
        payload.extend(b"\x00\x00\x00")

        rs232_command = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        rs232_command.append(0x50)
        rs232_command.append(0x02)
        rs232_command.append(0x00)
        data_length = len(payload) + 4
        rs232_command.append(data_length)
        rs232_command.extend(payload)

        self._next_sequence()
        self._set_sequence(rs232_command)

        payload_hex = " ".join(f"{byte:02X}" for byte in payload)
        frame_hex = " ".join(f"{byte:02X}" for byte in rs232_command)
        _LOGGER.debug(
            "Sending RS232 command on port %d with seq %d: data_length=%d command=%r decoded_command=%r payload_hex=%s frame_hex=%s",
            port_number,
            self._seq,
            data_length,
            command_string,
            decoded_command,
            payload_hex,
            frame_hex,
        )

        await self._async_send_command(bytes(rs232_command), port_number, self._seq)

    async def _async_send_command(self, command, port_number, _seq, ack=False):
        _stream = await self.async_udp_connect()

        if not _stream:
            return

        await _stream.send(command)

        if ack:
            try:
                _data, remote_addr = await asyncio.wait_for(_stream.recv(), timeout=0.2)
                await asyncio.sleep(0.1)
                _resp, remote_addr = await asyncio.wait_for(_stream.recv(), timeout=0.2)
            except Exception:
                _LOGGER.debug(
                    "No query response received for port %d, seq %d", port_number, _seq
                )
                self._resp = None
                return

            if (
                _resp[0] == command[0]
                and _resp[1] == command[1]
                and _resp[2] == command[2]
                and _resp[3] == 64
            ):
                _LOGGER.debug(
                    "Query response received for port %d, seq %d", port_number, _seq
                )
                self._resp = _resp

        await self.async_udp_disconnect(_stream)
