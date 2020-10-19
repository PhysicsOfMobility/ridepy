import pytest

import itertools as it
import collections as cl
import operator as op
import numpy as np

from tabulate import tabulate

from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    PickupEvent,
    StopEvent,
    DeliveryEvent,
    TransportationRequest,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean


def test_random_request_generator():
    rg = RandomRequestGenerator()
    reqs = list(it.islice(rg, 10))
    assert len(reqs) == 10
    assert all(
        reqs[i + 1].creation_timestamp > reqs[i].creation_timestamp for i in range(9)
    )
    for r in reqs:
        assert r.request_id is not None
        assert len(r.origin) == 2
        assert len(r.destination) == 2
        assert 0 <= r.origin[0] <= 1
        assert 0 <= r.origin[1] <= 1
        assert 0 <= r.destination[0] <= 1
        assert 0 <= r.destination[1] <= 1


@pytest.fixture
def initial_stoplists(request):
    n_buses = (
        request.node.get_closest_marker("n_buses").args[0]
        if request.node.get_closest_marker("n_buses") is not None
        else 10
    )
    initial_location = (
        request.node.get_closest_marker("initial_location").args[0]
        if request.node.get_closest_marker("initial_location") is not None
        else 0
    )
    return {
        vehicle_id: [
            Stop(
                location=initial_location,
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=initial_location
                ),
                action=StopAction.internal,
                estimated_arrival_time=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ]
        for vehicle_id in range(n_buses)
    }


@pytest.mark.n_buses(10)
def test_slow_simple_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator(rate=10)
    reqs = list(it.islice(rg, 1000))
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs, t_cutoff=20))
    # print([event.vehicle_id for event in events if isinstance(event, PickupEvent)])
    # print("\n".join(map(str, events)))


@pytest.mark.n_buses(10)
def test_mpi_futures_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator(rate=10)
    reqs = list(it.islice(rg, 1000))
    fs = MPIFuturesFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs, t_cutoff=20))
    # print([event.vehicle_id for event in events if isinstance(event, PickupEvent)])
    # print("\n".join(map(str, events)))


@pytest.mark.n_buses(10)
def test_with_taxicab_dispatcher_simple_1(initial_stoplists):
    # rg = RandomRequestGenerator(rate=1)
    reqs = [
        TransportationRequest(
            request_id=0,
            creation_timestamp=0,
            origin=0,
            destination=1,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        TransportationRequest(
            request_id=1,
            creation_timestamp=0,
            origin=0,
            destination=1,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
        TransportationRequest(
            request_id=2,
            creation_timestamp=0,
            origin=1,
            destination=0,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        ),
    ]
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs))

    stop_events = sorted(
        filter(lambda x: isinstance(x, (PickupEvent, DeliveryEvent)), events),
        key=op.attrgetter("timestamp"),
    )
    vehicle_id_idxs = dict(
        zip(sorted(set(map(op.attrgetter("vehicle_id"), stop_events))), it.count(1))
    )

    output_list = [
        [None for _ in range(len(vehicle_id_idxs) + 1)] for _ in range(len(stop_events))
    ]

    for row, event in zip(output_list, stop_events):
        row[0] = f"{event.timestamp:.2f}"
        row[
            vehicle_id_idxs[event.vehicle_id]
        ] = f"{'pu' if isinstance(event, PickupEvent) else 'do'} {event.request_id}"

    print()
    print(
        tabulate(
            output_list,
            headers=["time", *map(lambda x: f"v {x}", vehicle_id_idxs)],
            tablefmt="orgtbl",
        )
    )


@pytest.mark.n_buses(10)
@pytest.mark.initial_location(0)
def test_with_taxicab_everyone_delivered_zero_delay(initial_stoplists):
    """
    Tests that in a low request frequency regime, all requests are picked up
    and delivered without any delay
    """
    # rg = RandomRequestGenerator(rate=1)
    n_reqs = 10
    reqs = [
        TransportationRequest(
            request_id=i,
            creation_timestamp=0,
            origin=0,
            destination=1,
            pickup_timewindow_min=10 * i,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        )
        for i in range(n_reqs)
    ]
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = sorted(fs.simulate(reqs), key=op.attrgetter("timestamp"))

    pickup_events = [event for event in events if isinstance(event, PickupEvent)]
    delivery_events = [event for event in events if isinstance(event, DeliveryEvent)]

    actual_req_pickup_times = {pu.request_id: pu.timestamp for pu in pickup_events}
    actual_req_delivery_times = {pu.request_id: pu.timestamp for pu in delivery_events}

    desired_req_pickup_times = {
        req.request_id: req.pickup_timewindow_min for req in reqs
    }
    # all the requests are from 0 to 1 -> direct travel time is 1
    desired_req_delivery_times = {
        req.request_id: req.pickup_timewindow_min + 1 for req in reqs
    }

    assert actual_req_pickup_times == desired_req_pickup_times
    assert actual_req_delivery_times == desired_req_delivery_times


@pytest.mark.n_buses(1)
@pytest.mark.initial_location(0)
def test_with_taxicab_one_taxi_delivered_with_delay(initial_stoplists):
    """
    Tests that in a high request frequency regime, all requests arrive simultaneously,
    but served one after the other, by a single taxi.

    Each request is from 0 to 1. Hence req j is picked up at j*2 and delivered at j*2+1
    """
    # rg = RandomRequestGenerator(rate=1)
    n_reqs = 10
    reqs = [
        TransportationRequest(
            request_id=i,
            creation_timestamp=0,
            origin=0,
            destination=1,
            pickup_timewindow_min=0,
            pickup_timewindow_max=np.inf,
            delivery_timewindow_min=0,
            delivery_timewindow_max=np.inf,
        )
        for i in range(n_reqs)
    ]
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = sorted(fs.simulate(reqs), key=op.attrgetter("timestamp"))

    pickup_events = [event for event in events if isinstance(event, PickupEvent)]
    delivery_events = [event for event in events if isinstance(event, DeliveryEvent)]

    actual_req_pickup_times = {pu.request_id: pu.timestamp for pu in pickup_events}
    actual_req_delivery_times = {pu.request_id: pu.timestamp for pu in delivery_events}

    correct_req_pickup_times = {req.request_id: req.request_id * 2 for req in reqs}
    # all the requests are from 0 to 1 -> direct travel time is 1
    correct_req_delivery_times = {
        req.request_id: req.request_id * 2 + 1 for req in reqs
    }

    assert actual_req_pickup_times == correct_req_pickup_times
    assert actual_req_delivery_times == correct_req_delivery_times


if __name__ == "__main__":
    pytest.main(args=[__file__])
#
