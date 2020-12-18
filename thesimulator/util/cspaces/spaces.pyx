# distutils: language = c++
from .cspaces cimport(
    R2loc,
    Euclidean2D as CEuclidean2D,
    TransportSpace as CTransportSpace
)
from cython.operator cimport dereference

cdef class TransportSpace:
    def __cinit__(self, double velocity=1):
        print(f"Allocating base class pointer")
        self.c_space_ptr = new  CTransportSpace(velocity)
    def __dealloc__(self):
        if self.c_space_ptr:
            del self.c_space_ptr

    def d(self, R2loc u, R2loc v):
        return dereference(self.c_space_ptr).d(u, v)

    def t(self, R2loc u, R2loc v):
        return dereference(self.c_space_ptr).t(u, v)

    def interp_dist(self, R2loc u, R2loc v, double dist_to_dest):
        return dereference(self.c_space_ptr).interp_dist(u, v, dist_to_dest)

    def interp_time(self, R2loc u, R2loc v, double time_to_dest):
        return dereference(self.c_space_ptr).interp_time(u, v, time_to_dest)

cdef class Euclidean2D:
    def __cinit__(self, double velocity=1):
        #if self.c_space_ptr:
        #    print(f"Found base class pointer, deleting")
        #    del self.c_space_ptr
        print(f"Allocating euclidean class pointer")
        #self.derived_ptr = self.c_space_ptr = new  CEuclidean2D(velocity)
        self.derived_ptr = new  CEuclidean2D(velocity)
 #   def __init__(self):
 #       self.c_space_ptr = self.derived_ptr
    def bla(self):
        cdef R2loc x = (0,0)
        cdef R2loc y = (2, 8)
        return dereference(self.derived_ptr).d(x, y)

    def __dealloc__(self):
        if self.derived_ptr:
            del self.derived_ptr

