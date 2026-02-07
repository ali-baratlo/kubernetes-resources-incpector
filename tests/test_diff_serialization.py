import json
from jsondiff import diff
from collectors.resource_collector import wash_keys
import mongomock
from datetime import datetime

def test_wash_keys():
    """
    Test that wash_keys recursively ensures all dictionary keys are strings
    and converts tuples to lists, while preserving other types like datetime.
    """
    now = datetime.utcnow()
    d = {
        1: "a",
        "b": (2, 3),
        "c": {"d": {4: "e"}},
        "e": now
    }
    washed = wash_keys(d)

    # Check keys
    assert "1" in washed
    assert 1 not in washed
    assert isinstance(list(washed.keys())[0], str)

    # Check nested keys
    assert "4" in washed["c"]["d"]
    assert 4 not in washed["c"]["d"]

    # Check tuples to lists
    assert washed["b"] == [2, 3]
    assert isinstance(washed["b"], list)

    # Check datetime preservation
    assert washed["e"] == now
    assert isinstance(washed["e"], datetime)

def test_mongo_insertion_with_washed_keys():
    """
    Verify that a dictionary washed with wash_keys can be inserted into MongoDB.
    """
    client = mongomock.MongoClient()
    db = client.testdb
    coll = db.testcoll

    d = {1: "a", "nested": {2: "b"}}
    washed = wash_keys(d)

    # Should not raise any error
    coll.insert_one(washed)

    inserted = coll.find_one({"1": "a"})
    assert inserted is not None
    assert inserted["nested"]["2"] == "b"

def test_diff_serialization_with_wash_keys():
    """
    Test that wash_keys correctly handles output from jsondiff.
    """
    obj1 = {
        "spec": {
            "containers": [
                {"name": "c1", "image": "i1"},
                {"name": "c2", "image": "i2"}
            ]
        }
    }

    obj2 = {
        "spec": {
            "containers": [
                {"name": "c1", "image": "i1"},
                {"name": "c2", "image": "i3"}
            ]
        }
    }

    difference = diff(obj1, obj2, syntax='symmetric', marshal=True)
    # This difference contains integer keys (index 1) and potentially tuples

    washed_diff = wash_keys(difference)

    # Verify all keys are strings
    def check_keys_are_strings(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert isinstance(k, str), f"Key {k} is not a string, it is {type(k)}"
                check_keys_are_strings(v)
        elif isinstance(obj, list):
            for item in obj:
                check_keys_are_strings(item)

    check_keys_are_strings(washed_diff)

    # Verify we can dump it to JSON
    json_str = json.dumps(washed_diff)
    assert '"1"' in json_str
