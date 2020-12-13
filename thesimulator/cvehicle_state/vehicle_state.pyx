# distutils: language=c++


from thesimulator.data_structures import (PickupEvent, DeliveryEvent, InternalStopEvent)
from thesimulator.cdata_structures.data_structures cimport (
    TransportationRequest,
    Stop,
    StopAction,
    Stoplist,
)

from thesimulator.util.cspaces.spaces cimport Euclidean2D

from thesimulator.util.cdispatchers.dispatchers cimport (
    brute_force_distance_minimizing_dispatcher as c_disp,
)
from cython.operator cimport dereference
from typing import List

cdef class VehicleState:
    """
    Single vehicle insertion logic is implemented in Cython here.
    """

    #    def recompute_arrival_times_drive_first(self):
    #        # update CPATs
    #        for stop_i, stop_j in zip(self.stoplist, self.stoplist[1:]):
    #            stop_j.estimated_arrival_time = max(
    #                stop_i.estimated_arrival_time, stop_i.time_window_min
    #            ) + self.space.t(stop_i.location, stop_j.location)
    cdef Stoplist stoplist
    cdef Euclidean2D space
#    cdef TransportSpace space
    cdef int vehicle_id
    def __init__(
            self, *, vehicle_id, initial_stoplist, Euclidean2D space): # TODO currently transport_space cannot be specified at __init__
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        # Create a cython stoplist object from initial_stoplist
        self.stoplist = Stoplist(initial_stoplist)
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
                self.stoplist.remove_nth_elem(i)

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
            self, TransportationRequest cy_request
    ):
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
        return self.vehicle_id, c_disp(
            cy_request,
            self.stoplist,
            self.space)
