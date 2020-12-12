# distutils: language=c++
from libcpp.pair cimport pair

cdef extern from "cspaces.cpp":
    pass

cdef extern from "cspaces.h" namespace 'cstuff':

    ctypedef pair[double, double] R2loc
    cdef cppclass TransportSpace:
        double velocity

        double d(R2loc u, R2loc v)
        double t(R2loc u, R2loc v)
        pair[R2loc, double] interp_dist(R2loc u, R2loc v, double dist_to_dest);
        pair[R2loc, double] interp_time(R2loc u, R2loc v, double time_to_dest);


    cdef cppclass Euclidean2D(TransportSpace):
        double velocity

        double d(R2loc u, R2loc v)
        double t(R2loc u, R2loc v)
        pair[R2loc, double] interp_dist(R2loc u, R2loc v, double dist_to_dest);
        pair[R2loc, double] interp_time(R2loc u, R2loc v, double time_to_dest);

        Euclidean2D();
        Euclidean2D(double);
