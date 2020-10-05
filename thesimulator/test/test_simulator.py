from thesimulator.fleet_state import FleetState
from thesimulator.data_structures import TransportationRequest
from thesimulator.utils import RandomRequestGenerator
import itertools as it


def test_random_request_generator():
    rg = RandomRequestGenerator()
    reqs = it.islice(rg, 10)
    print(list(reqs))


def test_fleetstate_simulate():

    # FleetState.simulate()

    ...
