import itertools as it
import random
from time import time
import numpy as np
import pandas as pd
import sys
import argparse

from ridepy.data_structures import (
    TransportationRequest as PyTransportationRequest,
)
from ridepy.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from ridepy.data_structures_cython.data_structures import LocType

from ridepy.extras.spaces import make_nx_grid
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state import VehicleState as PyVehicleState
from ridepy.vehicle_state_cython import VehicleState as CyVehicleState
from ridepy.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)
from ridepy.util.dispatchers_cython import (
    # brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
    BruteForceTotalTravelTimeMinimizingDispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean2D as pyEuclidean2D, Graph as PyGraph
from ridepy.util.spaces_cython import Euclidean2D as cyEuclidean2D, Graph as CyGraph

from ridepy.util.analytics import get_stops_and_requests
import logging

sim_logger = logging.getLogger("ridepy")
sim_logger.setLevel(logging.CRITICAL)
sim_logger.handlers[0].setLevel(logging.CRITICAL)


def simulate(
    num_vehicles,
    rate,
    num_requests,
    seat_capacities,
    seed=0,
    request_kwargs={"max_pickup_delay": 3, "max_delivery_delay_rel": 1.9},
    use_cython=True,
    use_graph=False,
):
    random.seed(seed)
    np.random.seed(seed)

    fleet_state_class = SlowSimpleFleetState
    dispatcher = (
        (
            cy_brute_force_total_traveltime_minimizing_dispatcher(LocType.INT)
            if use_graph
            else cy_brute_force_total_traveltime_minimizing_dispatcher(LocType.R2LOC)
        )
        if use_cython
        else py_brute_force_total_traveltime_minimizing_dispatcher
    )
    if use_graph:
        space = (
            CyGraph.from_nx(make_nx_grid())
            if use_cython
            else PyGraph.from_nx(make_nx_grid())
        )
    else:
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
        space=space,
        rate=rate,
        request_class=request_class,
        seed=seed,
        **request_kwargs,
    )

    reqs = list(it.islice(rg, num_requests))

    sim_logger.debug(f"Request 0 from the generator: {reqs[0]}")
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
    parser.add_argument("--graph", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    if args.debug:
        sim_logger.setLevel(logging.DEBUG)
        sim_logger.handlers[0].setLevel(logging.DEBUG)

    N = args.num_vehicles
    stops, requests = simulate(
        num_vehicles=N,
        rate=N * 1.5,
        seat_capacities=4,
        num_requests=N * 10,
        use_cython=args.cython,
        use_graph=args.graph,
    )
