from aws.immutable.alarm_response import AlarmResponse


def test___init__():
    tested = AlarmResponse(
        name="theName",
        server="theServer",
        metric="theMetric",
        state="theState",
        period=5,
        statistic="theStatistic",
        threshold=57.63,
        unit="theUnit",
        datapoints_to_alarm=3,
        evaluation_periods=67,
        operator="theOperator",
    )
    assert "theName" == tested.name
    assert "theServer" == tested.server
    assert "theMetric" == tested.metric
    assert "theState" == tested.state
    assert 5 == tested.period
    assert "theStatistic" == tested.statistic
    assert 57.63 == tested.threshold
    assert "theUnit" == tested.unit
    assert 3 == tested.datapoints_to_alarm
    assert 67 == tested.evaluation_periods
    assert "theOperator" == tested.operator


def test___eq__():
    ...
