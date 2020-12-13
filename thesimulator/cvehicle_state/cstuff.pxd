# distutils: language=c++
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.utility cimport tuple as ctuple
from thesimulator.util.cspaces.cspaces cimport Euclidean2D, TransportSpace

cdef extern from "cstuff.cpp":
    pass



cdef extern from "cstuff.h" namespace 'cstuff':

    InsertionResult brute_force_distance_minimizing_dispatcher(
    Request& request,
    Stoplist& stoplist,
    TransportSpace& space
    )