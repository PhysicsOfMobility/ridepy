# distutils: language=c++
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.utility cimport tuple as ctuple

cdef extern from "cstuff.cpp":
    pass

cdef extern from "cstuff.h" namespace 'cstuff':

    ctypedef pair[double, double] R2loc
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

    cdef cppclass Euclidean2D:
        double velocity

        double d(R2loc u, R2loc v)
        double t(R2loc u, R2loc v)
        pair[R2loc, double] interp_dist(R2loc u, R2loc v, double dist_to_dest);
        pair[R2loc, double] interp_time(R2loc u, R2loc v, double time_to_dest);

        Euclidean2D();
        Euclidean2D(double);

    cdef cppclass Request:
        int request_id
        double creation_timestamp
        R2loc origin
        R2loc destination
        double pickup_timewindow_min
        double pickup_timewindow_max
        double delivery_timewindow_min
        double delivery_timewindow_max

        Request()
        Request(int, double, R2loc, R2loc, double, double, double, double)

    cdef cppclass Stop:
        R2loc location
        Request request
        StopAction action
        double estimated_arrival_time
        double time_window_min
        double time_window_max

        Stop()
        Stop(R2loc, Request, StopAction, double, double, double)


    ctypedef vector[Stop] Stoplist

    cdef struct InsertionResult:
        Stoplist new_stoplist
        double min_cost
        double EAST_pu
        double LAST_pu
        double EAST_do
        double LAST_do

    InsertionResult brute_force_distance_minimizing_dispatcher(
    Request& request,
    Stoplist& stoplist,
    Euclidean2D& space
    )