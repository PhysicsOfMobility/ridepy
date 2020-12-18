# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
TransportSpace as CTransportSpace,
Manhattan2D as CManhattan2D
)


cdef class TransportSpace:
    cdef CTransportSpace *c_space_ptr

cdef class Euclidean2D(TransportSpace):
    cdef CEuclidean2D *derived_ptr

cdef class Manhattan2D(TransportSpace):
    cdef CManhattan2D *derived_ptr

