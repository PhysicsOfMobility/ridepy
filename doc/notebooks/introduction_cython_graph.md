---
jupytext:
  encoding: '# -*- coding: utf-8 -*-'
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

# RidePy Tutorial 3: Simulations on Graphs
This tutorial is based on the first two tutorials and will cover simulations on graphs.
Here, we will use the cythonic components. However, using the Python components instead is straightforward as outlined in Tutorial 2.

+++

To simulate on graphs we need the `Graph` `TransportSpace`. To create the actual graph, we will use the convenience wrapper `make_nx_grid` from the `extras` package:

```{code-cell} ipython3
from ridepy.util.spaces_cython import Graph
from ridepy.extras.spaces import make_nx_grid

space = Graph.from_nx(make_nx_grid())
```

We can now proceed as before:

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.data_structures_cython import TransportationRequest as CyTransportationRequest

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    seed=42,
    request_class=CyTransportationRequest
)

n_buses = 50
```

Slight change: as we now have integer node ids serving for coordinates we need to set the initial location accordingly:

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
initial_location = 0
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state_cython import VehicleState as CyVehicleState
from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)

import itertools as it

fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=CyBruteForceTotalTravelTimeMinimizingDispatcher(space.loc_type),
    vehicle_state_class=CyVehicleState,
)
transportation_requests = it.islice(rg, 100)
```

With this slightly changed configuration, we can run the simulations as before:

```{code-cell} ipython3
events = list(fs.simulate(transportation_requests))
```

The resulting events looks as before, just containing integer locations instead of 2D coordinate pairs.

```{code-cell} ipython3
events[200:203]
```

```{code-cell} ipython3

```
