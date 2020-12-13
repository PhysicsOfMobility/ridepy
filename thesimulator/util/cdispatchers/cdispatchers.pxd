# distutils: language=c++

from libcpp.vector cimport vector
from thesimulator.cdata_structures.cdata_structures cimport (
    InsertionResult, Request, Stop)
from thesimulator.util.cspaces.cspaces cimport TransportSpace

cdef extern from "cdispatchers.h" namespace 'cstuff':
    InsertionResult brute_force_distance_minimizing_dispatcher(
    const Request &request,
          vector[Stop] &stoplist,
          const TransportSpace &space)
