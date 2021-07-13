# distutils: language = c++
"""
This cython module wraps the struct templates exposed from C++ by data_structures_cython.pxd into extension types.
However an extension type obviously cannot be templated (at compile time, all possible variations of a template
must be known). There is no really elegant way of doing it in cython as of v3.0a6. So we will use the [Explicit
Run-Time Dispatch approach](https://martinralbrecht.wordpress.com/2017/07/23/adventures-in-cython-templating/).

In short, an enum LocType (resides in data_structures.pxd) contains all template types Loc we are likely to need.
The extension dtype for C++ object e.g. CRequest[Loc] then will contain *an union* holding one of the variants (e.g.
CRequest[int], Request[tuple(double, double)]) etc. Then each member function will check the Loc type, and dispatch the
method call to the appropriate object inside that union.
"""

from numpy import inf

from cython.operator cimport dereference
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, make_shared
from libcpp.memory cimport dynamic_pointer_cast
from cython.operator cimport typeid


from ridepy.data_structures_cython.cdata_structures cimport (
    Request as CRequest,
    TransportationRequest as CTransportationRequest,
    InternalRequest as CInternalRequest,
    Stop as CStop,
    R2loc,
)


import logging
logger = logging.getLogger(__name__)

cdef class Request:
    """
    The base class, never to be instantiated.
    """
    def asdict(self):
        return dict(
            request_id=self.request_id,
            creation_timestamp=self.creation_timestamp,
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{k}={v}" for k, v in self.asdict().items()) + ")"

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
    """
    Cython equivalent of pure python dataclass :class:`.data_structures.TransportationRequest`. See its docstring for
    details of its attributes.

    .. admonition:: Implementation details for developers

       Wraps the C++ templated struct `data_structures_cython.cdata_structures.pxd::TransportationRequest[Loc]` into a
       cython extension type. The template parameter `Loc` defines the type of location objects (`Tuple[float, float]`
       for simulations in :math:`\mathbb{R}^2`), `int` for graphs.

       However a cython extension type obviously cannot be templated (at compile time, all possible variations of a template
       must be known). So we will use the Explicit Run-Time Dispatch approach, see this module's docstring or :ref:`desc_runtime_dispatch`
       for details.

       Holds a `shared_ptr` to C++ templated class `TransportationRequest<Loc>`. This class can be instantiated from an
       existing `shared_ptr` (only from the cython side and not from the calling python code). See the staticmethods
       `cdef TransportationRequest from_c_r2loc` and `cdef TransportationRequest from_c_int` for details.
    """
    def __init__(
            self,
            int request_id,
            double creation_timestamp,
            origin,
            destination,
            pickup_timewindow_min=0,
            pickup_timewindow_max=inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=inf,
    ):
        """
        Note
        ----
        We will try to infer `Loc` from what `origin` contains. The inference can be easily
        fooled by passing e.g. `origin = 2, destination = (0.3, 1.5)`.
        """
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

    def asdict(self):
        """
        Returns a dict representation of itself.
        """
        return dict(
            request_id=self.request_id,
            creation_timestamp=self.creation_timestamp,
            origin=self.origin,
            destination=self.destination,
            pickup_timewindow_min=self.pickup_timewindow_min,
            pickup_timewindow_max=self.pickup_timewindow_max,
            delivery_timewindow_min=self.delivery_timewindow_min,
            delivery_timewindow_max=self.delivery_timewindow_max
        )

    def __eq__(self, other: TransportationRequest):
        if not isinstance(other, TransportationRequest):
            return False
        return self.request_id == other.request_id \
            and self.loc_type == other.loc_type \
            and self.creation_timestamp == other.creation_timestamp \
            and self.origin == other.origin \
            and self.destination == other.destination \
            and self.pickup_timewindow_min == other.pickup_timewindow_min \
            and self.pickup_timewindow_max == other.pickup_timewindow_max \
            and self.delivery_timewindow_min == other.delivery_timewindow_min \
            and self.delivery_timewindow_max == other.delivery_timewindow_max

    def __repr__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{k}={v}" for k, v in self.asdict().items()) + ")"


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
        req.loc_type = LocType.INT
        return req


    def __dealloc__(self):
        # using unique_ptr's so no deletion
        pass

    def __reduce__(self):
        return self.__class__, \
            (
                self.request_id,
                self.creation_timestamp,
                self.origin,
                self.destination,
                self.pickup_timewindow_min,
                self.pickup_timewindow_max,
                self.delivery_timewindow_min,
                self.delivery_timewindow_max
            )

cdef class InternalRequest(Request):
    """
    Cython equivalent of pure python dataclass :class:`.data_structures.InternalRequest`. See its docstring for details
    of its attributes.

    .. admonition:: Implementation details for developers

       Wraps the C++ templated struct `data_structures_cython.cdata_structures.pxd::InternalRequest[Loc]` into a cython
       extension type. The template parameter `Loc` defines the type of location objects (`Tuple[float, float]` for
       simulations in :math:`\mathbb{R}^2`), `int` for graphs.

       However a cython extension type obviously cannot be templated (at compile time, all possible variations of a template
       must be known). So we will use the Explicit Run-Time Dispatch approach, see this module's docstring or
       :ref:`desc_runtime_dispatch` for details.

       Holds a `shared_ptr` to C++ templated class `InternalRequest<Loc>`. This class can be instantiated from an
       existing `shared_ptr` (only from the cython side and not from the calling python code). See the staticmethods
       `cdef InternalRequest from_c_r2loc` and `cdef InternalRequest from_c_int` for details.
    """
    def __init__(
            self, int request_id, double creation_timestamp,
            location
    ):
        """
        Note
        ----
        We will try to infer `Loc` from what `location` contains.
        """
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


    def __eq__(self, other: InternalRequest):
        if not isinstance(other, InternalRequest):
            return False
        return self.request_id == other.request_id \
            and self.loc_type == other.loc_type \
            and self.creation_timestamp == other.creation_timestamp \
            and self.location == other.location

    def __repr__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{k}={v}" for k, v in self.asdict().items()) + ")"

    def asdict(self):
        return dict(
            request_id=self.request_id,
            creation_timestamp=self.creation_timestamp,
            location=self.location,
        )


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
        req.loc_type = LocType.INT
        return req


    def __dealloc__(self):
        # using shared_ptr's so no deletion
        pass


    def __reduce__(self):
        return self.__class__, \
            (
                self.request_id,
                self.creation_timestamp,
                self.location
            )

cdef class Stop:
    """
    Cython equivalent of pure python dataclass :class:`.data_structures.Stop`. See its docstring for details
    of its attributes.

   .. admonition:: Implementation details for developers

    Wraps the C++ templated struct `data_structures_cython.cdata_structures.pxd::Stop[Loc]` into a cython extension type.
    The template parameter `Loc` defines the type of location objects (`Tuple[float, float]` for simulations in
    :math:`\mathbb{R}^2`), `int` for graphs.

    However a cython extension type obviously cannot be templated (at compile time, all possible variations of a template
    must be known). So we will use the Explicit Run-Time Dispatch approach, see this module's docstring or
    :ref:`desc_runtime_dispatch` for details.

    Holds a pointer to C++ templated class `Stop<Loc>`. This class can be instantiated from an existing pointer (only
    from the cython side and not from the calling python code). See the staticmethods `cdef Stop from_c_r2loc` and
    `cdef Stop from_c_int` for details.
    """
    def __cinit__(self):
        pass

    def __init__(
            self,
            location,
            Request request,
            StopAction action,
            double estimated_arrival_time,
            int occupancy_after_servicing,
            double time_window_min=0,
            double time_window_max=inf,
    ):
        """
        Note
        ----
        We will try to infer the `.LocType` from what `location` contains. Do not pass incompatible combinations like
        a `Request` with `LocType=R2LOC` and `location` of type `int`.
        """
        if hasattr(location, '__len__') and len(location) == 2:
            # let's assume both origin and destination are Tuple[double, double]
            self.loc_type = LocType.R2LOC
            self.ustop._stop_r2loc = new CStop[R2loc](
                location, request._ureq._req_r2loc, action, estimated_arrival_time, occupancy_after_servicing,
                time_window_min, time_window_max)
        elif isinstance(location, int):
            # let's assume both origin and destination are int
            self.loc_type = LocType.INT
            self.ustop._stop_int = new CStop[int](
                location, request._ureq._req_int, action, estimated_arrival_time, occupancy_after_servicing,
                time_window_min, time_window_max)
        else:
            raise ValueError("This line should never have been reached")

    def __eq__(self, other: Stop):
        if not isinstance(other, Stop):
            return False
        return self.location == other.location \
            and self.loc_type == other.loc_type \
            and self.request == other.request \
            and self.action == other.action \
            and self.estimated_arrival_time == other.estimated_arrival_time \
            and self.occupancy_after_servicing == other.occupancy_after_servicing \
            and self.time_window_min == other.time_window_min \
            and self.time_window_max == other.time_window_max


    def __deepcopy__(self, *args, **kwargs):
        return Stop(self.location, self.request, self.action, self.estimated_arrival_time,
                    self.occupancy_after_servicing, self.time_window_min, self.time_window_max)


    def __repr__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{k}={v}" for k, v in self.asdict().items()) + ")"


    def asdict(self):
        return dict(
            location=self.location,
            request=self.request.asdict(),
            estimated_arrival_time=self.estimated_arrival_time,
            action=self.action,
            time_window_min=self.time_window_min,
            time_window_max=self.time_window_max,
            occupancy_after_servicing=self.occupancy_after_servicing,
        )


    property location:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self.ustop._stop_r2loc).location
            elif self.loc_type == LocType.INT:
                return dereference(self.ustop._stop_int).location
            else:
                raise ValueError("This line should never have been reached")

        def __set__(self, loc):
            if self.loc_type == LocType.R2LOC:
                dereference(self.ustop._stop_r2loc).location = loc
            elif self.loc_type == LocType.INT:
                dereference(self.ustop._stop_int).location = loc
            else:
                raise ValueError("This line should never have been reached")

    property occupancy_after_servicing:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self.ustop._stop_r2loc).occupancy_after_servicing
            elif self.loc_type == LocType.INT:
                return dereference(self.ustop._stop_int).occupancy_after_servicing
            else:
                raise ValueError("This line should never have been reached")

        def __set__(self, occ):
            if self.loc_type == LocType.R2LOC:
                dereference(self.ustop._stop_r2loc).occupancy_after_servicing = occ
            elif self.loc_type == LocType.INT:
                dereference(self.ustop._stop_int).occupancy_after_servicing = occ
            else:
                raise ValueError("This line should never have been reached")

    @property
    def request(self):
        if self.loc_type == LocType.R2LOC:
            if typeid(dereference(dereference(self.ustop._stop_r2loc).request)) == typeid(CTransportationRequest[R2loc]):
                return TransportationRequest.from_c_r2loc(
                    dynamic_pointer_cast[CTransportationRequest[R2loc], CRequest[R2loc]](dereference(self.ustop._stop_r2loc).request))
            elif typeid(dereference(dereference(self.ustop._stop_r2loc).request)) == typeid(CInternalRequest[R2loc]):
                return InternalRequest.from_c_r2loc(
                    dynamic_pointer_cast[CInternalRequest[R2loc], CRequest[R2loc]](dereference(self.ustop._stop_r2loc).request))
            else:
                raise ValueError("This line should never have been reached")
        elif self.loc_type == LocType.INT:
            if typeid(dereference(dereference(self.ustop._stop_int).request)) == typeid(CTransportationRequest[int]):
                return TransportationRequest.from_c_int(
                    dynamic_pointer_cast[CTransportationRequest[int], CRequest[int]](dereference(self.ustop._stop_int).request))
            elif typeid(dereference(dereference(self.ustop._stop_int).request)) == typeid(CInternalRequest[int]):
                return InternalRequest.from_c_int(
                    dynamic_pointer_cast[CInternalRequest[int], CRequest[int]](dereference(self.ustop._stop_int).request))
            else:
                raise ValueError("This line should never have been reached")
        else:
            raise ValueError("This line should never have been reached")

    @property
    def action(self):
        if self.loc_type == LocType.R2LOC:
            return StopAction(dereference(self.ustop._stop_r2loc).action)
        elif self.loc_type == LocType.INT:
            return StopAction(dereference(self.ustop._stop_int).action)
        else:
            raise ValueError("This line should never have been reached")

    property estimated_arrival_time:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self.ustop._stop_r2loc).estimated_arrival_time
            elif self.loc_type == LocType.INT:
                return dereference(self.ustop._stop_int).estimated_arrival_time
            else:
                raise ValueError("This line should never have been reached")

        def __set__(self, estimated_arrival_time):
            if self.loc_type == LocType.R2LOC:
                dereference(self.ustop._stop_r2loc).estimated_arrival_time = estimated_arrival_time
            elif self.loc_type == LocType.INT:
                dereference(self.ustop._stop_int).estimated_arrival_time = estimated_arrival_time
            else:
                raise ValueError("This line should never have been reached")

    @property
    def time_window_min(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.ustop._stop_r2loc).time_window_min
        elif self.loc_type == LocType.INT:
            return dereference(self.ustop._stop_int).time_window_min
        else:
            raise ValueError("This line should never have been reached")

    @property
    def time_window_max(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.ustop._stop_r2loc).time_window_max
        elif self.loc_type == LocType.INT:
            return dereference(self.ustop._stop_int).time_window_max
        else:
            raise ValueError("This line should never have been reached")



    @staticmethod
    cdef Stop from_c_r2loc(CStop[R2loc] *cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.ptr_owner = False
        stop.ustop._stop_r2loc = cstop
        stop.loc_type = LocType.R2LOC
        return stop

    @staticmethod
    cdef Stop from_c_int(CStop[int] *cstop):
        cdef Stop stop = Stop.__new__(Stop)
        stop.ptr_owner = False
        stop.ustop._stop_int = cstop
        stop.loc_type = LocType.INT
        return stop

    def __reduce__(self):
        return self.__class__, \
            (
                self.location,
                self.request,
                self.action.value,
                self.estimated_arrival_time,
                self.occupancy_after_servicing,
                self.time_window_min,
                self.time_window_max,
            )

cdef class Stoplist:
    """
    The cythonic equivalent of `.data_structures.Stoplist`, which is just a python list of `.data_structures.Stop`.

    Note
    ----
    An instance of this class doies not support most of the functionalities of python lists, e.g. slicing. Please take a
    look at the available methods. In particular, use `stoplist.remove_nth_elem(int)` instead of `stoplist.pop(int)` or
    `del stoplist[i]`.


    .. admonition:: Implementation details for developers

       Wraps a C++ vector of `data_structures_cython.cdata_structures.pxd::Stop[Loc]` into a cython extension type.
       The template parameter `Loc` defines the type of location objects (`Tuple[float, float]` for simulations in
       :math:`\mathbb{R}^2`), `int` for graphs.

       However a cython extension type obviously cannot be templated (at compile time, all possible variations of a template
       must be known). So we will use the Explicit Run-Time Dispatch approach, see this module's docstring or
       :ref:`desc_runtime_dispatch` for details.

       This class can be instantiated from an existing C++ `vector<Stop>`, only from the cython side and not from the calling
       python code. See the staticmethods `Stoplist from_c_r2loc` and `Stoplist from_c_int` for details.
    """
    # TODO: May need to allow nice ways of converting a Stoplist to python lists or similar. Use case: calling code
    # doing post optimization
    def __init__(self, python_stoplist, loc_type):
        """
        Parameters
        ----------
        python_stoplist
            A python list of :class:`Stop` objects
        loc_type
            The type of location objects, as defined in the enum `.LocType`

        Note
        ----
        Do **not** pass a list of pure pythonic :class:`Stop<.data_structures.Stop>` objects to `__init__`, this will
        lead to a crash. Only pass a list of cython extension :class:`.Stop` objects.

        The `Stop` objects are **copied** here, therefore the original `Stop` objects can safely be garbage collected/
        otherwise deleted.
        """
        self.loc_type = loc_type

        if self.loc_type == LocType.R2LOC:
            self.ustoplist._stoplist_r2loc = vector[CStop[R2loc]](0)
        elif self.loc_type == LocType.INT:
            self.ustoplist._stoplist_int = vector[CStop[int]](0)
        else:
            raise ValueError(f"This line should never have been reached: {type(loc_type)}")

        if loc_type == LocType.R2LOC:
            for py_s in python_stoplist:
                self.ustoplist._stoplist_r2loc.push_back(dereference((<Stop> py_s).ustop._stop_r2loc))
        elif loc_type == LocType.INT:
            for py_s in python_stoplist:
                self.ustoplist._stoplist_int.push_back(dereference((<Stop> py_s).ustop._stop_int))
        else:
            raise ValueError("This line should never have been reached")
        logger.info("Created Stoplist")

    def __getitem__(self, i):
        """
        Works like `list.__getitem__`. Allows indexing by negative integers.
        """
        len_ = self.__len__()
        if 0 <= i < len_:
            i = i
        elif -len_ <= i < 0:
            i = len_+i
        else:
            raise IndexError(f"list index {i} out of range")
        if self.loc_type == LocType.R2LOC:
            return Stop.from_c_r2loc(&self.ustoplist._stoplist_r2loc[i])
        elif self.loc_type == LocType.INT:
            return Stop.from_c_int(&self.ustoplist._stoplist_int[i])
        else:
            raise ValueError("This line should never have been reached")

    def __len__(self):
        """
        Works like `list.__len__`.
        """
        if self.loc_type == LocType.R2LOC:
            return <int> self.ustoplist._stoplist_r2loc.size()
        elif self.loc_type == LocType.INT:
            return <int> self.ustoplist._stoplist_int.size()
        else:
            raise ValueError("This line should never have been reached")

    def remove_nth_elem(self, int n):
        """
        Removes the nth element. Does not return anything.
        """
        if self.loc_type == LocType.R2LOC:
            self.ustoplist._stoplist_r2loc.erase(
                self.ustoplist._stoplist_r2loc.begin()+n
            )
        elif self.loc_type == LocType.INT:
            self.ustoplist._stoplist_int.erase(
                self.ustoplist._stoplist_int.begin()+n
            )
        else:
            raise ValueError("This line should never have been reached")

    @staticmethod
    cdef Stoplist from_c_r2loc(vector[CStop[R2loc]] cstoplist):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist) # Calling __new__ bypasses __init__, see
        # https://cython.readthedocs.io/en/latest/src/userguide/extension_types.html#instantiation-from-existing-c-c-pointers
        stoplist.loc_type = LocType.R2LOC
        stoplist.ustoplist._stoplist_r2loc = cstoplist
        return stoplist

    @staticmethod
    cdef Stoplist from_c_int(vector[CStop[int]] cstoplist):
        cdef Stoplist stoplist = Stoplist.__new__(Stoplist) # Calling __new__ bypasses __init__, see
        # https://cython.readthedocs.io/en/latest/src/userguide/extension_types.html#instantiation-from-existing-c-c-pointers
        stoplist.loc_type = LocType.INT
        stoplist.ustoplist._stoplist_int = cstoplist
        return stoplist

    def __repr__(self):
        if self.loc_type == LocType.R2LOC:
            return f"[{', '.join(repr(Stop.from_c_r2loc(&s)) for s in self.ustoplist._stoplist_r2loc)}]"
        elif self.loc_type == LocType.INT:
            return f"[{', '.join(repr(Stop.from_c_int(&s)) for s in self.ustoplist._stoplist_int)}]"
        else:
            raise ValueError("This line should never have been reached")


    def to_pys(self):
        logger.debug("Converting cython Stoplist to python list")
        if self.loc_type == LocType.R2LOC:
            # According to cython docs, the following should have worked:
            # return list([Stop.from_c_r2loc(&s) for s in self.ustoplist._stoplist_r2loc])
            # However, it doesn't. So we need the more verbose loop:
            res = []
            for idx in range(self.ustoplist._stoplist_r2loc.size()):
                res.append(Stop.from_c_r2loc(&self.ustoplist._stoplist_r2loc[idx]))
            return res
        elif self.loc_type == LocType.INT:
            res = []
            for idx in range(self.ustoplist._stoplist_int.size()):
                res.append(Stop.from_c_int(&self.ustoplist._stoplist_int[idx]))
            return res
        else:
            raise ValueError("This line should never have been reached")

    def __reduce__(self):
        return self.__class__, (self.to_pys(), self.loc_type)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return all(self[i]==other[i] for i in range(len(self)))
