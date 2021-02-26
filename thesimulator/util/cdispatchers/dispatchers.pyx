# distutils: language=c++

from cython.operator cimport dereference
from libcpp.memory cimport dynamic_pointer_cast

from thesimulator.util.cspaces.spaces cimport Euclidean2D, TransportSpace
from thesimulator.cdata_structures.data_structures cimport TransportationRequest, Stoplist, LocType, R2loc
from thesimulator.cdata_structures.cdata_structures cimport InsertionResult, \
    TransportationRequest as CTransportationRequest, \
    Request as CRequest
from thesimulator.util.cdispatchers.cdispatchers cimport \
    brute_force_distance_minimizing_dispatcher as c_brute_force_distance_minimizing_dispatcher

# Just like we did in cdata_structures.Stop, we would have liked to have an union holding
# InsertionResult[R2loc] and InsertionResult[int] inside brute_force_distance_minimizing_dispatcher. However,
# that is nontrivial because any non-POD union member needs to have explicitly defined constructor and copy constructor
# (https://en.wikipedia.org/wiki/C%2B%2B11#Unrestricted_unions). Hence, the following union does *not* work, and we
# need to store two InsertionResult objects (one for each type) inside brute_force_distance_minimizing_dispatcher
#cdef union _UInsertionResult:
#     InsertionResult[R2loc] insertion_result_r2loc
#     InsertionResult[int] insertion_result_int

# This cpdef is crucial, otherwise we can't use this function from both python  and cython
cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               TransportSpace space):
    cdef InsertionResult[R2loc] insertion_result_r2loc
    cdef InsertionResult[int] insertion_result_int
    if cy_request.loc_type == LocType.R2LOC:
        insertion_result_r2loc = c_brute_force_distance_minimizing_dispatcher[R2loc](
            dynamic_pointer_cast[CTransportationRequest[R2loc], CRequest[R2loc]](cy_request._ureq._req_r2loc),
            dereference(stoplist.ustoplist._stoplist_r2loc_ptr),
            dereference(space.u_space.space_r2loc_ptr)
        )
        return insertion_result_r2loc.min_cost, Stoplist.from_c_r2loc(&insertion_result_r2loc.new_stoplist),\
               (insertion_result_r2loc.EAST_pu, insertion_result_r2loc.LAST_pu,
                insertion_result_r2loc.EAST_do, insertion_result_r2loc.LAST_do)
    elif cy_request.loc_type == LocType.INT:
        insertion_result_int = c_brute_force_distance_minimizing_dispatcher[int](
            dynamic_pointer_cast[CTransportationRequest[int], CRequest[int]](cy_request._ureq._req_int),
            dereference(stoplist.ustoplist._stoplist_int_ptr),
            dereference(space.u_space.space_int_ptr)
        )
        return insertion_result_int.min_cost, Stoplist.from_c_int(&insertion_result_int.new_stoplist),\
               (insertion_result_int.EAST_pu, insertion_result_int.LAST_pu,
                insertion_result_int.EAST_do, insertion_result_int.LAST_do)
    else:
        raise ValueError("This line should never have been reached")


