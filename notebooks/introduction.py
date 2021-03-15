# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
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

# +
dark = True

if dark:
    default_cycler = plt.rcParams["axes.prop_cycle"]
    plt.style.use("dark_background")
    plt.rcParams["axes.prop_cycle"] = default_cycler
    plt.rcParams["axes.facecolor"] = (1, 1, 1, 0)
    plt.rcParams["figure.facecolor"] = (1, 1, 1, 0)

# -

from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    StopEvent,
    TransportationRequest,
    RequestAcceptanceEvent,
    PickupEvent,
    DeliveryEvent,
)
from thesimulator.util.dispatchers import (
    taxicab_dispatcher_drive_first,
    brute_force_distance_minimizing_dispatcher,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean1D, Euclidean2D, Graph
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist

# +
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
# -

# # configure the simulation and supply initial values

# +
n_buses = 50
"""number of vehicles to simulate"""

initial_location = (0, 0)
"""initial location of all vehicles"""

initial_stoplists = {
    vehicle_id: [
        Stop(
            location=initial_location,
            request=InternalRequest(
                request_id="CPE", creation_timestamp=0, location=initial_location
            ),
            action=StopAction.internal,
            estimated_arrival_time=0,
            time_window_min=0,
            time_window_max=np.inf,
        )
    ]
    for vehicle_id in range(n_buses)
}
"""initial stoplists, containing only cpe"""
# -

# ## define simulation environment

# +
# space
space = Euclidean2D()
"""transport space to operate on"""

rg = RandomRequestGenerator(rate=10, space=space)
"""request generator"""

# generate 100 random requests
transportation_requests = list(it.islice(rg, 100))

# initialize the simulator
fs = SlowSimpleFleetState(
    initial_stoplists=initial_stoplists,
    space=space,
    dispatcher=brute_force_distance_minimizing_dispatcher,
    seat_capacities=8,
)
# -

# ## perform the simulation

# exhaust the simulator's iterator
# %time events = list(fs.simulate(transportation_requests))

# ## process the results

stops, reqs = get_stops_and_requests(
    events=events,
    initial_stoplists=initial_stoplists,
    transportation_requests=transportation_requests,
    space=space,
)

# # some distributions
# ## relative travel times

reqs[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:20j])
plt.gca().set_yscale("log")


# ## waiting times

reqs[("inferred", "waiting_time")].hist(bins=np.r_[1:3:20j])
# plt.gca().set_yscale('log')


# ## direct travel times

reqs[("supplied", "direct_travel_time")].hist(bins=np.r_[0:1:30j])


# ## occupancies

plot_occupancy_hist(stops)
