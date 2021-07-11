import dataclasses

import importlib

import collections.abc
import json
import operator as op
import functools as ft

from typing import Iterable

from ridepy.data_structures import TransportSpace
from ridepy.util.spaces_cython import TransportSpace as CyTransportSpace
import ridepy.events
from ridepy.events import Event
from pathlib import Path


class ParamsJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder to use when serializing a dictionary containing simulation parameters.
    This is able to serialize `RequestGenerator`, `TransportSpace` and dispatchers.

    Example
    -------

    .. code-block:: python

        >>> json.dumps(params, cls=ParamsJSONEncoder)

    """

    def default(self, obj):
        # request generator?
        if isinstance(obj, type):
            return f"{obj.__module__}.{obj.__name__}"
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
        else:
            return json.JSONEncoder.default(self, obj)


class ParamsJSONDecoder(json.JSONDecoder):
    """
    JSONDecoder to use when deserializing a dictionary containing simulation parameters.
    This is able to deserialize `RequestGenerator`, `TransportSpace` and dispatchers.

    Example
    -------

    .. code-block:: python

        >>> json.loads(params, cls=ParamsJSONDecoder)

    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if "coord_range" in dct:
            dct["coord_range"] = [(a, b) for a, b in dct["coord_range"]]
        else:
            if "initial_location" in dct and isinstance(dct["initial_location"], list):
                dct["initial_location"] = tuple(dct["initial_location"])

            for cls_str in [
                "TransportationRequestCls",
                "FleetStateCls",
                "VehicleStateCls",
                "RequestGeneratorCls",
            ]:
                if cls_str in dct:
                    module, cls = dct[cls_str].rsplit(".", 1)
                    dct[cls_str] = getattr(importlib.import_module(module), cls)

            if "dispatcher" in dct:
                module, cls = dct["dispatcher"].rsplit(".", 1)
                dct["dispatcher"] = getattr(importlib.import_module(module), cls)

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

        >>> json.dumps(events, cls=EventsJSONEncoder)

    """

    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return {obj.__class__.__name__: dataclasses.asdict(obj)}
        else:
            return json.JSONEncoder.default(self, obj)


class EventsJSONDecoder(json.JSONDecoder):
    """
    JSONDecoder to use when deserializing a list containing `Event`.

    This is able to deserialize

    * `VehicleStateBeginEvent`
    * `VehicleStateEndEvent`
    * `PickupEvent`
    * `DeliveryEvent`
    * `RequestSubmissionEvent`
    * `RequestAcceptanceEvent`
    * `RequestRejectionEvent`

    Example
    -------

    .. code-block:: python

        >>> json.loads(events, cls=EventsJSONDecoder)

    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        for location_like in ["origin", "destination", "location"]:
            if location_like in dct and isinstance(dct[location_like], list):
                dct[location_like] = tuple(dct[location_like])

        # NOTE: possibly make this call some list-of-events-generating function
        if (cls := next(iter(dct.keys()))) in [
            "VehicleStateBeginEvent",
            "VehicleStateEndEvent",
            "PickupEvent",
            "DeliveryEvent",
            "RequestSubmissionEvent",
            "RequestAcceptanceEvent",
            "RequestRejectionEvent",
        ]:
            dct = getattr(ridepy.events, cls)(**dct[cls])

        return dct


def create_params_json(*, params: dict) -> str:
    """
    Create a dictionary containing simulation parameters to pretty JSON.
    Parameter dictionaries may contain anything that is supported
    by `.ParamsJSONEncoder` and `.ParamsJSONDecoder`, e.g. `RequestGenerator`,
    `TransportSpace`s and dispatchers. For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    params
        dictionary containing the params to save
    """
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


def read_events_json(jsonl_path: Path) -> List[tuple[str, dict]]:
    """
    Read events from JSON lines file, where each line of the file contains a single event.
    For additional detail, see :ref:`Executing Simulations`.

    Parameters
    ----------
    jsonl_path
       JSON Lines input file path

    Returns
    -------
    List of (event_name, event_properties_dict) tuples
    """
    with jsonl_path.open("r", encoding="utf-8") as f:
        json_lines = f.readlines()

    return [next(iter(json.loads(line).items())) for line in json_lines]
