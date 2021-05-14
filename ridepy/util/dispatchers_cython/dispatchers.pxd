# distutils: language=c++

from ridepy.util.spaces_cython.spaces cimport TransportSpace
from ridepy.data_structures_cython.data_structures cimport TransportationRequest, Stoplist
from ridepy.util.dispatchers_cython.cdispatchers cimport ExternalCost

cpdef brute_force_total_traveltime_minimizing_dispatcher(
        TransportationRequest cy_request,
        Stoplist stoplist,
        TransportSpace space,
        int seat_capacity,
        ExternalCost external_cost=*,
        bint debug=*
)

cpdef zero_detour_dispatcher(
        TransportationRequest cy_request,
        Stoplist stoplist,
        TransportSpace space,
        int seat_capacity,
        bint debug=*
)
