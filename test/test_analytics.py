import itertools as it
import numpy as np
import pandas as pd

from pandas.testing import assert_frame_equal
from numpy import nan, inf

from ridepy.data_structures import (
    TransportationRequest,
)
from ridepy.events import (
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
    VehicleStateEndEvent,
    VehicleStateBeginEvent,
    RequestSubmissionEvent,
)
from ridepy.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from ridepy.util.spaces_cython import Euclidean2D as CyEuclidean2D
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.util.dispatchers import BruteForceTotalTravelTimeMinimizingDispatcher
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean1D, Euclidean2D
from ridepy.util.analytics import (
    get_stops_and_requests,
    get_system_quantities,
    get_vehicle_quantities,
    _add_insertion_stats_to_stoplist_dataframe,
)
from ridepy.util.analytics.plotting import plot_occupancy_hist
from ridepy.vehicle_state import VehicleState


def test_get_stops_and_requests_and_get_quantities():
    make_transportation_requests = lambda transp_req_class: [
        transp_req_class(
            request_id=0,
            creation_timestamp=0,
            origin=(0, 0.0),
            destination=(0, 0.3),
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        transp_req_class(
            request_id=1,
            creation_timestamp=0,
            origin=(0, 0.1),
            destination=(0, 0.2),
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        transp_req_class(
            request_id=2,
            creation_timestamp=1,
            origin=(0, 1),
            destination=(0, 0),
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        transp_req_class(
            request_id=3,
            creation_timestamp=2,
            origin=(0, 0),
            destination=(0, 1),
            pickup_timewindow_min=0,
            pickup_timewindow_max=0,
            delivery_timewindow_min=0,
            delivery_timewindow_max=0,
        ),
    ]

    for transportation_requests, space in zip(
        map(
            make_transportation_requests,
            [TransportationRequest, CyTransportationRequest],
        ),
        [Euclidean2D(), CyEuclidean2D()],
    ):
        events = [
            {
                "event_type": "VehicleStateBeginEvent",
                "vehicle_id": 0,
                "timestamp": 0,
                "location": (0, 0),
                "request_id": -100,
            },
            {
                "event_type": "VehicleStateBeginEvent",
                "vehicle_id": 1,
                "timestamp": 0,
                "location": (0, 0),
                "request_id": -100,
            },
            {
                "event_type": "VehicleStateBeginEvent",
                "vehicle_id": 2,
                "timestamp": 0,
                "location": (0, 0),
                "request_id": -100,
            },
            {
                "event_type": "RequestSubmissionEvent",
                "request_id": 0,
                "timestamp": 0,
                "origin": transportation_requests[0].origin,
                "destination": transportation_requests[0].destination,
                "pickup_timewindow_min": transportation_requests[
                    0
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    0
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    0
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    0
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestAcceptanceEvent",
                "request_id": 0,
                "timestamp": 0,
                "origin": transportation_requests[0].origin,
                "destination": transportation_requests[0].destination,
                "pickup_timewindow_min": transportation_requests[
                    0
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    0
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    0
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    0
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestSubmissionEvent",
                "request_id": 1,
                "timestamp": 0,
                "origin": transportation_requests[1].origin,
                "destination": transportation_requests[1].destination,
                "pickup_timewindow_min": transportation_requests[
                    1
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    1
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    1
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    1
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestAcceptanceEvent",
                "request_id": 1,
                "timestamp": 0,
                "origin": transportation_requests[1].origin,
                "destination": transportation_requests[1].destination,
                "pickup_timewindow_min": transportation_requests[
                    1
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    1
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    1
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    1
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestSubmissionEvent",
                "request_id": 2,
                "timestamp": 0,
                "origin": transportation_requests[2].origin,
                "destination": transportation_requests[2].destination,
                "pickup_timewindow_min": transportation_requests[
                    2
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    2
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    2
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    2
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestAcceptanceEvent",
                "request_id": 2,
                "timestamp": 0,
                "origin": transportation_requests[2].origin,
                "destination": transportation_requests[2].destination,
                "pickup_timewindow_min": transportation_requests[
                    2
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    2
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    2
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    2
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestSubmissionEvent",
                "request_id": 3,
                "timestamp": 2,
                "origin": transportation_requests[3].origin,
                "destination": transportation_requests[3].destination,
                "pickup_timewindow_min": transportation_requests[
                    3
                ].pickup_timewindow_min,
                "pickup_timewindow_max": transportation_requests[
                    3
                ].pickup_timewindow_max,
                "delivery_timewindow_min": transportation_requests[
                    3
                ].delivery_timewindow_min,
                "delivery_timewindow_max": transportation_requests[
                    3
                ].delivery_timewindow_max,
            },
            {
                "event_type": "RequestRejectionEvent",
                "timestamp": 2,
                "request_id": 3,
            },
            {
                "event_type": "PickupEvent",
                "timestamp": 0,
                "request_id": 0,
                "vehicle_id": 0,
            },
            {
                "event_type": "PickupEvent",
                "timestamp": 0.1,
                "request_id": 1,
                "vehicle_id": 0,
            },
            {
                "event_type": "DeliveryEvent",
                "timestamp": 0.2,
                "request_id": 1,
                "vehicle_id": 0,
            },
            {
                "event_type": "DeliveryEvent",
                "timestamp": 0.3,
                "request_id": 0,
                "vehicle_id": 0,
            },
            {
                "event_type": "PickupEvent",
                "timestamp": 1,
                "request_id": 2,
                "vehicle_id": 1,
            },
            {
                "event_type": "DeliveryEvent",
                "timestamp": 2,
                "request_id": 2,
                "vehicle_id": 1,
            },
            {
                "event_type": "VehicleStateEndEvent",
                "timestamp": 2,
                "vehicle_id": 0,
                "location": transportation_requests[0].destination,
                "request_id": -200,
            },
            {
                "event_type": "VehicleStateEndEvent",
                "timestamp": 2,
                "vehicle_id": 1,
                "location": transportation_requests[2].destination,
                "request_id": -200,
            },
            {
                "event_type": "VehicleStateEndEvent",
                "timestamp": 2,
                "vehicle_id": 2,
                "location": (0, 0),
                "request_id": -200,
            },
        ]

        stops, requests = get_stops_and_requests(events=events, space=space)
        stops = _add_insertion_stats_to_stoplist_dataframe(
            reqs=requests, stops=stops, space=space
        )

        expected_stops = pd.DataFrame(
            {
                "vehicle_id": {
                    0: 0.0,
                    1: 0.0,
                    2: 0.0,
                    3: 0.0,
                    4: 0.0,
                    5: 0.0,
                    6: 1.0,
                    7: 1.0,
                    8: 1.0,
                    9: 1.0,
                    10: 2.0,
                    11: 2.0,
                },
                "stop_id": {
                    0: 0,
                    1: 1,
                    2: 2,
                    3: 3,
                    4: 4,
                    5: 5,
                    6: 0,
                    7: 1,
                    8: 2,
                    9: 3,
                    10: 0,
                    11: 1,
                },
                "timestamp": {
                    0: 0.0,
                    1: 0.0,
                    2: 0.1,
                    3: 0.2,
                    4: 0.3,
                    5: 2.0,
                    6: 0.0,
                    7: 1.0,
                    8: 2.0,
                    9: 2.0,
                    10: 0.0,
                    11: 2.0,
                },
                "delta_occupancy": {
                    0: 0.0,
                    1: 1.0,
                    2: 1.0,
                    3: -1.0,
                    4: -1.0,
                    5: 0.0,
                    6: 0.0,
                    7: 1.0,
                    8: -1.0,
                    9: 0.0,
                    10: 0.0,
                    11: 0.0,
                },
                "request_id": {
                    0: -100,
                    1: 0,
                    2: 1,
                    3: 1,
                    4: 0,
                    5: -200,
                    6: -100,
                    7: 2,
                    8: 2,
                    9: -200,
                    10: -100,
                    11: -200,
                },
                "state_duration": {
                    0: 0.0,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 1.7,
                    5: 0.0,
                    6: 1.0,
                    7: 1.0,
                    8: 0.0,
                    9: 0.0,
                    10: 2.0,
                    11: 0.0,
                },
                "occupancy": {
                    0: 0.0,
                    1: 1.0,
                    2: 2.0,
                    3: 1.0,
                    4: 0.0,
                    5: 0.0,
                    6: 0.0,
                    7: 1.0,
                    8: 0.0,
                    9: 0.0,
                    10: 0.0,
                    11: 0.0,
                },
                "location": {
                    0: (0, 0),
                    1: (0, 0.0),
                    2: (0, 0.1),
                    3: (0, 0.2),
                    4: (0, 0.3),
                    5: (0, 0.3),
                    6: (0, 0),
                    7: (0, 1),
                    8: (0, 0),
                    9: (0, 0),
                    10: (0, 0),
                    11: (0, 0),
                },
                "dist_to_next": {
                    0: 0.0,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 0.0,
                    5: nan,
                    6: 1.0,
                    7: 1.0,
                    8: 0.0,
                    9: nan,
                    10: 0.0,
                    11: nan,
                },
                "time_to_next": {
                    0: 0.0,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 0.0,
                    5: nan,
                    6: 1.0,
                    7: 1.0,
                    8: 0.0,
                    9: nan,
                    10: 0.0,
                    11: nan,
                },
                "timestamp_submitted": {
                    0: nan,
                    1: 0.0,
                    2: 0.0,
                    3: 0.0,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "insertion_index": {
                    0: nan,
                    1: 0.0,
                    2: 1.0,
                    3: 2.0,
                    4: 3.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 1.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_1_dist_service_time": {
                    0: nan,
                    1: 0.0,
                    2: 0.0,
                    3: 0.0,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_2_dist_service_time": {
                    0: nan,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 1.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_direct_dist_service_time": {
                    0: nan,
                    1: 0.0,
                    2: 0.0,
                    3: 0.0,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "detour_dist_service_time": {
                    0: nan,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 1.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_1_dist_submission_time": {
                    0: nan,
                    1: 0.0,
                    2: 0.1,
                    3: 0.1,
                    4: 0.09999999999999998,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 1.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_2_dist_submission_time": {
                    0: nan,
                    1: 0.1,
                    2: 0.1,
                    3: 0.09999999999999998,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 1.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "leg_direct_dist_submission_time": {
                    0: nan,
                    1: 0.0,
                    2: 0.2,
                    3: 0.19999999999999998,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "detour_dist_submission_time": {
                    0: nan,
                    1: 0.1,
                    2: 0.0,
                    3: 0.0,
                    4: 0.09999999999999998,
                    5: nan,
                    6: nan,
                    7: 1.0,
                    8: 1.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "stoplist_length_submission_time": {
                    0: nan,
                    1: 2.0,
                    2: 2.0,
                    3: 2.0,
                    4: 2.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "stoplist_length_service_time": {
                    0: nan,
                    1: 2.0,
                    2: 1.0,
                    3: 1.0,
                    4: 0.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_segment_dist_submission_time": {
                    0: nan,
                    1: 0.09999999999999999,
                    2: 0.05,
                    3: 0.05,
                    4: 0.09999999999999999,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_segment_time_submission_time": {
                    0: nan,
                    1: 0.09999999999999999,
                    2: 0.05,
                    3: 0.05,
                    4: 0.09999999999999999,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_segment_dist_service_time": {
                    0: nan,
                    1: 0.09999999999999999,
                    2: 0.0,
                    3: 0.0,
                    4: nan,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_segment_time_service_time": {
                    0: nan,
                    1: 0.09999999999999999,
                    2: 0.0,
                    3: 0.0,
                    4: nan,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "system_stoplist_length_submission_time": {
                    0: nan,
                    1: 4.0,
                    2: 4.0,
                    3: 4.0,
                    4: 4.0,
                    5: nan,
                    6: nan,
                    7: 4.0,
                    8: 4.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "system_stoplist_length_service_time": {
                    0: nan,
                    1: 4.0,
                    2: 3.0,
                    3: 3.0,
                    4: 2.0,
                    5: nan,
                    6: nan,
                    7: 0.0,
                    8: 0.0,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_system_segment_dist_submission_time": {
                    0: nan,
                    1: 0.3,
                    2: 0.275,
                    3: 0.275,
                    4: 0.3,
                    5: nan,
                    6: nan,
                    7: 0.075,
                    8: 0.075,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_system_segment_time_submission_time": {
                    0: nan,
                    1: 0.3,
                    2: 0.275,
                    3: 0.275,
                    4: 0.3,
                    5: nan,
                    6: nan,
                    7: 0.075,
                    8: 0.075,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_system_segment_dist_service_time": {
                    0: nan,
                    1: 0.3,
                    2: 0.3333333333333333,
                    3: 0.3333333333333333,
                    4: 0.5,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "avg_system_segment_time_service_time": {
                    0: nan,
                    1: 0.3,
                    2: 0.3333333333333333,
                    3: 0.3333333333333333,
                    4: 0.5,
                    5: nan,
                    6: nan,
                    7: nan,
                    8: nan,
                    9: nan,
                    10: nan,
                    11: nan,
                },
                "relative_insertion_position": {
                    0: 1.0,
                    1: 0.0,
                    2: 0.5,
                    3: 1.0,
                    4: 1.5,
                    5: 1.0,
                    6: 1.0,
                    7: 1.0,
                    8: 1.0,
                    9: 1.0,
                    10: 1.0,
                    11: 1.0,
                },
            }
        )
        expected_requests = pd.DataFrame(
            {
                ("request_id", ""): {0: 0, 1: 1, 2: 2, 3: 3},
                ("accepted", "delivery_timewindow_max"): {
                    0: inf,
                    1: inf,
                    2: inf,
                    3: nan,
                },
                ("accepted", "delivery_timewindow_min"): {
                    0: 0.0,
                    1: 0.0,
                    2: 0.0,
                    3: nan,
                },
                ("accepted", "destination"): {
                    0: (0, 0.3),
                    1: (0, 0.2),
                    2: (0, 0.0),
                    3: nan,
                },
                ("accepted", "origin"): {0: (0, 0.0), 1: (0, 0.1), 2: (0, 1.0), 3: nan},
                ("accepted", "pickup_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: nan},
                ("accepted", "pickup_timewindow_min"): {0: 0.0, 1: 0.0, 2: 0.0, 3: nan},
                ("accepted", "timestamp"): {0: 0.0, 1: 0.0, 2: 0.0, 3: nan},
                ("inferred", "relative_travel_time"): {0: 1.0, 1: 1.0, 2: 1.0, 3: nan},
                ("inferred", "travel_time"): {0: 0.3, 1: 0.1, 2: 1.0, 3: nan},
                ("inferred", "waiting_time"): {0: 0.0, 1: 0.1, 2: 1.0, 3: nan},
                ("rejected", "timestamp"): {0: nan, 1: nan, 2: nan, 3: 2.0},
                ("serviced", "timestamp_dropoff"): {0: 0.3, 1: 0.2, 2: 2.0, 3: nan},
                ("serviced", "timestamp_pickup"): {0: 0.0, 1: 0.1, 2: 1.0, 3: nan},
                ("serviced", "vehicle_id"): {0: 0.0, 1: 0.0, 2: 1.0, 3: nan},
                ("submitted", "delivery_timewindow_max"): {
                    0: inf,
                    1: inf,
                    2: inf,
                    3: 0,
                },
                ("submitted", "delivery_timewindow_min"): {0: 0, 1: 0, 2: 0, 3: 0},
                ("submitted", "destination"): {
                    0: (0, 0.3),
                    1: (0, 0.2),
                    2: (0, 0.0),
                    3: (0, 1),
                },
                ("submitted", "direct_travel_distance"): {
                    0: 0.3,
                    1: 0.1,
                    2: 1.0,
                    3: 1.0,
                },
                ("submitted", "direct_travel_time"): {0: 0.3, 1: 0.1, 2: 1.0, 3: 1.0},
                ("submitted", "origin"): {
                    0: (0, 0.0),
                    1: (0, 0.1),
                    2: (0, 1.0),
                    3: (0, 0),
                },
                ("submitted", "pickup_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: 0},
                ("submitted", "pickup_timewindow_min"): {0: 0, 1: 0, 2: 0, 3: 0},
                ("submitted", "timestamp"): {0: 0, 1: 0, 2: 0, 3: 2},
            }
        ).rename_axis(["source", "quantity"], axis=1)

        for col in [
            ("submitted", "pickup_timewindow_min"),
            ("submitted", "delivery_timewindow_min"),
            ("submitted", "timestamp"),
        ]:
            expected_requests[col] = expected_requests[col].astype("f8")

        assert_frame_equal(stops.reset_index(), expected_stops)
        assert_frame_equal(requests.reset_index(), expected_requests)

        expected_vehicle_quantities = pd.DataFrame(
            {
                "vehicle_id": {0: 0.0, 1: 1.0, 2: 2.0},
                "avg_occupancy": {
                    0: (0.1 + 0.1 * 2 + 0.1) / (0.1 + 0.1 + 0.1 + 1.7),
                    1: 1 / 2,
                    2: 0.0,
                },
                "avg_segment_dist": {0: (0.1 + 0.1 + 0.1) / 5, 1: (1 + 1) / 3, 2: 0.0},
                "avg_segment_time": {0: (0.1 + 0.1 + 0.1) / 5, 1: (1 + 1) / 3, 2: 0.0},
                "total_dist_driven": {0: 0.3, 1: 2.0, 2: 0.0},
                "total_time_driven": {0: 0.3, 1: 2.0, 2: 0.0},
                "avg_direct_dist": {
                    0: 0.2,
                    1: 1,
                    2: nan,
                },
                "avg_direct_time": {
                    0: 0.2,
                    1: 1,
                    2: nan,
                },
                "total_direct_dist": {0: 0.4, 1: 1.0, 2: nan},
                "total_direct_time": {0: 0.4, 1: 1.0, 2: nan},
                "efficiency_dist": {0: 1.3333333333333335, 1: 0.5, 2: nan},
                "efficiency_time": {0: 1.3333333333333335, 1: 0.5, 2: nan},
                "avg_system_stoplist_length_service_time": {0: 2.2, 1: 0.0, 2: 0.0},
                "avg_system_stoplist_length_submission_time": {0: 4.0, 1: 2.0, 2: 0.0},
                "avg_stoplist_length_service_time": {0: 0.2, 1: 0.0, 2: 0.0},
                "avg_stoplist_length_submission_time": {0: 2.0, 1: 0.0, 2: 0.0},
            }
        )
        assert_frame_equal(
            get_vehicle_quantities(stops, requests).reset_index(),
            expected_vehicle_quantities,
        )

        expected_system_quantities = {
            "avg_occupancy": (0.1 + 0.1 * 2 + 0.1 + 1)
            / (0.1 + 0.1 + 0.1 + 1.7 + 1 + 1 + 2),
            "avg_segment_dist": (0.1 + 0.1 + 0.1 + 1 + 1) / (5 + 3 + 1),
            "avg_segment_time": (0.1 + 0.1 + 0.1 + 1 + 1) / (5 + 3 + 1),
            "total_dist_driven": 0.1 + 0.1 + 0.1 + 1 + 1,
            "total_time_driven": 0.1 + 0.1 + 0.1 + 1 + 1,
            "avg_direct_dist": (0.3 + 0.1 + 1) / 3,
            "avg_direct_time": (0.3 + 0.1 + 1) / 3,
            "total_direct_dist": 0.3 + 0.1 + 1,
            "total_direct_time": 0.3 + 0.1 + 1,
            "efficiency_dist": (0.3 + 0.1 + 1) / (0.1 + 0.1 + 0.1 + 1 + 1),
            "efficiency_time": (0.3 + 0.1 + 1) / (0.1 + 0.1 + 0.1 + 1 + 1),
            "avg_waiting_time": (0 + 0.1 + 1) / 3,
            "median_stoplist_length": np.median([3, 2, 1, 0, 0, 2, 1, 0, 0, 0]),
            "rejection_ratio": 0.25,
            "avg_detour": 1.0,
            "avg_system_stoplist_length_service_time": 1.4666666666666668,
            "avg_system_stoplist_length_submission_time": 4.0,
            "avg_stoplist_length_service_time": 0.13333333333333333,
            "avg_stoplist_length_submission_time": 1.3333333333333333,
        }

        assert get_system_quantities(stops, requests) == expected_system_quantities

        plot_occupancy_hist(stops)


def test_get_stops_and_requests_with_actual_simulation():
    space = Euclidean1D()
    rg = RandomRequestGenerator(rate=10, space=space)
    transportation_requests = list(it.islice(rg, 1000))

    fs = SlowSimpleFleetState(
        initial_locations={k: 0 for k in range(10)},
        seat_capacities=10,
        space=space,
        dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(),
        vehicle_state_class=VehicleState,
    )

    events = list(fs.simulate(transportation_requests))

    stops, requests = get_stops_and_requests(events=events, space=space)

    assert len(stops) == 2020
    assert len(requests) == 1000
