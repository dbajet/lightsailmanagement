from typing import NamedTuple


class AlarmResponse(NamedTuple):
    name: str
    server: str
    metric: str
    state: str
    period: int
    statistic: str
    threshold: float
    unit: str
    datapoints_to_alarm: int
    evaluation_periods: int
    operator: str

    def __eq__(self, other):
        assert isinstance(other, AlarmResponse)
        return self.server == other.server and self.metric == other.metric

    def __lt__(self, other):
        assert isinstance(other, AlarmResponse)
        if self.server < other.server:
            return True
        if self.server == other.server and self.metric < other.metric:
            return True
        return False
