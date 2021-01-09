# distutils: language = c++

from cython.operator cimport dereference
from libcpp.vector cimport vector

from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    Stop as CStop,
    R2loc,
)

import logging
logger = logging.getLogger(__name__)

cdef class TransportationRequest:
    def __init__(
            self, int request_id, float creation_timestamp,
            origin, destination, pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
    ):

        if hasattr(origin, '__len__') and len(origin) == 2:
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self._ureq._req_r2loc = CRequest[R2loc](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            )
        elif isinstance(origin, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self._ureq._req_int = CRequest[int](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            )
        else:
            raise TypeError(f"Cannot handle origin of type {type(origin)}")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Request(request_id={self._ureq._req_r2loc.request_id},creation_timestamp={self._ureq._req_r2loc.creation_timestamp})'
        elif self.loc_type == LocType.INT:
            return f'Request(request_id={self._ureq._req_int.request_id},creation_timestamp={self._ureq._req_int.creation_timestamp})'
        else:
            raise ValueError("This line should never have been reached")

    @property
    def request_id(self):
        if self.loc_type == LocType.R2LOC:
            return self._ureq._req_r2loc.request_id
        elif self.loc_type == LocType.INT:
            return self._ureq._req_int.request_id

    @property
    def creation_timestamp(self):
        if self.loc_type == LocType.R2LOC:
            return self._ureq._req_r2loc.creation_timestamp
        elif self.loc_type == LocType.INT:
            return self._ureq._req_int.creation_timestamp
        else:
            raise ValueError("This line should never have been reached")

    @staticmethod
    cdef TransportationRequest from_c_r2loc(CRequest[R2loc] creq):
        cdef TransportationRequest req = TransportationRequest.__new__(TransportationRequest)
        req._ureq._req_r2loc = creq
        req.loc_type = LocType.R2LOC
        return req

    @staticmethod
    cdef TransportationRequest from_c_int(CRequest[int] creq):
        cdef TransportationRequest req = TransportationRequest.__new__(TransportationRequest)
        req._ureq._req_int = creq
        req.loc_type = LocType.INT
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
        if hasattr(location, '__len__') and len(location) == 2:
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self.ustop._stop_r2loc = CStop[R2loc](
                location, request._ureq._req_r2loc, action, estimated_arrival_time,
                time_window_min, time_window_max)
        elif isinstance(location, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self.ustop._stop_int = CStop[int](
                location, request._ureq._req_int, action, estimated_arrival_time,
                time_window_min, time_window_max)
        else:
            raise ValueError("This line should never have been reached")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Stop(request={TransportationRequest.from_c_r2loc(self.ustop._stop_r2loc.request)}, estimated_arrival_time={self.ustop._stop_r2loc.estimated_arrival_time})'
        elif self.loc_type == LocType.INT:
            return f'Stop(request={TransportationRequest.from_c_int(self.ustop._stop_int.request)}, estimated_arrival_time={self.ustop._stop_int.estimated_arrival_time})'
        else:
            raise ValueError("This line should never have been reached")

    @property
    def action(self):
        if self.loc_type == LocType.R2LOC:
            return StopAction(self.ustop._stop_r2loc.action)
        elif self.loc_type == LocType.INT:
            return StopAction(self.ustop._stop_int.action)
        else:
            raise ValueError("This line should never have been reached")

    @property
    def estimated_arrival_time(self):
        if self.loc_type == LocType.R2LOC:
            return self.ustop._stop_r2loc.estimated_arrival_time
        elif self.loc_type == LocType.INT:
            return self.ustop._stop_int.estimated_arrival_time
    @estimated_arrival_time.setter
    def estimated_arrival_time(self, estimated_arrival_time):
        if self.loc_type == LocType.R2LOC:
            self.ustop._stop_r2loc.estimated_arrival_time = estimated_arrival_time
        elif self.loc_type == LocType.INT:
            self.ustop._stop_int.estimated_arrival_time = estimated_arrival_time
        else:
            raise ValueError("This line should never have been reached")

    @property
    def time_window_min(self):
        if self.loc_type == LocType.R2LOC:
            return self.ustop._stop_r2loc.time_window_min
        elif self.loc_type == LocType.INT:
            return self.ustop._stop_int.time_window_min
        else:
            raise ValueError("This line should never have been reached")

    @property
    def time_window_max(self):
        if self.loc_type == LocType.R2LOC:
            return self.ustop._stop_r2loc.time_window_max
        elif self.loc_type == LocType.INT:
            return self.ustop._stop_int.time_window_max
        else:
            raise ValueError("This line should never have been reached")

    @property
    def request(self):
        if self.loc_type == LocType.R2LOC:
            return TransportationRequest.from_c_r2loc(self.ustop._stop_r2loc.request)
        elif self.loc_type == LocType.INT:
            return TransportationRequest.from_c_int(self.ustop._stop_int.request)
        else:
            raise ValueError("This line should never have been reached")

    @staticmethod
    cdef Stop from_c_r2loc(CStop[R2loc] cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.ustop._stop_r2loc = cstop
        stop.loc_type = LocType.R2LOC
        return stop

    @staticmethod
    cdef Stop from_c_int(CStop[int] cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.ustop._stop_int = cstop
        stop.loc_type = LocType.INT
        return stop

cdef class Stoplist:
    def __init__(self, python_stoplist, loc_type):
        self.ptr_owner=True # I have not been created from an existing pointer
        self.loc_type = loc_type

        if self.loc_type == LocType.R2LOC:
            self.ustoplist._stoplist_r2loc_ptr = new vector[CStop[R2loc]](0)
        elif self.loc_type == LocType.INT:
            self.ustoplist._stoplist_int_ptr = new vector[CStop[int]](0)
        else:
            raise ValueError(f"This line should never have been reached: {type(loc_type)}")

        if loc_type == LocType.R2LOC:
            for self.py_s in python_stoplist:
                dereference(self.ustoplist._stoplist_r2loc_ptr).push_back(self.py_s.ustop._stop_r2loc)
        elif loc_type == LocType.INT:
            for self.py_s in python_stoplist:
                dereference(self.ustoplist._stoplist_int_ptr).push_back(self.py_s.ustop._stop_int)
        else:
            raise ValueError("This line should never have been reached")
        logger.info("Created Stoplist")

    def __getitem__(self, i):
        if self.loc_type == LocType.R2LOC:
            return Stop.from_c_r2loc(dereference(self.ustoplist._stoplist_r2loc_ptr)[i])
        elif self.loc_type == LocType.INT:
            return Stop.from_c_int(dereference(self.ustoplist._stoplist_int_ptr)[i])
        else:
            raise ValueError("This line should never have been reached")

    def __len__(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.ustoplist._stoplist_r2loc_ptr).size()
        elif self.loc_type == LocType.INT:
            return dereference(self.ustoplist._stoplist_int_ptr).size()
        else:
            raise ValueError("This line should never have been reached")

    def remove_nth_elem(self, int n):
        if self.loc_type == LocType.R2LOC:
            dereference(self.ustoplist._stoplist_r2loc_ptr).erase(
                dereference(self.ustoplist._stoplist_r2loc_ptr).begin()+n
            )
        elif self.loc_type == LocType.INT:
            dereference(self.ustoplist._stoplist_int_ptr).erase(
                dereference(self.ustoplist._stoplist_int_ptr).begin()+n
            )
        else:
            raise ValueError("This line should never have been reached")

    @staticmethod
    cdef Stoplist from_c_r2loc(vector[CStop[R2loc]] *cstoplist_ptr):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist) # Calling __new__ bypasses __init__, see
        # https://cython.readthedocs.io/en/latest/src/userguide/extension_types.html#instantiation-from-existing-c-c-pointers
        stoplist.loc_type = LocType.R2LOC
        stoplist.ptr_owner = False
        stoplist.ustoplist._stoplist_r2loc_ptr = cstoplist_ptr

    @staticmethod
    cdef Stoplist from_c_int(vector[CStop[int]] *cstoplist_ptr):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist) # Calling __new__ bypasses __init__, see
        # https://cython.readthedocs.io/en/latest/src/userguide/extension_types.html#instantiation-from-existing-c-c-pointers
        stoplist.loc_type = LocType.INT
        stoplist.ptr_owner = False
        stoplist.ustoplist._stoplist_int_ptr = cstoplist_ptr

    def __dealloc__(self):
        if self.ptr_owner:
            # I was not created from an existing c++ pointer ("owned" by another Stoplist object)
            if self.loc_type == LocType.R2LOC:
                del self.ustoplist._stoplist_r2loc_ptr
            elif self.loc_type == LocType.INT:
                del self.ustoplist._stoplist_int_ptr
            else:
                raise ValueError("This line should never have been reached")

