import os
from pathlib import Path
import boto3
from pprint import pprint
from aws.mutable.port import Port
from aws.mutable.server import Server


class LightSail:
    def __init__(self) -> None:
        session = boto3.Session(
            aws_access_key_id=os.getenv("LIGHTSAIL_ACCOUNT"),
            aws_secret_access_key=os.getenv("LIGHTSAIL_SECRET"),
            region_name="us-west-2",
        )
        self.client = session.client("lightsail")

    def list_servers(self) -> list[Server]:
        result: list[Server] = []

        response = self.client.get_instances()
        while True:
            for instance in response["instances"]:
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
                        Name=instance["name"],
                        Tags=sorted(instance["tags"], key=lambda x: x["key"]),
                        InternalIP=instance["privateIpAddress"],
                        ExternalIP=instance["publicIpAddress"],
                        Firewall=ports,
                        State=instance["state"]["name"],
                        Cpu=instance["hardware"]["cpuCount"],
                        MemoryGb=instance["hardware"]["ramSizeInGb"],
                    )
                )

            if "nextPageToken" not in response:
                break
            response = self.client.get_instances(pageToken=response["nextPageToken"])

        return result

    def list_alerts(self):
        response = self.client.get_alarms()
        pprint(response)

    def get_ssh_key(self):
        path = Path(__file__)
        print("--->", path.as_posix())

    def run_command(self, command: str) -> list[str]:
        ssh_key = self.get_ssh_key()
