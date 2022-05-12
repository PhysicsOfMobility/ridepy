# distutils: language = c++

from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.memory cimport shared_ptr

cdef extern from "cdata_structures.h" namespace 'ridepy':

    ctypedef pair[double, double] R2loc
    cpdef enum class StopAction(int):
        pickup=1
        dropoff=2
        internal=3

    cdef cppclass Request[Loc]:
        int request_id
        double creation_timestamp

    cdef cppclass TransportationRequest[Loc](Request[Loc]):
        Loc origin
        Loc destination
        double pickup_timewindow_min
        double pickup_timewindow_max
        double delivery_timewindow_min
        double delivery_timewindow_max

        TransportationRequest()
        TransportationRequest(int, double, Loc, Loc, double, double, double, double)

    cdef cppclass InternalRequest[Loc](Request[Loc]):
        Loc location

        InternalRequest()
        InternalRequest(int, double, Loc)


    cdef cppclass Stop[Loc]:
        Loc location
        shared_ptr[Request[Loc]] request
        StopAction action
        double estimated_arrival_time
        double time_window_min
        double time_window_max
        int occupancy_after_servicing

        Stop()
        Stop(Loc, const shared_ptr[Request]&, StopAction, double, int, double, double)

    cdef cppclass InsertionResult[Loc]:
        vector[Stop[Loc]] new_stoplist
        double min_cost
        double EAST_pu
        double LAST_pu
        double EAST_do
        double LAST_do

    cdef cppclass SingleVehicleSolution:
        int vehicle_id
        double min_cost
        double EAST_pu
        double LAST_pu
        double EAST_do
        double LAST_do

