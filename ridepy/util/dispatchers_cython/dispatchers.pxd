# distutils: language=c++

from .cdispatchers cimport (
    AbstractDispatcher as CAbstractDispatcher,
    BruteForceTotalTravelTimeMinimizingDispatcher as CBruteForceTotalTravelTimeMinimizingDispatcher,
    SimpleEllipseDispatcher as CSimpleEllipseDispatcher,
)

from ridepy.util.spaces_cython.spaces cimport Euclidean2D, TransportSpace
from ridepy.data_structures_cython.data_structures cimport TransportationRequest, Stoplist

from ridepy.data_structures_cython.data_structures cimport LocType, R2loc


cpdef simple_ellipse_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                              TransportSpace space, int seat_capacity, double max_relative_detour=*, bint debug=*)

cdef union UDispatcher:
    CAbstractDispatcher[R2loc] *dispatcher_r2loc_ptr
    CAbstractDispatcher[int] *dispatcher_int_ptr

cdef class Dispatcher:
    cdef UDispatcher u_dispatcher
    cdef readonly LocType loc_type