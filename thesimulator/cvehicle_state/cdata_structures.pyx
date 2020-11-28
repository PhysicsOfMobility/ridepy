# distutils: language = c++

from cstuff cimport Request as CRequest
from cstuff cimport Stop as CStop
from cstuff cimport StopAction as CAction
from cstuff cimport Stoplist as CStoplist
from cstuff cimport brute_force_distance_minimizing_dispatcher as c_disp
from libcpp.vector cimport vector



from numpy import inf
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Union, Tuple, List

ID = Union[str, int]

cdef class Request:
    cdef CRequest c_req
    def __cinit__(self):
        pass
    def __init__(self, int request_id, float creation_timestamp):
        self.c_req = CRequest(request_id, creation_timestamp)

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

    def __init__(self, Request request, float estimated_arrival_time):
        self.c_stop = CStop(request.c_req, estimated_arrival_time)

    def __repr__(self):
        return f'Stop(request={Request.from_c(self.c_stop.request)}, estimated_arrival_time={self.c_stop.estimated_arrival_time})'

    def foo(self):
        return self.c_stop.request.creation_timestamp

    @property
    def estimated_arrival_time(self):
        return self.c_req.estimated_arrival_time

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

    @staticmethod
    cdef Stoplist from_c(CStoplist cstoplist):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist)
        stoplist.c_stoplist = cstoplist
        return stoplist


@dataclass
class TransportationRequest(Request):
    """
    A request for the system to perform a transportation task,
    through creating a route through the system given spatio-temporal constraints.
    """
    origin: Any
    destination: Any
    # pickup_offset: float = 0
    pickup_timewindow_min: Optional[float]
    pickup_timewindow_max: Optional[float]
    delivery_timewindow_min: Optional[float]
    delivery_timewindow_max: Optional[float]


@dataclass
class InternalRequest(Request):
    """
    A request for the system to perform some action at a specific location
    that is not directly requested by a customer
    """

    location: Any


class StopAction(Enum):
    """
    Representing actions that the system may perform at a specific location
    """

    pickup = 1
    dropoff = 2
    internal = 3

RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
    InternalStopEvent,
    RequestAssignEvent,
]
Stoplist = List[Stop]
SingleVehicleSolution = Tuple[Any, float, Stoplist, Tuple[float, float, float, float]]
"""vehicle_id, cost, new_stop_list"""
RequestEvent = Union[RequestAcceptanceEvent, RequestRejectionEvent]
StopEvent = Union[InternalStopEvent, PickupEvent, DeliveryEvent]

def spam():
    cdef CRequest r
    r.request_id = 99

    cdef Request pyreq = Request.from_c(r)

    return pyreq

def dispatcher(Request request, Stoplist stoplist):
    res = c_disp(request.c_req, stoplist.c_stoplist)
    return Stoplist.from_c(res)