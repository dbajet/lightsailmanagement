from typing import NamedTuple, Callable


class PrintColumn(NamedTuple):
    label: str
    size: int
    formatter: Callable
    alignment: str

    @classmethod
    def left(cls) -> str:
        return "left"

    @classmethod
    def right(cls) -> str:
        return "right"

    @classmethod
    def center(cls) -> str:
        return "center"
