"""
Server configuration: the defaults must be safe (loopback only, debugger off), and the
Werkzeug debugger must never be started on a non-loopback interface.
"""
import pytest

from app import get_server_config


def test_defaults_are_safe():
    host, port, debug = get_server_config({})
    assert host == "127.0.0.1"
    assert port == 5000
    assert debug is False


def test_environment_overrides_defaults():
    env = {"NETCAT_HOST": "0.0.0.0", "NETCAT_PORT": "8080"}
    assert get_server_config(env) == ("0.0.0.0", 8080, False)


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes"])
def test_debug_can_be_enabled_on_loopback(value):
    assert get_server_config({"NETCAT_DEBUG": value}) == ("127.0.0.1", 5000, True)


@pytest.mark.parametrize("value", ["", "0", "false", "no", "anything-else"])
def test_debug_is_off_unless_explicitly_enabled(value):
    assert get_server_config({"NETCAT_DEBUG": value})[2] is False


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "::"])
def test_debugger_is_refused_on_public_interfaces(host):
    with pytest.raises(SystemExit):
        get_server_config({"NETCAT_DEBUG": "1", "NETCAT_HOST": host})


@pytest.mark.parametrize("port", ["abc", "0", "70000", "-1"])
def test_invalid_port_is_rejected(port):
    with pytest.raises(SystemExit):
        get_server_config({"NETCAT_PORT": port})
