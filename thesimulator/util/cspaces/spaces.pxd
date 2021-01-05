# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
TransportSpace as CTransportSpace,
TransportSpaceR2loc as CTransportSpaceR2loc,
TransportSpaceInt as CTransportSpaceInt,
Manhattan2D as CManhattan2D
)


#cdef class TransportSpace:
#    cdef CTransportSpace *c_space_ptr

cdef class TransportSpaceR2loc:
    cdef CTransportSpaceR2loc *c_space_ptr

cdef class Euclidean2D(TransportSpaceR2loc):
    cdef CEuclidean2D *derived_ptr

cdef class Manhattan2D(TransportSpaceR2loc):
    cdef CManhattan2D *derived_ptr

