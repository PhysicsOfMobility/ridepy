# distutils: language = c++
"""
This cython module wraps the struct templates exposed from c++ by cdata_structures.pxd into extension types.
However an extension type obviously cannot be templated (at compile time, all possible variations of a template
must be known). There is no really elegant way of doing it in cython as of v3.0a6. So we will use the [Explicit
Run-Time Dispatch approach](https://martinralbrecht.wordpress.com/2017/07/23/adventures-in-cython-templating/).

In short, an enum LocType (resides in data_structures.pxd) contains all template types Loc we are likely to need.
The extension dtype for Request[Loc] then will contain *an union* holding one of the variants (e.g. Request[int],
Request[tuple(double, double)]) etc. Then each member function will check the Loc type, and dispatch the method
call to the appropriate object inside that union.
"""
from cython.operator cimport dereference
from libcpp.vector cimport vector

from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    TransportationRequest as CTransportationRequest,
    InternalRequest as CInternalRequest,
    Stop as CStop,
    R2loc,
)


import logging
logger = logging.getLogger(__name__)

cdef class Request:
    # TODO: Since this is a base class never to be instantiated, probably we do not need
    # an __init__?
    def __init__(
            self, int request_id, float creation_timestamp, loc_type):
        self.ptr_owner=True # I have not been created from an existing pointer
        self.loc_type = <LocType> loc_type
        #if hasattr(origin, '__len__') and len(origin) == 2:
        if self.loc_type == LocType.R2LOC:
            self._ureq._req_r2loc = new CRequest[R2loc](
                request_id, creation_timestamp
            )
        #elif isinstance(origin, int):
        elif self.loc_type == LocType.INT:
            self._ureq._req_int = new CRequest[int](
                request_id, creation_timestamp
            )
        else:
            raise ValueError("This line should never have been reached")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Request(request_id={dereference(self._ureq._req_r2loc).request_id},' \
                   f'creation_timestamp={dereference(self._ureq._req_r2loc).creation_timestamp)})'
        elif self.loc_type == LocType.INT:
            return f'Request(request_id={dereference(self._ureq._req_int).request_id},' \
                   f'creation_timestamp={dereference(self._ureq._req_int).creation_timestamp})'
        else:
            raise ValueError("This line should never have been reached")

    @property
    def request_id(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self._ureq._req_r2loc).request_id
        elif self.loc_type == LocType.INT:
            return dereference(self._ureq._req_int).request_id

    @property
    def creation_timestamp(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self._ureq._req_r2loc).creation_timestamp
        elif self.loc_type == LocType.INT:
            return dereference(self._ureq._req_int).creation_timestamp
        else:
            raise ValueError("This line should never have been reached")

    @staticmethod
    cdef Request from_c_r2loc(CRequest[R2loc] *creq):
        cdef Request req = Request.__new__(Request)
        req.ptr_owner = False
        req._ureq._req_r2loc = creq
        req.loc_type = LocType.R2LOC
        return req

    @staticmethod
    cdef Request from_c_int(CRequest[int] *creq):
        cdef Request req = Request.__new__(Request)
        req.ptr_owner = False
        req._ureq._req_int = creq
        req.loc_type = LocType.INT
        return req

    def __dealloc__(self):
        """
        Since this is a base class that will never be instantiated, we do not need to free any pointer here.
        Take care to do so in the derived classes though.
        """
        ...


cdef class TransportationRequest(Request):
    def __init__(
            self, int request_id, float creation_timestamp,
            origin, destination, pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
    ):
        self.ptr_owner=True # I have not been created from an existing pointer
        if hasattr(origin, '__len__') and len(origin) == 2:
            # TODO: this inferring of LocType is kludgy. We should have it as an argument of __init__
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self._ureq._req_r2loc = new CTransportationRequest[R2loc](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            )
        elif isinstance(origin, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self._ureq._req_int = new CTransportationRequest[int](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            )
        else:
            raise TypeError(f"Cannot handle origin of type {type(origin)}")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Request(request_id={dereference(self._ureq._req_r2loc).request_id},"' \
                   f'f"creation_timestamp={dereference(self._ureq._req_r2loc).creation_timestamp})'
        elif self.loc_type == LocType.INT:
            return f'Request(request_id={dereference(self._ureq._req_int).request_id},"' \
                   f'f"creation_timestamp={dereference(self._ureq._req_int).creation_timestamp})'
        else:
            raise ValueError("This line should never have been reached")

    # TODO: Need to expose the properties origin, destination, (pickup|delivery)_timewindow_(min|max)
    def __dealloc__(self):
        if self.ptr_owner:
            # I was not created from an existing c++ pointer ("owned" by another object)
            if self.loc_type == LocType.R2LOC:
                del self._ureq._req_r2loc
            elif self.loc_type == LocType.INT:
                del self._ureq._req_int
            else:
                raise ValueError("This line should never have been reached")

cdef class InternalRequest(Request):
    def __init__(
            self, int request_id, float creation_timestamp,
            location
    ):
        self.ptr_owner=True # I have not been created from an existing pointer
        print(f"Request.__init__: request_id={request_id}")
        if hasattr(location, '__len__') and len(location) == 2:
            # TODO: this inferring of LocType is kludgy. We should have it as an argument of __init__
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self._ureq._req_r2loc = new CInternalRequest[R2loc](
                request_id, creation_timestamp, location
            )
        elif isinstance(location, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self._ureq._req_int = new CInternalRequest[int](
                request_id, creation_timestamp, location
            )
        else:
            raise TypeError(f"Cannot handle origin of type {type(location)}")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Request(request_id={dereference(self._ureq._req_r2loc).request_id},' \
                   f'creation_timestamp={dereference(self._ureq._req_r2loc).creation_timestamp})'
        elif self.loc_type == LocType.INT:
            return f'Request(request_id={dereference(self._ureq._req_int).request_id},"' \
                   f'creation_timestamp={dereference(self._ureq._req_int).creation_timestamp})'
        else:
            raise ValueError("This line should never have been reached")

    # TODO: Need to expose the properties origin, destination, (pickup|delivery)_timewindow_(min|max)
    def __dealloc__(self):
        if self.ptr_owner:
            # I was not created from an existing c++ pointer ("owned" by another object)
            if self.loc_type == LocType.R2LOC:
                del self._ureq._req_r2loc
            elif self.loc_type == LocType.INT:
                del self._ureq._req_int
            else:
                raise ValueError("This line should never have been reached")



cdef class Stop:
    def __cinit__(self):
        pass

    def __init__(
            self, location, Request request not None,
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
        # TODO: should also show the CPAT, EAST and LAST and Action
        if self.loc_type == LocType.R2LOC:
            print("at Stop.__repr__, reqid=", dereference(self.ustop._stop_r2loc.request).request_id)
            return f'Stop(request={Request.from_c_r2loc(self.ustop._stop_r2loc.request)}, ' \
                   f'estimated_arrival_time={self.ustop._stop_r2loc.estimated_arrival_time})'
        elif self.loc_type == LocType.INT:
            return f'Stop(request={Request.from_c_int(self.ustop._stop_int.request)},' \
                   f' estimated_arrival_time={self.ustop._stop_int.estimated_arrival_time})'
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
            return Request.from_c_r2loc(self.ustop._stop_r2loc.request)
        elif self.loc_type == LocType.INT:
            return Request.from_c_int(self.ustop._stop_int.request)
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
            for py_s in python_stoplist:
                print("before pushing back: ", py_s)
                # TODO: This is probably the cause of py_s changing: Stop needs move and copy constructur?
                dereference(self.ustoplist._stoplist_r2loc_ptr).push_back((<Stop> py_s).ustop._stop_r2loc)
                print("after pushing back: ", py_s)
        elif loc_type == LocType.INT:
            for py_s in python_stoplist:
                dereference(self.ustoplist._stoplist_int_ptr).push_back((<Stop> py_s).ustop._stop_int)
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

