# distutils: language = c++

from libcpp.vector cimport vector


from thesimulator.cdata_structures.cdata_structures cimport (
    Request as CRequest,
    Stop as CStop,
    R2loc
)

cdef extern from * namespace 'cstuff':
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

ctypedef enum LocType:
    R2LOC  = 1
    INT = 2

cdef union _URequest:
    CRequest[R2loc] _req_r2loc
    CRequest[int] _req_int

cdef union _UStop:
    CStop[R2loc] _stop_r2loc
    CStop[int] _stop_int

cdef union _UStoplist:
    vector[CStop[R2loc]]* _stoplist_r2loc_ptr
    vector[CStop[int]]* _stoplist_int_ptr


cdef class TransportationRequest:
    cdef _URequest _ureq
    cdef LocType loc_type
#    @staticmethod
#    cdef TransportationRequest from_c_union(_URequest, LocType)
    @staticmethod
    cdef TransportationRequest from_c_r2loc(CRequest[R2loc] creq)
    @staticmethod
    cdef TransportationRequest from_c_int(CRequest[int] creq)

cdef class Stop:
    cdef _UStop ustop
    cdef LocType loc_type
#    @staticmethod
#    cdef Stop from_c_union(_UStop ustop, LocType loc_type)
    @staticmethod
    cdef Stop from_c_r2loc(CStop[R2loc] cstop)
    @staticmethod
    cdef Stop from_c_int(CStop[int] cstop)


cdef class Stoplist:
    cdef LocType loc_type
    cdef _UStoplist ustoplist
    cdef _UStop this_stop
    cdef Stop py_s
#    @staticmethod
#    cdef Stoplist from_c_union(_UStoplist ustoplist, LocType loc_type)
    @staticmethod
    cdef Stoplist from_c_r2loc(vector[CStop[R2loc]] *cstoplist_ptr)
    @staticmethod
    cdef Stoplist from_c_int(vector[CStop[int]] *cstoplist_ptr)
