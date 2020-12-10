# distutils: language = c++

from .cspaces cimport (
Euclidean2D as CEuclidean2D,
)

cdef class Euclidean2D:
    cdef CEuclidean2D c_euclidean2d
