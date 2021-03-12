import pytest
import numpy as np
from numpy import inf
from functools import reduce
from time import time

from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    TransportationRequest,
)
from thesimulator.util.spaces import Euclidean2D
from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher
from thesimulator.util.testing_utils import stoplist_from_properties


def benchmark_insertion_into_long_stoplist(seed=0):
    space = Euclidean2D()
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
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=rnd.uniform(low=0, high=100, size=2),
        destination=rnd.uniform(low=0, high=100, size=2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    tick = time()
    brute_force_distance_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    tock = time()
    print(f"Computing insertion into {n}-element stoplist took: {tock-tick} seconds")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        seed = int(sys.argv[1])
    benchmark_insertion_into_long_stoplist(seed)
