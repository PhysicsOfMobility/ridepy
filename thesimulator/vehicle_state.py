import operator as op
import numpy as np

from typing import Optional, SupportsFloat, List

from .data_structures import (
    Request,
    Stoplist,
    SingleVehicleSolution,
    StopEvent,
    StopAction,
    PickupEvent,
    DeliveryEvent,
    InternalStopEvent,
    Stop,
    TransportationRequest,
)
from .utils import TransportSpace


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally  be implemented in Cython
    or other compiled language.
    """

    @property
    def vehicle_id(self):
        return self._vehicle_id

    @vehicle_id.setter
    def vehicle_id(self, vehicle_id):
        # TODO change both the stoplist's vehicle ids and the actual vehicle id
        # assert all(stop.vehicle_id == vehicle_id for stop in self.stoplist)
        self._vehicle_id = vehicle_id

    @property
    def stoplist(self) -> Stoplist:
        return self._stoplist

    @stoplist.setter
    def stoplist(self, stoplist: Stoplist):
        # TODO possibly updated the CPATs here (i.e. travel time computation, or using the sub/superdiagonal
        #  [depending of the definition] of the [updated] distance matrix)
        # for i, stop in enumerate(stoplist):
        #     stop.cpat = D[i, i + 1]
        stoplist = sorted(stoplist, key=op.attrgetter("estimated_arrival_time"))
        self._stoplist = stoplist

    def __init__(
        self, *, vehicle_id, initial_stoplist: Stoplist, space: TransportSpace
    ):
        """
        Create a vehicle.

        Parameters
        ----------
        vehicle_id:
            id of the vehicle to be created
        initial_stoplist
            stoplist to start out with, MUST contain CPE as first element
        space
            transport space the vehicle is operating on
        """
        self.vehicle_id = vehicle_id
        # TODO check for CPE existence in each supplied stoplist or encapsulate the whole thing
        self.stoplist = initial_stoplist
        self.space = space

    def fast_forward_time(self, t: float) -> List[StopEvent]:
        # TODO update CPE
        # TODO assert that the CPATs  are updated and the stops sorted accordingly
        # TODO optionally validate the travel time velocity constraints

        event_cache = []
        for i in range(len(self.stoplist) - 1, 0, -1):
            stop = self.stoplist[i]
            # service the stop at its estimated arrival time
            if stop.estimated_arrival_time <= t:
                event_cache.append(
                    {
                        StopAction.pickup: PickupEvent,
                        StopAction.dropoff: DeliveryEvent,
                        StopAction.internal: InternalStopEvent,
                    }[stop.action](
                        request_id=stop.request,
                        vehicle_id=stop.vehicle_id,
                        timestamp=stop.estimated_arrival_time,
                    )
                )
            # TODO I stand confused. Why does `del stop` not work?
            del self.stoplist[i]

        # TODO should update CPE
        return event_cache

    def handle_transportation_request_single_vehicle(
        self, req: TransportationRequest
    ) -> SingleVehicleSolution:
        """
        The computational bottleneck. An efficient simulator could do the following:
        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
        2. Implement as a c extension. The args and the return value are all basic c data types,
           so this should also be easy.

        Parameters
        ----------
        req

        Returns
        -------
        This returns the single best solution for the respective vehicle.
        """
        # TODO should this call fast_forward_time? (<---??)

        ##############################
        # TODO this be outsourced(!)

        # -- SIMPLE TAXICAB-STYLE INSERTION --
        CPAT_pu = (
            max(
                self.stoplist[-1].estimated_arrival_time,
                self.stoplist[-1].time_window_min
                if self.stoplist[-1].time_window_min is not None
                else 0,
            )
            + self.space.d(self.stoplist[-1].location, req.origin)
        )
        CPAT_do = CPAT_pu + self.space.d(req.origin, req.destination)
        EAST_pu = req.pickup_timewindow_min
        LAST_pu = (
            CPAT_pu + req.delivery_timewindow_max
            if req.delivery_timewindow_max is not None
            else np.inf
        )
        EAST_do = EAST_pu
        LAST_do = None

        cost = CPAT_do

        stoplist = self.stoplist + [
            Stop(
                location=req.origin,
                vehicle_id=self.vehicle_id,
                request=req,
                action=StopAction.pickup,
                estimated_arrival_time=CPAT_pu,
                time_window_min=EAST_pu,
                time_window_max=LAST_pu,
            ),
            Stop(
                location=req.destination,
                vehicle_id=self.vehicle_id,
                request=req,
                action=StopAction.dropoff,
                estimated_arrival_time=CPAT_do,
                time_window_min=EAST_do,
                time_window_max=LAST_do,
            ),
        ]
        ##############################
        return self.vehicle_id, cost, stoplist
