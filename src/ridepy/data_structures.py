from numpy import inf
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, Union, Tuple, List, Callable


ID = Union[str, int]
"""Generic ID, could be vehicle ID, request ID, ..."""


@dataclass
class Request:
    """
    A request for the system to perform a task
    """

    request_id: ID
    creation_timestamp: float


@dataclass
class TransportationRequest(Request):
    """
    A request for the system to perform a transportation task,
    through creating a route through the system given spatio-temporal constraints.
    """

    origin: Any
    destination: Any
    # pickup_offset: float = 0
    pickup_timewindow_min: float = 0
    pickup_timewindow_max: float = inf
    delivery_timewindow_min: float = 0
    delivery_timewindow_max: float = inf


@dataclass
class InternalRequest(Request):
    """
    A request for the system to perform some action at a specific location
    that is not directly requested by a customer
    """

    location: Any


class StopAction(Enum):
    """
    Representing actions that the system may perform at a specific location
    """

    pickup = 1
    dropoff = 2
    internal = 3


class LocType(Enum):
    """
    Represents the kind of location objects the simulator supports. Either of:

    1. `R2LOC` (for points in :math:`\mathbb{R}^2`, holds a `Tuple[float, float]`).
    2. `INT` (for e.g. graphs).

    Note
    ----
    Use this for simulations using the pure python components. For simulations using cythonic components,
    the cython version of this enum i.e. :class:`.data_structures_cython.LocType` has to be used.
    """

    R2LOC = 1  # points in R^2
    INT = 2


@dataclass
class Stop:
    """
    The notion of an action to be performed in fulfilling a request.
    Attached are spatio-temporal constraints.

    Parameters
    ----------
    location:
        location at which the stop is supposed to be serviced
    """

    location: Any
    request: Request
    action: StopAction
    estimated_arrival_time: float
    occupancy_after_servicing: int = 0
    time_window_min: float = 0
    time_window_max: float = inf

    @property
    def estimated_departure_time(self):
        return max(
            self.estimated_arrival_time,
            self.time_window_min,
        )


class TransportSpace(ABC):
    @abstractmethod
    def d(self, u, v) -> Union[int, float]:
        """
        Return distance between points `u` and `v`.

        Parameters
        ----------
        u
            origin coordinate
        v
            destination coordinate

        Returns
        -------
        d
            distance
        """
        ...

    @abstractmethod
    def t(self, u, v) -> Union[int, float]:
        """
        Return travel time between points `u` and `v`.

        Parameters
        ----------
        u
            origin coordinate
        v
            destination coordinate

        Returns
        -------
        d
            travel time
        """

        ...

    @abstractmethod
    def random_point(self):
        """
        Return a random point on the space.

        Returns
        -------
            random point
        """
        ...

    @abstractmethod
    def interp_time(self, u, v, time_to_dest) -> Tuple[Any, Union[int, float]]:
        """
        Interpolate a location `x` between the origin `u` and the destination `v`
        as a function of the travel time between the unknown
        location and the destination `t(x, v) == time_to_dest`.

        Parameters
        ----------
        u
            origin coordinate
        v
            destination coordinate

        time_to_dest
            travel time from the unknown location `x` to the destination `v`

        Returns
        -------
        x
            interpolated coordinate of the unknown location `x`
        jump_dist
            remaining distance until the returned interpolated coordinate will be reached

        Note
        ----
        The notion of `jump_dist` is necessary in transport spaces whose locations are *discrete* (e.g. graphs). There
        if someone is travelling along a trajectory, at a certain time `t` one may be "in between" two locations `w` \
        and `x`. Then the "position" at time `t` is ill defined, and we must settle for the fact that its location
        *will be* `x` at `t+jump_time`.
        """
        ...

    @abstractmethod
    def interp_dist(
        self, origin, destination, dist_to_dest
    ) -> Tuple[Any, Union[int, float]]:
        """
        Interpolate a location `x` between the origin `u` and the destination `v`
        as a function of the distance between the unknown
        location and the destination `d(x, v) == dist_to_dest`.

        Parameters
        ----------
        u
            origin coordinate
        v
            destination coordinate

        dist_to_dest
            distance from the unknown location `x` to the destination `v`

        Returns
        -------
        x
            interpolated coordinate of the unknown location `x`
        jump_dist
            remaining distance until the returned interpolated coordinate will be reached
        """
        ...

    @abstractmethod
    def asdict(self) -> dict: ...

    def __eq__(self, other: "TransportSpace"):
        return type(self) == type(other) and self.asdict() == other.asdict()


Stoplist = List[Stop]
"""A list of `.Stop` objects. Specifies completely the current position and future actions a vehicle will make."""

DispatcherSolution = tuple[float, Stoplist, tuple[float, float, float, float]]
"""cost, updated_stoplist, (
    pickup_timewindow_min,
    pickup_timewindow_max,
    delivery_timewindow_min, 
    delivery_timewindow_max,
)

This is what a dispatcher returns. In case no solution is found, the cost is 
:math:`\infty` and the timewindow variables are ``None``.
"""

SingleVehicleSolution = tuple[ID, float, tuple[float, float, float, float]]
"""vehicle_id, cost, (
    pickup_timewindow_min,
    pickup_timewindow_max,
    delivery_timewindow_min, 
    delivery_timewindow_max,
)

This is what `VehicleState.handle_transportation_request_single_vehicle` returns. 
In case no solution is found, the cost is :math:`\infty` and the timewindow variables are `None`.
"""

Dispatcher = Callable[
    [
        TransportationRequest,
        Stoplist,
        TransportSpace,
        int,
    ],
    DispatcherSolution,
]
"""Defines the `Dispatcher` interface. Actual dispatchers are implemented in `.util.dispatchers`."""

Location = Union[int, float, tuple[float]]
