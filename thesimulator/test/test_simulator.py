from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
)
from thesimulator.utils import RandomRequestGenerator, Euclidean
import itertools as it
import operator as op
import collections as cl
import pytest


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
def initial_stoplists():
    return {
        vehicle_id: [
            Stop(
                location=0,
                vehicle_id=vehicle_id,
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=None
                ),
                action=StopAction.internal,
                estimated_arrival_time=0,
                time_window_min=None,
                time_window_max=None,
            )
        ]
        for vehicle_id in range(10)
    }


def test_slow_simple_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator()
    reqs = list(it.islice(rg, 10))
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    cl.deque(fs.simulate(reqs), maxlen=0)


def test_mpi_futures_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator()
    reqs = list(it.islice(rg, 10))
    fs = MPIFuturesFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    cl.deque(fs.simulate(reqs), maxlen=0)
