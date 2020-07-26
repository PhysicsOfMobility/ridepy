from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class Request:
    req_id: str
    origin: Any
    destination: Any
    creation_timestamp: float
    pickup_offset: float = 0


class StopAction(Enum):
    PickUP = 1
    DropOff = 2


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


class PickupEvent:
    request_id: Any
    timestamp: float
    vehicle_id: Any


class DeliveryEvent:
    request_id: Any
    timestamp: float
    vehicle_id: Any
