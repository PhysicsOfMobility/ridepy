---
jupytext:
  encoding: '# -*- coding: utf-8 -*-'
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.15.2
kernelspec:
  display_name: Python 3.9 (ridepy)
  language: python
  name: ridepy
---

# RidePy Tutorial: Basic simulations

```{code-cell}
%matplotlib inline

import itertools as it
import math as m
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
```

```{code-cell}
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state import VehicleState

from ridepy.util.dispatchers import BruteForceTotalTravelTimeMinimizingDispatcher

from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean2D

from ridepy.util.analytics import get_stops_and_requests
from ridepy.util.analytics.plotting import plot_occupancy_hist
```

```{code-cell}
# assume dark background for plots?
dark = False

if dark:
    default_cycler = plt.rcParams["axes.prop_cycle"]
    plt.style.use("dark_background")
    plt.rcParams["axes.prop_cycle"] = default_cycler
    plt.rcParams["axes.facecolor"] = (1, 1, 1, 0)
    plt.rcParams["figure.facecolor"] = (1, 1, 1, 0)
```

```{code-cell}
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

evf = lambda S, f, **arg: (S, f(S, **arg))
```

## Configuring the simulation and supplying initial values
### Choosing a simulation space

+++

The first important step for performing a RidePy simulation is the choice of the physical space that the simulations should be run on. For this example, we choose the Euclidean 2D space from the `util` package.

```{code-cell}
space = Euclidean2D()
```

### Choosing a way of generating requests for transportation

The basis for RidePy simulations are `TransportationRequest`s. Each of these consists of:

- `origin`
- `destination`
- `pickup_timewindow_min`
- `pickup_timewindow_max`
- `delivery_timewindow_min`
- `delivery_timewindow_max`

To generate these `TransportationRequest`s, we will use the `RandomRequestGenerator` from the `util` package:

```{code-cell}
rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    seed=42,
)
```

### Setting up a fleet of vehicles

RidePy manages a fleet of vehicles using a `FleetState` object. It consumes a dictionary of `initial_locations` which maps arbitrary vehicle ids to their starting position in the simulation. The number of vehicles to set up is inferred from the number of entries in the `initial_conditions` dict. 

In addition, the fleet state needs to know about the space used for the simulation, and about the desired `dispatcher`. The dispatcher function contains the algorithm that determines how stops to serve incoming requests are scheduled. In this case, we use the included `BruteForceTotalTravelTimeMinimizingDispatcher`.

```{code-cell}
n_buses = 50
initial_location = (0, 0)
```

```{code-cell}
fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(),
    vehicle_state_class=VehicleState,
)
```

## Performing a simulation

To run the simulation we first take a slice of, in this case, 100 random requests out of the request generator we set up above...

```{code-cell}
transportation_requests = it.islice(rg, 100)
```

...and feed them into `FleetState.simulate`. Note that both of these operations use iterators and no computation actually happens until the iterators are exhausted. For `FleetState.simulate`, this happens when we cast its output into a Python list. In the case of the request generator, the output is an iterator of `TransportationRequest` objects, in the case of the `simulate` method an iterator of `Event` objects. These events describe e.g. that a request was accepted or that a "customer" or "rider" (represented by its `TransportationRequest`) was picked up or delivered to her destination.

```{code-cell}
# exhaust the simulator's iterator
events = list(fs.simulate(transportation_requests))
```

## Processing the results

+++

Running the simulations leaves us with a bunch of the events described above. This means that the raw output of the simulator looks something like this:

```{code-cell}
events[200:203]
```

### Obtaining all vehicle stops and requests

+++

To directly gain some insights from these raw events, we use the `get_stops_and_requests` function from the `analytics` package. It consumes the raw events (and the simulation space) and creates two pandas dataframes: `stops`, and `requests`.

```{code-cell}
stops, requests = get_stops_and_requests(events=events, space=space)
```

`stops` contains the stoplists (retrospective "schedules") of all vehicles operated during the simulation:

```{code-cell}
stops.head()
```

`requests` on the other hand contains all requests that we submitted by the request generator, along with detailed information about their status and service properties:

```{code-cell}
requests.head()
```

### Further Analyzing the results
Using the `stops` and `requests` dataframes, it's now straightforward to analyze the simulation run further.

+++

#### Relative travel time distribution
For example, we may obtain the distribution of the relative travel times (travel time using the service, compared to the direct trip distance)...

```{code-cell}
fig, ax = plt.subplots(figsize=(4,3), dpi=130)
requests[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:10j], ax=ax)
ax.grid(False)
ax.set_xlabel('Relative travel time')
ax.set_ylabel('Number of requests')
ax.set_yscale("log")
```

#### Waiting time distribution
... or of the waiting times (time between request submission and pick-up).

```{code-cell}
fig, ax = plt.subplots(figsize=(4,3), dpi=130)
requests[("inferred", "waiting_time")].hist(bins=np.r_[1:5:10j], ax=ax)
ax.grid(False)
ax.set_xlabel('Waiting time')
ax.set_ylabel('Number of requests')
ax.set_yscale("log")
```
