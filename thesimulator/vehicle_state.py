import operator as op

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
)


class VehicleState:
    """
    Single vehicle insertion logic is implemented here. Can optionally  be implemented in Cython
    or other compiled language.
    """

    def __init__(self, initial_stoplist: Optional[Stoplist] = None):
        self.stoplist = initial_stoplist

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

    def fast_forward_time(self, t: SupportsFloat) -> List[StopEvent]:
        # TODO update CPE
        # TODO assert that the CPATs  are updated and the stops sorted accordingly
        # TODO optionally validate the travel time velocity constraints

        event_cache = []
        for stop_idx, stop in enumerate(
            stop for stop in self.stoplist if stop.estimated_arrival_time <= t
        ):
            # service the stop at its estimated arrival time
            event_cache.append(
                {
                    StopAction.pick_up: PickupEvent,
                    StopAction.drop_off: DeliveryEvent,
                    StopAction.internal: InternalStopEvent,
                }[stop.action](
                    request_id=stop.request,
                    vehicle_id=stop.vehicle_id,
                    timestamp=stop.estimated_arrival_time,
                )
            )

        # drop the visited stops, except for CPE
        self.stoplist = self.stoplist[1 : stop_idx + 1]
        # TODO should update CPE
        return event_cache

    def handle_request_single_vehicle(self, req: Request) -> SingleVehicleSolution:
        """
        The computational bottleneck. An efficient simulator could do the following:
        1. Parallelize this over all vehicles. This function being without any side effects, it should be easy to do.
        2. Implement as a c extension. The args and the return value are all basic c data types,
           so this should also be easy.

        Parameters
        ----------
        req
        stoplist

        Returns
        -------
        This returns the single best solution for the respective vehicle.
        """
        # TODO should this call fast_forward_time?
        ...
