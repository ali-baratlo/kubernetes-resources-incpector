import json
from jsondiff import diff

def test_diff_serialization_with_marshal():
    """
    Test that jsondiff with marshal=True produces a JSON-serializable output
    even when there are changes that would normally result in Symbol keys.
    """
    obj1 = {
        "metadata": {"name": "test-pod", "labels": {"app": "old-app"}},
        "spec": {"containers": [{"image": "old-image"}]}
    }

    obj2 = {
        "metadata": {"name": "test-pod", "labels": {"app": "new-app", "env": "prod"}},
        "spec": {"containers": [{"image": "new-image"}]}
    }

    # This kind of change (addition of 'env' label, and multiple updates)
    # often triggers the use of symbols in jsondiff with symmetric syntax.

    difference = diff(obj1, obj2, syntax='symmetric', marshal=True)

    # If this fails, the fix is not working
    try:
        json_str = json.dumps(difference)
        print(f"Serialized diff: {json_str}")
    except TypeError as e:
        assert False, f"JSON serialization failed: {e}"

    # Verify that the marshaled diff contains the expected string keys instead of symbols
    assert "$insert" in str(difference) or "$update" in str(difference) or "$delete" in str(difference) or any(isinstance(k, str) and k.startswith('$') for k in difference.keys())

    # A more specific check for the produced structure
    # With symmetric syntax and marshal=True, it should look like this:
    # {'metadata': {'labels': {'env': 'prod', '$insert': {'env': 'prod'}, 'app': 'new-app'}}, ...}
    # Wait, actually it might vary, but the keys must be strings.
    for key in difference.keys():
        assert isinstance(key, str), f"Key {key} is not a string, it is {type(key)}"

def test_diff_serialization_failure_without_marshal():
    """
    Verify that without marshal=True, it indeed fails to serialize (sanity check).
    """
    obj1 = {'a': 1, 'b': 2}
    obj2 = {'a': 1, 'c': 3}

    difference = diff(obj1, obj2, syntax='symmetric')

    import pytest
    with pytest.raises(TypeError, match="keys must be str, int, float, bool or None, not Symbol"):
        json.dumps(difference)
