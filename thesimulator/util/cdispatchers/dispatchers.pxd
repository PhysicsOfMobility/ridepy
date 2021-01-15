# distutils: language=c++

from thesimulator.util.cspaces.spaces cimport Euclidean2D, TransportSpace
from thesimulator.cdata_structures.data_structures cimport TransportationRequest, Stoplist


cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                              TransportSpace space)
