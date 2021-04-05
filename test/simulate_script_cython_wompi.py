import itertools as it
import random
from time import time
import numpy as np
import pandas as pd
import sys

from thesimulator.data_structures_cython import (
    TransportationRequest,
)
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.vehicle_state_cython import VehicleState
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.spaces_cython import Euclidean2D
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.spaces import Euclidean2D as pyEuclidean2D
from thesimulator.util.analytics import get_stops_and_requests
import logging

sim_logger = logging.getLogger("thesimulator")
sim_logger.setLevel(logging.DEBUG)
sim_logger.handlers[0].setLevel(logging.DEBUG)


def simulate_on_r2(
    num_vehicles,
    rate,
    num_requests,
    seat_capacities,
    seed=0,
    request_kwargs={"max_pickup_delay": 3, "max_delivery_delay_rel": 1.9},
):
    random.seed(seed)
    np.random.seed(seed)

    space = pyEuclidean2D()

    ssfs = SlowSimpleFleetState(
        initial_locations={
            vehicle_id: space.random_point() for vehicle_id in range(num_vehicles)
        },
        space=Euclidean2D(),
        seat_capacities=seat_capacities,
        dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
        vehicle_state_class=VehicleState,
    )

    rg = RandomRequestGenerator(
        space=pyEuclidean2D(),
        rate=rate,
        request_class=TransportationRequest,
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
    if len(sys.argv) == 1:
        N = 10
    else:
        N = int(sys.argv[1])
    stops, requests = simulate_on_r2(
        num_vehicles=N, rate=N * 1.5, seat_capacities=4, num_requests=N * 1000
    )
