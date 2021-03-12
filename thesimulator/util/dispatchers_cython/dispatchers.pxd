# distutils: language=c++

from thesimulator.util.spaces_cython.spaces cimport Euclidean2D, TransportSpace
from thesimulator.data_structures_cython.data_structures cimport TransportationRequest, Stoplist


cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                              TransportSpace space, int seat_capacity)
