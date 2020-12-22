# distutils: language = c++

from libcpp.vector cimport vector
from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    Stop as CStop,
    R2loc,
)

from cython.operator cimport dereference




cdef class TransportationRequestBase:
    def __repr__(self):
       return f'Request(request_id={self.c_req.request_id},creation_timestamp={self.c_req.creation_timestamp})'

    @property
    def request_id(self):
        return self.c_req.request_id

    @property
    def creation_timestamp(self):
        return self.c_req.creation_timestamp

cdef class TransportationRequestR2loc(TransportationRequestBase):
    def __init__(
            self, int request_id, float creation_timestamp,
            origin, destination, pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
    ):
        self.c_req = CRequest[R2loc](
            request_id, creation_timestamp, origin, destination,
            pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
        )

    @staticmethod
    cdef TransportationRequestR2loc from_c(CRequest[R2loc] creq):
        cdef TransportationRequestR2loc req = TransportationRequestR2loc.__new__(TransportationRequestR2loc)
        req.c_req = creq
        return req


cdef class StopBase:
    def __repr__(self):
        return f'Stop(request={self.request}, estimated_arrival_time={self.c_stop.estimated_arrival_time})'

    @property
    def action(self):
        return StopAction(self.c_stop.action)

    @property
    def estimated_arrival_time(self):
        return self.c_stop.estimated_arrival_time
    @estimated_arrival_time.setter
    def estimated_arrival_time(self, estimated_arrival_time):
        self.c_stop.estimated_arrival_time = estimated_arrival_time

    @property
    def time_window_min(self):
        return self.c_stop.time_window_min

    @property
    def time_window_max(self):
        return self.c_stop.time_window_max

    @property
    def request(self):
        return self.transportation_request_class.from_c(self.c_stop.request)



cdef class StopR2loc(StopBase):
    def __init__(
            self, location, TransportationRequestR2loc request,
            StopAction action, double estimated_arrival_time,
            double time_window_min,
            double time_window_max,
    ):
        self.transportation_request_class = TransportationRequestR2loc
        self.c_stop = CStop[R2loc](
            location, request.c_req, action, estimated_arrival_time,
            time_window_min, time_window_max)

    @staticmethod
    cdef StopR2loc from_c(CStop[R2loc] cstop):
        cdef StopR2loc stop = StopR2loc.__new__(StopR2loc)
        stop.c_stop = cstop
        return stop

cdef class StoplistBase:

    def __getitem__(self, i):
        return self.stop_class.from_c(dereference(self.c_stoplist_ptr)[i])

    def __len__(self):
        return dereference(self.c_stoplist_ptr).size()

    def remove_nth_elem(self, int n):
        dereference(self.c_stoplist_ptr).erase(
            dereference(self.c_stoplist_ptr).begin()+n
        )




cdef class StoplistR2loc(StoplistBase):
    def __cinit__(self):
        self.ptr_owner=True
        self.c_stoplist_ptr = new vector[CStop[R2loc]](0)

    def __init__(self, python_stoplist):
        self.stop_class = StopR2loc
        cdef StopR2loc s
        for py_s in python_stoplist:
            s = py_s
            dereference(self.c_stoplist_ptr).push_back(s.c_stop)

    @staticmethod
    cdef StoplistR2loc from_ptr(vector[CStop[R2loc]] *cstoplist_ptr):
        cdef StoplistR2loc stoplist = StoplistR2loc.__new__(StoplistR2loc)
        stoplist.c_stoplist_ptr = cstoplist_ptr
        stoplist.ptr_owner = False
        return stoplist

    def __dealloc__(self):
        if self.ptr_owner:
            # I was not created from an existing c++ pointer ("owned" by another Stoplist object)
            del self.c_stoplist_ptr


def spam():
    cdef CRequest r
    r.request_id = 99
    cdef TransportationRequestR2loc pyreq = TransportationRequestR2loc.from_c(r)
    cdef StopR2loc pystop = StopR2loc((99,23), pyreq, StopAction.pickup, 0, 0,10)
    return pyreq, pystop
