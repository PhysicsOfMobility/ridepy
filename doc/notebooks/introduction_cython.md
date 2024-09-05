---
jupytext:
  encoding: '# -*- coding: utf-8 -*-'
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.15.2
---

# RidePy Tutorial 2: Faster simulations using Cython

+++

In Tutorial 1 we have seen how to set up a basic simulation, run, and analyze it. This tutorial is concerned with significantly increasing simulation performance by replacing the crucial components with their Cython equivalents. 

To demonstrate this, we will first show the complete process again in a condensed form, using the Python components. Afterwards, we will do the same using the Cython components.

The result processing and data analytics steps will not be covered again, as they are identical to using the Python components.

+++

## Simulation using Python components

First, we import all necessary **Python** components:

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
from ridepy.util.spaces import Euclidean2D
from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.vehicle_state import VehicleState
from ridepy.util.dispatchers import BruteForceTotalTravelTimeMinimizingDispatcher

import itertools as it
```

Now we can set up the simulation as explained in Tutorial 1:

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
space = Euclidean2D()

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    seed=42,
)

n_buses = 50
initial_location = (0, 0)

fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(),
    vehicle_state_class=VehicleState,
)

transportation_requests = it.islice(rg, 100)
```

And finally run the simulation. This time we will use the `%time` magic to record the execution time:

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
%time events = list(fs.simulate(transportation_requests))
```

The simulation is now done and events have been produced:

```{code-cell} ipython3
events[200:203]
```

## Simulation using Cython components

Now let's repeat the same process using the **Cython** components. The crucial step to do this is to change the imports to using the Cython equivalents of the `TransportSpace`, the `VehicleState`, the `TransportationRequest`, and the `Dispatcher`. To avoid name collisions with the Python components we will import them as prefixed with `Cy`/`cy`:

```{code-cell} ipython3
from ridepy.util.spaces_cython import Euclidean2D as CyEuclidean2D
from ridepy.data_structures_cython import TransportationRequest as CyTransportationRequest
from ridepy.vehicle_state_cython import VehicleState as CyVehicleState
from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)
```

Now that's basically it. We will now do the same configuration as above, using the new Cython components. 

There are two little extra changes we have to make: The first is to supply our `RandomRequestGenerator` with the Cython `TransportationRequest` type as `request_cls` to make it supply those instead of the Python ones. 

Secondly, the Cython `Dispatcher` needs to know about the type of spatial coordinates it is dealing with and therefore needs to be handed the `TransportSpace`'s `loc_type` attribute.

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
space = CyEuclidean2D()

rg = RandomRequestGenerator(
    rate=10,
    max_pickup_delay=3,
    max_delivery_delay_rel=1.9,
    space=space,
    seed=42,
    request_cls=CyTransportationRequest
)

n_buses = 50
initial_location = (0, 0)

fs = SlowSimpleFleetState(
    initial_locations={vehicle_id: initial_location for vehicle_id in range(n_buses)},
    seat_capacities=8,
    space=space,
    dispatcher=CyBruteForceTotalTravelTimeMinimizingDispatcher(space.loc_type),
    vehicle_state_class=CyVehicleState,
)

transportation_requests = it.islice(rg, 100)
```

Now we're ready to run the cythonized simulation: 

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
%time cy_events = list(fs.simulate(transportation_requests))
```

The simulation done and again, events have been produced:

```{code-cell} ipython3
cy_events[200:203]
```

So that's it. In this case, the Cython version was more than 20 times faster than the Python version.

```{code-cell} ipython3

```
