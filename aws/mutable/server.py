from dataclasses import dataclass

from aws.mutable.port import Port


@dataclass
class Server:
    Name: str
    Tags: list[dict[str, str]]
    InternalIP: str
    ExternalIP: str
    Firewall: list[Port]
    State: str
    Cpu: int
    MemoryGb: float
