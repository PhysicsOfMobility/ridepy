from dataclasses import dataclass
from typing import Any, Union

from thesimulator.data_structures import ID


@dataclass
class Event:
    """
    The base event class. Must hold a timestamp.
    """

    timestamp: float


@dataclass
class RequestAcceptanceEvent(Event):
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.
    """

    request_id: ID
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


@dataclass
class RequestAssignEvent(Event):
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.
    """

    request_id: ID
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


@dataclass
class RequestRejectionEvent(Event):
    """
    Inability of the system to fulfil a request.
    """

    request_id: ID


@dataclass
class PickupEvent(Event):
    """
    Successful pick-up action.
    """

    request_id: ID
    vehicle_id: ID


@dataclass
class DeliveryEvent(Event):
    """
    Successful drop-off action.
    """

    request_id: ID
    vehicle_id: ID


@dataclass
class InternalStopEvent(Event):
    """
    Successful internal action.
    """

    vehicle_id: ID


RequestEvent = Union[RequestAcceptanceEvent, RequestRejectionEvent]
StopEvent = Union[InternalStopEvent, PickupEvent, DeliveryEvent]
RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
Event = Union[
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
    InternalStopEvent,
    RequestAssignEvent,
]