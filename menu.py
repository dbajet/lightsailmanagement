import argparse
from aws.immutable.ssh_command_response import SshCommandResponse
from aws.lightsail import LightSail
from dataclasses import dataclass
from multiprocessing import Process, Queue
from pprint import pprint
from time import monotonic, sleep
from typing import Callable


@dataclass
class MenuItem:
    Label: str
    Method: Callable


class Menu:
    @classmethod
    def run(cls):
        parser = argparse.ArgumentParser(description="My Command-Line Tool")
        parser.add_argument("what", help="the command to run", choices=["servers", "alerts", "command"])
        parser.add_argument("--command", help="the command to run on each server", default="hostname")
        parser.add_argument("--tag", help="the tag to identify the servers (provided as key:value)", default="")

        args = parser.parse_args()
        if args.what == "servers":
            tag_key, tag_value, *_ = (args.tag + ":").split(":")
            cls.show_servers(tag_key, tag_value)
        elif args.what == "command":
            tag_key, tag_value, *_ = (args.tag + ":").split(":")
            cls.run_command(tag_key, tag_value, args.command)
        elif args.what == "alerts":
            tag_key, tag_value, *_ = (args.tag + ":").split(":")
            cls.show_alerts(tag_key, tag_value)

    @classmethod
    def display_menu(cls) -> list[MenuItem]:
        menus = [
            MenuItem("Exit", exit),
            MenuItem("List servers", cls.show_servers),
            MenuItem("List alerts", cls.show_alerts),
            MenuItem("Run command on servers", cls.run_command),
        ]
        for idx, menu in enumerate(menus):
            print(f"{idx:02d} - {menu.Label}")
        return menus

    @classmethod
    def wait_for_command(cls):
        menus = cls.display_menu()
        while True:
            try:
                selected = int(input())
                if 0 <= selected <= len(menus):
                    menus[selected].Method()
                    break
            except KeyboardInterrupt:
                print("\n")
                break
            except ValueError:
                print("selection incorrect, please retry...")
            except Exception as e:
                print(">>>>", e)

    @classmethod
    def show_servers(cls, tag: str, value: str):
        for server in LightSail().list_servers(tag, value):
            print(f"------")
            print(f" {server.name} ({str(server.cpu)} CPU, {str(server.memory_gb)} Gb)")
            print(f" IPs: {server.external_ip: >16} ({server.internal_ip})")
            tags = [f"{tag['key']}: {tag['value']}" for tag in server.tags]
            print(f" {', '.join(tags)}")

    @classmethod
    def show_alerts(cls, tag: str, value: str):
        LightSail().list_alerts(tag, value)

    @classmethod
    def run_command(cls, tag: str, value: str, command: str):
        if not command:
            command = input("Type the command:")
        if command:
            queue: Queue = Queue()
            processes = [
                Process(target=LightSail().run_command, args=[queue, server.name, server.external_ip, command])
                for server in LightSail().list_servers(tag, value)
            ]
            for process in processes:
                process.start()

            while any([process.is_alive() for process in processes]):
                while not queue.empty():
                    cls.print_response(queue.get())
                sleep(0.1)
            while not queue.empty():
                cls.print_response(queue.get())

    @classmethod
    def print_response(cls, response: SshCommandResponse):
        print(f"--- {response.server} ---")
        print("\n".join(response.response))


if __name__ == "__main__":
    Menu.run()
    # # Menu.wait_for_command()
    # start = monotonic()
    # Menu.run_command("hostname")
    # print(f"Time: {monotonic()-start:1.2f}s")
