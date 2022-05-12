# distutils: language=c++

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp.utility cimport pair
from ridepy.data_structures_cython.cdata_structures cimport (
     SingleVehicleSolution, TransportationRequest, Stop)
from ridepy.data_structures_cython.data_structures cimport StopAction
from ridepy.util.spaces_cython.cspaces cimport TransportSpace

cdef extern from "cvehicle_state.h" namespace 'ridepy':
    cdef cppclass StopEventSpec:
        StopAction action
        int request_id
        int vehicle_id
        double timestamp

    cdef cppclass VehicleState[Loc]:
        int vehicle_id
        vector[Stop[Loc]] stoplist
        int seat_capacity
        string dispatcher
        TransportSpace[Loc] &space

        VehicleState(
                int vehicle_id,
                vector[Stop[Loc]] initial_stoplist,
                TransportSpace[Loc] &space,
                string dispatcher,
                int seat_capacity
        )

        vector[StopEventSpec] fast_forward_time(double t)

        SingleVehicleSolution handle_transportation_request_single_vehicle(
                shared_ptr[TransportationRequest[Loc]] request
        )

        void select_new_stoplist()