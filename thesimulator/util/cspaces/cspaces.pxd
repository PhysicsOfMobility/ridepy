# distutils: language=c++
from libcpp.pair cimport pair

cdef extern from "cspaces.cpp":
    pass

"""
As explained in further detail in https://stackoverflow.com/a/28727488,
virtual functions that are later overridden in a child class **must be declared only for the base class**.
That is, we must *not* declare Euclidean2D.d/t/... here, only in TransportSpace.
Doing so will result in an *ambiguous overridden function* error from cython.
"""

cdef extern from "cspaces.h" namespace 'cstuff':

    ctypedef pair[double, double] R2loc
    cdef cppclass TransportSpace:
        double velocity
        TransportSpace();
        TransportSpace(double);
        double d(R2loc u, R2loc v)
        double t(R2loc u, R2loc v)
        pair[R2loc, double] interp_dist(R2loc u, R2loc v, double dist_to_dest);
        pair[R2loc, double] interp_time(R2loc u, R2loc v, double time_to_dest);


    cdef cppclass Euclidean2D(TransportSpace):
        double velocity

        Euclidean2D();
        Euclidean2D(double);

    cdef cppclass Manhattan2D(TransportSpace):
        double velocity

        Manhattan2D();
        Manhattan2D(double);
