import pandas as pd

from thesimulator.data_structures_cython import (
    TransportationRequest,
    InternalRequest,
    Stop,
    StopAction,
    Stoplist,
    LocType,
)
from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.vehicle_state_cython import VehicleState
from thesimulator.util.dispatchers_cython import (
    brute_force_distance_minimizing_dispatcher,
)
from thesimulator.util.spaces_cython import Euclidean2D
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.spaces import Euclidean2D as pyEuclidean2D
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist
import itertools as it

import random
import numpy as np

from time import time
import logging

sim_logger = logging.getLogger('thesimulator')
sim_logger.setLevel(logging.INFO)



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
    initial_stoplists = dict()

    for vehicle_id in range(num_vehicles):
        initial_location = space.random_point()
        initial_stoplist = [
            Stop(
                location=initial_location,
                request=InternalRequest(-1, 0, initial_location),
                action=StopAction.internal,
                estimated_arrival_time=0,
                occupancy_after_servicing=0,
                time_window_min=0,
                time_window_max=0,
            )
        ]
        initial_stoplists[vehicle_id] = initial_stoplist

    ssfs = SlowSimpleFleetState(
        initial_stoplists=initial_stoplists,
        space=Euclidean2D(),
        seat_capacities=seat_capacities,
        dispatcher=brute_force_distance_minimizing_dispatcher,
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

    stops, requests = get_stops_and_requests(
        events=events,
        initial_stoplists=initial_stoplists,
        transportation_requests=reqs,
        space=space,
    )
    del events

    num_requests = len(requests)
    num_requests_delivered = pd.notna(requests.loc[:, ('serviced', 'timestamp_dropoff')]).sum()

    print(f"{num_requests} requests filed, {num_requests_delivered} requests delivered")

    return stops, requests

if __name__ == "__main__":
    N = 200
    stops, requests = simulate_on_r2(
        num_vehicles=N, rate=N*1.5, seat_capacities=4, num_requests=N*1000
    )
