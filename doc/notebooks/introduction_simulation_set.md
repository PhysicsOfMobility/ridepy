---
jupytext:
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

# RidePy Tutorial 4: Parallelization

This tutorial covers the `SimulationSet` class from the `extras` package. Its purpose is to orchestrate multiple simulation runs at different parameters. Parameters scans can be configured, simulations run in parallel, stored to disk,  and analyzed automatically.

## Configuration

To get started, we first need to create a place to store the data at:

```{code-cell} ipython3
from pathlib import Path

tmp_path = Path("./simulations_tmp").resolve()
tmp_path.mkdir(exist_ok=True)
```

Now we can proceed with setting up the `SimulationSet`.

We configure the `base_params` applying to all simulations to simulate 100 requests (`n_reqs=100`) and use the `BruteForceTotalTravelTimeMinimizingDispatcher`.

`product_params` takes iterables of parameters of which all combinations are simulated (Cartesian product). In this case we vary the number of vehicles to be either 10 or 100, and the seat capacity of the vehicles to be either 2 or 8. We will thus have the following four combinations:

- 10 vehicles at capacity 2
- 100 vehicles at capacity 2
- 10 vehicles at capacity 8
- 100 vehicles at capacity 8

After executing the upcoming cell, those four combinations will be configured and can be executed automatically and at once.

```{code-cell} ipython3
from ridepy.extras.simulation_set import SimulationSet
from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)

simulation_set = SimulationSet(
    base_params={
        "general": {"n_reqs": 100},
        "dispatcher": {
            "dispatcher_cls": CyBruteForceTotalTravelTimeMinimizingDispatcher,
        },
    },
    product_params={
        "general": {
            "n_vehicles": [10, 100],
            "seat_capacity": [2, 8],
        },
    },
    data_dir=tmp_path,
)
```

Taking the length of the simulation set confirms the four combinations configured:

```{code-cell} ipython3
len(simulation_set)
```

## Running the simulations

To execute the simulations, we execute the `SimulationSet.run` method:

```{code-cell} ipython3
%time simulation_set.run()
```

This concludes the simulations.

## Running analytics

To additionally run the analytics code on the resulting events from all four simulation runs, we execute the `SimulationSet.run_analytics` method:

```{code-cell} ipython3
simulation_set.run_analytics(only_stops_and_requests=True)
```

## Inspecting the results

The simulation runs have created a bunch of files in the output directory. For each of the four parameter sets, four files are created by running the simulations and analytics:

- `<simulation_id>_params.json`, which contains the parameter set/configuration of the simulation run in JSON format
- `<simulation_id>_.jsonl`, which contains the events created by the simulation in JSON Lines format
- `<simulation_id>_stops.pq`, which contains the stops dataframe created by the analytics module in Parquet format
- `<simulation_id>_requests.pq`, which contains the requests dataframe created by the analytics module in Parquet format

The simulation ids can be retrieved from the simulation set object:

```{code-cell} ipython3
simulation_set.simulation_ids
```

We will conclude this tutorial with having a brief look at all four files.

### Parameter configuration file

Using the `read_params_json` function, we can easily retrieve the configuration for the first simulation:

```{code-cell} ipython3
from ridepy.extras.io import read_params_json

params = read_params_json(simulation_set.param_paths[0])

params
```

### Events file

Similarly, using `read_events_json`, we can load the events output by the same simulation:

```{code-cell} ipython3
from ridepy.extras.io import read_events_json, read_params_json

events = read_events_json(simulation_set.event_paths[0])

events[200:203]
```

### Stops file

First, `make_file_path` can be used to assemble the parquet filename, which is the readily read by pandas:

```{code-cell} ipython3
from ridepy.extras.simulation_set import make_file_path
import pandas as pd

stops_fpath = make_file_path(simulation_set.simulation_ids[0], tmp_path, "_stops.pq")
stops = pd.read_parquet(stops_fpath)
```

The result looks as expected:

```{code-cell} ipython3
stops.iloc[5]
```

### Requests file

Similarly, for the requests:

```{code-cell} ipython3
request_fpath = make_file_path(simulation_set.simulation_ids[0], tmp_path, "_requests.pq")
requests = pd.read_parquet(request_fpath)
```

```{code-cell} ipython3
requests.iloc[5]
```

```{code-cell} ipython3

```
