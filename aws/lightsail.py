from multiprocessing import Queue
from os import getenv
from pathlib import Path
from subprocess import check_output

from boto3 import Session

from aws.immutable.alarm_response import AlarmResponse
from aws.immutable.ssh_command_response import SshCommandResponse
from aws.mutable.alarm_definition import AlarmDefinition
from aws.mutable.port import Port
from aws.mutable.server import Server


class LightSail:
    def __init__(self, region: str) -> None:
        session = Session(
            aws_access_key_id=getenv("LIGHTSAIL_ACCOUNT"),
            aws_secret_access_key=getenv("LIGHTSAIL_SECRET"),
            region_name=region,
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

    def list_alarms(self, servers: list[str]) -> list[AlarmResponse]:
        result: list[AlarmResponse] = []
        response = self.client.get_alarms()
        while True:
            for alarm in response["alarms"]:
                server = alarm["monitoredResourceInfo"]["name"]
                if server not in servers:
                    continue
                result.append(
                    AlarmResponse(
                        name=alarm["name"],
                        server=server,
                        metric=alarm["metricName"],
                        period=alarm["period"],
                        statistic=alarm["statistic"],
                        threshold=alarm["threshold"],
                        unit=alarm["unit"],
                        state=alarm["state"],
                        datapoints_to_alarm=alarm["datapointsToAlarm"],
                        evaluation_periods=alarm["evaluationPeriods"],
                        operator=alarm["comparisonOperator"],
                    )
                )
            if "nextPageToken" not in response:
                break
            response = self.client.get_alarms(pageToken=response["nextPageToken"])
        return result

    def set_alarms(self, servers: list[str], alarms: list[AlarmDefinition]):
        # retrieve the current alarms
        current: dict[str, str] = {}
        for alarm_response in self.list_alarms(servers):
            definition = AlarmDefinition(
                name=alarm_response.name,
                server=alarm_response.server,
                metric=alarm_response.metric,
                threshold=alarm_response.threshold,
                evaluation_periods=alarm_response.evaluation_periods,
                datapoints_to_alarm=alarm_response.datapoints_to_alarm,
                operator=alarm_response.operator,
            )
            current[definition.name] = definition.hashed()
        # set the alarms (that have changed)
        for alarm_definition in alarms:
            if not (alarm_definition.name in current and alarm_definition.hashed() == current[alarm_definition.name]):
                json_alarm = alarm_definition.to_json()
                self.client.put_alarm(**json_alarm)
            if alarm_definition.name in current:
                del current[alarm_definition.name]
        # delete the alarms no longer in use
        for alarm_name in current.keys():
            self.client.delete_alarm(alarmName=alarm_name)

    def get_ssh_key(self) -> str:
        key_file = Path(f"{Path(__file__).parent.parent}/secrets/aws_private_key.txt")
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

    def set_rules(self, server: str, rules: list[Port]):
        json_rules: list[dict] = []
        for rule in rules:
            json_rule = rule.to_json()
            if rule.ToPort == 22:
                json_rule |= {"cidrListAliases": ["lightsail-connect"]}  # always allow the AWS console to access
            json_rules.append(json_rule)
        self.client.put_instance_public_ports(instanceName=server, portInfos=json_rules)
