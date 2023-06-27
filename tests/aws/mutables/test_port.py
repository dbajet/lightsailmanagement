import sys

app_root = "/media/RATIONALAI/code/lightsailmanagement/"
sys.path.append(app_root)
from aws.mutable.port import Port


def test_to_json():
    tested = Port(FromPort=10080, ToPort=10081, Protocol="tcp", Cidrs=["10.0.0.1/32", "10.0.0.2/32"])
    result = tested.to_json()
    expected = {
        'fromPort': 10080,
        'toPort': 10081,
        'protocol': 'tcp',
        'cidrs': ['10.0.0.1/32', '10.0.0.2/32'],
    }
    assert expected == result, "nope"
    print("OK")


if __name__ == "__main__":
    test_to_json()
