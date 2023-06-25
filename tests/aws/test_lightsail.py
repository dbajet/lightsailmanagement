from ast import List
from multiprocessing import Queue
from unittest import mock
from aws.lightsail import LightSail


@mock.patch("aws.lightsail.check_output")
@mock.patch("aws.lightsail.LightSail.get_ssh_key")
def test_run_command(get_ssh_key, check_output):
    tested = LightSail()
    #
    calls: list = []
    assert calls == get_ssh_key.mock_calls
    #
    calls = [mock.call()]
    queue: Queue = Queue()
    tested.run_command(queue, "extIp", "the command")
    assert calls == get_ssh_key.mock_calls
    assert 1 == queue.qsize()
