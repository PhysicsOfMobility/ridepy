# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr
from ridepy.data_structures_cython.cdata_structures cimport (
    InsertionResult, TransportationRequest, Stop)
from ridepy.util.spaces_cython.cspaces cimport TransportSpace, Euclidean2D


cdef extern from "cdispatchers.h" namespace 'ridepy':
    InsertionResult[Loc] brute_force_total_traveltime_minimizing_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space, int seat_capacity, bint debug)

    InsertionResult[Loc] simple_ellipse_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space,
          int seat_capacity,
          double max_relative_detour,
          bint debug
    )

    cdef cppclass AbstractDispatcher[Loc]:
        AbstractDispatcher()

    cdef cppclass BruteForceTotalTravelTimeMinimizingDispatcher[Loc](AbstractDispatcher[Loc]):
        BruteForceTotalTravelTimeMinimizingDispatcher()

    cdef cppclass SimpleEllipseDispatcher[Loc](AbstractDispatcher[Loc]):
        SimpleEllipseDispatcher(double)
