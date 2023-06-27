from __future__ import annotations

import argparse
import json
from multiprocessing import Process, Queue
from pathlib import Path
from time import monotonic, sleep

from aws.immutable.request_parameter import RequestParameter
from aws.lightsail import LightSail
from aws.mutable.port import Port


class Menu:
    def __init__(self, light_sail: LightSail):
        self.light_sail = light_sail

    @classmethod
    def run(cls, instance: Menu):
        commands = {
            "servers": instance.show_servers,
            "firewall": instance.show_firewall_rules,
            "setFirewall": instance.set_firewall_rules,
            "alerts": instance.show_alerts,
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
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            print(f"------")
            print(f" {server.name} ({str(server.cpu)} CPU, {str(server.memory_gb)} Gb)")
            print(f" IPs: {server.external_ip: >16} ({server.internal_ip})")
            tags = [f"{tag['key']}: {tag.get('value', '')}" for tag in server.tags if "value" in tag]
            tags += [f"{tag['key']}" for tag in server.tags if "value" not in tag]
            print(f" {', '.join(tags)}")

    def show_firewall_rules(self, request: RequestParameter):
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            print(f"------")
            print(f" {server.name} ({str(server.cpu)} CPU, {str(server.memory_gb)} Gb)")
            for rule in server.firewall:
                rules = f"{rule.Cidrs}"
                if rule.Cidrs == ["0.0.0.0/0"]:
                    rules = "open"
                print(f" port: {rule.ToPort: >6} ({rule.Protocol}) {rules}")

    def set_firewall_rules(self, request: RequestParameter):
        rules = self.read_firewall_rules()
        for server in self.light_sail.list_servers(request.tag_key, request.tag_value):
            fw_rules: list[Port] = rules.get("ALL", [])
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
                key = rule["tagKey"] or "ALL"
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
        print("Servers:", ", ".join(servers))
        if servers:
            for alert in self.light_sail.list_alerts(servers=servers):
                print(f"------")
                print(f" {alert.server} ({alert.metric}, {alert.state})")
                print(f" Every: {alert.period}s, check {alert.statistic} is under {alert.threshold} {alert.unit}")

    def run_command(self, request: RequestParameter):
        command = request.command
        if not request.command:
            command = input("Type the command:")
        if command:
            queue: Queue = Queue()
            processes = [
                Process(
                    target=self.light_sail.run_command, args=[queue, server.name, server.external_ip, command]
                )
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
