from typing import Tuple

import numpy as np
import itertools as it

from thesimulator.data_structures import (
    ID,
    TransportationRequest,
    Stoplist,
    Stop,
    StopAction,
    TransportSpace,
)

from thesimulator.util.spaces import Graph


def taxicab_dispatcher_drive_first(
    *,
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> Tuple[float, Stoplist, Tuple[float, float, float, float]]:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.

    Parameters
    ----------
    request
        request to be serviced
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist
    space
        transport space the vehicle is operating on

    Returns
    -------


    """
    CPAT_pu = (
        max(
            stoplist[-1].estimated_arrival_time,
            stoplist[-1].time_window_min
            if stoplist[-1].time_window_min is not None
            else 0,
        )
        + space.d(stoplist[-1].location, request.origin)
    )
    EAST_pu = request.pickup_timewindow_min
    CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request.origin, request.destination)
    LAST_pu = (
        CPAT_pu + request.delivery_timewindow_max
        if request.delivery_timewindow_max is not None
        else np.inf
    )
    EAST_do = EAST_pu
    LAST_do = np.inf

    cost = CPAT_do
    stoplist = stoplist + [
        Stop(
            location=request.origin,
            request=request,
            action=StopAction.pickup,
            estimated_arrival_time=CPAT_pu,
            time_window_min=EAST_pu,
            time_window_max=LAST_pu,
        ),
        Stop(
            location=request.destination,
            request=request,
            action=StopAction.dropoff,
            estimated_arrival_time=CPAT_do,
            time_window_min=EAST_do,
            time_window_max=LAST_do,
        ),
    ]
    return cost, stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)


# TODO make this a decorator
def taxicab_dispatcher_drive_first_with_trigger_locations(
    *,
    request: TransportationRequest,
    stoplist: Stoplist,
    space: Graph,
) -> Tuple[float, Stoplist, Tuple[float, float, float, float]]:

    cost, stoplist, time_windows = taxicab_dispatcher_drive_first(
        request=request, stoplist=stoplist, space=space
    )
    i_pu, i_do = it.islice(
        (i for i, s in enumerate(stoplist) if s.request == request), 2
    )

    for stop_a, stop_b in zip(stoplist[i_pu:i_do], stoplist[i_pu + 1 : i_do + 1]):
        space.shortest_path_vertex_sequence(stop_a, stop_b)
        breakpoint()
    return cost, stoplist, time_windows
