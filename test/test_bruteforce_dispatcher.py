import pytest
from numpy import inf
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    PickupEvent,
    StopEvent,
    DeliveryEvent,
    TransportationRequest,
)
from thesimulator.util.spaces import Euclidean2D

from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher


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
        request, stoplist, space
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


def stoplist_from_properties(stoplist_properties):
    return [
        Stop(
            location=loc,
            request=None,
            action=StopAction.internal,
            estimated_arrival_time=cpat,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]


def test_append_dueto_timewindow():
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
        request, stoplist, space
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


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
        request, stoplist, space
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination


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
        request, stoplist, space
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination


if __name__ == "__main__":
    pytest.main(args=[__file__])
#
