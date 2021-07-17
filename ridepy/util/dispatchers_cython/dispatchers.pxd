# distutils: language=c++

from .cdispatchers cimport AbstractDispatcher as CAbstractDispatcher
from ridepy.data_structures_cython.data_structures cimport LocType, R2loc


cdef union UDispatcher:
    CAbstractDispatcher[R2loc] *dispatcher_r2loc_ptr
    CAbstractDispatcher[int] *dispatcher_int_ptr

cdef class Dispatcher:
    cdef UDispatcher u_dispatcher
    cdef readonly LocType loc_type