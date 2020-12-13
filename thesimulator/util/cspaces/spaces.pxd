# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
R2loc,
TransportSpace as CTransportSpace
)


cdef class Euclidean2D:
    cdef CEuclidean2D c_space
