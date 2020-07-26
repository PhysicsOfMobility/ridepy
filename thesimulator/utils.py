from dataclasses import dataclass
from enum import Enum
from typing import Any, Union


@dataclass
class Request:
    req_id: str
    creation_timestamp: float


@dataclass
class TransportationRequest(Request):
    origin: Any
    destination: Any
    # pickup_offset: float = 0
    pickup_timewindow_min: Union[float, None]
    pickup_timewindow_max: Union[float, None]
    delivery_timewindow_min: Union[float, None]
    delivery_timewindow_max: Union[float, None]


@dataclass
class InternalRequest(Request):
    location: Any


class StopAction(Enum):
    pick_up = 1
    drop_off = 2
    internal = 3


@dataclass
class Stop:
    location: Any
    request: Request
    action: StopAction
    estimated_arrival_time: float
    time_window_min: float
    time_window_max: float


@dataclass
class RequestAcceptanceEvent:
    request_id: Any
    timestamp: float
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


@dataclass
class RequestRejectionEvent:
    request_id: Any
    timestamp: float


@dataclass
class PickupEvent:
    request_id: Any
    timestamp: float
    vehicle_id: Any


@dataclass
class DeliveryEvent:
    request_id: Any
    timestamp: float
    vehicle_id: Any


@dataclass
class InternalStopEvent:
    request_id: Any
    timestamp: float
    vehicle_id: Any
