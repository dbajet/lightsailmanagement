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

    def pair_tags(self) -> str:
        tags = [f"{tag['key']}: {tag.get('value', '')}" for tag in self.tags if "value" in tag]
        return f" {', '.join(tags)}"

    def single_tags(self) -> str:
        tags = [f"{tag['key']}" for tag in self.tags if "value" not in tag]
        return f" {', '.join(tags)}"
