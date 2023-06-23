from dataclasses import dataclass
from aws.lightsail import LightSail


@dataclass
class MenuItem:
    Label: str
    Method: callable


class Menu:
    @classmethod
    def displayMenu(cls) -> list[MenuItem]:
        menus = [
            MenuItem("Exit", exit),
            MenuItem("List servers", cls.ShowServers),
            MenuItem("List alerts", cls.ShowAlerts),
        ]
        for idx, menu in enumerate(menus):
            print(f"{idx:02d} - {menu.Label}")
        return menus

    @classmethod
    def WaitForCommand(cls):
        menus = cls.displayMenu()
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
    def ShowServers(cls):
        for server in LightSail().ListServers():
            print(f"------")
            print(f" {server.Name} ({str(server.Cpu)} CPU, {str(server.MemoryGb)} Gb)")
            print(f" IPs: {server.ExternalIP: >16} ({server.InternalIP})")
            tags = [f"{tag['key']}: {tag['value']}" for tag in server.Tags]
            print(f" {', '.join(tags)}")

        # print("--->", LightSail().ListServers())

    @classmethod
    def ShowAlerts(cls):
        print(">>>>", "ShowAlerts")
        LightSail().ListAlerts()


Menu.WaitForCommand()
