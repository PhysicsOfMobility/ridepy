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
    assert all(r.request_id is not None for r in reqs)


def test_fleetstate_simulate():

    # FleetState.simulate()

    ...
