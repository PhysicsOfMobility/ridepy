from functools import partial
from typing import Any, Tuple, List, Dict, Union, Iterator, Callable, Optional
from numpy import inf

from thesimulator.utils import Request, Stop, RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent

FleetState = Dict[int, List[Stop]]  # vehicle_id -> StopList
RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent]
SingleVehicleSolution = Tuple[int, float, List[Stop]]  # vehicle_id, cost, new_stop_list

# Thoughts
# UserRequest vs InternalRequest. Only the latter has more time windows etc.
# How to handle traveltime computing?
# Who interpolates current vehicle position?
# Who/where is CPE added?
# If fleet state is stored distributedly, how does simulator visit stops?
#  - It seems avoiding data copying is too complex/limiting.
# Alternate ideas:
# - Maintain FleetState as a Cython class -> No data copy.
# - handle_request maintains a process pool.

def handle_request_single_vehicle(req: Request, stoplist: List[Stop]) -> SingleVehicleSolution:
    """
    The computational bottleneck. An efficient simulator could do the following:
    1. Parallelize this over all vehicle. This function being without any side effects, it should be easy to do.
    2. Implement as a c extension. The args and the return value are all basic c data types, so this should also be easy.

    :param req:
    :param stoplist:
    :return:
    """
    pass


def handle_request(req: Request, fleet_state: FleetState) -> RequestResponse:
    # This is where all sorts of parallelization can be done, by replacing the map with
    # dask.map, multiprocessing.map, ...
    all_solutions = map(partial(handle_request_single_vehicle, req=req), fleet_state)
    best_vehicle, min_cost,  new_stoplist = min(all_solutions, key=lambda x:x[1])

    if min_cost == inf: # no solution was found
        # TODO: return a RequestRejectedEvent
        return RequestRejectionEvent()
    else:
        # TODO: modify the best vehicle's stoplist
        fleet_state[best_vehicle] = new_stoplist
        return RequestAcceptanceEvent()


def simulate(initial_fleet_state: FleetState, requests: Iterator[Request]) -> Iterator[Event]:
    # set internal clock to 0
    t = 0
    fleet_state = initial_fleet_state
    for request in requests:
        req_epoch = request.creation_timestamp
        # advance clock to req_epoch
        t = req_epoch
        # Visit all the stops upto req_epoch
        for vehicle_id, stop_list in fleet_state.items():
            for stop_idx, stop in enumerate(stop_list):
                # do not visit stops in future
                if stop.estimated_arrival_time > req_epoch:
                    break
                # TODO emit either a PickupEvent or a DeliveryEvent
                # TODO optionally validate the traveltime velocity constraints

            # drop the visited stops
            stop_list = stop_list[:stop_idx]
            # TODO: add the current position stop

        # handle the current request
        yield handle_request(request, fleet_state)
