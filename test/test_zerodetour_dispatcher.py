import numpy as np
import pytest

import itertools as it

from numpy import inf, isclose

from ridepy.events import (
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)
from ridepy.util.dispatchers_cython import zero_detour_dispatcher
from ridepy.extras.spaces import make_nx_grid
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces_cython import Euclidean2D, Graph
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.util.testing_utils import setup_insertion_data_structures
from ridepy.vehicle_state_cython import VehicleState


@pytest.mark.parametrize("kind", ["cython"])
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

    # location, cpat, tw_min, tw_max,
    stoplist_properties = [[(0, 0), 0, 0, inf]]
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


@pytest.mark.parametrize("kind", ["cython"])
def test_inserted_at_the_middle(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1.2),
        destination=(0, 2.8),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]

@pytest.mark.parametrize("kind", ["cython"])
def test_inserted_at_the_middle_with_detour(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 4), 4, 0, inf],
    ]
    # fmt: on
    eps = 1e-4

    ##########################################
    # Dropoff within pickup-to-next ellipse
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(1.5, 2),
        destination=(1, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1,
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]

    ##########################################
    # Pickup outside before-pickup-to-next ellipse
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(1.5+eps, 2),
        destination=(1, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1,
    )
    assert new_stoplist[2].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 1, 0]

    ##########################################
    # Dropoff outside pickup-to-next ellipse
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 2),
        destination=(1+eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1,
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0]



@pytest.mark.parametrize("kind", ["cython"])
def test_inserted_separately(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    eps = 1e-4
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
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]

@pytest.mark.parametrize("kind", ["cython"])
def test_inserted_separately_with_detour(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    eps = 1e-4

    ##########################################
    # Pickup and Dropoff inside respective ellipses
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(1, 2),
        destination=(-1, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1
    )

    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]

    ##########################################
    # Pickup outside ellipse
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(1+eps, 2),
        destination=(-1, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1
    )

    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 0, 0, 1, 0]

    ##########################################
    # Dropoff outside ellipse
    ##########################################
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(1, 2),
        destination=(-(1+eps), 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10, detour=1
    )

    assert new_stoplist[1].location == request.origin
    assert new_stoplist[-1].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 1, 1, 0]

@pytest.mark.parametrize("kind", ["cython"])
def test_dropoff_appended(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[-1].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 1, 1, 0]


@pytest.mark.parametrize("kind", ["cython"])
def test_pickup_and_dropoff_appended(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = setup_insertion_data_structures(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = zero_detour_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 0, 0, 1, 0]


if __name__ == "__main__":
    pytest.main(args=[__file__])
