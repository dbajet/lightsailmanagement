from dataclasses import dataclass

from aws.mutable.port import Port


@dataclass
class Server:
    name: str
    tags: list[dict[str, str]]
    internal_ip: str
    external_ip: str
    firewall: list[Port]
    state: str
    cpu: int
    memory_gb: float
