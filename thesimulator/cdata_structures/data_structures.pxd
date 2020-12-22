# distutils: language = c++

from libcpp.vector cimport vector


from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    R2loc,
    Stop as CStop,
)

cdef extern from "cdata_structures.cpp":
    pass

cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3


cdef class TransportationRequestBase:
    pass

cdef class TransportationRequestR2loc(TransportationRequestBase):
    cdef CRequest[R2loc] c_req
    @staticmethod
    cdef TransportationRequestR2loc from_c(CRequest[R2loc] creq)


cdef class StopBase:
    pass

cdef class StopR2loc(StopBase):
    cdef CStop[R2loc] c_stop
    @staticmethod
    cdef StopR2loc from_c(CStop[R2loc] cstop)


cdef class StoplistBase:
    cdef double *c_stoplist_ptr

cdef class StoplistR2loc(StoplistBase):
    cdef vector[CStop[R2loc]] *c_stoplist_ptr
    cdef bint ptr_owner
    @staticmethod
    cdef StoplistR2loc from_ptr(vector[CStop[R2loc]] *cstoplist_ptr)

