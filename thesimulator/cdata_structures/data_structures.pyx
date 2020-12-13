# distutils: language = c++

from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    Stop as CStop,
    R2loc,
    Stoplist as CStoplist,
)

from cython.operator cimport dereference

cdef class TransportationRequest:
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
    cdef TransportationRequest from_c(CRequest creq):
        cdef TransportationRequest req = TransportationRequest.__new__(TransportationRequest)
        req.c_req = creq
        return req


cdef class Stop:
    def __cinit__(self):
        pass

    def __init__(
            self, location, TransportationRequest request,
            StopAction action, double estimated_arrival_time,
            double time_window_min,
            double time_window_max,
    ):
        self.c_stop = CStop(
            location, request.c_req, action, estimated_arrival_time,
            time_window_min, time_window_max)

    def __repr__(self):
        return f'Stop(request={TransportationRequest.from_c(self.c_stop.request)}, estimated_arrival_time={self.c_stop.estimated_arrival_time})'

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
        return TransportationRequest.from_c(self.c_stop.request)

    @staticmethod
    cdef Stop from_c(CStop cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.c_stop = cstop
        return stop



cdef class Stoplist:
    def __cinit__(self):
        self.ptr_owner=True
        self.c_stoplist_ptr = new CStoplist(0)

    def __init__(self, python_stoplist):

        cdef Stop s
        for py_s in python_stoplist:
            s = py_s
            dereference(self.c_stoplist_ptr).push_back(s.c_stop)

    def __getitem__(self, i):
        return Stop.from_c(dereference(self.c_stoplist_ptr)[i])

    def __len__(self):
        return dereference(self.c_stoplist_ptr).size()

    def remove_nth_elem(self, int n):
        dereference(self.c_stoplist_ptr).erase(
            dereference(self.c_stoplist_ptr).begin()+n
        )

    @staticmethod
    cdef Stoplist from_ptr(CStoplist *cstoplist_ptr):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist)
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
    cdef TransportationRequest pyreq = TransportationRequest.from_c(r)
    cdef Stop pystop = Stop((99,23), pyreq, StopAction.pickup, 0, 0,10)
    return pyreq, pystop
