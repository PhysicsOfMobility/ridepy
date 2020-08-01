from enum import Enum
from dataclasses import dataclass
from typing import Any, Union, MutableSequence, Tuple


@dataclass
class Request:
    """
    A request for the system to perform a task
    """

    request_id: str
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
    pickup_timewindow_min: Union[float, None]
    pickup_timewindow_max: Union[float, None]
    delivery_timewindow_min: Union[float, None]
    delivery_timewindow_max: Union[float, None]


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

    pick_up = 1
    drop_off = 2
    internal = 3


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
    vehicle_id: Any
    request: Request
    action: StopAction
    estimated_arrival_time: float
    time_window_min: float
    time_window_max: float


@dataclass
class RequestAcceptanceEvent:
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.
    """

    request_id: Any
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

    request_id: Any
    timestamp: float


@dataclass
class PickupEvent:
    """
    Successful pick-up action
    """

    request_id: Any
    timestamp: float
    vehicle_id: Any


@dataclass
class DeliveryEvent:
    """
    Successful drop-off action
    """

    request_id: Any
    timestamp: float
    vehicle_id: Any


@dataclass
class InternalStopEvent:
    """
    Successful internal action
    """

    request_id: Any
    timestamp: float
    vehicle_id: Any


RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[RequestAcceptanceEvent, RequestRejectionEvent, PickupEvent, DeliveryEvent]
Stoplist = MutableSequence[Stop]
SingleVehicleSolution = Tuple[int, float, Stoplist]
"""vehicle_id, cost, new_stop_list"""
RequestEvent = Union[RequestAcceptanceEvent, RequestRejectionEvent]
StopEvent = Union[InternalStopEvent, PickupEvent, DeliveryEvent]
