"""
Tests that MPIFuturesFleetState and SlowSimpleFleetState produces identical results.
Currently this test cannot be run properly with pytest. Run this with:

```
mpirun --host localhost:<num_workers> -n <num_workers>  python -m mpi4py.futures  <name_of_this_file>.py
```
`num_workers` must be at least 2.
"""
import random
import re
import numpy as np
import pandas as pd
import itertools as it
from pandas.core.common import flatten
import logging
import pathlib
from mpi4py import MPI

from thesimulator import data_structures_cython as cyds
from thesimulator.util.spaces_cython import spaces as cyspaces
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.vehicle_state_cython import VehicleState as cy_VehicleState
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.extras.spaces import make_nx_grid


sim_logger = logging.getLogger("thesimulator")
sim_logger.setLevel(logging.DEBUG)
sim_logger.handlers[0].setLevel(logging.DEBUG)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

# we want to inspect the logs of the worker MPI processes. We are going to create one temp file for each process,
# which will will later read in the test itself.
logfile = pathlib.Path(f".tmp_test_logdir/rank_{rank}.out")
logfile.parent.mkdir(exist_ok=True)

vehicle_level_logger = logging.getLogger("thesimulator.vehicle_state_cython")
handler = logging.FileHandler(str(logfile))
handler.setLevel(logging.DEBUG)
vehicle_level_logger.addHandler(handler)
vehicle_level_logger.setLevel(logging.DEBUG)


def requests_handled_per_mpi_rank(logfile_dir: pathlib.Path):
    all_mpi_workers_outputs = ""
    for children_log in logfile_dir.glob("*.out"):
        with open(str(children_log), "r") as f:
            all_mpi_workers_outputs += f.read()
    mpi_process_distribution = re.findall(
        "Handling request #(.*) with vehicle (.*) from MPI rank (.*)",
        all_mpi_workers_outputs,
    )
    mpi_process_distribution = pd.DataFrame(
        mpi_process_distribution, columns=["request_id", "vehicle_id", "mpi_rank"]
    )
    return mpi_process_distribution["mpi_rank"].value_counts()


def test_equivalence_serial_and_mpi_bruteforce_dispatcher_cython(seed=42):
    """
    Tests that the simulation runs with slowsimple and mpifutures fleet states with brute force dispatcher produces
    identical events.
    """
    for cy_space in (
        cyspaces.Euclidean2D(),
        cyspaces.Graph.from_nx(make_nx_grid()),
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

        wo_mpi_request_per_rank = requests_handled_per_mpi_rank(
            logfile_dir=logfile.parent
        )
        print("Now mpi")
        ######################################################
        # With MPI
        ######################################################
        # assert comm.size > 1, "This test must be ran with at lest 2 MPI processes"

        # with redirect_stderr(f):
        mffs = MPIFuturesFleetState(
            initial_locations=initial_locations,
            seat_capacities=10,
            space=cy_space,
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=cy_VehicleState,
        )

        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
        )
        mpi_reqs = list(it.islice(rg, n_reqs))
        mpi_events = list(mffs.simulate(mpi_reqs))

        with_mpi_request_per_rank = requests_handled_per_mpi_rank(
            logfile_dir=logfile.parent
        )
        with_mpi_request_per_rank -= wo_mpi_request_per_rank.reindex(
            with_mpi_request_per_rank.index
        ).fillna(0)
        assert (
            with_mpi_request_per_rank[with_mpi_request_per_rank > 0].values
            == np.array([n_reqs, n_reqs])
        ).all()
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
    # remove old logfiles, if any
    for item in logfile.parent.glob("*.out"):
        item.unlink()
    try:
        test_equivalence_serial_and_mpi_bruteforce_dispatcher_cython()
    finally:
        # remove newly created logfiles
        for item in logfile.parent.glob("*.out"):
            item.unlink()
