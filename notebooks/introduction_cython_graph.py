# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.0
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
from ridepy.util.spaces_cython import Graph
from ridepy.data_structures_cython import TransportationRequest

from ridepy.util.analytics import get_stops_and_requests
from ridepy.util.analytics.plotting import plot_occupancy_hist

from ridepy.extras.spaces import make_nx_grid
from ridepy.util.testing_utils import convert_events_to_dicts

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

initial_location = 0

space = Graph.from_nx(make_nx_grid())

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


# ## Define simulation environment

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
stops, reqs = get_stops_and_requests(events=convert_events_to_dicts(events), space=space)
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
reqs[("submitted", "direct_travel_time")].hist(bins=np.r_[-0.5:5.5:7j])
# -


# ## Occupancies

# + tags=[]
plot_occupancy_hist(stops)

# + tags=[]

# -
