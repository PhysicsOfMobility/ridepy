import functools as ft
import itertools as it
import operator as op
import numpy as np

from collections import defaultdict
from abc import ABC, abstractmethod
from time import time
from mpi4py import MPI
from mpi4py.futures import MPICommExecutor
from typing import Dict, SupportsFloat, Iterator, List, Union, Tuple, Iterable, Sequence

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
    InternalAssignStopEvent,
    InternalAssignRequest,
    PickupEvent,
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

    def __init__(self, initial_stoplists: Dict[int, Stoplist], space: TransportSpace):
        """
        Parameters
        ----------
        initial_stoplists:
            Dictionary with vehicle ids as keys and initial stoplists as values.
            The initial stoplists *must* contain current position element (CPE) stops as their first entry.
            CPE is defined as a stop at the beginning of the stoplist with action set to StopAction.cpe.
        space
            transport space to perform the simulations on
        """

        self.space = space
        """transport space the simulations are performed on"""

        self.fleet: Dict[int, VehicleState] = {
            vehicle_id: VehicleState(
                vehicle_id=vehicle_id, initial_stoplist=stoplist, space=self.space
            )
            for vehicle_id, stoplist in initial_stoplists.items()
        }
        """dictionary of vehicle states, keyed by their vehicle_id"""

    @abstractmethod
    def fast_forward_time(self, t: SupportsFloat) -> Sequence[StopEvent]:
        """
        Advance the fleet_state to the simulator time `t`, if possible.
        However, if the simulator must take action as time is evolved, an appropriate internal
        stop event is emitted and fast_forward_time interrupted. In this case, the time is
        not evolved to the supplied `t` but rather to the estimated arrival time of the
        last stop before the internal stop that requires the action to be taken.

        Parameters
        ----------
        t
            time to advance to, if possible

        Returns
        -------
        stop events
            sequence of stop events. May be empty if no stop is serviced.
        """

        ...

    def handle_transportation_request(self, req: TransportationRequest) -> RequestEvent:
        """
        Handle a single request for transportation by mapping it and the fleet
        state onto a request response event, modifying the fleet state in-place.

        This is where all sorts of parallelization can be done, by replacing the map with
        dask.map, multiprocessing.map, ...

        Parameters
        ----------
        req
            transportation request to handle

        Returns
        -------
        request_event
        """

        ...

    @abstractmethod
    def handle_internal_requests(self, req: InternalRequest) -> Iterator[RequestEvent]:
        """
        Handle a single internal request. This can mean various things, e.g. assigning
        previously cached stops.

        Parameters
        ----------
        req

        Returns
        -------
        request_events
        """

        ...

    def simulate(
        self, requests: Iterator[Request], t_cutoff: float = np.inf
    ) -> Iterator[Event]:
        """
        Perform the simulation.

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

        # loop over the request iterator
        for request in requests:
            # create a request cache to be able to handle additional
            # requests within # this iteration
            request_cache = [request]

            # advance clock to request epoch
            t = request.creation_timestamp

            # service all the stops upto request epoch and keep the events
            event_cache = self.fast_forward_time(t)

            # now yield the events while checking whether an internal
            # event has been emitted
            for event in event_cache:
                if isinstance(event, InternalAssignStopEvent):
                    # if an internal assign stop event was emitted
                    # an internal assign request is generated to
                    # trigger assignment of cached requests
                    request_cache.append(
                        InternalAssignRequest(
                            creation_timestamp=t,
                            vehicle_id=event.vehicle_id,
                        )
                    )
                yield event

            # now process the request cache
            for cached_request in request_cache:
                # first handle internal requests
                if isinstance(cached_request, InternalRequest):
                    yield from self.handle_internal_requests(cached_request)
                # then transportation requests
                elif isinstance(cached_request, TransportationRequest):
                    yield self.handle_transportation_request(cached_request)
                else:
                    raise NotImplementedError(
                        f"Unknown request type: {type(cached_request)}"
                    )

            # possibly end the simulation if cutoff time is reached
            if t >= t_cutoff:
                return

        # service all remaining stops
        event_cache = []
        while new_events := self.fast_forward_time(
            min(
                t_cutoff,
                max(
                    vehicle.stoplist[-1].estimated_arrival_time
                    for vehicle in self.fleet.values()
                ),
            )
        ):
            event_cache += new_events

        yield from event_cache

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
        request_event
        """

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

        if min_cost == np.inf:
            # no solution found...
            return RequestRejectionEvent(request_id=req.request_id, timestamp=time())
        else:
            # otherwise, modify the best vehicle's stoplist
            self.fleet[best_vehicle].stoplist = new_stoplist
            return RequestAcceptanceEvent(
                request_id=req,
                timestamp=time(),
                origin=req.origin,
                destination=req.destination,
                pickup_timewindow_min=pickup_timewindow_min,
                pickup_timewindow_max=pickup_timewindow_max,
                delivery_timewindow_min=dropoff_timewindow_min,
                delivery_timewindow_max=dropoff_timewindow_max,
            )


class SlowSimpleFleetState(FleetState):
    """
    Implementation of FleetState that uses standard python for-loops.
    This makes for easy debugging and possibly bad performance.
    """

    def fast_forward_time(self, t: float):
        # return an iterator over the StopEvents emitted by the fleets fast_forward_time methods
        return list(
            it.chain.from_iterable(
                vehicle_state.fast_forward_time(t)
                for vehicle_state in self.fleet.values()
            )
        )

    def handle_transportation_request(self, req: TransportationRequest):
        # return a single request event
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

    def handle_internal_requests(self, req: InternalRequest):
        ...


class LocationTriggeredFleetState(FleetState):
    """
    Implementation of FleetState that does not process requests immediately but
    rather assigns them to a cache which is indexed by the (graph-like)
    transport space's vertices.
    """

    registry = defaultdict(lambda: defaultdict(lambda: []))
    """cache for accepted but not yet assigned requests, 
       indexed by pick-up and delivery nodes of the requests."""

    def fast_forward_time(self, t: float):
        # return an iterator over the StopEvents emitted by the fleets fast_forward_time methods
        return list(
            it.chain.from_iterable(
                vehicle_state.fast_forward_time(t)
                for vehicle_state in self.fleet.values()
            )
        )

    def handle_transportation_request(self, req: TransportationRequest):
        # instead of assigning the request, append it to the queued ones in the registry
        self.registry[req.origin][req.destination].append(req)

        # still, emit an acceptance event.
        # NOTE that this might be reconsidered.
        return RequestAcceptanceEvent(
            request_id=req.request_id,
            timestamp=time(),
            origin=req.origin,
            destination=req.destination,
            pickup_timewindow_min=np.nan,
            pickup_timewindow_max=np.nan,
            delivery_timewindow_min=np.nan,
            delivery_timewindow_max=np.nan,
        )

    def _assign_queued_at_location(
        self, vehicle_id, method="max_dest"
    ) -> Sequence[Event]:
        """
        Assign the queued requests to the vehicle that just reached the node.
        NOTE: If multiple vehicles reach a vertex simultaneously, the order in which
        this will assign to the vehicles is given by their position in the fleet dict.

        Parameters
        ----------
        vehicle_id
            id of the vehicle that has just reached a location
        method
            the dispatching algorithm. currently the only option is "max_dest".

        Returns
        -------
        events
            sequence of stop assign events

        """

        vehicle = self.fleet[vehicle_id]
        event_cache = []

        if method == "max_dest":
            # if there a queued stops at the current location...
            if len(self.registry[vehicle.location]):
                # determine the destination by choosing the vertex that maximizes the
                # number of requests having it as destination.
                destination, n_reqs = max(
                    (
                        (destination, len(reqs))
                        for destination, reqs in self.registry[vehicle.location].items()
                    ),
                    key=op.itemgetter(1),
                )
                # if the chosen maximum-share destination has a
                # non-empty set of requests associated to it...
                if n_reqs:
                    # ...bulk-assign these requests to the vehicle...
                    event_cache += vehicle.assign_bulk_requests(
                        reqs=self.registry[vehicle.location][destination]
                    )
                    # ...and empty the queue.
                    self.registry[vehicle.location][destination] = []
        else:
            raise NotImplementedError(f"Method {method} not implemented.")

        return event_cache

    def handle_internal_requests(self, req: InternalRequest):
        if isinstance(req, InternalAssignRequest):
            yield from self._assign_queued_at_location(vehicle_id=req.vehicle_id)


class MPIFuturesFleetState(FleetState):
    def fast_forward_time(self, t: float):
        with MPICommExecutor(MPI.COMM_WORLD, root=0) as executor:
            if executor is not None:
                return list(
                    it.chain.from_iterable(
                        executor.map(
                            ft.partial(VehicleState.fast_forward_time, t=t),
                            self.fleet.values(),
                        )
                    )
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

    def handle_internal_requests(self, req: InternalRequest):
        ...
