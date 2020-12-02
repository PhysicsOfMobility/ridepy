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

# +
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
# -

# ## configure the simulation and supply initial values

# +
n_buses = 50
"""number of vehicles to simulate"""

initial_location = 0
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
space = Euclidean1D()
"""transport space to operate on"""

rg = RandomRequestGenerator(rate=10, transport_space=space)
"""request generator"""

# generate 1000 random requests
transportation_requests = list(it.islice(rg, 1000))

# initialize the simulator
fs = SlowSimpleFleetState(
    initial_stoplists=initial_stoplists,
    space=space,
    #         dispatcher=taxicab_dispatcher_drive_first,
    dispatcher=brute_force_distance_minimizing_dispatcher,
)
# -

# ## perform the simulation

# exhaust the simulator's iterator
# %time events = list(fs.simulate(transportation_requests))

# ## process the results: stops

# convert the returned list of events into a pandas DataFrame
evs = pd.DataFrame(
    map(
        lambda ev: dict(dataclasses.asdict(ev), event_type=ev.__class__.__name__),
        events,
    )
)
evs

# ### recreate the stoplists

# +
stops = evs[
    (evs["event_type"] == "PickupEvent") | (evs["event_type"] == "DeliveryEvent")
][["vehicle_id", "timestamp", "event_type", "request_id"]]

stops["delta_occupancy"] = stops.apply(
    lambda t: {"PickupEvent": 1, "DeliveryEvent": -1}[t["event_type"]], axis=1
)

stops.drop("event_type", axis=1, inplace=True)

vehicle_ids = list(initial_stoplists)
begin_stops = pd.DataFrame(
    np.r_[
        "-1,2,0", vehicle_ids, np.zeros(len(vehicle_ids)), np.zeros(len(vehicle_ids))
    ],
    columns=["vehicle_id", "timestamp", "delta_occupancy"],
)

# NOTE this could/should use the cutoff time, if applicable
end_time = stops["timestamp"].max()

end_stops = pd.DataFrame(
    np.r_[
        "-1,2,0",
        vehicle_ids,
        np.full(len(vehicle_ids), end_time),
        np.zeros(len(vehicle_ids)),
    ],
    columns=["vehicle_id", "timestamp", "delta_occupancy"],
)

begin_stops["request_id"] = "START"
end_stops["request_id"] = "STOP"
stops = pd.concat((begin_stops, stops, end_stops), ignore_index=True)

stops.sort_values(["vehicle_id", "timestamp", "request_id"], inplace=True)

stops["state_duration"] = (
    stops.groupby("vehicle_id")["timestamp"].diff().shift(-1).fillna(0)
)
stops["occupancy"] = stops.groupby("vehicle_id")["delta_occupancy"].cumsum()

stops.set_index(["vehicle_id", "timestamp"], inplace=True)

# check total operational times of all vehicles are identical
assert len(stops.groupby("vehicle_id")["state_duration"].sum().unique()) == 1
# -


# ## process the results: requests

# +
reqs_as_accepted = (
    evs[(evs["event_type"] == "RequestAcceptanceEvent")]
    .drop(["event_type", "vehicle_id"], axis=1)
    .set_index("request_id")
)

reqs_as_supplied = (
    pd.DataFrame(map(dataclasses.asdict, transportation_requests))
    .set_index("request_id")
    .rename({"creation_timestamp": "timestamp"}, axis=1)
)

# +
reqs = pd.concat(
    (reqs_as_supplied, reqs_as_accepted),
    axis=1,
    keys=["supplied", "accepted"],
    names=["source", "quantity"],
)
stops_tmp = stops.reset_index()[
    ["request_id", "vehicle_id", "timestamp", "delta_occupancy"]
].set_index("request_id")

reqs[("serviced", "vehicle_id")] = stops_tmp[stops_tmp["delta_occupancy"] == 1][
    "vehicle_id"
]
reqs[("serviced", "timestamp_pickup")] = stops_tmp[stops_tmp["delta_occupancy"] == 1][
    "timestamp"
]
reqs[("serviced", "timestamp_dropoff")] = stops_tmp[stops_tmp["delta_occupancy"] == -1][
    "timestamp"
]

# +
reqs[("supplied", "direct_travel_time")] = space.t(
    reqs[("supplied", "origin")], reqs[("supplied", "destination")]
)

reqs[("supplied", "direct_travel_distance")] = space.d(
    reqs[("supplied", "origin")], reqs[("supplied", "destination")]
)
# -

reqs[("inferred", "waiting_time")] = (
    reqs[("serviced", "timestamp_pickup")] - reqs[("supplied", "pickup_timewindow_min")]
)
reqs[("inferred", "travel_time")] = (
    reqs[("serviced", "timestamp_dropoff")] - reqs[("serviced", "timestamp_pickup")]
)
reqs[("inferred", "relative_travel_time")] = (
    reqs[("inferred", "travel_time")] / reqs[("supplied", "direct_travel_time")]
)

reqs.sort_values(["source", "quantity"], axis=1, inplace=True)
reqs


# ## process the results: add locations to stoplist

# +
locations = reqs.loc[:, ("accepted", ["origin", "destination"])]
locations.columns = locations.columns.droplevel(0).rename("delta_occupancy")
locations = locations.stack().rename("location")
locations.index.set_levels(
    locations.index.levels[1]
    .astype("category")
    .rename_categories({"origin": 1, "destination": -1}),
    1,
    inplace=True,
)

stops = stops.join(locations, on=["request_id", "delta_occupancy"])
# -

begin_locations = pd.Series(
    [stoplist[0].location for stoplist in initial_stoplists.values()],
    index=pd.MultiIndex.from_product(
        [["START"], vehicle_ids], names=["request_id", "vehicle_id"]
    ),
    name="location",
)
stops["location"] = stops["location"].fillna(
    stops.join(begin_locations, on=["request_id", "vehicle_id"], lsuffix="_")[
        "location"
    ]
)

stops

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

maxval = max(stops.occupancy)
fig, ax = plt.subplots(figsize=(16, 8))
ax.hist(
    stops["occupancy"],
    weights=stops["state_duration"],
    bins=np.r_[-0.5 : maxval + 0.5 : 1j * (maxval + 2)],
    rwidth=0.9,
)
ax.set_xticks(np.r_[0 : maxval : 1j * (maxval + 1)])
ax.set_xlim((-1, maxval + 1))
ax.set_xlabel("occupancy")
ax.set_ylabel("total duration at occupancy")
ax.set_yscale("log")
