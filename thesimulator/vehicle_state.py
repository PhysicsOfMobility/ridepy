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
    InternalStopEvent,
    Stop,
    TransportationRequest,
    TransportSpace,
    Dispatcher,
    LocType,
)


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
        self,
        *,
        vehicle_id,
        initial_stoplist: Stoplist,
        space: TransportSpace,
        loc_type: Optional[LocType] = None,
        dispatcher: Dispatcher,
        seat_capacity: int = np.inf,
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
        self.dispatcher = dispatcher
        self.seat_capacity = seat_capacity

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

        last_stop = None

        # drop all non-future stops from the stoplist, except for the (outdated) CPE
        for i in range(len(self.stoplist) - 1, 0, -1):
            stop = self.stoplist[i]
            # service the stop at its estimated arrival time
            if stop.estimated_arrival_time <= t:
                # as we are iterating backwards, the first stop iterated over is the last one serviced
                if last_stop is None:
                    last_stop = stop

                event_cache.append(
                    {
                        StopAction.pickup: PickupEvent,
                        StopAction.dropoff: DeliveryEvent,
                        StopAction.internal: InternalStopEvent,
                    }[stop.action](
                        request_id=stop.request.request_id,
                        vehicle_id=self.vehicle_id,
                        timestamp=max(
                            stop.estimated_arrival_time, stop.time_window_min
                        ),
                    )
                )

                del self.stoplist[i]

        # fix event cache order
        event_cache = event_cache[::-1]

        # if no stop was serviced, the last stop is the outdated CPE
        if last_stop is None:
            last_stop = self.stoplist[0]

        # set CPE time to current time
        self.stoplist[0].estimated_arrival_time = t

        # set CPE location to current location as inferred from the time delta to the upcoming stop's CPAT
        if len(self.stoplist) > 1:
            self.stoplist[0].location, _ = self.space.interp_time(
                u=last_stop.location,
                v=self.stoplist[1].location,
                time_to_dest=self.stoplist[1].estimated_arrival_time - t,
            )
        else:
            # stoplist is empty, only CPE is there. Therefore we just stick around...
            pass
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

        return self.vehicle_id, *self.dispatcher(
            request=request,
            stoplist=self.stoplist,
            space=self.space,
            seat_capacity=self.seat_capacity,
        )
