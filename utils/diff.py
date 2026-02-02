import json
import difflib


def get_diff(old, new, path=""):
    """
    Recursively compares two nested dictionaries and returns detailed changes.

    Returns:
        dict with added, removed, modified, and raw_diff.
    """
    added = {}
    removed = {}
    modified = {}

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    for key in new_keys - old_keys:
        full_path = f"{path}.{key}" if path else key
        added[full_path] = new[key]

    for key in old_keys - new_keys:
        full_path = f"{path}.{key}" if path else key
        removed[full_path] = old[key]

    for key in old_keys & new_keys:
        full_path = f"{path}.{key}" if path else key
        old_val = old[key]
        new_val = new[key]

        if isinstance(old_val, dict) and isinstance(new_val, dict):
            sub_diff = get_diff(old_val, new_val, path=full_path)
            added.update(sub_diff["added"])
            removed.update(sub_diff["removed"])
            modified.update(sub_diff["modified"])
        elif old_val != new_val:
            modified[full_path] = {
                "old": old_val,
                "new": new_val
            }

    old_json = json.dumps(old, indent=2, sort_keys=True).splitlines()
    new_json = json.dumps(new, indent=2, sort_keys=True).splitlines()
    raw_diff = list(difflib.unified_diff(old_json, new_json, fromfile="old", tofile="new", lineterm=""))

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "raw_diff": raw_diff
    }
