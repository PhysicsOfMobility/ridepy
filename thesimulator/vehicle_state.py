import operator as op
import numpy as np

from typing import Optional, SupportsFloat, List, Sequence

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
    Event,
)
from .util.dispatchers import (
    taxicab_dispatcher_drive_first,
    taxicab_dispatcher_drive_first_location_trigger_bulk,
)


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally  be implemented in Cython
    or other compiled language.
    """

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
        self.max_capacity = None

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

        # now update CPE and deal with other internal stops

        # if we have not passed CPE yet, there is nothing to do.
        # in this case i_first_future_stop == 0.
        # if we have passed CPE b/c either jump time was zero or we are on a continuous space we have
        # to update CPE's eta and possibly its location, in case we have serviced a stop and are now empty or
        # are on the way to another stop. otherwise we remain at the CPE's old location.
        if len(self.stoplist) == 1:
            # case I:
            # we have an empty stoplist, just idle around
            self.stoplist[0].estimated_arrival_time = t

        elif i_first_future_stop == len(self.stoplist):
            # case II:
            # all stops currently in the stop list have to be serviced. as we are
            # then-idle we move the CPE to the last-served stop.
            self.stoplist[0].location = self.stoplist[i_first_future_stop - 1].location
            self.stoplist[0].estimated_arrival_time = t
        else:
            # case III:
            # only stops up to some stop have to be served.
            # then we are on the way between the last-served stop and the first future one.
            (
                self.stoplist[0].location,
                self.stoplist[0].estimated_arrival_time,
            ) = self.space.interp_time(
                u=self.stoplist[i_first_future_stop - 1].location,
                v=self.stoplist[i_first_future_stop].location,
                time_to_dest=self.stoplist[i_first_future_stop].estimated_arrival_time
                - t,
            )

            # if the next upcoming stop is an internal_assign stop, emit an event
            if self.stoplist[i_first_future_stop].action == StopAction.internal_assign:
                event_cache.append(
                    InternalAssignStopEvent(timestamp=t, vehicle_id=self.vehicle_id)
                )

        # if we have serviced any stops, remove them from the stoplist
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
            request=request,
            stoplist=self.stoplist,
            space=self.space,
        )

    def assign_bulk_requests(self, reqs) -> Sequence[Event]:
        return self.vehicle_id, *taxicab_dispatcher_drive_first_location_trigger_bulk(
            requests=reqs, stoplist=self.stoplist, space=self.space
        )

    def recompute_arrival_times_drive_first(self):
        # update CPATs
        for stop_i, stop_j in zip(self.stoplist, self.stoplist[1:]):
            stop_j.estimated_arrival_time = max(
                stop_i.estimated_arrival_time, stop_i.time_window_min
            ) + self.space.t(stop_i.location, stop_j.location)

    @property
    def location(self):
        return self.stoplist[0].location

    @property
    def capacity(self):
        # TODO calculate actual current capacity to enable capacity constraints
        return None
