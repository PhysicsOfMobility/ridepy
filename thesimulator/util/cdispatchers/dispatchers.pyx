# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.utility cimport tuple as ctuple
from cython.operator cimport dereference

from thesimulator.util.cspaces.spaces cimport Euclidean2D, TransportSpace
from thesimulator.cdata_structures.data_structures cimport TransportationRequest, Stoplist
from thesimulator.cdata_structures.cdata_structures cimport InsertionResult
from thesimulator.util.cdispatchers.cdispatchers cimport \
    brute_force_distance_minimizing_dispatcher as c_brute_force_distance_minimizing_dispatcher

#cdef extern from "cstuff.cpp":
#    pass

# This cpdef is crucial, otherwise we can't use this function from both python  and cython
cpdef brute_force_distance_minimizing_dispatcher(TransportationRequest cy_request, Stoplist stoplist,
                                               TransportSpace space):
    cdef InsertionResult res = c_brute_force_distance_minimizing_dispatcher(
            cy_request.c_req,
            dereference(stoplist.c_stoplist_ptr),
            dereference(space.c_space_ptr)
        )
    return res.min_cost, Stoplist.from_ptr(&res.new_stoplist), (res.EAST_pu, res.LAST_pu, res.EAST_do, res.LAST_do)




