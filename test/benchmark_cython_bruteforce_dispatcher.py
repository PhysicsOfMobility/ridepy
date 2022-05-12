import os
import psutil

import numpy as np
import functools as ft

from time import time
from numpy import inf
from random import randint

from ridepy.data_structures_cython import (
    Stop,
    TransportationRequest,
    InternalRequest,
    StopAction,
    LocType,
    Stoplist,
)

from ridepy.util.spaces_cython import Euclidean2D, Manhattan2D
from ridepy.util.dispatchers_cython import BruteForceTotalTravelTimeMinimizingDispatcher
from ridepy.util.testing_utils_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)
from ridepy.vehicle_state_cython import VehicleState

from ridepy.util.testing_utils import stoplist_from_properties
import logging

sim_logger = logging.getLogger("ridepy")
sim_logger.setLevel(logging.DEBUG)
sim_logger.handlers[0].setLevel(logging.DEBUG)


def benchmark_insertion_into_long_stoplist(seed=0):
    space = Euclidean2D(1)
    # space = Manhattan2D(1)
    n = 10000
    rnd = np.random.RandomState(seed)
    stop_locations = rnd.uniform(low=0, high=100, size=(n, 2))
    arrival_times = np.cumsum(
        [np.linalg.norm(x - y) for x, y in zip(stop_locations[:-1], stop_locations[1:])]
    )
    arrival_times = np.insert(arrival_times, 0, 0)
    # location, CPAT, tw_min, tw_max,
    stoplist_properties = [
        [stop_loc, CPAT, 0, inf]
        for stop_loc, CPAT in zip(stop_locations, arrival_times)
    ]
    stoplist = stoplist_from_properties(
        stoplist_properties=stoplist_properties, kind="cython", space=space
    )
    # vehicle_id, new_stoplist, (min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do)

    vs = VehicleState(
        vehicle_id=12,
        initial_stoplist=stoplist,
        space=space,
        dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(
            loc_type=LocType.R2LOC
        ),
        seat_capacity=1000,
    )
    request = TransportationRequest(
        request_id=100,
        creation_timestamp=1,
        origin=rnd.uniform(low=0, high=100, size=2),
        destination=rnd.uniform(low=0, high=100, size=2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    tick = time()
    # TODO: instead of creating VehicleState, call cythonic dispatcher directly (same as the pythonic benchmark script)
    # vs.handle_transportation_request_single_vehicle(request)
    cythonic_solution = CyBruteForceTotalTravelTimeMinimizingDispatcher(LocType.R2LOC)(
        request, stoplist, space, seat_capacity=100
    )
    tock = time()
    print(f"Computing insertion into {n}-element stoplist took: {tock-tick} seconds")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        seed = int(sys.argv[1])
    else:
        seed = 0
    if len(sys.argv) > 2 and sys.argv[2] == "memcheck":
        # Run 100 times
        for i in range(100):
            process = psutil.Process(os.getpid())
            print(f"Before run #{i}: {process.memory_info().rss/1024} kB")
            benchmark_insertion_into_long_stoplist(seed)
    else:  # run only once
        benchmark_insertion_into_long_stoplist(seed)
