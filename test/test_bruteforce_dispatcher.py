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


@pytest.fixture
def foo():
    return 100


def test_append_to_empty_stoplist(foo):
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
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination


def test_append_dueto_timewindow():
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [[]]


if __name__ == "__main__":
    pytest.main(args=[__file__])
#
