# distutils: language=c++

from ridepy.util import MAX_SEAT_CAPACITY

from ridepy.events import PickupEvent, DeliveryEvent, InternalEvent
from ridepy.data_structures import (
    Dispatcher,
    SingleVehicleSolution,
    TransportationRequest as pyTransportationRequest,
)
from ridepy.data_structures_cython.data_structures cimport (
    TransportationRequest,
    Stop,
    StopAction,
    Stoplist,
    LocType
)

from ridepy.data_structures_cython.cdata_structures cimport R2loc, Stop as CStop
from ridepy.data_structures_cython.cdata_structures cimport InsertionResult, \
    TransportationRequest as CTransportationRequest, \
    Request as CRequest

from ridepy.util.spaces_cython.spaces cimport TransportSpace

from typing import List, Union
from copy import deepcopy

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

import logging
logger = logging.getLogger(__name__)




from ridepy.vehicle_state_cython.cvehicle_state cimport VehicleState as CVehicleState,\
    StopEventSpec, AvailableDispatcher
from libcpp.memory cimport unique_ptr, make_unique
from libcpp.utility cimport pair
from libcpp.memory cimport make_shared
from libcpp.vector cimport vector
from libcpp.string cimport string
from cython.operator cimport dereference

cdef extern from "limits.h":
    cdef int INT_MAX


cdef union UVehicleState:
    unique_ptr[CVehicleState[R2loc]] vstate_r2loc
    unique_ptr[CVehicleState[int]] vstate_int


cdef union UStoplist:
    cdef vector[CStop[R2loc]] c_stoplist_r2loc
    cdef vector[CStop[int]] c_stoplist_int

cdef class VehicleState:
    """
    Single vehicle insertion logic is implemented in Cython here. Can be used interchangeably
    with its pure-python equivalent `.vehicle_state.VehicleState`.
    """
    cdef Stoplist initial_stoplist
    cdef UStoplist _ustoplist_new
    cdef UStoplist _ustoplist
    cdef TransportSpace _space
    cdef int _vehicle_id
    cdef int _seat_capacity
    cdef object _dispatcher

    cdef UVehicleState _uvstate
    cdef LocType loc_type

    def __init__(
        self,
        #*, # haven't figured out yet how to get __reduce__+unpickling to work with keyword-only
        # arguments, hence we have to support __init__ with positional arguments for the time being
        int vehicle_id,
        initial_stoplist,
        TransportSpace space,
        AvailableDispatcher dispatcher,
        int seat_capacity,
    ):
        # Create a cython stoplist object from initial_stoplist
        if isinstance(initial_stoplist, Stoplist):
            # if a `data_structures_cython.Stoplist` object, no need to re-create the cythonic stoplist
            self.initial_stoplist = initial_stoplist
        else:
            # assume that a python list of `data_structures_cython.Stop` objects are being passed
            # create a `data_structures_cython.Stoplist` object
            self.initial_stoplist = Stoplist(initial_stoplist, space.loc_type)
        if seat_capacity > INT_MAX:
            raise ValueError("Cannot use seat_capacity bigger that C++'s INT_MAX")
        if space.loc_type == LocType.R2LOC:
            self.loc_type = LocType.R2LOC
            self._uvstate.vstate_r2loc = make_unique[CVehicleState[R2loc]](
                vehicle_id, self.initial_stoplist.ustoplist._stoplist_r2loc,
                dereference(space.u_space.space_r2loc_ptr), dispatcher, seat_capacity)
        elif space.loc_type == LocType.INT:
            self.loc_type = LocType.INT
            self._uvstate.vstate_int = make_unique[CVehicleState[int]](
                vehicle_id, self.initial_stoplist.ustoplist._stoplist_int,
                dereference(space.u_space.space_int_ptr), dispatcher, seat_capacity)
        else:
            raise ValueError("This line should never have been reached")

        logger.info(f"Created VehicleState with space of type {type(self._space)}")


    def fast_forward_time(self, t: float) -> Tuple[List[StopEvent], List[Stop]]:
        """
        Update the vehicle_state to the simulator time `t`.

        Parameters
        ----------
        t
            time to be updated to

        Returns
        -------
        events
            List of stop events emitted through servicing stops upto time=t
        new_stoplist
            Stoplist remaining after servicing the stops upto time=t
        """
        # TODO assert that the CPATs are updated and the stops sorted accordingly
        # TODO optionally validate the travel time velocity constraints
        logger.debug(f"Fast forwarding vehicle {self._vehicle_id} from MPI rank {rank}")

        if self.loc_type = LocType.R2LOC:
            cdef vector[StopEventSpec] res = dereference(
                self._uvstate.vstate_r2loc).fast_forward_time(t)
        elif self.loc_type = LocType.INT:
            cdef vector[StopEventSpec] res = dereference(
                self._uvstate.vstate_int).fast_forward_time(t)
        else:
            raise ValueError("bla")

        #stop_event_specc, stoplist = res[0],
        event_cache = []
        cdef StopEventSpec evspec

        for ev in res:
            event_cache.append({
                        StopAction.pickup: PickupEvent,
                        StopAction.dropoff: DeliveryEvent,
                        StopAction.internal: InternalEvent,
                        }[ev.action](
                        request_id=ev.request_id,
                        vehicle_id=ev.vehicle_id,
                        timestamp=ev.timestamp))

        return event_cache

    def handle_transportation_request_single_vehicle(
            self, request: pyTransportationRequest
    ) -> SingleVehicleSolution:
        """
        The computational bottleneck. An efficient simulator could:

        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.

        Parameters
        ----------
        request
            Request to be handled.

        Returns
        -------
            The `SingleVehicleSolution` for the respective vehicle.
        """
        # Logging the folloowing in this specific format is crucial for
        # `test/mpi_futures_fleet_state_test.py` to pass
        logger.debug(f"Handling request #{request.request_id} with vehicle {self._vehicle_id} from MPI rank {rank}")
        if self.loc_type == LocType.R2LOC:
        cdef pair[int, InsertionResult[R2loc]] insertion_result_and_vid_r2loc = dereference(
            self._uvstate.vstate_r2loc).handle_transportation_request_single_vehicle(
                make_shared[CTransportationRequest[R2loc]](
                    <int> request.request_id, <double> request.creation_timestamp, <R2loc> request.origin,
                    <R2loc> request.destination, <double> request.pickup_timewindow_min, <double> request.pickup_timewindow_max,
                    <double> request.delivery_timewindow_min, <double> request.delivery_timewindow_max))

        cdef vid = insertion_result_and_vid_r2loc.first
        cdef InsertionResult[R2loc] insertion_result_r2loc = insertion_result_and_vid_r2loc.second
        self.c_stoplist_new = insertion_result_r2loc.new_stoplist

        return vid, insertion_result_r2loc.min_cost, \
               (insertion_result_r2loc.EAST_pu, insertion_result_r2loc.LAST_pu,
                insertion_result_r2loc.EAST_do, insertion_result_r2loc.LAST_do)

    def select_new_stoplist(self):
        #dereference(self._uvstate.vstate_r2loc).stoplist.reset()
        dereference(self._uvstate.vstate_r2loc).stoplist = self.c_stoplist_new


    property stoplist:
        def __get__(self):
            return Stoplist.from_c_r2loc(dereference(self._uvstate.vstate_r2loc).stoplist)

    property seat_capacity:
        def __get__(self):
            return dereference(self._uvstate.vstate_r2loc).seat_capacity