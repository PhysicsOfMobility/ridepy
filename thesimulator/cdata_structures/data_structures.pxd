# distutils: language = c++

from libcpp.vector cimport vector


from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    Stop as CStop,
    Stoplist as CStoplist,
)


cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

cdef class TransportationRequest:
    cdef CRequest c_req
    @staticmethod
    cdef TransportationRequest from_c(CRequest creq)

cdef class Stop:
    cdef CStop c_stop
    @staticmethod
    cdef Stop from_c(CStop cstop)

cdef class Stoplist:
    cdef CStoplist* c_stoplist_ptr
    cdef bint ptr_owner
    @staticmethod
    cdef Stoplist from_ptr(CStoplist *cstoplist_ptr)

