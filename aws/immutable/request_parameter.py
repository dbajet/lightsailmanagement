from typing import NamedTuple


class RequestParameter(NamedTuple):
    tag_key: str
    tag_value: str
    command: str
