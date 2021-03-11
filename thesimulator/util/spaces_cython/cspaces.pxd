# distutils: language=c++
# distutils: include_dirs = boost_1_75_0

from libcpp.pair cimport pair
from libcpp.vector cimport vector

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
    cdef cppclass TransportSpace[Loc]:
        double velocity
        TransportSpace();
        TransportSpace(double);
        double d(Loc u, Loc v)
        double t(Loc u, Loc v)
        pair[Loc, double] interp_dist(Loc u, Loc v, double dist_to_dest);
        pair[Loc, double] interp_time(Loc u, Loc v, double time_to_dest);

    cdef cppclass Euclidean2D(TransportSpace[R2loc]):
        double velocity

        Euclidean2D();
        Euclidean2D(double);

    cdef cppclass Manhattan2D(TransportSpace[R2loc]):
        double velocity

        Manhattan2D();
        Manhattan2D(double);



cdef extern from "boost_graph_space.h" namespace 'cstuff':
    cdef cppclass GraphSpace[Loc](TransportSpace[Loc]):
        ctypedef pair[Loc, Loc] Edge
        double velocity

        GraphSpace(double, vector[Loc] vertex_vec, vector[Edge] edge_vec, vector[double] weight_vec)
        GraphSpace(double, vector[Loc] vertex_vec, vector[Edge] edge_vec)