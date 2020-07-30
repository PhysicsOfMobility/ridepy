import functools as ft
from abc import abstractmethod
from time import time
from typing import Tuple, List, Dict, Union, Iterator, Optional, SupportsFloat

from mpi4py import MPI
from mpi4py.futures import MPICommExecutor

from numpy import inf

from thesimulator.utils import (
    Request,
    Stop,
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)

RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]

Event = Union[RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent]
SingleVehicleSolution = Tuple[int, float, List[Stop]]
"""vehicle_id, cost, new_stop_list"""


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally  be implemented in Cython
    or other compiled language.
    """

    def __init__(self, initial_stoplist: Optional[List[Stop]] = None):
        self._stoplist = initial_stoplist

    def fast_forward_time(self, t: SupportsFloat):
        for stop_idx, stop in enumerate(
            stop for stop in self._stoplist if stop.estimated_arrival_time <= t
        ):
            # TODO emit either a PickupEvent or a DeliveryEvent
            ...
            # TODO optionally validate the traveltime velocity constraints

            # todo assert that the cpats are updated and the stops sorted accordingly

            # drop the visited stops
        stop_list = stop_list[: stop_idx + 1]
        # TODO: add the current position stop
        ...

    def handle_request_single_vehicle(self, req: Request) -> SingleVehicleSolution:
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


# TODO: Decision: Do we need UserRequest vs InternalRequest. Only the latter has more time windows etc.
# TODo: Decision: Who/where is CPE added?


class FleetState:
    """
    Provides the interface for running the whole simulation.
    The fleet state is stored as a dictionary of (vehicle_id, VehicleState) pairs.
    Exposes the methods fast_forward, handle_request and simulate.

    To gain maximum computational efficiency, one can:
    * Subclass VehicleState and implement the main methods in Cython.
    * Implement fast_forward and handle_request using distributed computing e.g. MPI (See MPIFuturesFleetState)
    """

    def __init__(self, initial_stoplists: Dict[int, List[Stop]]):
        self._fleet = {
            vehicle_id: VehicleState(stoplist)
            for vehicle_id, stoplist in initial_stoplists.items()
        }

    @abstractmethod
    def fast_forward(self, t: SupportsFloat):
        ...

    @abstractmethod
    def handle_request(self, req: Request):
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
        ...

    def simulate(self, requests: Iterator[Request]) -> List[Event]:
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

        for request in requests:
            req_epoch = request.creation_timestamp
            # advance clock to req_epoch
            t = req_epoch
            # Visit all the stops upto req_epoch
            self.fast_forward(t)
            # handle the current request
            yield self.handle_request(request)


class SlowSimpleFleetState(FleetState):
    def fast_forward(self, t: SupportsFloat):
        for vehicle_id, vehicle_state in self._fleet.items():
            vehicle_state.fast_forward_time(t)

    def handle_request(self, req: Request):
        """
        Handle a request by mapping the request and the fleet state onto a request response,
        modifying the fleet state in-place.

        Parameters
        ----------
        req
        fleet_state

        Returns
        -------

        """
        all_solutions = map(
            ft.partial(VehicleState.handle_request_single_vehicle, req=req),
            self._fleet.values(),
        )
        best_vehicle, min_cost, new_stoplist = min(all_solutions, key=lambda x: x[1])

        if min_cost == inf:  # no solution was found
            return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
        else:
            # TODO: modify the best vehicle's stoplist
            self._fleet[best_vehicle] = new_stoplist
            return RequestAcceptanceEvent(...)


class MPIFuturesFleetState(FleetState):
    def fast_forward(self, t: SupportsFloat):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                res = executor.map(
                    ft.partial(VehicleState.fast_forward_time, t=t),
                    self._fleet.values(),
                )

    def handle_request(self, req: Request):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                all_solutions = executor.map(
                    ft.partial(VehicleState.handle_request_single_vehicle, req=req),
                    self._fleet.values(),
                )
        best_vehicle, min_cost, new_stoplist = min(all_solutions, key=lambda x: x[1])

        if min_cost == inf:  # no solution was found
            return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
        else:
            # TODO: modify the best vehicle's stoplist
            self._fleet[best_vehicle] = new_stoplist
            return RequestAcceptanceEvent(...)
