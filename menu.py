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
    def show_servers(cls):
        for server in LightSail().list_servers():
            print(f"------")
            print(f" {server.name} ({str(server.cpu)} CPU, {str(server.memory_gb)} Gb)")
            print(f" IPs: {server.external_ip: >16} ({server.internal_ip})")
            tags = [f"{tag['key']}: {tag['value']}" for tag in server.tags]
            print(f" {', '.join(tags)}")

    @classmethod
    def show_alerts(cls):
        print(">>>>", "ShowAlerts")
        LightSail().list_alerts()

    @classmethod
    def run_command(cls, command: str = ""):
        if not command:
            command = input("Type the command:")
        if command:
            queue: Queue = Queue()
            processes = [
                Process(target=LightSail().run_command, args=[queue, server.external_ip, command])
                for server in LightSail().list_servers()
            ]
            for process in processes:
                process.start()

            while any([process.is_alive() for process in processes]):
                while not queue.empty():
                    print(queue.get())
                sleep(0.1)
            while not queue.empty():
                print(queue.get())


if __name__ == "__main__":
    # Menu.wait_for_command()
    start = monotonic()
    Menu.run_command("hostname")
    print(f"Time: {monotonic()-start:1.2f}s")
