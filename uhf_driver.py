# filename: uhf_driver.py (GIVE THIS VERSION TO THE CANDIDATE)

import re

import serial


class UHFException(Exception):
    """Base exception for UHF device errors."""

    pass


class UHFResponseParsingError(UHFException):
    """Custom exception for when a device response is malformed."""

    pass


class MockSerial:
    """Mock serial port. NOTE: Some responses may be outdated."""

    def __init__(self):
        self.last_command = None
        self.is_open = True

    def write(self, command_bytes):
        self.last_command = command_bytes
        return len(command_bytes)

    def readline(self):
        if self.last_command.startswith(b"ES+R2202"):
            return b"OK+D8001A2B3C DEADBEEF\n"

        if self.last_command.startswith(b"ES+R2200"):
            return b"OK+D8220001FF BD888E1F\n"
        else:
            return b"ERR-UNKNOWN_CMD\n"

    def close(self):
        self.is_open = False


_UPTIME_RESPONSE_RE = re.compile(
    r"^OK\+(?P<rssi>[0-9A-Fa-f]{2})(?P<uptime>[0-9A-Fa-f]{8}) (?P<crc>[0-9A-Fa-f]{8})$"
)


class UHF_Device:
    """A driver for interacting with our UHF radio."""

    def __init__(self, port_instance):
        self.port = port_instance

    def _send_command(self, command_str):
        if not self.port.is_open:
            raise UHFException("Port is not open.")
        full_command = command_str + "\n"
        self.port.write(full_command.encode("ascii"))
        try:
            response = self.port.readline().decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise UHFResponseParsingError(f"Non-ASCII response: {exc}") from exc
        if response.startswith("ERR"):
            raise UHFException(f"Device returned an error: {response}")
        return response

    def get_uptime_seconds(self):
        """Reads the device uptime in seconds. Response: OK+[RR][PPPPPPPP] [CRC32]."""

        raw_response = self._send_command("ES+R2202")
        match = _UPTIME_RESPONSE_RE.match(raw_response)
        if match is None:
            raise UHFResponseParsingError(f"Invalid uptime response: {raw_response!r}")
        return int(match.group("uptime"), 16)

    def get_status_control_word(self):

        raw_response = self._send_command("ES+R2200")
        if not raw_response.startswith("OK+"):
            raise UHFResponseParsingError(f"Invalid response prefix: {raw_response}")
        payload = raw_response[3:]
        if len(payload) < 19:
            raise UHFResponseParsingError(f"Response is too short: {payload}")
        return payload[6:10]
