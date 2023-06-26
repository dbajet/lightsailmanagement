from __future__ import annotations
import argparse
from aws.immutable.request_parameter import RequestParameter
from aws.immutable.ssh_command_response import SshCommandResponse
from aws.lightsail import LightSail
from dataclasses import dataclass
from multiprocessing import Process, Queue
from pprint import pprint
from time import monotonic, sleep
from typing import Callable


class Menu:
    def __init__(self, light_sail: LightSail):
        self.light_sail = light_sail

    @classmethod
    def run(cls, instance: Menu):
        commands = {
            "servers": instance.show_servers,
            "firewall": instance.show_firewall_rules,
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
            tags = [f"{tag['key']}: {tag['value']}" for tag in server.tags]
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

    def show_alerts(self, request: RequestParameter):
        servers = [server.name for server in self.light_sail.list_servers(request.tag_key, request.tag_value)]
        print("Servers:", ", ".join(servers))
        if servers:
            for alert in self.light_sail.list_alerts(servers=servers):
                print(f"------")
                print(f" {alert.server} ({alert.metric}, {alert.state})")
                print(f" Every: {alert.period}s, check {alert.statistic} is under {alert.threshold} {alert.unit}")

    def run_command(self, request: RequestParameter):
        if not request.command:
            command = input("Type the command:")
        if request.command:
            queue: Queue = Queue()
            processes = [
                Process(
                    target=self.light_sail.run_command, args=[queue, server.name, server.external_ip, request.command]
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
    print(f"Time: {monotonic()-start:1.2f}s")
