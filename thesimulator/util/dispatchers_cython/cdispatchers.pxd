# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr
from thesimulator.data_structures_cython.data_structures_cython cimport (
    InsertionResult, TransportationRequest, Stop)
from thesimulator.util.spaces_cython.spaces_cython cimport TransportSpace, Euclidean2D

#cdef extern from "dispatchers_cython.cpp":
#    pass

#cdef extern from "dispatchers_cython_utils.cpp":
#    pass

cdef extern from "dispatchers_cython.h" namespace 'cstuff':
    InsertionResult[Loc] brute_force_distance_minimizing_dispatcher[Loc](
          shared_ptr[TransportationRequest[Loc]] request,
          vector[Stop[Loc]] &stoplist,
          const TransportSpace &space)
