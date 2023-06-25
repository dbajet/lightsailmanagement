from typing import NamedTuple


class SshCommandResponse(NamedTuple):
    server: str
    response: list[str]
