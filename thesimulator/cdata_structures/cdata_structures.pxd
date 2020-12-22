# distutils: language = c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair

cdef extern from "cdata_structures.h" namespace 'cstuff':

    ctypedef pair[double, double] R2loc
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

    cdef cppclass Request[Loc]:
        int request_id
        double creation_timestamp
        Loc origin
        Loc destination
        double pickup_timewindow_min
        double pickup_timewindow_max
        double delivery_timewindow_min
        double delivery_timewindow_max

        Request()
        Request(int, double, Loc, Loc, double, double, double, double)

    cdef cppclass Stop[Loc]:
        Loc location
        Request[Loc] request
        StopAction action
        double estimated_arrival_time
        double time_window_min
        double time_window_max

        Stop()
        Stop(Loc, Request, StopAction, double, double, double)

    cdef cppclass InsertionResult[Loc]:
        vector[Stop[Loc]] new_stoplist
        double min_cost
        double EAST_pu
        double LAST_pu
        double EAST_do
        double LAST_do


