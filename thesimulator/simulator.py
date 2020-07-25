from functools import partial
from typing import Any, Tuple, List, Dict, Union, Iterator, Callable, Optional
from numpy import inf

from thesimulator.utils import Request, Stop, RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent

FleetState = Dict[Any, List[Stop]]  # vehicle_id -> StopList
RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent]
SingleVehicleSolution = Tuple[Any, float, List[Stop]]  # vehicle_id, cost, new_stop_list


def handle_request_single_vehicle(req: Request, stoplist: List[Stop]) -> SingleVehicleSolution:
    pass


def handle_request(req: Request, fleet_state: FleetState) -> RequestResponse:
    all_solutions = map(partial(handle_request_single_vehicle, req=req), fleet_state)
    best_vehicle, min_cost,  new_stoplist = min(all_solutions, key=lambda x:x[1])

    if min_cost == inf: # no solution was found
        # TODO: return a RequestRejectedEvent
    else:
        # TODO: modify the best vehicle's stoplist



def simulate(initial_fleet_state: FleetState, requests: Iterator[Request],
             request_handler: Callable[[Request, FleetState], RequestResponse]) -> List[Event]:
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
            # drop the visited stops
            stop_list = stop_list[:stop_idx]

        # handle the current request
        handle_request(request, fleet_state)
