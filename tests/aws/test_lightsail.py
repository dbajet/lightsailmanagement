from multiprocessing import Queue
from time import sleep
from unittest.mock import patch, call
from aws.immutable.ssh_command_response import SshCommandResponse
from aws.lightsail import LightSail


@patch("aws.lightsail.check_output")
@patch("aws.lightsail.LightSail.get_ssh_key")
def test_run_command(get_ssh_key, check_output):
    get_ssh_key.return_value = "theKeyFile"
    check_output.return_value = b"line1\nline2\nline3"

    tested = LightSail("region")
    #
    calls: list = []
    assert calls == get_ssh_key.mock_calls
    assert calls == check_output.mock_calls
    #
    queue: Queue = Queue()
    tested.run_command(queue, "theServer", "extIp", "the command")
    sleep(0.001)  # <-- give the queue the chance to store the response
    calls = [call()]
    assert calls == get_ssh_key.mock_calls
    calls = [call('ssh -i theKeyFile -o StrictHostKeyChecking=no ubuntu@extIp  "the command" ', shell=True)]
    assert calls == check_output.mock_calls
    responses: list = []
    while not queue.empty():
        responses.append(queue.get())
    expected = [SshCommandResponse(server="theServer (extIp)", response=["line1", "line2", "line3"])]
    assert expected == responses
