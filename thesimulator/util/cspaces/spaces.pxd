# distutils: language = c++

from .cspaces cimport (
    Euclidean2D as CEuclidean2D,
    TransportSpace as CTransportSpace,
    Manhattan2D as CManhattan2D
)

from thesimulator.cdata_structures.data_structures cimport LocType, R2loc

#cdef class TransportSpace:
#    cdef CTransportSpace *c_space_ptr

cdef union USpace:
    CTransportSpace[R2loc] *space_r2loc_ptr
    CTransportSpace[int] *space_int_ptr


#cdef class TransportSpaceR2loc:
#    cdef CTransportSpaceR2loc *c_space_ptr

cdef class TransportSpace:
    cdef USpace u_space
    cdef LocType loc_type

cdef class Euclidean2D(TransportSpace):
    cdef CEuclidean2D *derived_ptr

cdef class Manhattan2D(TransportSpace):
    cdef CManhattan2D *derived_ptr

