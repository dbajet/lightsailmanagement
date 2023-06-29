import hashlib
import json
from typing import NamedTuple


class AlarmDefinition(NamedTuple):
    name: str
    server: str
    metric: str
    operator: str
    threshold: float
    evaluation_periods: int
    datapoints_to_alarm: int

    def to_json(self) -> dict:
        return {
            "alarmName": self.name,
            "metricName": self.metric,
            "monitoredResourceName": self.server,
            "comparisonOperator": self.operator,
            "threshold": self.threshold,
            "evaluationPeriods": self.evaluation_periods,
            "datapointsToAlarm": self.datapoints_to_alarm,
            "treatMissingData": "breaching",
            "contactProtocols": ["Email"],
            "notificationTriggers": ["OK", "ALARM"],
            "notificationEnabled": True,
        }

    def hashed(self) -> str:
        return hashlib.md5(json.dumps(self.to_json(), sort_keys=True).encode()).hexdigest()

