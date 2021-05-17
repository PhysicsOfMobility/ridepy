# distutils: language=c++

from ridepy.util.spaces_cython.spaces cimport Euclidean2D, TransportSpace
from ridepy.data_structures_cython.data_structures cimport TransportationRequest, Stoplist


cpdef brute_force_total_traveltime_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                              TransportSpace space, int seat_capacity, bint debug=*)

cpdef zero_detour_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                              TransportSpace space, int seat_capacity, double detour=*, bint debug=*)
