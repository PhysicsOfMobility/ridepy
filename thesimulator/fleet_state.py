import functools as ft
import operator as op
import numpy as np

from abc import ABC, abstractmethod
from time import time
from typing import Dict, SupportsFloat, Iterator, List
from mpi4py import MPI
from mpi4py.futures import MPICommExecutor

from .utils import (
    Stoplist,
    Request,
    Event,
    RequestRejectionEvent,
    RequestAcceptanceEvent,
)
from .vehicle_state import VehicleState


class FleetState(ABC):
    """
    Provides the interface for running the whole simulation.
    The fleet state is stored as a dictionary of (vehicle_id, VehicleState) pairs.
    Exposes the methods fast_forward, handle_request and simulate.

    To gain maximum computational efficiency, one can:
    * Subclass VehicleState and implement the main methods in Cython.
    * Implement fast_forward and handle_request using distributed computing e.g. MPI (See MPIFuturesFleetState)
    """

    def __init__(self, initial_stoplists: Dict[int, Stoplist]):
        # note here that in the current design the vehicle ID is unknown to the vehicle
        self.fleet: Dict[int, VehicleState] = {
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
        for vehicle_id, vehicle_state in self.fleet.items():
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
            self.fleet.values(),
        )
        best_vehicle, min_cost, new_stoplist = min(all_solutions, key=op.itemgetter(1))

        if min_cost == np.inf:  # no solution was found
            return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
        else:
            # TODO: modify the best vehicle's stoplist
            self.fleet[best_vehicle].stoplist = new_stoplist
            return RequestAcceptanceEvent(...)


class MPIFuturesFleetState(FleetState):
    def fast_forward(self, t: SupportsFloat):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                res = executor.map(
                    ft.partial(VehicleState.fast_forward_time, t=t),
                    self.fleet.values(),
                )

    def handle_request(self, req: Request):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                all_solutions = executor.map(
                    ft.partial(VehicleState.handle_request_single_vehicle, req=req),
                    self.fleet.values(),
                )
        best_vehicle, min_cost, new_stoplist = min(all_solutions, key=op.itemgetter(1))

        if min_cost == np.inf:  # no solution was found
            return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
        else:
            # TODO: modify the best vehicle's stoplist
            self.fleet[best_vehicle].stoplist = new_stoplist
            return RequestAcceptanceEvent(...)
