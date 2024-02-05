---
jupytext:
  encoding: '# -*- coding: utf-8 -*-'
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.7
kernelspec:
  display_name: Python 3.9 (ridepy)
  language: python
  name: ridepy
---

# RidePy Introduction: Simulations with Cython

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
from ridepy.vehicle_state_cython import VehicleState

from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher,
    SimpleEllipseDispatcher,
)

from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces_cython import Euclidean2D
from ridepy.data_structures_cython import TransportationRequest

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

## Configure the simulation and supply initial values

```{code-cell}
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
transportation_requests = it.islice(rg, 1000)
```

### Initialize a `FleetState`

```{code-cell}
fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    # dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(space.loc_type),
    dispatcher=SimpleEllipseDispatcher(space.loc_type, 3),
    vehicle_state_class=VehicleState,
)
```

### Perform the simulation

```{code-cell}
# exhaust the simulator's iterator
%time events = list(fs.simulate(transportation_requests))
# ### Process the results
```

```{code-cell}
%time stops, reqs = get_stops_and_requests( events=events, space=Euclidean2D())
# ## Some distributions
# ### Relative travel times
```

```{code-cell}
reqs[("inferred", "relative_travel_time")].hist(bins=np.r_[1:5:20j])
plt.gca().set_yscale("log")
```

### Waiting times

```{code-cell}
reqs[("inferred", "waiting_time")].hist(bins=np.r_[1:3:20j])
```

### Direct travel times

```{code-cell}
reqs[("submitted", "direct_travel_time")].hist(bins=np.r_[0 : m.sqrt(2) : 30j])
```

### Occupancies

```{code-cell}
plot_occupancy_hist(stops)
```
