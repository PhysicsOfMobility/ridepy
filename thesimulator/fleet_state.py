import functools as ft
import itertools as it
import operator as op
import numpy as np


from abc import ABC, abstractmethod
from typing import Dict, SupportsFloat, Iterator, List, Union, Tuple, Iterable
from mpi4py import MPI
from mpi4py.futures import MPICommExecutor

from .data_structures import (
    Stoplist,
    Request,
    Event,
    RequestRejectionEvent,
    RequestAcceptanceEvent,
    RequestEvent,
    StopEvent,
    TransportationRequest,
    InternalRequest,
    TransportSpace,
    SingleVehicleSolution,
    Dispatcher,
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

    def __init__(
        self,
        *,
        initial_stoplists: Dict[int, Stoplist],
        space: TransportSpace,
        dispatcher: Dispatcher,
    ):
        """
        Parameters
        ----------
        initial_stoplists:
            Dictionary with vehicle ids as keys and initial stoplists as values.
            The initial stoplists *must* contain current position element (CPE) stops as their first entry.
        """

        self.space = space
        self.dispatcher = dispatcher
        self.fleet: Dict[int, VehicleState] = {
            vehicle_id: VehicleState(
                vehicle_id=vehicle_id,
                initial_stoplist=stoplist,
                space=self.space,
                dispatcher=self.dispatcher,
            )
            for vehicle_id, stoplist in initial_stoplists.items()
        }

    @abstractmethod
    def fast_forward(self, t: SupportsFloat) -> Iterator[StopEvent]:
        """
        Advance the simulator's state in time from the previous time `$t'$` to the new time `$t$`, with `$t >= t'$`.
        E.g. vehicle locations may change and vehicle stops may be serviced.
        The latter will emit `StopEvents` which are returned.

        Parameters
        ----------
        t
            Time to advance to.

        Returns
        -------
        stop events
            Iterator of stop events. May be empty if no stop is serviced.
        """
        ...

    def handle_transportation_request(self, req: TransportationRequest) -> RequestEvent:
        """
        Handle a request by mapping the request and the fleet state onto a request response,
        modifying the fleet state in-place.

        This is where all sorts of parallelization can be done, by replacing the map with
        dask.map, multiprocessing.map, ...

        Parameters
        ----------
        req
            request to handle

        Returns
        -------
        event

        """
        ...

    @abstractmethod
    def handle_internal_request(self, req: InternalRequest) -> RequestEvent:
        """

        Parameters
        ----------
        req

        Returns
        -------

        """
        ...

    def _apply_request_solution(
        self, req, all_solutions: Iterable[SingleVehicleSolution]
    ) -> RequestEvent:
        """
        Given a request and a bunch of solutions, pick the one with the minimum cost and apply it,
        thereby changing the stoplist of the chosen vehicle and emitting an RequestAcceptanceEvent.
        If the minimum cost is infinite, RequestRejectionEvent is returned.

        Parameters
        ----------
        req
        all_solutions

        Returns
        -------

        """
        # breakpoint()
        (
            best_vehicle,
            min_cost,
            new_stoplist,
            (
                pickup_timewindow_min,
                pickup_timewindow_max,
                dropoff_timewindow_min,
                dropoff_timewindow_max,
            ),
        ) = min(all_solutions, key=op.itemgetter(1))
        # print(f"best vehicle: {best_vehicle}, at min_cost={min_cost}")
        if min_cost == np.inf:  # no solution was found
            return RequestRejectionEvent(request_id=req.request_id, timestamp=self.t)
        else:
            # modify the best vehicle's stoplist
            # print(f"len of new stoplist={len(new_stoplist)}")
            self.fleet[best_vehicle].stoplist = new_stoplist
            # print(
            #     f"{best_vehicle}: [{', '.join(map(str,[stop.request.request_id for stop in new_stoplist]))}]\n"
            # )
            return RequestAcceptanceEvent(
                request_id=req.request_id,
                timestamp=self.t,
                origin=req.origin,
                destination=req.destination,
                pickup_timewindow_min=pickup_timewindow_min,
                pickup_timewindow_max=pickup_timewindow_max,
                delivery_timewindow_min=dropoff_timewindow_min,
                delivery_timewindow_max=dropoff_timewindow_max,
            )

    def simulate(
        self, requests: Iterator[Request], t_cutoff: float = np.inf
    ) -> Iterator[Event]:
        """
        Perform a simulation.

        Parameters
        ----------
        requests
            iterator that supplies incoming requests
        t_cutoff
            optional cutoff time after which the simulation is forcefully ended,
            disregarding any remaining stops or requests.

        Returns
        -------
        events
            Iterator of events that have been emitted during the simulation.
            Because of lazy evaluation the returned iterator *must* be exhausted
            for the simulation to be actually be performed.
        """

        self.t = 0

        for request in requests:
            req_epoch = request.creation_timestamp

            # advance clock to req_epoch
            self.t = req_epoch

            # Visit all the stops upto req_epoch
            yield from self.fast_forward(self.t)

            # handle the current request
            if isinstance(request, TransportationRequest):
                yield self.handle_transportation_request(request)
            elif isinstance(request, InternalRequest):
                yield self.handle_internal_request(request)
            else:
                raise NotImplementedError(f"Unknown request type: {type(request)}")

            if self.t >= t_cutoff:
                return

        # service all remaining stops
        yield from self.fast_forward(
            min(
                t_cutoff,
                max(
                    vehicle.stoplist[-1].estimated_arrival_time
                    for vehicle in self.fleet.values()
                ),
            )
        )


class SlowSimpleFleetState(FleetState):
    def fast_forward(self, t: float):
        return sorted(
            it.chain.from_iterable(
                vehicle_state.fast_forward_time(t)
                for vehicle_state in self.fleet.values()
            ),
            key=op.attrgetter("timestamp"),
        )

    def handle_transportation_request(self, req: TransportationRequest):
        return self._apply_request_solution(
            req,
            map(
                ft.partial(
                    VehicleState.handle_transportation_request_single_vehicle,
                    request=req,
                ),
                self.fleet.values(),
            ),
        )

    def handle_internal_request(self, req: InternalRequest) -> RequestEvent:
        ...


class MPIFuturesFleetState(FleetState):
    def fast_forward(self, t: float):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                return sorted(
                    it.chain.from_iterable(
                        executor.map(
                            ft.partial(VehicleState.fast_forward_time, t=t),
                            self.fleet.values(),
                        )
                    ),
                    key=op.attrgetter("timestamp"),
                )

    def handle_transportation_request(self, req: TransportationRequest):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            # TODO: what happens if executor is not there?
            if executor is not None:
                return self._apply_request_solution(
                    req,
                    executor.map(
                        ft.partial(
                            VehicleState.handle_transportation_request_single_vehicle,
                            request=req,
                        ),
                        self.fleet.values(),
                    ),
                )

    def handle_internal_request(self, req: InternalRequest) -> RequestEvent:
        ...
