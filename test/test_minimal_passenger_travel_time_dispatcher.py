import numpy as np
import pytest

import itertools as it

from numpy import inf, isclose

from ridepy.events import (
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)
from ridepy.util.dispatchers.ridepooling import (
    MinimalPassengerTravelTimeDispatcher,
)
from ridepy.extras.spaces import make_nx_grid
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean2D, Graph
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.util.testing_utils import (
    setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher,
)
from ridepy.vehicle_state import VehicleState


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_append_to_empty_stoplist(kind):
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1),
        destination=(0, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )

    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [[(0, 0), 0, 0, inf]]
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_no_solution_found(kind):
    """Test that if no solution exists, none is returned"""
    # FIXME: Unclear, how to use the Manhatten graph with shortest paths.
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 1, 1],
        [(0, 3), 3, 3, 3]
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=eps / 2,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )

    (
        min_cost,
        new_stoplist,
        timewindows,
    ) = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert np.isinf(min_cost)
    assert not new_stoplist  # an empty `Stoplist` for cython, None for python
    assert np.isnan(timewindows).all()

    # But the same shouldn't occur if the tw_max were higher:
    # FIXME: It is unclear, if this is true for the minimal passenger travel time dispatcher
    stoplist_properties = [
        [(0, 1), 1, 1, 0],
        [(0, 3), 3, 3, 3 + 3 * eps],  # tw_max just enough
    ]
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=1 + 2 * eps,  # just enough
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    # assert not np.isinf(min_cost)


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_append_due_to_pickup_not_on_shortest_path(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 3, 3]
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(0, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert np.allclose(new_stoplist[-2].location, request.origin)
    assert np.allclose(new_stoplist[-1].location, request.destination)

    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 1, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_inserted_at_the_middle(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1.5),
        destination=(0, 2.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_inserted_separately(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 2),
        destination=(0, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_not_inserted_separately_dueto_capacity_constraint(kind):
    """
    Forces the pickup and dropoff to be inserted together solely because
    of seat_capacity=1
    """
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1.5),
        destination=(0, 2.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    # the best insertion would be [s0, +, -, s1, s2, s3]
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    for s, cap in zip(stoplist, [0, 1, 0, 1]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 1, 0, 1]

    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    # the best insertion would be [s0, s1, s2, s3, +, -,]
    for s, cap in zip(stoplist, [1, 1, 1, 0]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[4].location == request.origin
    assert new_stoplist[5].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [1, 1, 1, 0, 1, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_stoplist_not_modified_inplace(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max, occupancy
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    eps = 0
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1.5),
        destination=(eps, 2.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        minimal_passenger_travel_time_dispatcher,
    ) = setup_insertion_data_structures_minimal_passenger_travel_time_dispatcher(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = minimal_passenger_travel_time_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert new_stoplist[3].estimated_arrival_time == 3 + 2 * eps
    assert stoplist[1].estimated_arrival_time == 3


def test_sanity_in_graph():
    """
    Insert a request, note delivery time.
    Handle more requests so that there's no pooling.
    Assert that the delivery time is not changed.

    Or more simply, assert that the vehicle moves at either the space's velocity or 0.
    """

    for velocity in [0.9, 1, 1.1]:
        space = Graph.from_nx(make_nx_grid(), velocity=velocity)

        rg = RandomRequestGenerator(
            rate=10,
            space=space,
            max_delivery_delay_abs=0,
        )

        transportation_requests = list(it.islice(rg, 10000))

        fs = SlowSimpleFleetState(
            initial_locations={k: 0 for k in range(50)},
            seat_capacities=10,
            space=space,
            dispatcher=MinimalPassengerTravelTimeDispatcher(),
            vehicle_state_class=VehicleState,
        )

        events = list(fs.simulate(transportation_requests))

        rejections = set(
            ev["request_id"]
            for ev in events
            if ev["event_type"] == "RequestRejectionEvent"
        )
        pickup_times = {
            ev["request_id"]: ev["timestamp"]
            for ev in events
            if ev["event_type"] == "PickupEvent"
        }
        delivery_times = {
            ev["request_id"]: ev["timestamp"]
            for ev in events
            if ev["event_type"] == "DeliveryEvent"
        }

        assert len(transportation_requests) > len(rejections)
        for req in transportation_requests:
            if (rid := req.request_id) not in rejections:
                assert isclose(req.delivery_timewindow_max, delivery_times[rid])
                assert isclose(
                    delivery_times[rid] - pickup_times[rid],
                    space.t(req.origin, req.destination),
                )


if __name__ == "__main__":
    pytest.main(args=[__file__])
