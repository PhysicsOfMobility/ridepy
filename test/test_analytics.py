import pytest

import itertools as it
import numpy as np
import pandas as pd

from numpy import nan, inf

from thesimulator.data_structures import (
    TransportationRequest,
    RequestAcceptanceEvent,
    PickupEvent,
    DeliveryEvent,
    RequestRejectionEvent,
)
from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean1D, Euclidean2D
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist


@pytest.mark.n_buses(3)
def test_get_stops_and_requests(initial_stoplists):
    space = Euclidean1D()
    transportation_requests = [
        TransportationRequest(
            request_id=0,
            creation_timestamp=0,
            origin=0.0,
            destination=0.3,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        TransportationRequest(
            request_id=1,
            creation_timestamp=0,
            origin=0.1,
            destination=0.2,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        TransportationRequest(
            request_id=2,
            creation_timestamp=1,
            origin=1,
            destination=0,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        TransportationRequest(
            request_id=3,
            creation_timestamp=2,
            origin=0,
            destination=1,
            pickup_timewindow_min=0,
            pickup_timewindow_max=0,
            delivery_timewindow_min=0,
            delivery_timewindow_max=0,
        ),
    ]
    events = [
        RequestAcceptanceEvent(
            request_id=0,
            timestamp=0,
            origin=transportation_requests[0].origin,
            destination=transportation_requests[0].destination,
            pickup_timewindow_min=transportation_requests[0].pickup_timewindow_min,
            pickup_timewindow_max=transportation_requests[0].pickup_timewindow_max,
            delivery_timewindow_min=transportation_requests[0].delivery_timewindow_min,
            delivery_timewindow_max=transportation_requests[0].delivery_timewindow_max,
        ),
        RequestAcceptanceEvent(
            request_id=1,
            timestamp=0,
            origin=transportation_requests[1].origin,
            destination=transportation_requests[1].destination,
            pickup_timewindow_min=transportation_requests[1].pickup_timewindow_min,
            pickup_timewindow_max=transportation_requests[1].pickup_timewindow_max,
            delivery_timewindow_min=transportation_requests[1].delivery_timewindow_min,
            delivery_timewindow_max=transportation_requests[1].delivery_timewindow_max,
        ),
        RequestAcceptanceEvent(
            request_id=2,
            timestamp=0,
            origin=transportation_requests[2].origin,
            destination=transportation_requests[2].destination,
            pickup_timewindow_min=transportation_requests[2].pickup_timewindow_min,
            pickup_timewindow_max=transportation_requests[2].pickup_timewindow_max,
            delivery_timewindow_min=transportation_requests[2].delivery_timewindow_min,
            delivery_timewindow_max=transportation_requests[2].delivery_timewindow_max,
        ),
        RequestRejectionEvent(request_id=3, timestamp=2),
        PickupEvent(request_id=0, timestamp=0, vehicle_id=0),
        PickupEvent(request_id=1, timestamp=0.1, vehicle_id=0),
        DeliveryEvent(request_id=1, timestamp=0.2, vehicle_id=0),
        DeliveryEvent(request_id=0, timestamp=0.3, vehicle_id=0),
        PickupEvent(request_id=2, timestamp=1, vehicle_id=1),
        DeliveryEvent(request_id=2, timestamp=2, vehicle_id=1),
    ]

    stops, requests = get_stops_and_requests(
        events=events,
        initial_stoplists=initial_stoplists,
        transportation_requests=transportation_requests,
        space=space,
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
                0: "START",
                1: 0,
                2: 1,
                3: 1,
                4: 0,
                5: "STOP",
                6: "START",
                7: 2,
                8: 2,
                9: "STOP",
                10: "START",
                11: "STOP",
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
                0: 0.0,
                1: 0.0,
                2: 0.1,
                3: 0.2,
                4: 0.3,
                5: nan,
                6: 0.0,
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
            ("accepted", "delivery_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: nan},
            ("accepted", "delivery_timewindow_min"): {0: 0.0, 1: 0.0, 2: 0.0, 3: nan},
            ("accepted", "destination"): {0: 0.3, 1: 0.2, 2: 0.0, 3: nan},
            ("accepted", "origin"): {0: 0.0, 1: 0.1, 2: 1.0, 3: nan},
            ("accepted", "pickup_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: nan},
            ("accepted", "pickup_timewindow_min"): {0: 0.0, 1: 0.0, 2: 0.0, 3: nan},
            ("accepted", "timestamp"): {0: 0.0, 1: 0.0, 2: 0.0, 3: nan},
            ("inferred", "relative_travel_time"): {0: 1.0, 1: 1.0, 2: 1.0, 3: nan},
            ("inferred", "travel_time"): {0: 0.3, 1: 0.1, 2: 1.0, 3: nan},
            ("inferred", "waiting_time"): {0: 0.0, 1: 0.1, 2: 1.0, 3: nan},
            ("serviced", "timestamp_dropoff"): {0: 0.3, 1: 0.2, 2: 2.0, 3: nan},
            ("serviced", "timestamp_pickup"): {0: 0.0, 1: 0.1, 2: 1.0, 3: nan},
            ("serviced", "vehicle_id"): {0: 0.0, 1: 0.0, 2: 1.0, 3: nan},
            ("supplied", "delivery_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: 0},
            ("supplied", "delivery_timewindow_min"): {0: 0, 1: 0, 2: 0, 3: 0},
            ("supplied", "destination"): {0: 0.3, 1: 0.2, 2: 0.0, 3: 1},
            ("supplied", "direct_travel_distance"): {0: 0.3, 1: 0.1, 2: 1.0, 3: 1.0},
            ("supplied", "direct_travel_time"): {0: 0.3, 1: 0.1, 2: 1.0, 3: 1.0},
            ("supplied", "origin"): {0: 0.0, 1: 0.1, 2: 1.0, 3: 0},
            ("supplied", "pickup_timewindow_max"): {0: inf, 1: inf, 2: inf, 3: 0},
            ("supplied", "pickup_timewindow_min"): {0: 0, 1: 0, 2: 0, 3: 0},
            ("supplied", "timestamp"): {0: 0, 1: 0, 2: 1, 3: 2},
        }
    )

    assert all(stops.reset_index() == expected_stops)
    assert all(requests.reset_index() == expected_requests)

    stops_wo_reqs, requests_wo_reqs = get_stops_and_requests(
        events=events,
        initial_stoplists=initial_stoplists,
        space=space,
    )

    assert all(stops_wo_reqs.reset_index() == expected_stops)
    assert all(
        requests_wo_reqs.reset_index()
        == expected_requests.drop(
            [
                "supplied",
                ("inferred", "relative_travel_time"),
                ("inferred", "waiting_time"),
            ],
            axis=1,
        )
    )

    plot_occupancy_hist(stops)


@pytest.mark.n_buses(10)
def test_get_stops_and_requests_with_actual_simulation(initial_stoplists):
    space = Euclidean1D()
    rg = RandomRequestGenerator(rate=10, space=space)
    transportation_requests = list(it.islice(rg, 1000))

    fs = SlowSimpleFleetState(
        initial_stoplists=initial_stoplists,
        space=space,
        dispatcher=brute_force_distance_minimizing_dispatcher,
    )

    events = list(fs.simulate(transportation_requests))

    stops, requests = get_stops_and_requests(
        events=events,
        initial_stoplists=initial_stoplists,
        transportation_requests=transportation_requests,
        space=space,
    )

    assert len(stops) == 2020
    assert len(requests) == 1000
