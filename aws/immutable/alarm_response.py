from typing import NamedTuple


class AlarmResponse(NamedTuple):
    server: str
    metric: str
    state: str
    period: int
    statistic: str
    threshold: float
    unit: str
