import pytest

from uhf_driver import MockSerial, UHF_Device, UHFException, UHFResponseParsingError


class ScriptedSerial(MockSerial):
    """MockSerial that returns a fixed raw reply."""

    def __init__(self, reply):
        super().__init__()
        self.reply = reply

    def readline(self):
        return self.reply


@pytest.fixture
def device():
    return UHF_Device(MockSerial())


def test_uptime_success(device):
    uptime = device.get_uptime_seconds()
    assert uptime == 0x001A2B3C
    assert isinstance(uptime, int)


def test_uptime_sends_correct_command():
    port = MockSerial()
    UHF_Device(port).get_uptime_seconds()
    assert port.last_command.startswith(b"ES+R2202")


def test_uptime_rssi_is_not_part_of_value():
    # RSSI 'FF' must not leak into the uptime value.
    dev = UHF_Device(ScriptedSerial(b"OK+FF00000010 DEADBEEF\n"))
    assert dev.get_uptime_seconds() == 16


def test_uptime_max_value():
    dev = UHF_Device(ScriptedSerial(b"OK+00FFFFFFFF DEADBEEF\n"))
    assert dev.get_uptime_seconds() == 0xFFFFFFFF


@pytest.mark.parametrize(
    "reply",
    [
        b"",  # timeout / no data
        b"\n",
        b"OK+\n",
        b"OK+D8001A2B3C\n",  # missing CRC
        b"OK+D8001A2B DEADBEEF\n",  # uptime too short
        b"OK+D8001A2B3C4D DEADBEEF\n",  # uptime too long
        b"OK+D8001A2BZZ DEADBEEF\n",  # non-hex uptime
        b"OK+D8001A2B3C DEADBE\n",  # truncated CRC
        b"D8001A2B3C DEADBEEF\n",  # missing OK+ prefix
        b"OK+001A2B3C\n",  # legacy format
        b"\xff\xfe\x00\n",  # non-ASCII garbage
    ],
)
def test_uptime_malformed_response_raises(reply):
    dev = UHF_Device(ScriptedSerial(reply))
    with pytest.raises(UHFResponseParsingError):
        dev.get_uptime_seconds()


def test_uptime_device_error_raises():
    dev = UHF_Device(ScriptedSerial(b"ERR-UNKNOWN_CMD\n"))
    with pytest.raises(UHFException):
        dev.get_uptime_seconds()


def test_uptime_closed_port_raises():
    port = MockSerial()
    port.close()
    with pytest.raises(UHFException):
        UHF_Device(port).get_uptime_seconds()


def test_status_control_word_unchanged(device):
    assert device.get_status_control_word() == "01FF"


def test_status_control_word_sends_correct_command():
    port = MockSerial()
    UHF_Device(port).get_status_control_word()
    assert port.last_command.startswith(b"ES+R2200")


@pytest.mark.parametrize("reply", [b"OK+D8220001FF\n", b"BAD+D8220001FF BD888E1F\n"])
def test_status_control_word_malformed_raises(reply):
    dev = UHF_Device(ScriptedSerial(reply))
    with pytest.raises(UHFResponseParsingError):
        dev.get_status_control_word()
