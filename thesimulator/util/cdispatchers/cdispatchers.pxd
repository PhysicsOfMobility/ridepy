# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr
from thesimulator.cdata_structures.cdata_structures cimport (
    InsertionResult, TransportationRequest, Stop)
from thesimulator.util.cspaces.cspaces cimport TransportSpace, Euclidean2D

#cdef extern from "cdispatchers.cpp":
#    pass

#cdef extern from "cdispatchers_utils.cpp":
#    pass

cdef extern from "cdispatchers.h" namespace 'cstuff':
    InsertionResult[Loc] brute_force_distance_minimizing_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space)
