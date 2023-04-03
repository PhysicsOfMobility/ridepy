from typing import Any, Union, TypedDict

from ridepy.data_structures import ID


class Event(TypedDict):
    """
    The base event class. Must hold a timestamp.

    .. code-block:: python

        event = {
            "event_type": "Event",
            "timestamp": ...,
        }

    """

    event_type: str
    timestamp: float


class RequestSubmissionEvent(Event):
    """
    Submission of a request with specific spatio-temporal constraints to the system.

    .. code-block:: python

        request_submission_event = {
            "event_type": "RequestSubmissionEvent",
            "timestamp": ...,
            "request_id": ...,
            "origin": ...,
            "destination": ...,
            "pickup_timewindow_min": ...,
            "pickup_timewindow_max": ...,
            "delivery_timewindow_min": ...,
            "delivery_timewindow_max": ...,
        }

    """

    request_id: ID
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


class RequestAcceptanceEvent(Event):
    """
    Commitment of the system to fulfil a request given
    the returned spatio-temporal constraints.

    .. code-block:: python

        request_acceptance_event = {
            "event_type": "RequestAcceptanceEvent",
            "timestamp": ...,
            "request_id": ...,
            "origin": ...,
            "destination": ...,
            "pickup_timewindow_min": ...,
            "pickup_timewindow_max": ...,
            "delivery_timewindow_min": ...,
            "delivery_timewindow_max": ...,
        }

    """

    request_id: ID
    origin: Any
    destination: Any
    pickup_timewindow_min: float
    pickup_timewindow_max: float
    delivery_timewindow_min: float
    delivery_timewindow_max: float


class RequestRejectionEvent(Event):
    """
    Inability of the system to fulfil a request.

    .. code-block:: python

        request_rejection_event = {
            "event_type": "RequestRejectionEvent",
            "timestamp": ...,
            "request_id": ...,
        }

    """

    request_id: ID


class PickupEvent(Event):
    """
    Successful pick-up action.

    .. code-block:: python

        pickup_event = {
            "event_type": "PickupEvent",
            "timestamp": ...,
            "request_id": ...,
            "vehicle_id": ...,
        }

    """

    request_id: ID
    vehicle_id: ID


class DeliveryEvent(Event):
    """
    Successful drop-off action.

    .. code-block:: python

        delivery_event = {
            "event_type": "DeliveryEvent",
            "timestamp": ...,
            "request_id": ...,
            "vehicle_id": ...,
        }

    """

    request_id: ID
    vehicle_id: ID


class InternalEvent(Event):
    """
    Successful internal action.

    .. code-block:: python

        internal_event = {
            "event_type": "InternalEvent",
            "timestamp": ...,
            "vehicle_id": ...,
        }

    """

    vehicle_id: ID


class VehicleStateBeginEvent(InternalEvent):
    """
    .. code-block:: python

        vehicle_state_begin_event = {
            "event_type": "VehicleStateBeginEvent",
            "timestamp": ...,
            "vehicle_id": ...,
            "location": ...,
            "request_id": -100,
        }

    """

    location: Any
    request_id: ID


class VehicleStateEndEvent(InternalEvent):
    """
    .. code-block:: python

        vehicle_state_end_event = {
            "event_type": "VehicleStateEndEvent",
            "timestamp": ...,
            "vehicle_id": ...,
            "location": ...,
            "request_id": -200,
        }

    """

    location: Any
    request_id: ID


RequestEvent = Union[
    RequestSubmissionEvent, RequestAcceptanceEvent, RequestRejectionEvent
]
"""Emitted when a `.TransportationRequest` is handled."""

StopEvent = Union[InternalEvent, PickupEvent, DeliveryEvent]
"""Emitted when a `.Stop` is serviced."""

RequestResponse = Union[RequestAcceptanceEvent, RequestRejectionEvent]
"""Emitted when a `.TransportationRequest` is handled."""
