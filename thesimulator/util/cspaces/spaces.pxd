# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
TransportSpace as CTransportSpace
)


cdef class TransportSpace:
    cdef CTransportSpace c_space

cdef class Euclidean2D(TransportSpace):
    cdef CEuclidean2D c_space
