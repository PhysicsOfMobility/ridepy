# distutils: language=c++
import warnings

from ridepy.util import MAX_SEAT_CAPACITY

from ridepy.events import PickupEvent, DeliveryEvent, InternalEvent
from ridepy.data_structures import  (TransportationRequest as pyTransportationRequest,SingleVehicleSolution as pySingleVehicleSolution)
from ridepy.data_structures_cython.data_structures cimport (
    TransportationRequest,
    Stop,
    StopAction,
    Stoplist,
    LocType
)

from ridepy.data_structures_cython.cdata_structures cimport R2loc, Stop as CStop
from ridepy.data_structures_cython.cdata_structures cimport SingleVehicleSolution, \
    TransportationRequest as CTransportationRequest, \
    Request as CRequest

from ridepy.util.spaces_cython.spaces cimport TransportSpace
from ridepy.util.dispatchers_cython.dispatchers cimport Dispatcher

from typing import List, Union
from copy import deepcopy

import logging
logger = logging.getLogger(__name__)

from ridepy.vehicle_state_cython.cvehicle_state cimport VehicleState as CVehicleState, StopEventSpec
from libcpp.memory cimport unique_ptr, make_unique
from libcpp.utility cimport pair
from libcpp.memory cimport make_shared
from libcpp.vector cimport vector
from libcpp.string cimport string
from cython.operator cimport dereference

cdef extern from "limits.h":
    cdef int INT_MAX


cdef union _UVehicleState:
    unique_ptr[CVehicleState[R2loc]] _vstate_r2loc
    unique_ptr[CVehicleState[int]] _vstate_int

cdef class VehicleState:
    """
    Single vehicle insertion logic is implemented in Cython here. Can be used interchangeably
    with its pure-python equivalent `.vehicle_state.VehicleState`.
    """
    cdef Stoplist initial_stoplist
    cdef _UVehicleState _uvstate
    cdef LocType loc_type

    def __init__(
        self,
        #*, # haven't figured out yet how to get __reduce__+unpickling to work with keyword-only
        # arguments, hence we have to support __init__ with positional arguments for the time being
        int vehicle_id,
        initial_stoplist,
        TransportSpace space,
        Dispatcher dispatcher,
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
            self._uvstate._vstate_r2loc = make_unique[CVehicleState[R2loc]](
                vehicle_id, self.initial_stoplist.ustoplist._stoplist_r2loc,
                dereference(space.u_space.space_r2loc_ptr), dereference(dispatcher.u_dispatcher.dispatcher_r2loc_ptr), seat_capacity)
        elif space.loc_type == LocType.INT:
            self.loc_type = LocType.INT
            self._uvstate._vstate_int = make_unique[CVehicleState[int]](
                vehicle_id, self.initial_stoplist.ustoplist._stoplist_int,
                dereference(space.u_space.space_int_ptr), dereference(dispatcher.u_dispatcher.dispatcher_int_ptr), seat_capacity)
        else:
            raise ValueError("This line should never have been reached")



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

        cdef vector[StopEventSpec] res
        if self.loc_type == LocType.R2LOC:
            res = dereference(self._uvstate._vstate_r2loc).fast_forward_time(t)
        elif self.loc_type == LocType.INT:
            res = dereference(self._uvstate._vstate_int).fast_forward_time(t)
        else:
            raise ValueError("This line should never have been reached")

        #stop_event_specc, stoplist = res[0],
        event_cache = []
        cdef StopEventSpec evspec

        for ev in res:
            if ev.action == StopAction.pickup:
                stop_event = {
                    "event_type": "PickupEvent",
                    "timestamp": ev.timestamp,
                    "request_id": ev.request_id,
                    "vehicle_id": ev.vehicle_id,
                }
            elif ev.action == StopAction.dropoff:
                stop_event = {
                    "event_type": "DeliveryEvent",
                    "timestamp": ev.timestamp,
                    "request_id": ev.request_id,
                    "vehicle_id": ev.vehicle_id,
                }
            elif ev.action == StopAction.internal:
                stop_event = {
                    "event_type": "InternalEvent",
                    "timestamp": ev.timestamp,
                    "vehicle_id": ev.vehicle_id,
                }
            else:
                raise ValueError(f"Unknown StopAction={ev.action}")

            event_cache.append(stop_event)

        return event_cache

    def handle_transportation_request_single_vehicle(
            self, request: pyTransportationRequest
    ) -> pySingleVehicleSolution:
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
        cdef SingleVehicleSolution single_vehicle_solution

        if self.loc_type == LocType.R2LOC:
            single_vehicle_solution = (
                dereference(self._uvstate._vstate_r2loc).handle_transportation_request_single_vehicle(
                    make_shared[CTransportationRequest[R2loc]](
                        <int> request.request_id,
                        <double> request.creation_timestamp,
                        <R2loc> request.origin,
                        <R2loc> request.destination,
                        <double> request.pickup_timewindow_min,
                        <double> request.pickup_timewindow_max,
                        <double> request.delivery_timewindow_min,
                        <double> request.delivery_timewindow_max
                    )
                )
            )
        elif self.loc_type == LocType.INT:
            single_vehicle_solution = (
                dereference(self._uvstate._vstate_int).handle_transportation_request_single_vehicle(
                    make_shared[CTransportationRequest[int]](
                        <int> request.request_id,
                        <double> request.creation_timestamp,
                        <int> request.origin,
                        <int> request.destination,
                        <double> request.pickup_timewindow_min,
                        <double> request.pickup_timewindow_max,
                        <double> request.delivery_timewindow_min,
                        <double> request.delivery_timewindow_max
                    )
                )
            )
        else:
            raise ValueError("This line should never have been reached")


        return (
            self.vehicle_id,
            single_vehicle_solution.min_cost,
            (
                single_vehicle_solution.EAST_pu,
                single_vehicle_solution.LAST_pu,
                single_vehicle_solution.EAST_do,
                single_vehicle_solution.LAST_do
            )
        )

    def select_new_stoplist(self):
        if self.loc_type == LocType.R2LOC:
            return dereference(self._uvstate._vstate_r2loc).select_new_stoplist()
        elif self.loc_type == LocType.INT:
            return dereference(self._uvstate._vstate_int).select_new_stoplist()
        else:
            raise ValueError("This line should never have been reached")

    property stoplist:
        def __get__(self):
            warnings.warn("Extracting the C++ stoplist will impact performance", UserWarning)
            if self.loc_type == LocType.R2LOC:
                return Stoplist.from_c_r2loc(dereference(self._uvstate._vstate_r2loc).stoplist)
            elif self.loc_type == LocType.INT:
                return Stoplist.from_c_int(dereference(self._uvstate._vstate_int).stoplist)
            else:
                raise ValueError("This line should never have been reached")

    property seat_capacity:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._uvstate._vstate_r2loc).seat_capacity
            elif self.loc_type == LocType.INT:
                return dereference(self._uvstate._vstate_int).seat_capacity
            else:
                raise ValueError("This line should never have been reached")

    property vehicle_id:
        def __get__(self):
            if self.loc_type == LocType.R2LOC:
                return dereference(self._uvstate._vstate_r2loc).vehicle_id
            elif self.loc_type == LocType.INT:
                return dereference(self._uvstate._vstate_int).vehicle_id
            else:
                raise ValueError("This line should never have been reached")
