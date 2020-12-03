# distutils: language = c++


from thesimulator.data_structures import (PickupEvent, DeliveryEvent, InternalStopEvent)

from .cstuff cimport Request as CRequest
from .cstuff cimport Stop as CStop
from .cstuff cimport R2loc
from .cstuff cimport StopAction as CStopAction
from .cstuff cimport Stoplist as CStoplist
from .cstuff cimport brute_force_distance_minimizing_dispatcher as c_disp
from libcpp.vector cimport vector



from numpy import inf
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Union, Tuple, List

ID = Union[str, int]


cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3


cdef class Request:
    cdef CRequest c_req
    def __cinit__(self):
        pass
    def __init__(
            self, int request_id, float creation_timestamp,
            origin, destination, pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
    ):
        self.c_req = CRequest(
            request_id, creation_timestamp, origin, destination,
            pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
        )

    def __repr__(self):
       return f'Request(request_id={self.c_req.request_id},creation_timestamp={self.c_req.creation_timestamp})'

    @property
    def request_id(self):
        return self.c_req.request_id

    @property
    def creation_timestamp(self):
        return self.c_req.creation_timestamp

    @staticmethod
    cdef Request from_c(CRequest creq):
        cdef Request req = Request.__new__(Request)
        req.c_req = creq
        return req


cdef class Stop:
    cdef CStop c_stop
    def __cinit__(self):
        pass

    def __init__(
            self, location, Request request,
            StopAction action, double estimated_arrival_time,
            double time_window_min,
            double time_window_max,
    ):
        self.c_stop = CStop(
            location, request.c_req, action, estimated_arrival_time,
            time_window_min, time_window_max)

    def __repr__(self):
        return f'Stop(request={Request.from_c(self.c_stop.request)}, estimated_arrival_time={self.c_stop.estimated_arrival_time})'

    @property
    def action(self):
        return StopAction(self.c_stop.action)

    @property
    def estimated_arrival_time(self):
        return self.c_stop.estimated_arrival_time

    @property
    def time_window_min(self):
        return self.c_stop.time_window_min

    @property
    def time_window_max(self):
        return self.c_stop.time_window_max

    @property
    def request(self):
        return Request.from_c(self.c_stop.request)

    @staticmethod
    cdef Stop from_c(CStop cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.c_stop = cstop
        return stop


cdef class Stoplist:
    cdef CStoplist c_stoplist
    def __cinit__(self):
        pass
    def __init__(self, python_stoplist):
        cdef Stop s
        for py_s in python_stoplist:
            s = py_s
            self.c_stoplist.push_back(s.c_stop)

    def __getitem__(self, i):
        return Stop.from_c(self.c_stoplist[i])

    def __len__(self):
        return self.c_stoplist.size()

    @staticmethod
    cdef Stoplist from_c(CStoplist cstoplist):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist)
        stoplist.c_stoplist = cstoplist
        return stoplist



def spam():
    cdef CRequest r
    r.request_id = 99

    cdef Request pyreq = Request.from_c(r)

    cdef Stop pystop = Stop((99,23), pyreq, StopAction.pickup, 0, 0,10)

    return pyreq, pystop


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

    def __init__(
        self, *, vehicle_id, initial_stoplist): # TODO currently transport_space cannot be specified
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        # Create a cython stoplist object from initial_stoplist
        self.stoplist = Stoplist(initial_stoplist)
        # TODO: re-enable choosing space
        # self.space = space

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

#    def handle_transportation_request_single_vehicle(
#        self, request: TransportationRequest
#    ) -> SingleVehicleSolution:
#        """
#        The computational bottleneck. An efficient simulator could do the following:
#        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
#        2. Implement as a c extension. The args and the return value are all basic c data types,
#           so this should also be easy.
#
#        Parameters
#        ----------
#        request
#
#        Returns
#        -------
#        This returns the single best solution for the respective vehicle.
#        """
#
#        return self.vehicle_id, *taxicab_dispatcher_drive_first(
#            request=request, stoplist=self.stoplist, space=self.space
#        )


