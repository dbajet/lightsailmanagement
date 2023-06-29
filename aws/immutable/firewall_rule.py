from typing import NamedTuple


class FirewallRule(NamedTuple):
    server: str
    port: int
    protocol: str
    rules: list[str]
