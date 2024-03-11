import numpy as np

from ridepy.data_structures import (
    TransportationRequest,
    Stoplist,
    TransportSpace,
    DispatcherSolution,
    Stop,
    StopAction,
)
from ridepy.util.dispatchers.dispatcher_class import dispatcherclass


@dispatcherclass
def TaxicabDispatcherDriveFirst(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
    seat_capacity: int,
) -> DispatcherSolution:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.

    This pure function is turned into a callable class by the decorator `.dispatcherclass` whose __init__ accepts
    optional arguments, see the docstring of `.dispatcherclass` for details.

    See the dispatcher interface in :ref:`desc_dispatcher` for details.

    Parameters
    ----------
    request
        request to be serviced.
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist.
    space
        transport space the vehicle is operating on.
    seat_capacity
        the maximum number of `.TransportationRequest` s that can be in a vehicle at the same time.


    Returns
    -------
        The best solution as defined in `.SingleVehicleSolution`.
    """
    # TODO: When we have multi-passenger requests, this dispatcher needs to be changed and
    # include capacity constraints. Currently, taxi := single seat
    assert seat_capacity == 1
    CPAT_pu = max(
        stoplist[-1].estimated_arrival_time,
        stoplist[-1].time_window_min if stoplist[-1].time_window_min is not None else 0,
    ) + space.t(stoplist[-1].location, request.origin)
    EAST_pu = request.pickup_timewindow_min
    CPAT_do = max(EAST_pu, CPAT_pu) + space.t(request.origin, request.destination)
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
            occupancy_after_servicing=stoplist[-1].occupancy_after_servicing + 1,
            time_window_min=EAST_pu,
            time_window_max=LAST_pu,
        ),
        Stop(
            location=request.destination,
            request=request,
            action=StopAction.dropoff,
            estimated_arrival_time=CPAT_do,
            occupancy_after_servicing=0,
            time_window_min=EAST_do,
            time_window_max=LAST_do,
        ),
    ]
    return cost, stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
