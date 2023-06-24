from dataclasses import dataclass
from typing import Callable
from aws.lightsail import LightSail


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
            print(f" {server.Name} ({str(server.Cpu)} CPU, {str(server.MemoryGb)} Gb)")
            print(f" IPs: {server.ExternalIP: >16} ({server.InternalIP})")
            tags = [f"{tag['key']}: {tag['value']}" for tag in server.Tags]
            print(f" {', '.join(tags)}")

        # print("--->", LightSail().ListServers())

    @classmethod
    def show_alerts(cls):
        print(">>>>", "ShowAlerts")
        LightSail().list_alerts()

    @classmethod
    def run_command(cls):
        print(">>>>", "RunCommand")
        LightSail().run_command("whoami")


if __name__ == "__main__":
    Menu.wait_for_command()
