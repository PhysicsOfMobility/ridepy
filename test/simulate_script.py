import itertools as it
import os
import random
from time import time
import numpy as np
import pandas as pd
import psutil
import sys
import argparse

from thesimulator.data_structures import (
    TransportationRequest as PyTransportationRequest,
)
from thesimulator.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.vehicle_state import VehicleState as PyVehicleState
from thesimulator.vehicle_state_cython import VehicleState as CyVehicleState
from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean2D as pyEuclidean2D
from thesimulator.util.spaces_cython import Euclidean2D as cyEuclidean2D

from thesimulator.util.analytics import get_stops_and_requests
import logging

sim_logger = logging.getLogger("thesimulator")
sim_logger.setLevel(logging.CRITICAL)
sim_logger.handlers[0].setLevel(logging.CRITICAL)


def simulate_on_r2(
    num_vehicles,
    rate,
    num_requests,
    seat_capacities,
    seed=0,
    request_kwargs={"max_pickup_delay": 3, "max_delivery_delay_rel": 1.9},
    use_mpi=True,
    use_cython=True,
):
    random.seed(seed)
    np.random.seed(seed)

    fleet_state_class = MPIFuturesFleetState if use_mpi else SlowSimpleFleetState
    dispatcher = (
        cy_brute_force_total_traveltime_minimizing_dispatcher
        if use_cython
        else py_brute_force_total_traveltime_minimizing_dispatcher
    )
    space = cyEuclidean2D() if use_cython else pyEuclidean2D()
    vehicle_state_class = CyVehicleState if use_cython else PyVehicleState
    request_class = CyTransportationRequest if use_cython else PyTransportationRequest

    ssfs = fleet_state_class(
        initial_locations={
            vehicle_id: space.random_point() for vehicle_id in range(num_vehicles)
        },
        space=space,
        seat_capacities=seat_capacities,
        dispatcher=dispatcher,
        vehicle_state_class=vehicle_state_class,
    )

    rg = RandomRequestGenerator(
        space=pyEuclidean2D(),
        rate=rate,
        request_class=request_class,
        **request_kwargs,
    )

    reqs = list(it.islice(rg, num_requests))
    tick = time()
    events = list(ssfs.simulate(reqs))
    tock = time()

    print(f"Simulating took {tock-tick} seconds")

    stops, requests = get_stops_and_requests(events=events, space=space)
    del events

    num_requests = len(requests)
    num_requests_delivered = pd.notna(
        requests.loc[:, ("serviced", "timestamp_dropoff")]
    ).sum()

    print(f"{num_requests} requests filed, {num_requests_delivered} requests delivered")

    return stops, requests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enter simulation parameters")
    parser.add_argument(
        "--num_vehicles", "-N", type=int, default=10, help="number of vehicles"
    )
    parser.add_argument(
        "--cython", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("--mpi", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--memcheck", action=argparse.BooleanOptionalAction, default=False
    )
    args = parser.parse_args()

    N = args.num_vehicles
    if args.memcheck is False:
        # stops, requests = \
        simulate_on_r2(
            num_vehicles=N,
            rate=N * 1.5,
            seat_capacities=4,
            num_requests=N * 100,
            use_cython=args.cython,
            use_mpi=args.mpi,
        )
    else:
        for i in range(5):
            process = psutil.Process(os.getpid())
            print(f"before run #{i}: {process.memory_info().rss/1024} kB")
            # stops, requests = \
            simulate_on_r2(
                num_vehicles=N,
                rate=N * 1.5,
                seat_capacities=4,
                num_requests=N * 100,
                use_cython=args.cython,
                use_mpi=args.mpi,
            )
            print(f"after  run #{i}: {process.memory_info().rss / 1024} kB")
