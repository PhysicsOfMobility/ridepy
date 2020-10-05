from thesimulator.fleet_state import FleetState
from thesimulator.data_structures import TransportationRequest
from thesimulator.utils import RandomRequestGenerator
import itertools as it
import operator as op


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


def test_fleetstate_simulate():

    # FleetState.simulate()

    ...
