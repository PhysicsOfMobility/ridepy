# distutils: language = c++

from thesimulator.util.cspaces.spaces cimport (
Euclidean2D as CEuclidean2D,
)

cdef class Euclidean2D:
    cdef CEuclidean2D c_euclidean2d
