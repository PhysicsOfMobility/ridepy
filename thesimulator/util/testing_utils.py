from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.spaces_cython import spaces as cyspaces
from typing import Literal

from thesimulator import data_structures as pyds, data_structures_cython as cyds
from thesimulator import data_structures_cython as cyds
from thesimulator.util import spaces as pyspaces
from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)


def stoplist_from_properties(*, stoplist_properties, space, kind):
    if kind == "python":
        data_structure_module = pyds
    elif kind == "cython":
        data_structure_module = cyds
    else:
        raise ValueError(f"Supplied invalid {kind=}, must be 'python' or 'cython'")

    python_stoplist = [
        data_structure_module.Stop(
            location=loc,
            request=data_structure_module.InternalRequest(
                request_id=-1, creation_timestamp=0, location=loc
            ),
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=cpat,
            occupancy_after_servicing=0,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]

    if kind == "python":
        return python_stoplist
    else:
        return cyds.Stoplist(python_stoplist=python_stoplist, loc_type=space.loc_type)


def setup_insertion_data_structures(
    stoplist_properties,
    request_properties,
    space_type: str,
    kind,
):
    """

    Parameters
    ----------
    stoplist_properties
    request_properties
    kind
        'cython' or 'python'

    Returns
    -------
    space, request, stoplist, dispatcher
    """

    if kind == "python":
        spaces = pyspaces
        ds = pyds
        dispatcher = py_brute_force_total_traveltime_minimizing_dispatcher
    elif kind == "cython":
        spaces = cyspaces
        ds = cyds
        dispatcher = cy_brute_force_total_traveltime_minimizing_dispatcher
    else:
        raise ValueError(f"Supplied invalid {kind=}, must be 'python' or 'cython'")

    space = getattr(spaces, space_type)()

    # set up the request
    request = ds.TransportationRequest(**request_properties)

    # set up the stoplist
    stoplist = stoplist_from_properties(
        stoplist_properties=stoplist_properties, space=space, kind=kind
    )

    return space, request, stoplist, dispatcher
