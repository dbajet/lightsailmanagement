from dataclasses import dataclass


@dataclass
class Port:
    # {'fromPort': 80, 'toPort': 80, 'protocol': 'tcp', 'accessFrom': 'Anywhere (0.0.0.0/0 and ::/0)', 'accessType': 'public', 'commonName': '', 'accessDirection': 'inbound', 'cidrs': ['0.0.0.0/0'], 'ipv6Cidrs': ['::/0'], 'cidrListAliases': []
    FromPort: int
    ToPort: int
    Protocol: str
    Cidrs: list[str]

    def to_json(self) -> dict:
        return {
            'fromPort': self.FromPort,
            'toPort': self.ToPort,
            'protocol': self.Protocol,
            'cidrs': self.Cidrs,
        }
