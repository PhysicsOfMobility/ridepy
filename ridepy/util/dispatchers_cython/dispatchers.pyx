# distutils: language=c++
# distutils: libraries = ortools pthread

from cython.operator cimport dereference
from libcpp.memory cimport dynamic_pointer_cast
from libcpp.vector cimport vector

from ridepy.util.spaces_cython.spaces cimport Euclidean2D, TransportSpace
from ridepy.data_structures_cython.data_structures cimport TransportationRequest, Stoplist, LocType, R2loc
from ridepy.data_structures_cython.cdata_structures cimport InsertionResult, \
    TransportationRequest as CTransportationRequest, \
    Request as CRequest, \
    Stop as CStop
from ridepy.util.dispatchers_cython.cdispatchers cimport \
    brute_force_total_traveltime_minimizing_dispatcher as c_brute_force_total_traveltime_minimizing_dispatcher, \
    simple_ellipse_dispatcher as c_simple_ellipse_dispatcher, \
    optimize_stoplists as c_optimize_stoplists

# Just like we did in data_structures_cython.Stop, we would have liked to have an union holding
# InsertionResult[R2loc] and InsertionResult[int] inside brute_force_total_traveltime_minimizing_dispatcher. However,
# that is nontrivial because any non-POD union member needs to have explicitly defined constructor and copy constructor
# (https://en.wikipedia.org/wiki/C%2B%2B11#Unrestricted_unions). Hence, the following union does *not* work, and we
# need to store two InsertionResult objects (one for each type) inside brute_force_total_traveltime_minimizing_dispatcher
#cdef union _UInsertionResult:
#     InsertionResult[R2loc] insertion_result_r2loc
#     InsertionResult[int] insertion_result_int

# This cpdef is crucial, otherwise we can't use this function from both python  and cython
cpdef brute_force_total_traveltime_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               TransportSpace space, int seat_capacity, bint debug=False):
    cdef InsertionResult[R2loc] insertion_result_r2loc
    cdef InsertionResult[int] insertion_result_int
    if cy_request.loc_type == LocType.R2LOC:
        insertion_result_r2loc = c_brute_force_total_traveltime_minimizing_dispatcher[R2loc](
            dynamic_pointer_cast[CTransportationRequest[R2loc], CRequest[R2loc]](cy_request._ureq._req_r2loc),
            stoplist.ustoplist._stoplist_r2loc,
            dereference(space.u_space.space_r2loc_ptr), seat_capacity, debug
        )
        return insertion_result_r2loc.min_cost, Stoplist.from_c_r2loc(insertion_result_r2loc.new_stoplist),\
               (insertion_result_r2loc.EAST_pu, insertion_result_r2loc.LAST_pu,
                insertion_result_r2loc.EAST_do, insertion_result_r2loc.LAST_do)
    elif cy_request.loc_type == LocType.INT:
        insertion_result_int = c_brute_force_total_traveltime_minimizing_dispatcher[int](
            dynamic_pointer_cast[CTransportationRequest[int], CRequest[int]](cy_request._ureq._req_int),
            stoplist.ustoplist._stoplist_int,
            dereference(space.u_space.space_int_ptr), seat_capacity, debug
        )
        return insertion_result_int.min_cost, Stoplist.from_c_int(insertion_result_int.new_stoplist),\
               (insertion_result_int.EAST_pu, insertion_result_int.LAST_pu,
                insertion_result_int.EAST_do, insertion_result_int.LAST_do)
    else:
        raise ValueError("This line should never have been reached")


cpdef simple_ellipse_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               TransportSpace space, int seat_capacity, double max_relative_detour=0, bint debug=False):
    cdef InsertionResult[R2loc] insertion_result_r2loc
    cdef InsertionResult[int] insertion_result_int
    if cy_request.loc_type == LocType.R2LOC:
        insertion_result_r2loc = c_simple_ellipse_dispatcher[R2loc](
            dynamic_pointer_cast[CTransportationRequest[R2loc], CRequest[R2loc]](cy_request._ureq._req_r2loc),
            stoplist.ustoplist._stoplist_r2loc,
            dereference(space.u_space.space_r2loc_ptr), seat_capacity, max_relative_detour, debug
        )
        return insertion_result_r2loc.min_cost, Stoplist.from_c_r2loc(insertion_result_r2loc.new_stoplist),\
               (insertion_result_r2loc.EAST_pu, insertion_result_r2loc.LAST_pu,
                insertion_result_r2loc.EAST_do, insertion_result_r2loc.LAST_do)
    elif cy_request.loc_type == LocType.INT:
        insertion_result_int = c_simple_ellipse_dispatcher[int](
            dynamic_pointer_cast[CTransportationRequest[int], CRequest[int]](cy_request._ureq._req_int),
            stoplist.ustoplist._stoplist_int,
            dereference(space.u_space.space_int_ptr), seat_capacity, max_relative_detour, debug
        )
        return insertion_result_int.min_cost, Stoplist.from_c_int(insertion_result_int.new_stoplist),\
               (insertion_result_int.EAST_pu, insertion_result_int.LAST_pu,
                insertion_result_int.EAST_do, insertion_result_int.LAST_do)
    else:
        raise ValueError("This line should never have been reached")


def optimize_stoplists(stoplists,
                       TransportSpace space,
                       vector[int] seat_capacities,
                       double current_time=0,
                       double time_resolution=1e-8):
    cdef vector[vector[CStop[R2loc]]] c_stoplists_old_r2loc
    cdef vector[vector[CStop[R2loc]]] c_stoplists_new_r2loc
    cdef vector[vector[CStop[int]]] c_stoplists_old_int
    cdef vector[vector[CStop[int]]] c_stoplists_new_int

    if space.loc_type == LocType.R2LOC:
        for stoplist in stoplists:
            c_stoplists_old_r2loc.push_back((<Stoplist>stoplist).ustoplist._stoplist_r2loc)

        c_stoplists_new_r2loc = c_optimize_stoplists[R2loc](
                    c_stoplists_old_r2loc,
                    dereference(space.u_space.space_r2loc_ptr),
                    seat_capacities, current_time, time_resolution)
        return [Stoplist.from_c_r2loc(sl) for sl in c_stoplists_new_r2loc]

    if space.loc_type == LocType.INT:
        for stoplist in stoplists:
            c_stoplists_old_int.push_back((<Stoplist>stoplist).ustoplist._stoplist_int)

        c_stoplists_new_int = c_optimize_stoplists[int](
                    c_stoplists_old_int,
                    dereference(space.u_space.space_int_ptr),
                    seat_capacities, current_time, time_resolution)
        return [Stoplist.from_c_int(sl) for sl in c_stoplists_new_int]
    else:
        raise ValueError("This line should never have been reached")