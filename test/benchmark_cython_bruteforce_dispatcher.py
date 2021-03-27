import pytest
import numpy as np
from numpy import inf
from functools import reduce
from time import time
import os
import psutil

from thesimulator.data_structures_cython import (
    Stop,
    TransportationRequest,
    InternalRequest,
    StopAction,
    LocType,
    Stoplist,
)

from thesimulator.util.spaces_cython import Euclidean2D, Manhattan2D
from thesimulator.util.dispatchers_cython import (
    brute_force_time_minimizing_dispatcher,
)

from random import randint

from thesimulator.vehicle_state_cython import VehicleState
import logging

sim_logger = logging.getLogger("thesimulator")
sim_logger.setLevel(logging.DEBUG)


def stoplist_from_properties(stoplist_properties):
    return [
        Stop(
            location=loc,
            request=InternalRequest(
                request_id=randint(0, 100), creation_timestamp=0, location=(0, 0)
            ),
            action=StopAction.internal,
            estimated_arrival_time=cpat,
            occupancy_after_servicing=0,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]


def benchmark_insertion_into_long_stoplist(seed=0):
    space = Euclidean2D(1)
    # space = Manhattan2D(1)
    n = 1000
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
    stoplist = stoplist_from_properties(stoplist_properties)
    vs = VehicleState(
        vehicle_id=12,
        initial_stoplist=stoplist,
        space=space,
        loc_type=LocType.R2LOC,
        dispatcher=brute_force_time_minimizing_dispatcher,
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
    vs.handle_transportation_request_single_vehicle(request)
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
