import random
import pytest
import numpy as np
import itertools as it
from pandas.core.common import flatten


from thesimulator import data_structures_cython as cyds

from thesimulator.util.spaces_cython import spaces as cyspaces
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.vehicle_state_cython import VehicleState as cy_VehicleState

from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.extras.spaces import make_nx_grid

import logging

sim_logger = logging.getLogger("thesimulator")
sim_logger.setLevel(logging.DEBUG)
sim_logger.handlers[0].setLevel(logging.DEBUG)


def stoplist_from_properties(stoplist_properties, data_structure_module):
    return [
        data_structure_module.Stop(
            location=loc,
            request=data_structure_module.InternalRequest(
                request_id=-1, creation_timestamp=0, location=loc
            ),
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=cpat,
            occupancy_after_servicing=0,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]


# @pytest.mark.mpi
def test_equivalence_serial_and_mpi_bruteforce_dispatcher_euclidean2D_cython(seed=42):
    """
    Tests that the simulation runs with slowsimple and mpifutures fleet states with brute force dispatcher produces
    identical events.
    """
    for cy_space in (cyspaces.Euclidean2D(), cyspaces.Graph.from_nx(make_nx_grid())):
        n_reqs = 100

        random.seed(seed)
        init_loc = py_space.random_point()
        random.seed(seed)
        assert init_loc == cy_space.random_point()

        ######################################################
        # Without MPI
        ######################################################

        ssfs = SlowSimpleFleetState(
            initial_locations={7: init_loc},
            seat_capacities=10,
            space=cy_space,
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=cy_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
        )
        serial_reqs = list(it.islice(rg, n_reqs))
        serial_events = list(ssfs.simulate(cy_reqs))

        ######################################################
        # With MPI
        ######################################################

        mfss = MPIFuturesFleetState(
            initial_locations={7: init_loc},
            seat_capacities=10,
            space=cy_space,
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=cy_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
        )
        mpi_reqs = list(it.islice(rg, n_reqs))
        mpi_events = list(ssfs.simulate(cy_reqs))

        ######################################################
        # COMPARE
        ######################################################
        # assert that the returned events are the same
        assert len(serial_events) == len(mpi_events)
        for num, (sev, mev) in enumerate(zip(serial_events, mpi_events)):
            assert type(sev) == type(mev)
            assert np.allclose(
                list(flatten(list(mev.__dict__.values()))),
                list(flatten(list(sev.__dict__.values()))),
                rtol=1e-4,
            )
