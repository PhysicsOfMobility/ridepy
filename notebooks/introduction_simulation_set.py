# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + tags=[]
# %matplotlib inline

from ridepy.extras.simulation_set import SimulationSet
from pathlib import Path

# -

# # Simulation Set

tmp_path = Path()
simulation_set = SimulationSet(
    base_params={"general": {"n_reqs": 10}},
    product_params={
        "general": {
            "n_vehicles": [10, 100],
            "seat_capacity": [2, 8],
        }
    },
    data_dir=tmp_path,
)
