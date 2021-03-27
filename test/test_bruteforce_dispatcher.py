import pytest

import itertools as it

from numpy import inf, isclose

from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    TransportationRequest,
    RequestRejectionEvent,
    RequestAcceptanceEvent,
    PickupEvent,
    DeliveryEvent,
)
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher
from thesimulator.util.testing_utils import stoplist_from_properties
from thesimulator.util.convenience.spaces import make_nx_grid
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean2D, Graph
from thesimulator.fleet_state import SlowSimpleFleetState


def test_append_to_empty_stoplist():
    space = Euclidean2D()
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(0, 1),
        destination=(0, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    cpestop = Stop(
        location=(0, 0),
        request=InternalRequest(
            request_id="CPE", creation_timestamp=0, location=(0, 0)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        time_window_min=0,
        time_window_max=inf,
    )
    stoplist = [cpestop]
    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


def test_append_due_to_timewindow():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 3, 3]
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination

    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 1, 0]


def test_inserted_at_the_middle():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]


def test_inserted_separately():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]


def test_not_inserted_separately_dueto_capacity_constraint():
    """
    Forces the pickup and dropoff to be inserted together solely because
    of seat_capacity=1
    """
    space = Euclidean2D()
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
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    # the best insertion would be [s0, +, -, s1, s2, s3]
    stoplist = stoplist_from_properties(stoplist_properties)
    for s, cap in zip(stoplist, [0, 1, 0, 1]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 1, 0, 1]

    stoplist = stoplist_from_properties(stoplist_properties)
    # the best insertion would be [s0, s1, s2, s3, +, -,]
    for s, cap in zip(stoplist, [1, 1, 1, 0]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[4].location == request.origin
    assert new_stoplist[5].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [1, 1, 1, 0, 1, 0]


def test_stoplist_not_modified_inplace():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert new_stoplist[3].estimated_arrival_time == 3 + 2 * eps
    assert stoplist[1].estimated_arrival_time == 3


@pytest.mark.n_buses(50)
@pytest.mark.initial_location(0)
def test_sanity_in_graph(initial_stoplists):
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

        transportation_requests = list(it.islice(rg, 1000))

        fs = SlowSimpleFleetState(
            initial_stoplists=initial_stoplists,
            seat_capacities=[10] * len(initial_stoplists),
            space=space,
            dispatcher=brute_force_distance_minimizing_dispatcher,
        )

        events = list(fs.simulate(transportation_requests))

        rejections = set(
            ev.request_id for ev in events if isinstance(ev, RequestRejectionEvent)
        )
        pickup_times = {
            ev.request_id: ev.timestamp for ev in events if isinstance(ev, PickupEvent)
        }
        delivery_times = {
            ev.request_id: ev.timestamp
            for ev in events
            if isinstance(ev, DeliveryEvent)
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
