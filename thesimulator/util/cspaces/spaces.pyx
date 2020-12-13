# distutils: language = c++
from .cspaces cimport(
    R2loc,
)


cdef class Euclidean2D:
    def __init__(self, double velocity):
        self.c_space.velocity = velocity
    def d(self, R2loc u, R2loc v):
        return self.c_space.d(u, v)

    def t(self, R2loc u, R2loc v):
        return self.c_space.t(u, v)

    def interp_dist(self, R2loc u, R2loc v, double dist_to_dest):
        return self.c_space.interp_dist(u, v, dist_to_dest)

    def interp_time(self, R2loc u, R2loc v, double time_to_dest):
        return self.c_space.interp_time(u, v, time_to_dest)
