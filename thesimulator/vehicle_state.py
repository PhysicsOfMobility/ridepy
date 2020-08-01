import operator as op

from typing import Optional, SupportsFloat

from .utils import Request, Stoplist, SingleVehicleSolution


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
        if stoplist is None:
            self._stoplist = []
        else:
            # TODO possibly updated the cpats here (i.e. travel time computation, or using the sub/superdiagonal
            #  [depending of the definition] of the [updated] distance matrix)
            # for i, stop in enumerate(stoplist):
            #     stop.cpat = D[i, i + 1]
            stoplist = sorted(stoplist, key=op.attrgetter("estimated_arrival_time"))
            self._stoplist = stoplist

    def fast_forward_time(self, t: SupportsFloat):
        for stop_idx, stop in enumerate(
            stop for stop in self.stoplist if stop.estimated_arrival_time <= t
        ):
            # TODO emit either a PickupEvent or a DeliveryEvent
            ...
            # TODO optionally validate the travel time velocity constraints

            # TODO assert that the cpats are updated and the stops sorted accordingly

            # drop the visited stops
        self.stoplist = self.stoplist[: stop_idx + 1]
        # TODO: re-add the current position stop (which has been dropped in the last step)
        ...

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
        """
        # TODO should this call fast_forward_time?
        ...
