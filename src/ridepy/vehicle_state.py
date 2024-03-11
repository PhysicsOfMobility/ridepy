from __future__ import annotations

import numpy as np

from typing import Optional, SupportsFloat, List, Tuple

from .data_structures import (
    Request,
    Stoplist,
    SingleVehicleSolution,
    StopAction,
    Stop,
    TransportationRequest,
    TransportSpace,
    Dispatcher,
    LocType,
)
from .events import PickupEvent, DeliveryEvent, InternalEvent, StopEvent

import logging

logger = logging.getLogger(__name__)


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally be implemented in Cython
    or another compiled language.
    """

    def recompute_arrival_times_drive_first(self):
        # update CPATs
        for stop_i, stop_j in zip(self.stoplist, self.stoplist[1:]):
            stop_j.estimated_arrival_time = max(
                stop_i.estimated_arrival_time, stop_i.time_window_min
            ) + self.space.t(stop_i.location, stop_j.location)

    def __init__(
        self,
        *,
        vehicle_id,
        initial_stoplist: Stoplist,
        space: TransportSpace,
        dispatcher: Dispatcher,
        seat_capacity: int,
    ):
        """
        Parameters
        ----------
        vehicle_id
            id of the vehicle to be created.
        initial_stoplist
            stoplist to start out with, MUST contain CPE as first element.
        space
        dispatcher
            see the docstring of `.FleetState`.
        seat_capacity
            the maximum number of `.TransportationRequest` s
             that can be in a vehicle at the same time.
        """
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        self.stoplist: Stoplist = initial_stoplist
        """The list of `.Stop` objects specifying the planned future actions to be undertaken by this vehicle."""
        self.space = space
        self.dispatcher = dispatcher
        self.seat_capacity = seat_capacity

        logger.info(f"Created VehicleState with space of type {type(self.space)}")

    def fast_forward_time(self, t: float) -> Tuple[List[StopEvent], List[Stop]]:
        """
        Update the vehicle_state to the simulator time `t`.

        Parameters
        ----------
        t
            time to be updated to.

        Returns
        -------
        events
            List of stop events emitted through servicing stops upto time=t
        new_stoplist
            Stoplist remaining after servicing the stops upto time=t
        """
        # TODO assert that the CPATs are updated and the stops sorted accordingly
        # TODO optionally validate the travel time velocity constraints

        event_cache = []

        # Here, last_stop refers to the stop with the largest departure time value smaller or equal than t.
        # This can either be the last stop in the stoplist that is serviced here, or it can be the
        # (possibly outdated) CPE stop, of no other stop is serviced.
        last_stop = None

        # drop all non-future stops from the stoplist, except for the (outdated) CPE
        for i in range(len(self.stoplist) - 1, 0, -1):
            stop = self.stoplist[i]
            service_time = max(stop.estimated_arrival_time, stop.time_window_min)
            # service the stop at the minimum time at which it can leave
            if service_time <= t:
                # as we are iterating backwards, the first stop iterated over is the last one serviced
                if last_stop is None:
                    last_stop = stop

                if stop.action == StopAction.pickup:
                    stop_event = {
                        "event_type": "PickupEvent",
                        "timestamp": service_time,
                        "request_id": stop.request.request_id,
                        "vehicle_id": self.vehicle_id,
                    }
                elif stop.action == StopAction.dropoff:
                    stop_event = {
                        "event_type": "DeliveryEvent",
                        "timestamp": service_time,
                        "request_id": stop.request.request_id,
                        "vehicle_id": self.vehicle_id,
                    }
                elif stop.action == StopAction.internal:
                    stop_event = {
                        "event_type": "InternalEvent",
                        "timestamp": service_time,
                        "vehicle_id": self.vehicle_id,
                    }
                else:
                    raise ValueError(f"Unknown StopAction={stop.action}")

                event_cache.append(stop_event)

                del self.stoplist[i]

        # fix event cache order
        event_cache = event_cache[::-1]

        # if no stop was serviced, the last stop is the outdated CPE
        if last_stop is None:
            last_stop = self.stoplist[0]

        # set the occupancy at CPE
        self.stoplist[0].occupancy_after_servicing = last_stop.occupancy_after_servicing

        # set CPE location to current location as inferred from the time delta to the
        # upcoming stop's CPAT still mid-jump from last interpolation, no need to
        # interpolate again
        if self.stoplist[0].estimated_arrival_time <= t:
            if len(self.stoplist) > 1:
                loc, jump_time = self.space.interp_time(
                    u=last_stop.location,
                    v=self.stoplist[1].location,
                    time_to_dest=self.stoplist[1].estimated_arrival_time - t,
                )
                self.stoplist[0].location = loc
                # set CPE time
                self.stoplist[0].estimated_arrival_time = t + jump_time
            else:
                # Stoplist is (now) empty, only CPE is there. Set CPE time to
                # current time and move CPE to last_stop's location (which is
                # identical to CPE, if we haven't served anything.
                self.stoplist[0].location = last_stop.location
                self.stoplist[0].estimated_arrival_time = t

        return event_cache

    def handle_transportation_request_single_vehicle(
        self, request: TransportationRequest
    ) -> SingleVehicleSolution:
        """
        The computational bottleneck. An efficient simulator could do the following:

        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
        2. Implement as a c extension. The args and the return value are all basic c data types, so this should also be easy.

        Parameters
        ----------
        request
            Request to be handled.

        Returns
        -------
        The `SingleVehicleSolution` for the respective vehicle.
        """

        cost, self.stoplist_new, (EAST_pu, LAST_pu, EAST_do, LAST_do) = self.dispatcher(
            request=request,
            stoplist=self.stoplist,
            space=self.space,
            seat_capacity=self.seat_capacity,
        )
        return self.vehicle_id, cost, (EAST_pu, LAST_pu, EAST_do, LAST_do)

    def select_new_stoplist(self):
        self.stoplist = self.stoplist_new
