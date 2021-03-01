from numpy import inf
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Union, Tuple, List, Callable

ID = Union[str, int]


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
    pickup_timewindow_min: Optional[float]
    pickup_timewindow_max: Optional[float]
    delivery_timewindow_min: Optional[float]
    delivery_timewindow_max: Optional[float]


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
    Representing the kind of location objects the simulator supports.
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
    time_window_min: Optional[float] = 0
    time_window_max: Optional[float] = inf

    @property
    def estimated_departure_time(self):
        return max(
            self.estimated_arrival_time,
            self.time_window_min if self.time_window_min else 0,
        )


@dataclass
class RequestAcceptanceEvent:
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.
    """

    request_id: ID
    timestamp: float
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


@dataclass
class RequestAssignEvent:
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.
    """

    request_id: ID
    timestamp: float
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


@dataclass
class RequestRejectionEvent:
    """
    Inability of the system to fulfil a request.
    """

    request_id: ID
    timestamp: float


@dataclass
class PickupEvent:
    """
    Successful pick-up action
    """

    request_id: ID
    timestamp: float
    vehicle_id: ID


@dataclass
class DeliveryEvent:
    """
    Successful drop-off action
    """

    request_id: ID
    timestamp: float
    vehicle_id: ID


@dataclass
class InternalStopEvent:
    """
    Successful internal action
    """

    timestamp: float
    vehicle_id: ID


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
        jump_time
            remaining time until the returned interpolated coordinate will be reached
        """
        ...


RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
    InternalStopEvent,
    RequestAssignEvent,
]
Stoplist = List[Stop]
SingleVehicleSolution = Tuple[
    float, Optional[Stoplist], Tuple[float, float, float, float]
]
"""vehicle_id, cost, new_stop_list"""
RequestEvent = Union[RequestAcceptanceEvent, RequestRejectionEvent]
StopEvent = Union[InternalStopEvent, PickupEvent, DeliveryEvent]
Dispatcher = Callable[
    [
        TransportationRequest,
        Stoplist,
        TransportSpace,
    ],
    Tuple[float, Stoplist, Tuple[float, float, float, float]],
]
