import json
from typing import Iterable

from thesimulator.util import make_dict
from pathlib import Path


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (s := make_dict(obj, raise_errors=False)) is not None:
            return {obj.__class__.__name__: s}
        elif isinstance(obj, type):
            return obj.__name__
        elif callable(obj):
            return obj.__name__
        else:
            try:
                return json.JSONEncoder.default(self, obj)
            except TypeError:
                return repr(obj)


def save_params_json(param_path: Path, params: dict):
    """
    Save params dictionary to pretty JSON, overwriting existing.

    Parameters
    ----------
    param_path
        JSON output file path
    params
        dictionary containing the params to save
    """
    json.dump(params, param_path.open("w"), indent=4, cls=CustomJSONEncoder)


def save_events_json(jsonl_path: Path, events: Iterable):
    """
    Save events iterable to file according to JSONL specs, appending to existing.

    Parameters
    ----------
    jsonl_path
        JSON Lines output file path
    events
        iterable containing the events to save
    """
    with jsonl_path.open("a", encoding="utf-8") as f:
        for event in events:
            print(json.dumps(event, cls=CustomJSONEncoder), file=f)
