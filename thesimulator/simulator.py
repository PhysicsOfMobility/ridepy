from typing import Any, Tuple, List, Dict, Union, Iterator, Callable, Optional
from numpy import inf
from time import time
import operator as op
import functools as ft

from thesimulator.utils import (
    Request,
    Stop,
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)

FleetState = Dict[int, List[Stop]]
"""vehicle_id: StopList"""

RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]

Event = Union[RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent]

SingleVehicleSolution = Tuple[int, float, List[Stop]]
"""vehicle_id, cost, new_stop_list"""


def handle_request_single_vehicle(
    req: Request, stoplist: List[Stop]
) -> SingleVehicleSolution:
    """
    The computational bottleneck. An efficient simulator could do the following:
    1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
    2. Implement as a c extension. The args and the return value are all basic c data types,
       so this should also be easy.

    Parameters
    ----------
    req
    stoplist
    """

    ...


def handle_request(req: Request, fleet_state: FleetState) -> RequestResponse:
    """
    Handle a request by mapping the request and the fleet state onto a request response,
    modifying the fleet state in-place.

    This is where all sorts of parallelization can be done, by replacing the map with
    dask.map, multiprocessing.map, ...

    Parameters
    ----------
    req
    fleet_state

    Returns
    -------

    """
    all_solutions = map(ft.partial(handle_request_single_vehicle, req=req), fleet_state)
    best_vehicle, min_cost, new_stoplist = min(all_solutions, key=lambda x: x[1])

    if min_cost == inf:  # no solution was found
        return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
    else:
        # TODO: modify the best vehicle's stoplist
        ...


def simulate(
    initial_fleet_state: FleetState, requests: Iterator[Request]
) -> List[Event]:
    """
    TODO this should probably modify something in-place, instead of returning a list of events

    Parameters
    ----------
    initial_fleet_state
    requests

    Returns
    -------

    """
    t = 0  # set internal clock to 0
    fleet_state = initial_fleet_state

    for request in requests:
        req_epoch = request.creation_timestamp
        # advance clock to req_epoch
        t = req_epoch
        # Visit all the stops upto req_epoch
        for vehicle_id, stop_list in fleet_state.items():
            # todo assert that the cpats are updated and the stops sorted accordingly
            for stop_idx, stop in enumerate(
                stop for stop in stop_list if stop.estimated_arrival_time <= req_epoch
            ):
                # TODO emit either a PickupEvent or a DeliveryEvent
                ...
            # drop the visited stops
            stop_list = stop_list[: stop_idx + 1]

        # handle the current request
        handle_request(request, fleet_state)
