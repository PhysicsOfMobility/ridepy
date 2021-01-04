# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.utility cimport tuple as ctuple
from cython.operator cimport dereference

from thesimulator.util.cspaces.spaces cimport Euclidean2D, TransportSpace
from thesimulator.cdata_structures.data_structures cimport TransportationRequest, Stoplist, LocType, R2loc
from thesimulator.cdata_structures.cdata_structures cimport InsertionResult
from thesimulator.util.cdispatchers.cdispatchers cimport \
    brute_force_distance_minimizing_dispatcher as c_brute_force_distance_minimizing_dispatcher

#cdef extern from "cstuff.cpp":
#    pass


cdef union _UInsertionResult:
     InsertionResult[R2loc] insertion_result_r2loc
     InsertionResult[int] insertion_result_int

# This cpdef is crucial, otherwise we can't use this function from both python  and cython
cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               TransportSpace space):
    cdef InsertionResult[R2loc] insertion_result_r2loc
    cdef InsertionResult[int] insertion_result_int
    if cy_request.loc_type == LocType.R2LOC:
        insertion_result_r2loc = c_brute_force_distance_minimizing_dispatcher[R2loc](
            cy_request._ureq._req_r2loc,
            dereference(stoplist.ustoplist._stoplist_r2loc_ptr),
            dereference(space.c_space_ptr)
        )
        return insertion_result_r2loc.min_cost, Stoplist.from_c_r2loc(&insertion_result_r2loc.new_stoplist),\
               (insertion_result_r2loc.EAST_pu, insertion_result_r2loc.LAST_pu,
                insertion_result_r2loc.EAST_do, insertion_result_r2loc.LAST_do)
    elif cy_request.loc_type == LocType.INT:
        insertion_result_int = c_brute_force_distance_minimizing_dispatcher[int](
            cy_request._ureq._req_int,
            dereference(stoplist.ustoplist._stoplist_int_ptr),
            dereference(space.c_space_ptr)
        )
        return insertion_result_int.min_cost, Stoplist.from_c_int(&insertion_result_int.new_stoplist),\
               (insertion_result_int.EAST_pu, insertion_result_int.LAST_pu,
                insertion_result_int.EAST_do, insertion_result_int.LAST_do)
    else:
        raise ValueError("This line should never have been reached")




