# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr
from ridepy.data_structures_cython.cdata_structures cimport (
    InsertionResult, TransportationRequest, Stop)
from ridepy.util.spaces_cython.cspaces cimport TransportSpace, Euclidean2D


cdef extern from "cdispatchers.h" namespace 'cstuff':
    InsertionResult[Loc] brute_force_total_traveltime_minimizing_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space, int seat_capacity, bint debug)

    InsertionResult[Loc] zero_detour_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space, int seat_capacity, bint debug)
