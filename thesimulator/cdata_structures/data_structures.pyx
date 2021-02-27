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
from libcpp.memory cimport shared_ptr
from libcpp.memory cimport dynamic_pointer_cast
from cython.operator cimport typeid


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
    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'Request(request_id={dereference(self._ureq._req_r2loc).request_id},' \
                   f'creation_timestamp={dereference(self._ureq._req_r2loc).creation_timestamp)}))'
        elif self.loc_type == LocType.INT:
            return f'Request(request_id={dereference(self._ureq._req_int).request_id},' \
                   f'creation_timestamp={dereference(self._ureq._req_int).creation_timestamp}))'
        else:
            raise ValueError("This line should never have been reached")

    property request_id:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._ureq._req_r2loc).request_id
            elif self.loc_type == LocType.INT:
                return dereference(self._ureq._req_int).request_id
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._ureq._req_r2loc).request_id = value
            elif self.loc_type == LocType.INT:
                dereference(self._ureq._req_int).request_id = value
            else:
                raise ValueError("This line should never have been reached")

    property creation_timestamp:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._ureq._req_r2loc).creation_timestamp
            elif self.loc_type == LocType.INT:
                return dereference(self._ureq._req_int).creation_timestamp
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._ureq._req_r2loc).creation_timestamp = value
            elif self.loc_type == LocType.INT:
                dereference(self._ureq._req_int).creation_timestamp = value
            else:
                raise ValueError("This line should never have been reached")


    def __dealloc__(self):
        """
        Using smart pointers. Do not need to delete the base pointer.
        """
        ...


cdef class TransportationRequest(Request):
    def __init__(
            self, int request_id, float creation_timestamp,
            origin, destination, pickup_timewindow_min, pickup_timewindow_max,
            delivery_timewindow_min, delivery_timewindow_max
    ):
        if hasattr(origin, '__len__') and len(origin) == 2:
            # TODO: this inferring of LocType is kludgy. We should have it as an argument of __init__
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self._utranspreq._req_r2loc = shared_ptr[CTransportationRequest[R2loc]](new CTransportationRequest[R2loc](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            ))
            self._ureq._req_r2loc = dynamic_pointer_cast[CRequest[R2loc], CTransportationRequest[R2loc]](self._utranspreq._req_r2loc)
        elif isinstance(origin, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self._utranspreq._req_int = shared_ptr[CTransportationRequest[int]](new CTransportationRequest[int](
                request_id, creation_timestamp, origin, destination,
                pickup_timewindow_min, pickup_timewindow_max,
                delivery_timewindow_min, delivery_timewindow_max
            ))
            self._ureq._req_int = dynamic_pointer_cast[CRequest[int], CTransportationRequest[int]](self._utranspreq._req_int)
        else:
            raise TypeError(f"Cannot handle origin of type {type(origin)}")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'TransportationRequest(request_id={dereference(self._utranspreq._req_r2loc).request_id}, ' \
                   f'creation_timestamp={dereference(self._utranspreq._req_r2loc).creation_timestamp}, ' \
                   f'origin={dereference(self._utranspreq._req_r2loc).origin}, ' \
                   f'destination={dereference(self._utranspreq._req_r2loc).destination}, ' \
                   f'pickup_timewindow_min={dereference(self._utranspreq._req_r2loc).pickup_timewindow_min}, ' \
                   f'pickup_timewindow_max={dereference(self._utranspreq._req_r2loc).pickup_timewindow_max}, ' \
                   f'delivery_timewindow_min={dereference(self._utranspreq._req_r2loc).delivery_timewindow_min}, ' \
                   f'delivery_timewindow_max={dereference(self._utranspreq._req_r2loc).delivery_timewindow_max})'
        elif self.loc_type == LocType.INT:
            return f'TransportationRequest(request_id={dereference(self._utranspreq._req_int).request_id}, ' \
                   f'creation_timestamp={dereference(self._utranspreq._req_int).creation_timestamp}, ' \
                   f'origin={dereference(self._utranspreq._req_int).origin}, ' \
                   f'destination={dereference(self._utranspreq._req_int).destination}, ' \
                   f'pickup_timewindow_min={dereference(self._utranspreq._req_int).pickup_timewindow_min}, ' \
                   f'pickup_timewindow_max={dereference(self._utranspreq._req_int).pickup_timewindow_max}, ' \
                   f'delivery_timewindow_min={dereference(self._utranspreq._req_int).delivery_timewindow_min}, ' \
                   f'delivery_timewindow_max={dereference(self._utranspreq._req_int).delivery_timewindow_max})'
        else:
            raise ValueError("This line should never have been reached")

    # TODO: Need to expose the properties origin, destination, (pickup|delivery)_timewindow_(min|max)

    property origin:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).origin
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).origin
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).origin = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).origin = value
            else:
                raise ValueError("This line should never have been reached")


    property destination:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).destination
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).destination
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).destination = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).destination = value
            else:
                raise ValueError("This line should never have been reached")



    property pickup_timewindow_min:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).pickup_timewindow_min
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).pickup_timewindow_min
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).pickup_timewindow_min = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).pickup_timewindow_min = value
            else:
                raise ValueError("This line should never have been reached")



    property pickup_timewindow_max:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).pickup_timewindow_max
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).pickup_timewindow_max
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).pickup_timewindow_max = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).pickup_timewindow_max = value
            else:
                raise ValueError("This line should never have been reached")


    property delivery_timewindow_min:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).delivery_timewindow_min
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).delivery_timewindow_min
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).delivery_timewindow_min = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).delivery_timewindow_min = value
            else:
                raise ValueError("This line should never have been reached")



    property delivery_timewindow_max:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._utranspreq._req_r2loc).delivery_timewindow_max
            elif self.loc_type == LocType.INT:
                return dereference(self._utranspreq._req_int).delivery_timewindow_max
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._utranspreq._req_r2loc).delivery_timewindow_max = value
            elif self.loc_type == LocType.INT:
                dereference(self._utranspreq._req_int).delivery_timewindow_max = value
            else:
                raise ValueError("This line should never have been reached")

    @staticmethod
    cdef TransportationRequest from_c_r2loc(shared_ptr[CTransportationRequest[R2loc]] creq):
        cdef TransportationRequest req = TransportationRequest.__new__(TransportationRequest)
        req._utranspreq._req_r2loc = creq
        req._ureq._req_r2loc = dynamic_pointer_cast[CRequest[R2loc], CTransportationRequest[R2loc]](creq)
        req.loc_type = LocType.R2LOC
        return req

    @staticmethod
    cdef TransportationRequest from_c_int(shared_ptr[CTransportationRequest[int]] creq):
        cdef TransportationRequest req = TransportationRequest.__new__(TransportationRequest)
        req._utranspreq._req_int = creq
        req._ureq._req_int = dynamic_pointer_cast[CRequest[int], CTransportationRequest[int]](creq)
        req.loc_type = LocType.R2LOC
        return req


    def __dealloc__(self):
        # using unique_ptr's so no deletion
        pass


cdef class InternalRequest(Request):
    def __init__(
            self, int request_id, float creation_timestamp,
            location
    ):
        if hasattr(location, '__len__') and len(location) == 2:
            # TODO: this inferring of LocType is kludgy. We should have it as an argument of __init__
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self._uinternreq._req_r2loc = shared_ptr[CInternalRequest[R2loc]](new CInternalRequest[R2loc](
                request_id, creation_timestamp, location
            ))
            self._ureq._req_r2loc = dynamic_pointer_cast[CRequest[R2loc], CInternalRequest[R2loc]](self._uinternreq._req_r2loc)
        elif isinstance(location, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self._uinternreq._req_int = shared_ptr[CInternalRequest[int]](new CInternalRequest[int](
                request_id, creation_timestamp, location
            ))
            self._ureq._req_int = dynamic_pointer_cast[CRequest[int], CInternalRequest[int]](self._uinternreq._req_int)

        else:
            raise TypeError(f"Cannot handle origin of type {type(location)}")


    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f'InternalRequest(request_id={dereference(self._uinternreq._req_r2loc).request_id}, ' \
                   f'creation_timestamp={dereference(self._uinternreq._req_r2loc).creation_timestamp}, ' \
                   f'location={dereference(self._uinternreq._req_r2loc).location})'
        elif self.loc_type == LocType.INT:
            return f'InternalRequest(request_id={dereference(self._uinternreq._req_int).request_id}, ' \
                   f'creation_timestamp={dereference(self._uinternreq._req_int).creation_timestamp}, ' \
                   f'location={dereference(self._uinternreq._req_int).location})'
        else:
            raise ValueError("This line should never have been reached")

    property location:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._uinternreq._req_r2loc).location
            elif self.loc_type == LocType.INT:
                return dereference(self._uinternreq._req_int).location
            else:
                raise ValueError("This line should never have been reached")
        def __set__(self, value):
            if self.loc_type == LocType.R2LOC:
                dereference(self._uinternreq._req_r2loc).location = value
            elif self.loc_type == LocType.INT:
                dereference(self._uinternreq._req_int).location = value
            else:
                raise ValueError("This line should never have been reached")

    @staticmethod
    cdef InternalRequest from_c_r2loc(shared_ptr[CInternalRequest[R2loc]] creq):
        cdef InternalRequest req = InternalRequest.__new__(InternalRequest)
        req._uinternreq._req_r2loc = creq
        req._ureq._req_r2loc = dynamic_pointer_cast[CRequest[R2loc], CInternalRequest[R2loc]](creq)
        req.loc_type = LocType.R2LOC
        return req

    @staticmethod
    cdef InternalRequest from_c_int(shared_ptr[CInternalRequest[int]] creq):
        cdef InternalRequest req = InternalRequest.__new__(InternalRequest)
        req._uinternreq._req_int = creq
        req._ureq._req_int = dynamic_pointer_cast[CRequest[int], CInternalRequest[int]](creq)
        req.loc_type = LocType.R2LOC
        return req


    def __dealloc__(self):
        # using shared_ptr's so no deletion
        pass

cdef class Stop:
    def __cinit__(self):
        pass

    def __init__(
            self, location, Request request,
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
            return f'Stop(location={self.ustop._stop_r2loc.location}, '\
                   f'request={self.request}, ' \
                   f'estimated_arrival_time={self.ustop._stop_r2loc.estimated_arrival_time}, ' \
                   f'action={StopAction(self.ustop._stop_r2loc.action).name}, ' \
                   f'time_window_min={self.ustop._stop_r2loc.time_window_min}, '\
                   f'time_window_max={self.ustop._stop_r2loc.time_window_max})'
        elif self.loc_type == LocType.INT:
            return f'Stop(location={self.ustop._stop_int.location}, '\
                   f'request={self.request}, ' \
                   f'estimated_arrival_time={self.ustop._stop_int.estimated_arrival_time}, ' \
                   f'action={StopAction(self.ustop._stop_int.action).name}, ' \
                   f'time_window_min={self.ustop._stop_int.time_window_min}, '\
                   f'time_window_max={self.ustop._stop_int.time_window_max})'
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
            if typeid(dereference(self.ustop._stop_r2loc.request)) == typeid(CTransportationRequest[R2loc]):
                return TransportationRequest.from_c_r2loc(
                    dynamic_pointer_cast[CTransportationRequest[R2loc], CRequest[R2loc]](self.ustop._stop_r2loc.request))
            elif typeid(dereference(self.ustop._stop_r2loc.request)) == typeid(CInternalRequest[R2loc]):
                return InternalRequest.from_c_r2loc(
                    dynamic_pointer_cast[CInternalRequest[R2loc], CRequest[R2loc]](self.ustop._stop_r2loc.request))
            else:
                raise ValueError("This line should never have been reached")
        elif self.loc_type == LocType.INT:
            if typeid(dereference(self.ustop._stop_int.request)) == typeid(CTransportationRequest[int]):
                return TransportationRequest.from_c_int(
                    dynamic_pointer_cast[CTransportationRequest[int], CRequest[int]](self.ustop._stop_int.request))
            elif typeid(dereference(self.ustop._stop_int.request)) == typeid(CInternalRequest[int]):
                return InternalRequest.from_c_int(
                    dynamic_pointer_cast[CInternalRequest[int], CRequest[int]](self.ustop._stop_int.request))
            else:
                raise ValueError("This line should never have been reached")
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
    # TODO: May need to allow nice ways of converting a Stoplist to python lists or similar. Use case: calling code
    # doing post optimization
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
                dereference(self.ustoplist._stoplist_r2loc_ptr).push_back((<Stop> py_s).ustop._stop_r2loc)
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
        # TODO: Use smart pointer and get rid of manual del
        if self.ptr_owner:
            # I was not created from an existing c++ pointer ("owned" by another Stoplist object)
            if self.loc_type == LocType.R2LOC:
                del self.ustoplist._stoplist_r2loc_ptr
            elif self.loc_type == LocType.INT:
                del self.ustoplist._stoplist_int_ptr
            else:
                raise ValueError("This line should never have been reached")

