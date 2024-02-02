# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3.9 (ridepy)
#     language: python
#     name: ridepy
# ---

# # RidePy Introduction: Basics

# +
# %matplotlib inline

import itertools as it
import math as m
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# +
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state import VehicleState

from ridepy.util.dispatchers import BruteForceTotalTravelTimeMinimizingDispatcher

from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean2D

from ridepy.util.analytics import get_stops_and_requests
from ridepy.util.analytics.plotting import plot_occupancy_hist

# +
# assume dark background for plots?
dark = True

if dark:
    default_cycler = plt.rcParams["axes.prop_cycle"]
    plt.style.use("dark_background")
    plt.rcParams["axes.prop_cycle"] = default_cycler
    plt.rcParams["axes.facecolor"] = (1, 1, 1, 0)
    plt.rcParams["figure.facecolor"] = (1, 1, 1, 0)

# +
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
# -

# ## Configure the simulation and supply initial values

# +
n_buses = 50

initial_location = (0, 0)

space = Euclidean2D()

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    seed=42,
)

# create iterator yielding 100 random requests
transportation_requests = it.islice(rg, 100)
# -

# ### Initialize a `FleetState`

fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(),
    vehicle_state_class=VehicleState,
)

# ### Perform the simulation

# exhaust the simulator's iterator
# %time events = list(fs.simulate(transportation_requests))

# ### Process the results

stops, reqs = get_stops_and_requests(events=events, space=space)

# ## Some distributions
# ### Relative travel times

reqs[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:20j])
plt.gca().set_yscale("log")


# ### Waiting times

reqs[("inferred", "waiting_time")].hist(bins=np.r_[1:3:20j])


# ### Direct travel times

reqs[("submitted", "direct_travel_time")].hist(bins=np.r_[0 : m.sqrt(2) : 30j])


# ### Occupancies

plot_occupancy_hist(stops)
