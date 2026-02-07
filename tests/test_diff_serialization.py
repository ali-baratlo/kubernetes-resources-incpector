import json
from jsondiff import diff

def test_diff_serialization_with_marshal_and_json_dumps():
    """
    Test that jsondiff with marshal=True and json.loads(json.dumps(...))
    produces a JSON-serializable output with only string keys,
    even for nested list changes.
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

    # This change in a nested list produces integer keys in the diff
    difference = diff(obj1, obj2, syntax='symmetric', marshal=True)

    # Verify that it contains integer keys (which would fail MongoDB insert)
    has_int_key = False
    def check_keys(d):
        nonlocal has_int_key
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(k, int):
                    has_int_key = True
                check_keys(v)
        elif isinstance(d, (list, tuple)):
            for item in d:
                check_keys(item)

    check_keys(difference)
    assert has_int_key, "Should have integer keys for nested list changes"

    # Now apply the fix
    serializable_diff = json.loads(json.dumps(difference))

    # Verify all keys are now strings
    def check_keys_are_strings(d):
        if isinstance(d, dict):
            for k, v in d.items():
                assert isinstance(k, str), f"Key {k} is not a string, it is {type(k)}"
                check_keys_are_strings(v)
        elif isinstance(d, (list, tuple)):
            for item in d:
                check_keys_are_strings(item)

    check_keys_are_strings(serializable_diff)

    # Final check: serializable by standard json
    json_str = json.dumps(serializable_diff)
    assert '"1"' in json_str, "Integer key should be converted to string key"

def test_diff_serialization_with_symbols():
    """
    Verify that marshal=True handles symbols correctly.
    """
    obj1 = {'a': 1, 'b': 2}
    obj2 = {'a': 1, 'c': 3}

    difference = diff(obj1, obj2, syntax='symmetric', marshal=True)
    serializable_diff = json.loads(json.dumps(difference))

    assert "$insert" in serializable_diff or "$delete" in serializable_diff
    for k in serializable_diff.keys():
        assert isinstance(k, str)

def test_resource_dict_key_wash():
    """
    Test that a dictionary with integer keys is washed to have string keys
    using the json.loads(json.dumps()) pattern.
    """
    resource_dict = {
        "metadata": {"name": "test"},
        "data": {1: "val1", 2: "val2"}
    }

    # Wash it
    washed_dict = json.loads(json.dumps(resource_dict))

    assert "1" in washed_dict["data"]
    assert "2" in washed_dict["data"]
    assert 1 not in washed_dict["data"]
    assert isinstance(list(washed_dict["data"].keys())[0], str)
