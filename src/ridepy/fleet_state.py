from __future__ import annotations

from collections import defaultdict

import functools as ft
import itertools as it
import operator as op

import numpy as np


from abc import ABC, abstractmethod
from typing import (
    Dict,
    SupportsFloat,
    Iterator,
    Union,
    Tuple,
    Iterable,
    Type,
)

import logging

from .util import supress_stoplist_extraction_warning

logger = logging.getLogger(__name__)

from ridepy.data_structures import (
    Stop,
    Request,
    TransportationRequest as pyTransportationRequest,
    InternalRequest as pyInternalRequest,
    SingleVehicleSolution,
    Dispatcher,
    StopAction,
    InternalRequest,
    TransportationRequest,
)
from .events import (
    Event,
    RequestEvent,
    StopEvent,
)
from ridepy.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
    InternalRequest as CyInternalRequest,
    StopAction as CyStopAction,
    Stop as CyStop,
)

from ridepy.vehicle_state import VehicleState
from ridepy.vehicle_state_cython import VehicleState as CyVehicleState

from ridepy.data_structures import TransportSpace
from ridepy.util.spaces_cython import TransportSpace as CyTransportSpace


class FleetState(ABC):
    """
    Provides the interface for running the whole simulation.
    The fleet state is stored as a dictionary of (vehicle_id, VehicleState) pairs.
    Exposes the methods fast_forward, handle_request and simulate.

    To gain maximum computational efficiency, one can:

    * Subclass VehicleState and implement the main methods in Cython.
    * Implement fast_forward and handle_request using distributed computing e.g. MPI
    """

    def __init__(
        self,
        *,
        initial_locations: Union[Dict[int, int], Dict[int, Tuple[float, ...]]],
        vehicle_state_class: Union[Type[VehicleState], Type[CyVehicleState]],
        space: Union[TransportSpace, CyTransportSpace],
        dispatcher: Dispatcher,
        seat_capacities: Union[int, Dict[int, int]],
    ):
        """
        Create a `FleetState`, holding a number of `VehicleState` objects.

        Parameters
        ----------
        initial_locations
            Dictionary with vehicle ids as keys and initial locations as values.
        vehicle_state_class
            The vehicle state class to be used. Can be either `.vehicle_state.VehicleState` (pure pythonic) or
            `.vehicle_state_cython.VehicleState` (implemented in cython).
        space
            The `.data_structures.TransportSpace` (e.g. Euclidean2D, Graph) in which the simulation will be run.
        dispatcher
            The dispatching algorithm that maps a (stoplist, TransportationRequest) pair into a cost and new stoplist.
            See :doc:`introduction` for more details.
        seat_capacities
            Integers denoting the maximum number of persons a vehicle can hold. Either a dictionary with vehicle ids as
            keys or a positive integer (Causes each vehicle to have the same capacity).

        Note
        ----
        * Explain the graph nodes have in notes and why.
        * define LocType in a central place and motivate why we have it.
        """
        if issubclass(vehicle_state_class, VehicleState):
            StopCls = Stop
            StopActionCls = StopAction
            InternalRequestCls = InternalRequest
            TransportationRequestCls = TransportationRequest
            assert isinstance(space, TransportSpace), "unsuitable transport space"
            logger.debug(
                f"Creating FleetState with vehicle state class {vehicle_state_class}"
            )
        elif issubclass(vehicle_state_class, CyVehicleState):
            StopCls = CyStop
            StopActionCls = CyStopAction
            InternalRequestCls = CyInternalRequest
            TransportationRequestCls = CyTransportationRequest
            assert isinstance(space, CyTransportSpace), "unsuitable transport space"
            logger.debug(
                f"Creating FleetState with vehicle state class {vehicle_state_class}"
            )
        else:
            raise TypeError(f"Unknown VehicleStateCls {type(vehicle_state_class)}")

        if isinstance(seat_capacities, Dict):
            assert set(initial_locations) == set(
                seat_capacities
            ), "vehicle_ids in seat_capacities and initial_stoplists must match"
        elif isinstance(seat_capacities, int):
            seat_capacities = defaultdict(lambda x=seat_capacities: x)
        else:
            raise TypeError(f"seat_capacities must be either dict or int")

        self.vehicle_state_class = vehicle_state_class
        self.dispatcher = dispatcher
        self.space = space

        assert initial_locations, "No initial locations supplied."
        for initial_location in initial_locations.values():
            # note that NumPy's dimensions start from 0
            assert space.n_dim == np.ndim(initial_location) + 1, (
                f"Dimension mismatch: Initial location {initial_location} of "
                f"dimensionality {np.ndim(initial_location) + 1} supplied, "
                f"but space has {space.n_dim} dimensions."
            )

        self.fleet: Dict[int, VehicleState] = {
            vehicle_id: vehicle_state_class(
                vehicle_id=vehicle_id,
                initial_stoplist=[
                    StopCls(
                        location=initial_locations[vehicle_id],
                        request=InternalRequestCls(
                            request_id=-1,
                            creation_timestamp=0,
                            location=initial_locations[vehicle_id],
                        ),
                        action=StopActionCls.internal,
                        estimated_arrival_time=0,
                        occupancy_after_servicing=0,
                        time_window_min=0,
                        time_window_max=np.inf,
                    )
                ],
                space=space,
                dispatcher=self.dispatcher,
                seat_capacity=seat_capacities[vehicle_id],
            )
            for vehicle_id in initial_locations.keys()
        }

    @classmethod
    def from_fleet(
        cls,
        *,
        fleet: Dict[int, VehicleState],
        space: Union[TransportSpace, CyTransportSpace],
        dispatcher: Dispatcher,
        validate: bool = True,
    ):
        """
        Create a `FleetState` from a dictionary of `VehicleState` objects, keyed by an integer `vehicle_id`.

        Parameters
        ----------
        fleet
            Initial stoplists *must* contain current position element (CPE) stops with
            `StopAction.internal` and `InternalRequest` with `request_id==-1` as their first entries.
        space
            TransportSpace to operate on
        dispatcher
            dispatcher to use to assign requests to vehicles or reject them.
        validate
            If true, try to figure out whether something is off. If not, raise.

        Returns
        -------

        """
        self = super().__new__(cls)
        self.dispatcher = dispatcher
        self.fleet = fleet
        self.space = space

        if validate:
            VehicleStateCls = type(next(iter(self.fleet.values())))
            assert all(
                isinstance(vehicle_state, VehicleStateCls)
                for vehicle_state in self.fleet.values()
            ), "fleet inhomogeneous"

            if issubclass(VehicleStateCls, VehicleState):
                StopCls = Stop
                StopActionCls = StopAction
                InternalRequestCls = InternalRequest
                TransportationRequestCls = TransportationRequest
                assert isinstance(space, TransportSpace), "unsuitable transport space"
            elif issubclass(VehicleStateCls, CyVehicleState):
                StopCls = CyStop
                StopActionCls = CyStopAction
                InternalRequestCls = CyInternalRequest
                TransportationRequestCls = CyTransportationRequest
                assert isinstance(space, CyTransportSpace), "unsuitable transport space"
            else:
                raise TypeError(f"Unknown VehicleStateCls {type(VehicleStateCls)}")

            for vehicle_state in self.fleet.values():
                assert (
                    vehicle_state.stoplist[0].request.request_id == -1
                ), "malformed CPE: request_id must be -1"
                assert (
                    vehicle_state.stoplist[0].action == StopActionCls.internal
                ), "malformed CPE: action must be 'internal'"
                assert isinstance(
                    vehicle_state.stoplist[0].request, InternalRequestCls
                ), "malformed CPE: request type must be 'internal'"
                assert all(isinstance(stop, StopCls) for stop in vehicle_state.stoplist)
                assert all(
                    isinstance(
                        stop.request, (InternalRequestCls, TransportationRequestCls)
                    )
                    for stop in vehicle_state.stoplist
                )

        return self

    def simulate(
        self, requests: Iterator[Request], t_cutoff: float = np.inf
    ) -> Iterator[Event]:
        """
        Run a simulation.

        Parameters
        ----------
        requests
            `Iterator` that supplies incoming requests.
        t_cutoff
            optional cutoff time after which the simulation is forcefully ended,
            disregarding any remaining stops or requests.

        Returns
        -------
        Iterator of events that have been emitted during the simulation.

        Note
        ----
        Because of lazy evaluation the returned iterator must be exhausted
        for the simulation to be actually be performed.
        """

        self.t = 0

        with supress_stoplist_extraction_warning():
            for vehicle_id, fleet_state in self.fleet.items():
                yield {
                    "event_type": "VehicleStateBeginEvent",
                    "vehicle_id": vehicle_id,
                    "timestamp": self.t,
                    "location": fleet_state.stoplist[0].location,
                    "request_id": -100,
                }

        for n_req, request in enumerate(requests):
            # advance clock to req_epoch
            self.t = request.creation_timestamp

            if self.t > t_cutoff:
                break

            # Visit all the stops upto req_epoch
            yield from self.fast_forward(self.t)

            if isinstance(request, (TransportationRequest, CyTransportationRequest)):
                yield {
                    "event_type": "RequestSubmissionEvent",
                    "request_id": request.request_id,
                    "timestamp": self.t,
                    "origin": request.origin,
                    "destination": request.destination,
                    "pickup_timewindow_min": request.pickup_timewindow_min,
                    "pickup_timewindow_max": request.pickup_timewindow_max,
                    "delivery_timewindow_min": request.delivery_timewindow_min,
                    "delivery_timewindow_max": request.delivery_timewindow_max,
                }

            # handle the current request
            if isinstance(request, (pyTransportationRequest, CyTransportationRequest)):
                yield self.handle_transportation_request(request)
            elif isinstance(request, (pyInternalRequest, CyInternalRequest)):
                yield self.handle_internal_request(request)
            else:
                raise NotImplementedError(f"Unknown request type: {type(request)}")
            logger.info(f"Handled request # {n_req}")

        with supress_stoplist_extraction_warning():
            self.t = min(
                t_cutoff,
                max(
                    vehicle.stoplist[-1].estimated_arrival_time
                    for vehicle in self.fleet.values()
                ),
            )

        # service all remaining stops
        yield from self.fast_forward(self.t)

        with supress_stoplist_extraction_warning():
            for vehicle_id, fleet_state in self.fleet.items():
                yield {
                    "event_type": "VehicleStateEndEvent",
                    "vehicle_id": vehicle_id,
                    "timestamp": self.t,
                    "location": fleet_state.stoplist[0].location,
                    "request_id": -200,
                }

    @abstractmethod
    def fast_forward(self, t: SupportsFloat) -> Iterator[StopEvent]:
        """
        Advance the simulator's state in time from the previous time :math:`t'`
        to the new time :math:`t`, with :math:`t >= t'`.
        E.g. vehicle locations may change and vehicle stops may be serviced.
        The latter will emit `.StopEvent` s which are returned.

        Parameters
        ----------
        t
            Time to advance to.

        Returns
        -------
            Iterator of stop events. May be empty if no stop is serviced.
        """
        ...

    def handle_transportation_request(
        self, req: pyTransportationRequest
    ) -> RequestEvent:
        """
        Handle a request by mapping the request and the fleet state onto a request response,
        modifying the fleet state in-place.

        This method can be implemented in child classes using various parallelization techniques like
        `multiprocessing`, `OpenMPI` or `dask`.

        Parameters
        ----------
        req
            Request to handle.

        Returns
        -------
            An `.Event`.
        """
        ...

    @abstractmethod
    def handle_internal_request(self, req: pyInternalRequest) -> RequestEvent:
        """

        Parameters
        ----------
        req
            request to handle.

        Returns
        -------
            An `.Event`.
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
            request to handle.
        all_solutions
            a dictionary mapping a vehicle_id to a `.SingleVehicleSolution`.

        Returns
        -------
            Either a `.RequestAcceptanceEvent`, or a `.RequestRejectionEvent` if no suitable vehicle could be found.

        Note
        ----
            Modifies the `.VehicleState` of the vehicle with the least cost inplace.

        """
        (
            best_vehicle,
            min_cost,
            (
                pickup_timewindow_min,
                pickup_timewindow_max,
                delivery_timewindow_min,
                delivery_timewindow_max,
            ),
        ) = min(all_solutions, key=op.itemgetter(1))
        logger.debug(f"best vehicle: {best_vehicle}, at min_cost={min_cost}")
        if min_cost == np.inf:  # no solution was found
            return {
                "event_type": "RequestRejectionEvent",
                "timestamp": self.t,
                "request_id": req.request_id,
            }
        else:
            # modify the best vehicle's stoplist
            self.fleet[best_vehicle].select_new_stoplist()

            return {
                "event_type": "RequestAcceptanceEvent",
                "timestamp": self.t,
                "request_id": req.request_id,
                "origin": req.origin,
                "destination": req.destination,
                "pickup_timewindow_min": pickup_timewindow_min,
                "pickup_timewindow_max": pickup_timewindow_max,
                "delivery_timewindow_min": delivery_timewindow_min,
                "delivery_timewindow_max": delivery_timewindow_max,
            }


class SlowSimpleFleetState(FleetState):
    def fast_forward(self, t: float):
        events = (
            vehicle_state.fast_forward_time(t) for vehicle_state in self.fleet.values()
        )

        # no need to swap the old stoplists of each vehicle with the new (fast-forwarded)
        # stoplists, because vehicle_state_class.fast_forward did that already.

        return sorted(it.chain.from_iterable(events), key=op.itemgetter("timestamp"))

    def handle_transportation_request(
        self, req: pyTransportationRequest
    ) -> RequestEvent:
        logger.debug(f"Handling Request: {req}")

        if req.origin == req.destination:
            return {
                "event_type": "RequestRejectionEvent",
                "timestamp": self.t,
                "request_id": req.request_id,
            }

        return self._apply_request_solution(
            req,
            map(
                ft.partial(
                    self.vehicle_state_class.handle_transportation_request_single_vehicle,
                    request=req,
                ),
                self.fleet.values(),
            ),
        )

    def handle_internal_request(self, req: pyInternalRequest) -> RequestEvent: ...
