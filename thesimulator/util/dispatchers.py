from typing import Tuple

import numpy as np

from thesimulator.data_structures import (
    ID,
    TransportationRequest,
    Stoplist,
    Stop,
    StopAction,
    TransportSpace,
)


def taxicab_dispatcher(
    vehicle_id: ID,
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> Tuple[ID, float, Stoplist, Tuple[float, float, float, float]]:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.

    Parameters
    ----------
    vehicle_id
        vehicle id of the vehicle owning the stoplist
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
    # print(vehicle_id, CPAT_pu)
    CPAT_do = CPAT_pu + space.d(request.origin, request.destination)
    EAST_pu = request.pickup_timewindow_min
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
            vehicle_id=vehicle_id,
            request=request,
            action=StopAction.pickup,
            estimated_arrival_time=CPAT_pu,
            time_window_min=EAST_pu,
            time_window_max=LAST_pu,
        ),
        Stop(
            location=request.destination,
            vehicle_id=vehicle_id,
            request=request,
            action=StopAction.dropoff,
            estimated_arrival_time=CPAT_do,
            time_window_min=EAST_do,
            time_window_max=LAST_do,
        ),
    ]

    return vehicle_id, cost, stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)