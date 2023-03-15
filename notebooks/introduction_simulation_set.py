# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: Python (ridepy39)
#     language: python
#     name: ridepy39
# ---

# # RidePy Introduction: Multiple Simulations

# +
# %matplotlib inline

from ridepy.extras.simulation_set import SimulationSet
from ridepy.extras.io import read_events_json, read_params_json
from ridepy.util.dispatchers_cython import SimpleEllipseDispatcher
from pathlib import Path

# -

# ## Simulation Set

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

simulation_set.run()
simulation_set.run_analytics(only_stops_and_requests=True)

read_params_json(simulation_set.param_paths[0])

read_events_json(simulation_set.event_paths[0])
