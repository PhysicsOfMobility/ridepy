# distutils: language = c++

from libcpp.vector cimport vector


from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    TransportationRequest as CTransportationRequest,
    InternalRequest as CInternalRequest,
    Stop as CStop,
    R2loc
)

cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

cpdef enum class LocType:
    R2LOC  = 1
    INT = 2

cdef union _URequest:
    CRequest[R2loc]* _req_r2loc
    CRequest[int]* _req_int

cdef union _UStop:
    CStop[R2loc] _stop_r2loc
    CStop[int] _stop_int

cdef union _UStoplist:
    vector[CStop[R2loc]]* _stoplist_r2loc_ptr
    vector[CStop[int]]* _stoplist_int_ptr


cdef class Request:
    cdef _URequest _ureq
    cdef LocType loc_type
    @staticmethod
    cdef Request from_c_r2loc(CRequest[R2loc] *creq)
    @staticmethod
    cdef Request from_c_int(CRequest[int] *creq)

cdef class TransportationRequest(Request):
    pass

cdef class Stop:
    cdef _UStop ustop
    cdef LocType loc_type
    @staticmethod
    cdef Stop from_c_r2loc(CStop[R2loc] cstop)
    @staticmethod
    cdef Stop from_c_int(CStop[int] cstop)


cdef class Stoplist:
    cdef bint ptr_owner
    cdef LocType loc_type
    cdef _UStoplist ustoplist
    cdef Stop py_s
    @staticmethod
    cdef Stoplist from_c_r2loc(vector[CStop[R2loc]] *cstoplist_ptr)
    @staticmethod
    cdef Stoplist from_c_int(vector[CStop[int]] *cstoplist_ptr)
