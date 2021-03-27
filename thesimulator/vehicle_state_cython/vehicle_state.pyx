# distutils: language=c++

from thesimulator.util import MAX_SEAT_CAPACITY

from thesimulator.data_structures import (
    PickupEvent,
    DeliveryEvent,
    InternalStopEvent,
    StopEvent,
    Dispatcher
)
from thesimulator.data_structures_cython.data_structures cimport (
    TransportationRequest,
    Stop,
    StopAction,
    Stoplist,
)

from thesimulator.data_structures_cython.data_structures import StopAction  as pStopAction # only for a debug print statemnet

from thesimulator.util.spaces_cython.spaces cimport Euclidean2D, TransportSpace

from thesimulator.util.dispatchers_cython.dispatchers cimport (
    brute_force_total_traveltime_minimizing_dispatcher as c_disp,
)
from typing import Optional, SupportsFloat, List
from copy import deepcopy

from wurlitzer import pipes
import logging
logger = logging.getLogger(__name__)



cdef extern from "limits.h":
    cdef int INT_MAX

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
    cdef TransportSpace space
    cdef int vehicle_id
    cdef int seat_capacity
    cdef dict __dict__

    def __init__(
        self,
        *,
        vehicle_id,
        initial_stoplist: List[Stop],
        space: TransportSpace,
        dispatcher: Dispatcher,
        seat_capacity: int,
    ):
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        # Create a cython stoplist object from initial_stoplist
        self.stoplist = Stoplist(initial_stoplist, space.loc_type)
        self.space = space
        self.dispatcher = dispatcher
        if seat_capacity > INT_MAX:
            raise ValueError("Cannot use seat_capacity bigger that c++'s INT_MAX")
        self.seat_capacity = seat_capacity
        logger.info(f"Created VehicleState with space of type {type(self.space)}")

    property stoplist:
        def __get__(self):
            return self.stoplist
        def __set__(self, new_stoplist):
            self.stoplist = new_stoplist

    property seat_capacity:
        def __get__(self):
            return self.seat_capacity


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
                    # this deepcopy is necessary because otherwise after removing elements from stoplist,
                    # last_stop will point to the wrong element.  See the failing test as well:
                    # test.test_data_structures_cython.test_stoplist_getitem_and_elem_removal_consistent
                    last_stop = deepcopy(stop)

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

        # set the occupancy at CPE
        self.stoplist[0].occupancy_after_servicing = last_stop.occupancy_after_servicing

        # set CPE location to current location as inferred from the time delta to the upcoming stop's CPAT
        if len(self.stoplist) > 1:
            if last_stop.estimated_arrival_time > t:
                # still mid-jump from last interpolation, no need to interpolate
                # again
                pass
            else:
                self.stoplist[0].location, jump_time = self.space.interp_time(
                    u=last_stop.location,
                    v=self.stoplist[1].location,
                    time_to_dest=self.stoplist[1].estimated_arrival_time - t,
                )
                # set CPE time
                self.stoplist[0].estimated_arrival_time = t + jump_time
        else:
            # stoplist is empty, only CPE is there. set CPE time to current time
            self.stoplist[0].estimated_arrival_time = t

        return event_cache

    def handle_transportation_request_single_vehicle(
            self, TransportationRequest request
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

        with pipes() as (out, err):
            ret = self.vehicle_id, *self.dispatcher(
                request,
                self.stoplist,
                self.space, self.seat_capacity)
        #TODO: when cython supports walrus operator, change to more readable
        # if (msg:=out.read().strip()):
        msg = out.read().strip()
        if msg:
            logger.info(msg)
        msg = err.read().strip()
        if msg:
            logger.critical(msg)
        return ret
