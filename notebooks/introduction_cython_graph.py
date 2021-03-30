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

import dataclasses

import itertools as it
import functools as ft
import operator as op
import math as m
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# + tags=[]
dark = True

if dark:
    default_cycler = plt.rcParams["axes.prop_cycle"]
    plt.style.use("dark_background")
    plt.rcParams["axes.prop_cycle"] = default_cycler
    plt.rcParams["axes.facecolor"] = (1, 1, 1, 0)
    plt.rcParams["figure.facecolor"] = (1, 1, 1, 0)


# + tags=[]
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.vehicle_state_cython import VehicleState
from thesimulator.data_structures_cython import (
    Stop,
    InternalRequest,
    StopAction,
    TransportationRequest,
    LocType,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean2D as pyEuclidean2D
from thesimulator.util.spaces_cython import Euclidean2D, Graph
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist
from thesimulator.extras.spaces import make_nx_grid

# + tags=[]
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
# -

# # configure the simulation and supply initial values

# + tags=[]
n_buses = 50
"""number of vehicles to simulate"""

initial_location = 0

# -


# ## define simulation environment

# + tags=[]
# space = Euclidean2D()
space = Graph.from_nx(make_nx_grid())
"""transport space"""

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    request_class=TransportationRequest,
)
"""request generator"""

# generate 100 random requests
transportation_requests = it.islice(rg, 100)

# initialize the simulator
fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
    vehicle_state_class=VehicleState,
)
# -

# ## perform the simulation

# + tags=[]
# exhaust the simulator's iterator
# %time events = list(fs.simulate(transportation_requests))
# -

# ## process the results


# + tags=[]
stops, reqs = get_stops_and_requests(events=events, space=space)
# -

# # some distributions
# ## relative travel times

# + tags=[]
reqs[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:20j])
plt.gca().set_yscale("log")
# -


# ## waiting times

# + tags=[]
reqs[("inferred", "waiting_time")].hist(bins=np.r_[1:3:20j])
# plt.gca().set_yscale('log')
# -


# ## direct travel times

# + tags=[]
reqs[("submitted", "direct_travel_time")].hist(bins=np.r_[-0.5:5.5:7j])
# -


# ## occupancies

# + tags=[]
plot_occupancy_hist(stops)

# + tags=[]
stops
# -
