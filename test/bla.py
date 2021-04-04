import random
from contextlib import redirect_stderr
from wurlitzer import pipes
import io
import re

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


from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()


def test_equivalence_serial_and_mpi_bruteforce_dispatcher_cython(seed=42):
    """
    Tests that the simulation runs with slowsimple and mpifutures fleet states with brute force dispatcher produces
    identical events.
    """
    for cy_space in (
        cyspaces.Euclidean2D(),
        #        cyspaces.Graph.from_nx(make_nx_grid())
    ):
        n_reqs = 100

        random.seed(seed)
        init_loc = cy_space.random_point()
        random.seed(seed)
        assert init_loc == cy_space.random_point()

        initial_locations = {7: cy_space.random_point(), 9: cy_space.random_point()}

        ######################################################
        # Without MPI
        ######################################################

        ssfs = SlowSimpleFleetState(
            initial_locations=initial_locations,
            seat_capacities=10,
            space=cy_space,
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=cy_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
        )
        serial_reqs = list(it.islice(rg, n_reqs))
        serial_events = list(ssfs.simulate(serial_reqs))

        ######################################################
        # With MPI
        ######################################################
        assert comm.size > 1, "This test must be ran with at lest 2 MPI processes"

        f = io.StringIO()
        # with redirect_stderr(f):
        with pipes() as (out, err):
            mffs = MPIFuturesFleetState(
                initial_locations=initial_locations,
                seat_capacities=10,
                space=cy_space,
                dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
                vehicle_state_class=cy_VehicleState,
            )
        # mpi_outputs = f.getvalue()
        mpi_outputs = err.read()
        extr = re.findall(
            "Handling request (.*) with vehicle (.*) from MPI rank (.*)", mpi_outputs
        )
        breakpoint()

        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
        )
        mpi_reqs = list(it.islice(rg, n_reqs))
        mpi_events = list(mffs.simulate(mpi_reqs))

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


if __name__ == "__main__":
    test_equivalence_serial_and_mpi_bruteforce_dispatcher_cython()
