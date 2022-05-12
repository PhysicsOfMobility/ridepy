# distutils: language = c++

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr


from ridepy.data_structures_cython.cdata_structures cimport (
    Request as CRequest,
    TransportationRequest as CTransportationRequest,
    InternalRequest as CInternalRequest,
    Stop as CStop,
    R2loc
)

cdef extern from * namespace 'ridepy':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

cpdef enum class LocType:
    R2LOC  = 1
    INT = 2


cdef union _URequest:
    shared_ptr[CRequest[R2loc]] _req_r2loc
    shared_ptr[CRequest[int]] _req_int

cdef union _UTransportationRequest:
    shared_ptr[CTransportationRequest[R2loc]] _req_r2loc
    shared_ptr[CTransportationRequest[int]] _req_int

cdef union _UInternalRequest:
    shared_ptr[CInternalRequest[R2loc]] _req_r2loc
    shared_ptr[CInternalRequest[int]] _req_int

cdef union _UStop:
    # have to store a pointer otherwise setting attribute from python side does not work
    CStop[R2loc] *_stop_r2loc
    CStop[int] *_stop_int

cdef union _UStoplist:
    vector[CStop[R2loc]] _stoplist_r2loc
    vector[CStop[int]] _stoplist_int


cdef class Request:
    cdef _URequest _ureq
    cdef LocType loc_type

cdef class TransportationRequest(Request):
    cdef _UTransportationRequest _utranspreq
    @staticmethod
    cdef TransportationRequest from_c_r2loc(shared_ptr[CTransportationRequest[R2loc]] creq)
    @staticmethod
    cdef TransportationRequest from_c_int(shared_ptr[CTransportationRequest[int]] creq)

cdef class InternalRequest(Request):
    cdef _UInternalRequest _uinternreq
    @staticmethod
    cdef InternalRequest from_c_r2loc(shared_ptr[CInternalRequest[R2loc]] creq)
    @staticmethod
    cdef InternalRequest from_c_int(shared_ptr[CInternalRequest[int]] creq)

cdef class Stop:
    cdef bint ptr_owner
    cdef _UStop ustop
    cdef LocType loc_type
    @staticmethod
    cdef Stop from_c_r2loc(CStop[R2loc] *cstop)
    @staticmethod
    cdef Stop from_c_int(CStop[int] *cstop)


cdef class Stoplist:
    cdef LocType loc_type
    cdef _UStoplist ustoplist
    cdef Stop py_s
    @staticmethod
    cdef Stoplist from_c_r2loc(vector[CStop[R2loc]] cstoplist)
    @staticmethod
    cdef Stoplist from_c_int(vector[CStop[int]] cstoplist)
