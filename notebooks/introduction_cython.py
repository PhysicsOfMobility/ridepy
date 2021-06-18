# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + tags=[]
# %matplotlib inline

import itertools as it
import math as m
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# + tags=[]
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state_cython import VehicleState

from ridepy.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher,
)

from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces_cython import Euclidean2D
from ridepy.data_structures_cython import TransportationRequest

from ridepy.util.analytics import get_stops_and_requests
from ridepy.util.analytics.plotting import plot_occupancy_hist

# + tags=[]
# assume dark background for plots?
dark = True

if dark:
    default_cycler = plt.rcParams["axes.prop_cycle"]
    plt.style.use("dark_background")
    plt.rcParams["axes.prop_cycle"] = default_cycler
    plt.rcParams["axes.facecolor"] = (1, 1, 1, 0)
    plt.rcParams["figure.facecolor"] = (1, 1, 1, 0)

# + tags=[]
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
# -

# # Configure the simulation and supply initial values

# + tags=[]
n_buses = 50

initial_location = (0, 0)

space = Euclidean2D()

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    request_class=TransportationRequest,
    seed=42,
)

# create iterator yielding 100 random requests
transportation_requests = it.islice(rg, 100)
# -


# ## Initialize a `FleetState`

# + tags=[]
fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
    vehicle_state_class=VehicleState,
)
# -

# ## Perform the simulation

# + tags=[]
# exhaust the simulator's iterator
# %time events = list(fs.simulate(transportation_requests))
# -

# ## Process the results


# + tags=[]
stops, reqs = get_stops_and_requests(events=events, space=Euclidean2D())
# -

# # Some distributions
# ## Relative travel times

# + tags=[]
reqs[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:20j])
plt.gca().set_yscale("log")
# -


# ## Waiting times

# + tags=[]
reqs[("inferred", "waiting_time")].hist(bins=np.r_[1:3:20j])
# -


# ## Direct travel times

# + tags=[]
reqs[("submitted", "direct_travel_time")].hist(bins=np.r_[0 : m.sqrt(2) : 30j])
# -


# ## Occupancies

# + tags=[]
plot_occupancy_hist(stops)
# -

# ## Scratch

# + tags=[]
from ridepy.util.dispatchers_cython import optimize_stoplists

# + tags=[]
n_buses = 50

initial_location = (0, 0)

space = Euclidean2D()

rg = RandomRequestGenerator(
    rate=n_buses*3,
    max_pickup_delay=3,
    max_delivery_delay_rel=3,
    space=space,
    request_class=TransportationRequest,
    seed=90,
)

# create iterator yielding 100 random requests
transportation_requests = list(it.islice(rg, n_buses*100))
transportation_requests[-1]


# + tags=[]
fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
    vehicle_state_class=VehicleState,
)

# exhaust the simulator's iterator
events = list(fs.simulate(transportation_requests, t_cutoff=transportation_requests[-1].creation_timestamp/2))
len(events)


# + tags=[]
old_stoplists = [vs.stoplist for vid, vs in fs.fleet.items()]
len(old_stoplists), sum(len(l) for l in old_stoplists)
# -

new_stoplists = optimize_stoplists(old_stoplists, space, [8]*len(old_stoplists), search_timeout_sec=100)

# + tags=[]
# %timeit -n 1 -r1 new_stoplists = optimize_stoplists(old_stoplists, space, [8]*len(old_stoplists), search_timeout_sec=100)

# + tags=[]
old_sum = sum(l[-1].estimated_arrival_time-l[0].estimated_arrival_time for l in old_stoplists)
new_sum = sum(l[-1].estimated_arrival_time-l[0].estimated_arrival_time for l in new_stoplists)

old_sum, new_sum, (old_sum-new_sum)*100/old_sum

# + tags=[]
from numpy.random import RandomState

def benchmark_improvement_by_ortools(n_repeat=100):
    results = []
    n_buses = 50
    initial_location = (0, 0)
    space = Euclidean2D()

    rstate = RandomState(seed=0)
    for _ in range(n_repeat):
        seed = rstate.randint(0, 100000)

        rg = RandomRequestGenerator(
            rate=n_buses*3,
            max_pickup_delay=np.inf,
            max_delivery_delay_rel=3,
            space=space,
            request_class=TransportationRequest,
            seed=seed,
        )

        # create iterator yielding 100 random requests
        transportation_requests = list(it.islice(rg, n_buses*100))
        transportation_requests[-1]

        fs = SlowSimpleFleetState(
            initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
            seat_capacities=8,
            space=space,
            dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=VehicleState,
        )

        # exhaust the simulator's iterator
        events = list(fs.simulate(transportation_requests, t_cutoff=transportation_requests[-1].creation_timestamp/4))

        old_stoplists = [vs.stoplist for vid, vs in fs.fleet.items()]

        new_stoplists = optimize_stoplists(old_stoplists, space, [8]*len(old_stoplists), search_timeout_sec=100)

        old_sum = sum(l[-1].estimated_arrival_time-l[0].estimated_arrival_time for l in old_stoplists)
        new_sum = sum(l[-1].estimated_arrival_time-l[0].estimated_arrival_time for l in new_stoplists)

        results.append([old_sum, new_sum, (old_sum-new_sum)*100/old_sum])
        print(results[-1])
    return pd.DataFrame(results, columns=['old', 'new', 'relative_improvement'])


# + tags=[]
benchmark = benchmark_improvement_by_ortools(n_repeat=20)
benchmark

# + tags=[]
benchmark['relative_improvement'].describe()

# + tags=[]
benchmark['relative_improvement'].hist(bins=5)
# -


