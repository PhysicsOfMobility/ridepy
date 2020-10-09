import pytest

import itertools as it
import collections as cl
import operator as op
import numpy as np

from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    PickupEvent,
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

    return {
        vehicle_id: [
            Stop(
                location=(0, 0),
                vehicle_id=vehicle_id,
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=(0, 0)
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


def test_mpi_futures_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator(rate=10)
    reqs = list(it.islice(rg, 1000))
    fs = MPIFuturesFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs, t_cutoff=20))
    # print([event.vehicle_id for event in events if isinstance(event, PickupEvent)])
    # print("\n".join(map(str, events)))
