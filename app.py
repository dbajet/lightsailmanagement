from __future__ import annotations

import argparse
import json
from multiprocessing import Process, Queue
from pathlib import Path
from time import monotonic, sleep

from aws.immutable.firewall_rule import FirewallRule
from aws.immutable.print_column import PrintColumn
from aws.immutable.request_parameter import RequestParameter
from aws.lightsail import LightSail
from aws.mutable.alarm_definition import AlarmDefinition
from aws.mutable.port import Port
from aws.mutable.server import Server


class Menu:
    ALL_SERVER = "ALL_SERVER"

    def __init__(self, light_sail: LightSail):
        self.light_sail = light_sail

    @classmethod
    def run(cls, instance: Menu):
        commands = {
            "servers": instance.show_servers,
            "firewall": instance.show_firewall_rules,
            "setFirewall": instance.set_firewall_rules,
            "alerts": instance.show_alerts,
            "setAlerts": instance.set_alerts,
            "command": instance.run_command,
        }
        parser = argparse.ArgumentParser(description="LightSail management helper")
        parser.add_argument("what", help="the command to run", choices=list(commands.keys()))
        parser.add_argument("--command", help="the command to run on each server", default="hostname")
        parser.add_argument("--tag", help="the tag to identify the servers (provided as key:value)", default="")

        args = parser.parse_args()
        tag_key, tag_value, *_ = (args.tag + ":").split(":")
        request = RequestParameter(tag_key=tag_key, tag_value=tag_value, command=args.command)
        if args.what in commands:
            commands[args.what](request)

    def show_servers(self, request: RequestParameter):
        columns = [
            PrintColumn(label="server", alignment=PrintColumn.left(), size=32, formatter=lambda x: x.name),
            PrintColumn(label="cpu", alignment=PrintColumn.right(), size=3, formatter=lambda x: x.cpu),
            PrintColumn(label="RAM (Gb)", alignment=PrintColumn.center(), size=6, formatter=lambda x: x.memory_gb),
            PrintColumn(label="public IP", alignment=PrintColumn.left(), size=16, formatter=lambda x: x.external_ip),
            PrintColumn(label="private IP", alignment=PrintColumn.left(), size=16, formatter=lambda x: x.internal_ip),
            PrintColumn(label="flags", alignment=PrintColumn.left(), size=5, formatter=lambda x: x.single_tags()),
            PrintColumn(label="tags", alignment=PrintColumn.left(), size=5, formatter=lambda x: x.pair_tags()),
        ]
        servers = self.light_sail.list_servers(request.tag_key, request.tag_value)
        servers.sort(key=lambda x: x.name)
        self.print_table(columns, servers)

    def show_firewall_rules(self, request: RequestParameter):
        columns = [
            PrintColumn(label="server", alignment=PrintColumn.left(), size=32, formatter=lambda x: x.server),
            PrintColumn(label="port", alignment=PrintColumn.right(), size=5, formatter=lambda x: x.port),
            PrintColumn(label="protocol", alignment=PrintColumn.center(), size=5, formatter=lambda x: x.protocol),
            PrintColumn(label="limited to", alignment=PrintColumn.left(), size=5,
                        formatter=lambda x: ",".join(x.rules)),
        ]
        fw_rules: list[FirewallRule] = []
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            for rule in server.firewall:
                rules = rule.Cidrs
                if "0.0.0.0/0" in rule.Cidrs:
                    rules = ["all"]
                fw_rules.append(FirewallRule(
                    server=server.name,
                    port=rule.ToPort,
                    protocol=rule.Protocol,
                    rules=rules,
                ))
        fw_rules.sort(key=lambda x: (x.server, x.port))
        self.print_table(columns, fw_rules)

    def set_firewall_rules(self, request: RequestParameter):
        rules = self.read_firewall_rules()
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            fw_rules: list[Port] = rules.get(self.ALL_SERVER, [])
            for tag in server.tags:
                key = tag["key"]
                if "value" in tag:
                    key = f"{tag['key']}:{tag['value']}"
                fw_rules.extend(rules.get(key, []))
            self.light_sail.set_rules(server.name, fw_rules)
        #
        self.show_firewall_rules(request)

    @classmethod
    def read_firewall_rules(cls) -> dict[str, list[Port]]:
        result: dict[str, list[Port]] = {}
        fw_file = Path(f"{Path(__file__).parent}/secrets/aws_firewall_rules.json")
        if fw_file.exists() is True:
            rules = json.loads(fw_file.read_text())
            for rule in rules:
                key = rule["tagKey"] or cls.ALL_SERVER
                if rule["tagValue"]:
                    key = f"{rule['tagKey']}:{rule['tagValue']}"
                if key not in result:
                    result[key] = []

                result[key].append(Port(
                    FromPort=rule["fromPort"],
                    ToPort=rule["toPort"],
                    Protocol=rule["protocol"],
                    Cidrs=rule["cidrs"],
                ))
        return result

    def show_alerts(self, request: RequestParameter):
        servers = [server.name for server in self.light_sail.list_servers(request.tag_key, request.tag_value)]
        metric_label = {
            "CPUUtilization": "CPU",
            "BurstCapacityPercentage": "Burst",
        }
        unit_label = {
            "Percent": "%",
        }
        columns = [
            PrintColumn(label="server", alignment=PrintColumn.left(), size=32, formatter=lambda x: x.server),
            PrintColumn(label="metric", alignment=PrintColumn.right(), size=32,
                        formatter=lambda x: metric_label.get(x.metric, x.metric)),
            PrintColumn(label="state", alignment=PrintColumn.center(), size=6,
                        formatter=lambda x: "" if x.state == "OK" else "!!"),
            PrintColumn(label="operator", alignment=PrintColumn.center(), size=3,
                        formatter=lambda x: ">" if x.operator.startswith("Greater") else "<"),
            PrintColumn(label="threshold", alignment=PrintColumn.right(), size=5, formatter=lambda x: x.threshold),
            PrintColumn(label="unit", alignment=PrintColumn.center(), size=3,
                        formatter=lambda x: unit_label.get(x.unit, "?")),
            PrintColumn(label="incidents", alignment=PrintColumn.center(), size=3,
                        formatter=lambda x: x.datapoints_to_alarm),
            PrintColumn(label="period (sec.)", alignment=PrintColumn.right(), size=3,
                        formatter=lambda x: x.period * x.evaluation_periods),
        ]
        alerts = self.light_sail.list_alarms(servers=servers)
        # alerts.sort(key=lambda x: [x.name, x.metric])
        alerts.sort()

        self.print_table(columns, alerts)
        print("Servers:", ", ".join(servers))

    @classmethod
    def print_table(cls, columns: list[PrintColumn], lines: list):
        col_sizes: dict[str, int] = {c.label: max(c.size, len(c.label)) for c in columns}
        for line in lines:
            for c in columns:
                col_sizes[c.label] = max(len(str(c.formatter(line))), col_sizes[c.label])

        length = sum(col_sizes.values()) + len(columns) * 3 - 1
        dashed_line = f"+{'-' * length}+"
        title = ' | '.join([f"{c.label.center(col_sizes[c.label])}" for c in columns])

        print(dashed_line)
        print(f"| {title} |")
        print(dashed_line)
        for line in lines:
            rows: list[str] = []
            for c in columns:
                if c.alignment == PrintColumn.right():
                    text = str(c.formatter(line)).rjust(col_sizes[c.label])
                elif c.alignment == PrintColumn.left():
                    text = str(c.formatter(line)).ljust(col_sizes[c.label])
                else:  # center
                    text = str(c.formatter(line)).center(col_sizes[c.label])
                rows.append(text)
            data = ' | '.join(rows)
            print(f"| {data} |")
        print(dashed_line)

    def set_alerts(self, request: RequestParameter):
        alerts: list[AlarmDefinition] = []
        servers: list[str] = []
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            servers.append(server.name)
            alerts += self.read_alarms(server)

        self.light_sail.set_alarms(servers, alerts)
        #
        self.show_alerts(request)

    @classmethod
    def read_alarms(cls, server: Server) -> list[AlarmDefinition]:
        result: list[AlarmDefinition] = []
        alarms_file = Path(f"{Path(__file__).parent}/secrets/aws_alarms.json")
        if alarms_file.exists() is True:
            alarms = json.loads(alarms_file.read_text())

            tags = [cls.ALL_SERVER]
            tags += [f"{tag['key']}:{tag['value']}" for tag in server.tags if 'value' in tag]
            tags += [tag['key'] for tag in server.tags if 'value' not in tag]

            for alarm in alarms:
                key = alarm["tagKey"] or cls.ALL_SERVER
                if alarm["tagValue"]:
                    key = f"{alarm['tagKey']}:{alarm['tagValue']}"
                if key not in tags:
                    continue

                result.append(AlarmDefinition(
                    name=f"{server.name}_{alarm['alarmName']}",
                    server=server.name,
                    metric=alarm["metricName"],
                    threshold=alarm["threshold"],
                    evaluation_periods=alarm["evaluationPeriods"],
                    datapoints_to_alarm=alarm["datapointsToAlarm"],
                    operator=alarm["comparisonOperator"]
                ))
        return result

    def run_command(self, request: RequestParameter):
        command = request.command
        if not request.command:
            command = input("Type the command:")
        if command:
            queue: Queue = Queue()
            processes = [
                Process(target=self.light_sail.run_command, args=[queue, server.name, server.external_ip, command])
                for server in self.light_sail.list_servers(request.tag_key, request.tag_value)
            ]
            for process in processes:
                process.start()

            while any([process.is_alive() for process in processes]):
                self.print_queue(queue)
                sleep(0.1)
            # last chance
            self.print_queue(queue)

    @classmethod
    def print_queue(cls, queue: Queue):
        while not queue.empty():
            response = queue.get()
            print(f"--- {response.server} ---")
            print("\n".join(response.response))


if __name__ == "__main__":
    start = monotonic()
    Menu.run(Menu(LightSail("us-west-2")))
    # Menu.run(Menu(LightSail("eu-west-3")))
    print(f"Time: {monotonic() - start:1.2f}s")
