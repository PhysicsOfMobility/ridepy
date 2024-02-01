# distutils: language = c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair

from .cspaces cimport (
    Euclidean2D as CEuclidean2D,
    TransportSpace as CTransportSpace,
    Manhattan2D as CManhattan2D,
    GraphSpace as CGraphSpace
)

from ridepy.data_structures_cython.data_structures cimport LocType, R2loc


cdef union USpace:
    CTransportSpace[R2loc] *space_r2loc_ptr
    CTransportSpace[int] *space_int_ptr


cdef class TransportSpace:
    cdef USpace u_space
    cdef readonly LocType loc_type
    cdef readonly int n_dim


cdef class Euclidean2D(TransportSpace):
    cdef CEuclidean2D *derived_ptr
    cdef readonly vector[pair[float, float]] coord_range


cdef class Manhattan2D(TransportSpace):
    cdef CManhattan2D *derived_ptr
    cdef readonly vector[pair[float, float]] coord_range

cdef class Grid2D(Manhattan2D):
    cdef readonly float n
    cdef readonly float m
    cdef readonly float dn
    cdef readonly float dm
    cdef readonly float velocity

# cdef class Grid2D_QM(Grid2D):
#     ...

cdef class Graph(TransportSpace):
    cdef CGraphSpace[int] *derived_ptr
