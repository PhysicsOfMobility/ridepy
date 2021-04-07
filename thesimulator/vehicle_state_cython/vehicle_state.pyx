# distutils: language=c++

from thesimulator.util import MAX_SEAT_CAPACITY

from thesimulator.events import PickupEvent, DeliveryEvent, InternalEvent
from thesimulator.data_structures import (
    Dispatcher,
    SingleVehicleSolution,
)
from thesimulator.data_structures_cython.data_structures cimport (
    TransportationRequest,
    Stop,
    StopAction,
    Stoplist,
)

from thesimulator.util.spaces_cython.spaces cimport TransportSpace

from typing import List, Union
from copy import deepcopy

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

import logging
logger = logging.getLogger(__name__)


cdef extern from "limits.h":
    cdef int INT_MAX

cdef class VehicleState:
    """
    Single vehicle insertion logic is implemented in Cython here. Can be used interchangeably
    with its pure-python equivalent `.vehicle_state.VehicleState`.
    """

    #    def recompute_arrival_times_drive_first(self):
    #        # update CPATs
    #        for stop_i, stop_j in zip(self.stoplist, self.stoplist[1:]):
    #            stop_j.estimated_arrival_time = max(
    #                stop_i.estimated_arrival_time, stop_i.time_window_min
    #            ) + self.space.t(stop_i.location, stop_j.location)
    cdef Stoplist _stoplist
    cdef TransportSpace _space
    cdef int _vehicle_id
    cdef int _seat_capacity
    cdef object _dispatcher

    def __init__(
        self,
        #*, # haven't figured out yet how to get __reduce__+unpickling to work with keyword-only
        # arguments, hence we have to support __init__ with positional arguments for the time being
        vehicle_id,
        initial_stoplist: Union[List[Stop], Stoplist],
        space: TransportSpace,
        dispatcher: Dispatcher,
        seat_capacity: int,
    ):
        self._vehicle_id = vehicle_id
        """
        See the docstring of `.vehicle_state.VehicleState` for details of the parameters.
        """
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        # Create a cython stoplist object from initial_stoplist
        if isinstance(initial_stoplist, Stoplist):
            # if a `data_structures_cython.Stoplist` object, no need to re-create the cythonic stoplist
            self._stoplist = initial_stoplist
        else:
            # assume that a python list of `data_structures_cython.Stop` objects are being passed
            # create a `data_structures_cython.Stoplist` object
            self._stoplist = Stoplist(initial_stoplist, space.loc_type)
        self._space = space
        self._dispatcher = dispatcher
        if seat_capacity > INT_MAX:
            raise ValueError("Cannot use seat_capacity bigger that C++'s INT_MAX")
        self._seat_capacity = seat_capacity
        logger.info(f"Created VehicleState with space of type {type(self._space)}")

    property stoplist:
        def __get__(self):
            return self._stoplist
        def __set__(self, new_stoplist):
            self._stoplist = new_stoplist

    property seat_capacity:
        def __get__(self):
            return self._seat_capacity

    property vehicle_id:
        def __get__(self):
            return self._vehicle_id

    property space:
        def __get__(self):
            return self._space

    property dispatcher:
        def __get__(self):
            return self._dispatcher

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
        event_cache = []

        last_stop = None

        # drop all non-future stops from the stoplist, except for the (outdated) CPE
        for i in range(len(self._stoplist) - 1, 0, -1):
            stop = self._stoplist[i]
            # service the stop at its estimated arrival time
            if stop.estimated_arrival_time <= t:
                # as we are iterating backwards, the first stop iterated over is the last one serviced
                if last_stop is None:
                    # this deepcopy is necessary because otherwise after removing elements from stoplist,
                    # last_stop will point to the wrong element.  See the failing test as well:
                    # test.test_data_structures_cython.test_stoplist_getitem_and_elem_removal_consistent
                    last_stop = deepcopy(stop)

                event_cache.append(
                    {
                        StopAction.pickup: PickupEvent,
                        StopAction.dropoff: DeliveryEvent,
                        StopAction.internal: InternalEvent,
                    }[stop.action](
                        request_id=stop.request.request_id,
                        vehicle_id=self._vehicle_id,
                        timestamp=max(
                            stop.estimated_arrival_time, stop.time_window_min
                        ),
                    )
                )
                self._stoplist.remove_nth_elem(i)


        # fix event cache order
        event_cache = event_cache[::-1]

        # if no stop was serviced, the last stop is the outdated CPE
        if last_stop is None:
            last_stop = self._stoplist[0]

        # set the occupancy at CPE
        self._stoplist[0].occupancy_after_servicing = last_stop.occupancy_after_servicing

        # set CPE location to current location as inferred from the time delta to the upcoming stop's CPAT
        if len(self._stoplist) > 1:
            if last_stop.estimated_arrival_time > t:
                # still mid-jump from last interpolation, no need to interpolate
                # again
                pass
            else:
                self._stoplist[0].location, jump_time = self._space.interp_time(
                    u=last_stop.location,
                    v=self._stoplist[1].location,
                    time_to_dest=self._stoplist[1].estimated_arrival_time - t,
                )
                # set CPE time
                self._stoplist[0].estimated_arrival_time = t + jump_time
        else:
            # stoplist is empty, only CPE is there. set CPE time to current time
            self._stoplist[0].estimated_arrival_time = t

        return event_cache, self._stoplist

    def handle_transportation_request_single_vehicle(
            self, TransportationRequest request
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
        ret = self._vehicle_id, *self._dispatcher(
                request,
                self._stoplist,
                self._space, self._seat_capacity)
        return ret

    def __reduce__(self):
        return self.__class__, \
            (
                self._vehicle_id,
                self._stoplist.to_pys(),
                self._space,
                self._dispatcher,
                self._seat_capacity
            )