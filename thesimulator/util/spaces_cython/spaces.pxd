# distutils: language = c++

from .cspaces cimport (
    Euclidean2D as CEuclidean2D,
    TransportSpace as CTransportSpace,
    Manhattan2D as CManhattan2D,
    GraphSpace as CGraphSpace
)

from thesimulator.data_structures_cython.data_structures cimport LocType, R2loc


cdef union USpace:
    CTransportSpace[R2loc] *space_r2loc_ptr
    CTransportSpace[int] *space_int_ptr


cdef class TransportSpace:
    cdef USpace u_space
    cdef LocType loc_type
    cdef readonly int n_dim


cdef class Euclidean2D(TransportSpace):
    cdef CEuclidean2D *derived_ptr


cdef class Manhattan2D(TransportSpace):
    cdef CManhattan2D *derived_ptr


cdef class Graph(TransportSpace):
    cdef CGraphSpace[int] *derived_ptr
