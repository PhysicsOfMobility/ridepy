---
jupytext:
  text_representation:
  formats: md:myst
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.7
kernelspec:
  display_name: Python 3.9 (ridepy)
  language: python
  name: ridepy
---

# RidePy Introduction: Multiple Simulations

```{code-cell}
%matplotlib inline

from ridepy.extras.simulation_set import SimulationSet
from ridepy.extras.io import read_events_json, read_params_json
from ridepy.util.dispatchers_cython import SimpleEllipseDispatcher
from pathlib import Path
```

## Simulation Set

```{code-cell}
tmp_path = Path("./simulations_tmp").resolve()
tmp_path.mkdir(exist_ok=True)
simulation_set = SimulationSet(
    base_params={
        "general": {"n_reqs": 10},
        "dispatcher": {
            "dispatcher_cls": SimpleEllipseDispatcher,
            "max_relative_detour": 3,
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

```{code-cell}
simulation_set.run()
simulation_set.run_analytics(only_stops_and_requests=True)
```

```{code-cell}
read_params_json(simulation_set.param_paths[0])
```

```{code-cell}
read_events_json(simulation_set.event_paths[0])
```
