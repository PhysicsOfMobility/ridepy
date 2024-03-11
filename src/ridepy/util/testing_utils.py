import dataclasses

from ridepy.data_structures import Location, TransportSpace, Stoplist, Dispatcher
from ridepy.util.spaces_cython import TransportSpace as CyTransportSpace
from ridepy.util.testing_utils_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)
from ridepy.util.spaces_cython import spaces as cyspaces
from typing import Literal, Iterable, Union, Callable, Sequence

from ridepy import data_structures as pyds, data_structures_cython as cyds
from ridepy import data_structures_cython as cyds
from ridepy.util import spaces as pyspaces
from ridepy.util.dispatchers.ridepooling import (
    BruteForceTotalTravelTimeMinimizingDispatcher,
)


def stoplist_from_properties(
    *,
    stoplist_properties: Iterable[Sequence[Union[Location, float]]],
    space: Union[TransportSpace, CyTransportSpace],
    kind: str,
) -> Union[Stoplist, cyds.Stoplist]:
    """
    Generate stoplist from an iterable of stop properties.
    Format:

    .. code-block:: python

        (
            (location, CPAT, timewindow_min, timewindow_max),
            ...,
        )

    or

    .. code-block:: python

        (
            (location, CPAT, timewindow_min, timewindow_max, occupancy_after_servicing),
            ...,
        )

    Parameters
    ----------
    stoplist_properties
        Iterable of stop property tuples `(location, CPAT, timewindow_min, timewindow_max)`
    space
        Space to place the stops on
    kind
        "cython" or "python"

    Returns
    -------

    """

    if kind == "python":
        data_structure_module = pyds
    elif kind == "cython":
        data_structure_module = cyds
    else:
        raise ValueError(f"Supplied invalid {kind=}, must be 'python' or 'cython'")

    python_stoplist = [
        data_structure_module.Stop(
            location=prop[0],
            request=data_structure_module.InternalRequest(
                request_id=-1, creation_timestamp=0, location=prop[0]
            ),
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=prop[1],
            occupancy_after_servicing=prop[4] if len(prop) == 5 else 0,
            time_window_min=prop[2],
            time_window_max=prop[3],
        )
        for prop in stoplist_properties
    ]

    if kind == "python":
        return python_stoplist
    else:
        return cyds.Stoplist(python_stoplist=python_stoplist, loc_type=space.loc_type)


def setup_insertion_data_structures(
    *,
    stoplist_properties: Iterable[Sequence[Union[Location, float]]],
    request_properties,
    space_type: str,
    kind: str,
) -> tuple[
    Union[TransportSpace, CyTransportSpace],
    Union[pyds.TransportationRequest, cyds.TransportationRequest],
    Union[Stoplist, cyds.Stoplist],
    Dispatcher,
]:
    """

    Parameters
    ----------
    stoplist_properties
    request_properties
    space_type
    kind
        'cython' or 'python'

    Returns
    -------
    space, request, stoplist, dispatcher
    """

    if kind == "python":
        spaces = pyspaces
        ds = pyds
        dispatcher = BruteForceTotalTravelTimeMinimizingDispatcher
    elif kind == "cython":
        spaces = cyspaces
        ds = cyds
        dispatcher = CyBruteForceTotalTravelTimeMinimizingDispatcher
    else:
        raise ValueError(f"Supplied invalid {kind=}, must be 'python' or 'cython'")

    space = getattr(spaces, space_type)()

    # set up the request
    request = ds.TransportationRequest(**request_properties)

    # set up the stoplist
    stoplist = stoplist_from_properties(
        stoplist_properties=stoplist_properties, space=space, kind=kind
    )

    return space, request, stoplist, dispatcher(loc_type=space.loc_type)
