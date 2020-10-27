import operator as op
import numpy as np

from typing import Optional, SupportsFloat, List

from .data_structures import (
    Request,
    Stoplist,
    SingleVehicleSolution,
    StopEvent,
    StopAction,
    PickupEvent,
    DeliveryEvent,
    InternalAssignStopEvent,
    Stop,
    TransportationRequest,
    TransportSpace,
)
from .util.dispatchers import taxicab_dispatcher_drive_first


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally  be implemented in Cython
    or other compiled language.
    """

    def recompute_arrival_times_drive_first(self):
        # update CPATs
        for stop_i, stop_j in zip(self.stoplist, self.stoplist[1:]):
            stop_j.estimated_arrival_time = max(
                stop_i.estimated_arrival_time, stop_i.time_window_min
            ) + self.space.t(stop_i.location, stop_j.location)

    def __init__(
        self, *, vehicle_id, initial_stoplist: Stoplist, space: TransportSpace
    ):
        """
        Create a vehicle.

        Parameters
        ----------
        vehicle_id:
            id of the vehicle to be created
        initial_stoplist
            stoplist to start out with, MUST contain CPE as first element
        space
            transport space the vehicle is operating on
        """
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        self.stoplist = initial_stoplist
        self.space = space

    def fast_forward_time(self, t: float) -> List[StopEvent]:
        """
        Update the vehicle_state to the simulator time `t`.

        Parameters
        ----------
        t
            time to be updated to

        Returns
        -------
        events
            List of stop events emitted through servicing stops
        """

        # TODO assert that the CPATs are updated and the stops sorted accordingly
        # TODO optionally validate the travel time velocity constraints

        event_cache = []

        # first determine the first stop which is not to be serviced just yet. this can either be
        # the next pickup/dropoff or an internal assign stop.
        i_first_future_stop = next(
            (
                i
                for i, s in enumerate(self.stoplist)
                if s.estimated_arrival_time > t
                or s.action == StopAction.internal_assign
            ),
            len(self.stoplist),
        )

        # now emit serviced events for all the stops up to the previously determined one, except CPE
        for i, stop in enumerate(self.stoplist[1:i_first_future_stop]):
            event_cache.append(
                {StopAction.pickup: PickupEvent, StopAction.dropoff: DeliveryEvent}[
                    stop.action
                ](
                    request_id=stop.request.request_id,
                    vehicle_id=self.vehicle_id,
                    timestamp=max(stop.estimated_arrival_time, stop.time_window_min),
                )
            )

        # now update CPE
        # update eta if we have passed the its location already
        if self.stoplist[0].estimated_arrival_time < t:
            # if a next stop exists, update the CPEs location by interpolating from the location of either the
            # CPE or any other last serviced upcoming stop to the next location.
            # If they are identical nothing will happen.
            if len(self.stoplist) > 1:
                if i_first_future_stop != len(self.stoplist):
                    (
                        self.stoplist[0].location,
                        self.stoplist[0].estimated_arrival_time,
                    ) = self.space.interp_time(
                        u=self.stoplist[i_first_future_stop - 1].location,
                        v=self.stoplist[i_first_future_stop].location,
                        time_to_dest=self.stoplist[
                            i_first_future_stop
                        ].estimated_arrival_time
                        - t,
                    )
                else:
                    self.stoplist[0].location = self.stoplist[
                        i_first_future_stop - 1
                    ].location
                    self.stoplist[0].estimated_arrival_time = t

            else:
                self.stoplist[0].estimated_arrival_time = t

        if (
            i_first_future_stop != len(self.stoplist)
            and self.stoplist[i_first_future_stop].action == StopAction.internal_assign
        ):
            event_cache.append(
                InternalAssignStopEvent(timestamp=t, vehicle_id=self.vehicle_id)
            )

        if i_first_future_stop > 0:
            self.stoplist = [self.stoplist[0]] + self.stoplist[i_first_future_stop:]

        return event_cache

    def handle_transportation_request_single_vehicle(
        self, request: TransportationRequest
    ) -> SingleVehicleSolution:
        """
        The computational bottleneck. An efficient simulator could do the following:
        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
        2. Implement as a c extension. The args and the return value are all basic c data types,
           so this should also be easy.

        Parameters
        ----------
        request

        Returns
        -------
        This returns the single best solution for the respective vehicle.
        """

        return self.vehicle_id, *taxicab_dispatcher_drive_first(
            request=request, stoplist=self.stoplist, space=self.space
        )
