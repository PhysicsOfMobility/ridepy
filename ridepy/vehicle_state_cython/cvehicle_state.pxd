# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp.utility cimport pair
from ridepy.data_structures_cython.cdata_structures cimport (
    InsertionResult, TransportationRequest, Stop, StopAction)
from ridepy.util.spaces_cython.cspaces cimport TransportSpace

cdef extern from "cvehicle_state.h" namespace 'cstuff':
    cdef cppclass StopEventSpec:
        StopAction action
        int request_id
        int vehicle_id
        double timestamp

    cdef cppclass VehicleState[Loc]:
        int vehicle_id
        shared_ptr[vector[Stop[Loc]]] stoplist
        int seat_capacity
        string dispatcher
        TransportSpace[Loc] &space

        VehicleState(int vehicle_id, vector[Stop[Loc]] initial_stoplist,
                     TransportSpace[Loc] &space, str dispatcher, int seat_capacity)

        pair[vector[StopEventSpec], shared_ptr[vector[Stop[Loc]]]] fast_forward_time(double t)
        pair[int, InsertionResult[Loc]] handle_transportation_request_single_vehicle(
              shared_ptr[TransportationRequest[Loc]] request)