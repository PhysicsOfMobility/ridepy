# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.utility cimport tuple as ctuple
from cython.operator cimport dereference

from thesimulator.util.cspaces.spaces cimport Euclidean2D
from thesimulator.cdata_structures.data_structures cimport TransportationRequest, Stoplist
from thesimulator.cdata_structures.cdata_structures cimport InsertionResult
from thesimulator.util.cdispatchers.cdispatchers cimport \
    brute_force_distance_minimizing_dispatcher as c_brute_force_distance_minimizing_dispatcher


cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               Euclidean2D space)
