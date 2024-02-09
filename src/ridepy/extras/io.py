import dataclasses
import importlib
import collections.abc
import json

import operator as op
import functools as ft
import numpy as np

from typing import Iterable
from pathlib import Path

from ridepy.data_structures import TransportSpace
from ridepy.util.spaces_cython import TransportSpace as CyTransportSpace


class ParamsJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder to use when serializing a dictionary containing simulation parameters.
    This is able to serialize `RequestGenerator`, `TransportSpace` and dispatchers.

    Example
    -------

    .. code-block:: python

        json.dumps(params, cls=ParamsJSONEncoder)

    """

    def default(self, obj):
        # request generator?
        if isinstance(obj, type):
            return f"{obj.__module__}.{obj.__qualname__}"
        # TransportSpace?
        elif isinstance(obj, (TransportSpace, CyTransportSpace)):
            # TODO in future, large networks might be saved in another file to be reused
            return {
                f"{obj.__class__.__module__}.{obj.__class__.__name__}": obj.asdict()
            }
        # dispatcher?
        elif callable(obj):
            return f"{obj.__module__}.{obj.__name__}"
        elif isinstance(obj, Path):
            return str(obj.expanduser().resolve())
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return json.JSONEncoder.default(self, obj)


class ParamsJSONDecoder(json.JSONDecoder):
    """
    JSONDecoder to use when deserializing a dictionary containing simulation parameters.
    This is able to deserialize `RequestGenerator`, `TransportSpace` and dispatchers.

    Example
    -------

    .. code-block:: python

       json.loads(params, cls=ParamsJSONDecoder)

    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if "coord_range" in dct:
            dct["coord_range"] = [(a, b) for a, b in dct["coord_range"]]
        else:
            if "initial_location" in dct and isinstance(dct["initial_location"], list):
                dct["initial_location"] = tuple(dct["initial_location"])

            if "initial_locations" in dct and dct["initial_locations"] is not None:
                dct["initial_locations"] = {
                    int(vehicle_id): location
                    for vehicle_id, location in dct["initial_locations"].items()
                }

            for cls_str in [
                "transportation_request_cls",
                "fleet_state_cls",
                "vehicle_state_cls",
                "request_generator_cls",
            ]:
                if cls_str in dct:
                    module, cls = dct[cls_str].rsplit(".", 1)
                    dct[cls_str] = getattr(importlib.import_module(module), cls)

            if "dispatcher_cls" in dct:
                module, cls = dct["dispatcher_cls"].rsplit(".", 1)
                dct["dispatcher_cls"] = getattr(importlib.import_module(module), cls)

            if "space" in dct:
                path, kwargs = next(iter(dct["space"].items()))
                module, cls = path.rsplit(".", 1)
                dct["space"] = getattr(importlib.import_module(module), cls)(**kwargs)

            if "data_dir" in dct:
                dct["data_dir"] = Path(dct["data_dir"])

        return dct


class EventsJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder to use when serializing a list containing `Event`.

    Example
    -------

    .. code-block:: python

        json.dumps(events, cls=EventsJSONEncoder)

    """

    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return {"event_type": obj.__class__.__name__} | dataclasses.asdict(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def sort_params(params: dict) -> dict:
    """
    Returns a copy of the two-level nested dict `params` which is sorted
    in both levels.

    Parameters
    ----------
    params
        Parameter dictionary, two levels of nesting

    Returns
    -------
    params
        Sorted params dict
    """
    params = dict(sorted(params.items(), key=op.itemgetter(0)))
    for outer_key, inner_dict in params.items():
        params[outer_key] = dict(sorted(inner_dict.items(), key=op.itemgetter(0)))
    return params


def create_params_json(*, params: dict, sort=True) -> str:
    """
    Create a dictionary containing simulation parameters to pretty JSON.
    Parameter dictionaries may contain anything that is supported
    by `.ParamsJSONEncoder` and `.ParamsJSONDecoder`, e.g. `RequestGenerator`,
    `TransportSpace`s and dispatchers. For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    params
        dictionary containing the params to save
    sort
        if sort is True, sort the dict recursively to ensure consistent order.
    """
    if sort:
        params = sort_params(params)
    return json.dumps(params, indent=4, cls=ParamsJSONEncoder)


def save_params_json(*, param_path: Path, params: dict) -> None:
    """
    Save a dictionary containing simulation parameters to pretty JSON,
    overwriting existing. Parameter dictionaries may contain anything that is supported
    by `.ParamsJSONEncoder` and `.ParamsJSONDecoder`, e.g. `RequestGenerator`,
    `TransportSpace`s and dispatchers. For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    param_path
        JSON output file path
    params
        dictionary containing the params to save
    """
    with open(str(param_path), "w") as f:
        f.write(create_params_json(params=params))


def read_params_json(param_path: Path) -> dict:
    """
    Read a dictionary containing simulation parameters from JSON.
    Parameter dictionaries may contain anything that is supported
    by `.ParamsJSONEncoder` and `.ParamsJSONDecoder`, e.g. `RequestGenerator`,
    `TransportSpace`s and dispatchers. For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    param_path

    Returns
    -------
    parameter dictionary
    """

    return json.load(param_path.open("r"), cls=ParamsJSONDecoder)


def save_events_json(*, jsonl_path: Path, events: Iterable) -> None:
    """
    Save events iterable to a file according to JSONL specs, appending to existing.
    For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    jsonl_path
        JSON Lines output file path
    events
        iterable containing the events to save
    """
    with jsonl_path.open("a", encoding="utf-8") as f:
        for event in events:
            print(json.dumps(event, cls=EventsJSONEncoder), file=f)


def read_events_json(jsonl_path: Path) -> list[dict]:
    """
    Read events from JSON lines file, where each line of the file contains a single event.
    For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    jsonl_path
       JSON Lines input file path

    Returns
    -------
    List of dicts
    """
    with jsonl_path.open("r", encoding="utf-8") as f:
        return list(map(json.loads, f.readlines()))
