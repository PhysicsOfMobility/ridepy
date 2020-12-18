# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
TransportSpace as CTransportSpace
)


cdef class TransportSpace:
    cdef CTransportSpace *c_space_ptr

cdef class Euclidean2D:
    cdef CEuclidean2D *derived_ptr
