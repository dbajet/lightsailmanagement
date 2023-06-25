from aws.immutable.ssh_command_response import SshCommandResponse
from aws.mutable.port import Port
from aws.mutable.server import Server
from boto3 import Session
from multiprocessing import Queue
from os import getenv
from pathlib import Path
from pprint import pprint
from subprocess import check_output


class LightSail:
    def __init__(self) -> None:
        session = Session(
            aws_access_key_id=getenv("LIGHTSAIL_ACCOUNT"),
            aws_secret_access_key=getenv("LIGHTSAIL_SECRET"),
            region_name="us-west-2",
        )
        self.client = session.client("lightsail")

    def list_servers(self, tag_key: str, tag_value: str) -> list[Server]:
        result: list[Server] = []

        response = self.client.get_instances()
        while True:
            for instance in response["instances"]:
                if tag_key and {"key": tag_key, "value": tag_value} not in instance["tags"]:
                    continue

                ports: list[Port] = []
                for port in instance["networking"]["ports"]:
                    ports.append(
                        Port(
                            FromPort=port["fromPort"],
                            ToPort=port["toPort"],
                            Protocol=port["protocol"],
                            Cidrs=port["cidrs"],
                        )
                    )
                result.append(
                    Server(
                        name=instance["name"],
                        tags=sorted(instance["tags"], key=lambda x: x["key"]),
                        internal_ip=instance["privateIpAddress"],
                        external_ip=instance["publicIpAddress"],
                        firewall=ports,
                        state=instance["state"]["name"],
                        cpu=instance["hardware"]["cpuCount"],
                        memory_gb=instance["hardware"]["ramSizeInGb"],
                    )
                )

            if "nextPageToken" not in response:
                break
            response = self.client.get_instances(pageToken=response["nextPageToken"])

        return result

    def list_alerts(self, tag_key: str, tag_value: str):
        response = self.client.get_alarms()
        pprint(response)

    def get_ssh_key(self) -> str:
        key_file = Path(f"{Path(__file__).parent}/aws_private_key.txt")
        if key_file.exists() is False:
            response = self.client.download_default_key_pair()
            # with open(key_file, "w") as f:
            #     f.write(response["privateKeyBase64"])
            key_file.write_text(response["privateKeyBase64"])
            key_file.chmod(0o600)
        return key_file.as_posix()

    def run_command(self, queue: Queue, server: str, public_ip: str, command: str) -> SshCommandResponse:
        ssh_key = self.get_ssh_key()
        ssh_command = f'ssh -i {ssh_key} -o StrictHostKeyChecking=no ubuntu@{public_ip}  "{command}" '
        output = check_output(ssh_command, shell=True)
        result = SshCommandResponse(server=f"{server} ({public_ip})", response=output.decode("utf-8").split("\n"))
        queue.put(result)
        return result
