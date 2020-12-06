# distutils: language = c++

from .cstuff cimport (
    Request as CRequest,
    Stop as CStop,
    Euclidean2D as CEuclidean2D,
    Stoplist as CStoplist,
)

cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

cdef class Euclidean2D:
    cdef CEuclidean2D c_euclidean2d

cdef class Request:
    cdef CRequest c_req
    @staticmethod
    cdef Request from_c(CRequest creq)

cdef class Stop:
    cdef CStop c_stop
    @staticmethod
    cdef Stop from_c(CStop cstop)

cdef class Stoplist:
    cdef CStoplist* c_stoplist_ptr
    cdef bint ptr_owner
    @staticmethod
    cdef Stoplist from_ptr(CStoplist *cstoplist_ptr)

