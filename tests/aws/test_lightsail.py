from ast import List
from unittest import mock
from aws.lightsail import LightSail


@mock.patch("aws.lightsail.LightSail.get_ssh_key")
def test_run_command(get_ssh_key):
    tested = LightSail()
    #
    calls: list = []
    assert calls == get_ssh_key.mock_calls
    #
    calls = [mock.call()]
    tested.run_command("the command")
    assert calls == get_ssh_key.mock_calls
