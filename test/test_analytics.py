import pytest

import itertools as it
import numpy as np
import pandas as pd

from numpy import nan, inf

from thesimulator.data_structures import (
    TransportationRequest,
)
from thesimulator.events import (
    RequestAcceptanceEvent,
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
    InternalEvent,
    VehicleStateEndEvent,
    VehicleStateBeginEvent,
    RequestEvent,
    RequestSubmissionEvent,
)
from thesimulator.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from thesimulator.util.spaces_cython import Euclidean2D as CyEuclidean2D
from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean1D, Euclidean2D
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist
from thesimulator.vehicle_state import VehicleState


def test_get_stops_and_requests():
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
            VehicleStateBeginEvent(vehicle_id=0, timestamp=0, location=(0, 0)),
            VehicleStateBeginEvent(vehicle_id=1, timestamp=0, location=(0, 0)),
            VehicleStateBeginEvent(vehicle_id=2, timestamp=0, location=(0, 0)),
            RequestSubmissionEvent(
                request_id=0,
                timestamp=0,
                origin=transportation_requests[0].origin,
                destination=transportation_requests[0].destination,
                pickup_timewindow_min=transportation_requests[0].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[0].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    0
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    0
                ].delivery_timewindow_max,
            ),
            RequestAcceptanceEvent(
                request_id=0,
                timestamp=0,
                origin=transportation_requests[0].origin,
                destination=transportation_requests[0].destination,
                pickup_timewindow_min=transportation_requests[0].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[0].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    0
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    0
                ].delivery_timewindow_max,
            ),
            RequestSubmissionEvent(
                request_id=1,
                timestamp=0,
                origin=transportation_requests[1].origin,
                destination=transportation_requests[1].destination,
                pickup_timewindow_min=transportation_requests[1].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[1].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    1
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    1
                ].delivery_timewindow_max,
            ),
            RequestAcceptanceEvent(
                request_id=1,
                timestamp=0,
                origin=transportation_requests[1].origin,
                destination=transportation_requests[1].destination,
                pickup_timewindow_min=transportation_requests[1].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[1].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    1
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    1
                ].delivery_timewindow_max,
            ),
            RequestSubmissionEvent(
                request_id=2,
                timestamp=0,
                origin=transportation_requests[2].origin,
                destination=transportation_requests[2].destination,
                pickup_timewindow_min=transportation_requests[2].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[2].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    2
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    2
                ].delivery_timewindow_max,
            ),
            RequestAcceptanceEvent(
                request_id=2,
                timestamp=0,
                origin=transportation_requests[2].origin,
                destination=transportation_requests[2].destination,
                pickup_timewindow_min=transportation_requests[2].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[2].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    2
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    2
                ].delivery_timewindow_max,
            ),
            RequestSubmissionEvent(
                request_id=3,
                timestamp=2,
                origin=transportation_requests[3].origin,
                destination=transportation_requests[3].destination,
                pickup_timewindow_min=transportation_requests[3].pickup_timewindow_min,
                pickup_timewindow_max=transportation_requests[3].pickup_timewindow_max,
                delivery_timewindow_min=transportation_requests[
                    3
                ].delivery_timewindow_min,
                delivery_timewindow_max=transportation_requests[
                    3
                ].delivery_timewindow_max,
            ),
            RequestRejectionEvent(request_id=3, timestamp=2),
            PickupEvent(request_id=0, timestamp=0, vehicle_id=0),
            PickupEvent(request_id=1, timestamp=0.1, vehicle_id=0),
            DeliveryEvent(request_id=1, timestamp=0.2, vehicle_id=0),
            DeliveryEvent(request_id=0, timestamp=0.3, vehicle_id=0),
            PickupEvent(request_id=2, timestamp=1, vehicle_id=1),
            DeliveryEvent(request_id=2, timestamp=2, vehicle_id=1),
            VehicleStateEndEvent(
                vehicle_id=0,
                timestamp=2,
                location=transportation_requests[0].destination,
            ),
            VehicleStateEndEvent(
                vehicle_id=1,
                timestamp=2,
                location=transportation_requests[2].destination,
            ),
            VehicleStateEndEvent(vehicle_id=2, timestamp=2, location=(0, 0)),
        ]

        stops, requests = get_stops_and_requests(events=events, space=space)
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
                ("submitted", "timestamp"): {0: 0, 1: 0, 2: 1, 3: 2},
            }
        )

        assert all(stops.reset_index() == expected_stops)
        assert all(requests.reset_index() == expected_requests)

        plot_occupancy_hist(stops)


def test_get_stops_and_requests_with_actual_simulation():
    space = Euclidean1D()
    rg = RandomRequestGenerator(rate=10, space=space)
    transportation_requests = list(it.islice(rg, 1000))

    fs = SlowSimpleFleetState(
        initial_locations={k: 0 for k in range(10)},
        seat_capacities=10,
        space=space,
        dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
        vehicle_state_class=VehicleState,
    )

    events = list(fs.simulate(transportation_requests))

    stops, requests = get_stops_and_requests(events=events, space=space)

    assert len(stops) == 2020
    assert len(requests) == 1000
