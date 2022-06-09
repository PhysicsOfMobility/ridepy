import pandas as pd
import pytest
import os
import re

import itertools as it
import numpy as np

from ridepy.extras.io import (
    save_params_json,
    read_params_json,
    read_events_json,
)
from ridepy.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
)
from ridepy.extras.simulation_set import (
    SimulationSet,
    thaw_two_level_dict,
    freeze_two_level_dict,
)
from ridepy.util.analytics import (
    get_stops_and_requests,
    get_stops_and_requests_from_events_dataframe,
)
from ridepy.util.spaces_cython import (
    Euclidean2D as CyEuclidean2D,
    Graph as CyGraph,
)


def test_spaces():
    grid = make_nx_grid()
    assert grid.order() == 9
    assert grid.size() == 12

    star = make_nx_star_graph()
    assert star.order() == 10
    assert star.size() == 9

    ring = make_nx_cycle_graph()
    assert ring.order() == 10
    assert ring.size() == 10


@pytest.mark.skipif(
    "GITLAB_CI" in os.environ, reason="does not pass in GitLab CI because num_cpu is 1"
)
@pytest.mark.parametrize("cython", [True, False])
def test_simulate(cython, tmp_path, capfd):
    simulation_set = SimulationSet(
        base_params={"general": {"n_reqs": 10}},
        product_params={"general": {"n_vehicles": [10, 100], "seat_capacity": [2, 8]}},
        zip_params={
            "general": {
                "space": [CyEuclidean2D(), CyGraph.from_nx(make_nx_cycle_graph())],
                "initial_location": [(0.0, 0.0), 0],
            }
        },
        data_dir=tmp_path,
        debug=True,
    )

    simulation_set.run()

    # evaluate multiprocessing
    out, _ = capfd.readouterr()
    pids = re.findall(r"Simulating run on process (\d+) @", out)
    assert 1 < len(set(pids)) <= os.cpu_count()

    n_sim = 8
    assert len(simulation_set.simulation_ids) == n_sim
    assert len(simulation_set.param_paths) == n_sim
    assert len(simulation_set.event_paths) == n_sim
    assert len(simulation_set) == n_sim

    assert all(
        path.exists()
        for path in it.chain(simulation_set.param_paths, simulation_set.event_paths)
    )


def test_io_simulate(tmp_path):
    simulation_set = SimulationSet(
        base_params={"general": {"n_reqs": 10}},
        data_dir=tmp_path,
        debug=True,
    )

    simulation_set.run()

    evs = read_events_json(simulation_set.event_paths[0])
    params = read_params_json(simulation_set.param_paths[0])
    stops1, requests1 = get_stops_and_requests(
        space=params["general"]["space"], events=evs
    )

    stops2, requests2 = get_stops_and_requests_from_events_dataframe(
        space=params["general"]["space"],
        events_df=pd.read_json(simulation_set.event_paths[0], lines=True),
    )

    pd.testing.assert_frame_equal(stops1, stops2)
    pd.testing.assert_frame_equal(requests1, requests2)


@pytest.mark.parametrize("cython", [True, False])
def test_io_params(cython, tmp_path):
    param_path = tmp_path / f"params.json"

    simulation_set = SimulationSet(
        base_params={"general": {"n_reqs": 10}},
        product_params={"general": {"n_vehicles": [10, 100], "seat_capacity": [2, 8]}},
        zip_params={
            "general": {
                "space": [CyEuclidean2D(), CyGraph.from_nx(make_nx_cycle_graph())],
                "initial_location": [(0.0, 0.0), 0],
            }
        },
        data_dir=tmp_path,
        debug=True,
        cython=cython,
    )
    params = next(iter(simulation_set))

    save_params_json(param_path=param_path, params=params)
    restored_params = read_params_json(param_path=param_path)
    print()
    print(params)
    print(restored_params)

    assert thaw_two_level_dict(params) == restored_params


def test_param_scan_length(tmp_path):
    params_to_zip = {
        1: {"a": [10, 20, 30], "c": [33, 44, 55]},
        2: {"z": [100, 200, 300]},
    }
    params_to_product = {
        1: {"b": [21, 22], "d": [66, 67, 68, 69]},
        2: {"w": [1000, 2000]},
    }
    simulation_set = SimulationSet(
        product_params=params_to_product,
        zip_params=params_to_zip,
        data_dir=tmp_path,
        validate=False,
    )
    simulation_set._base_params = {}
    simulation_set._update_parameter_combinations()
    res = set(iter(simulation_set))

    assert len([i for i in res if i[1]["a"] == 10]) == 2 * 4 * 2
    assert len([i for i in res if i[2]["w"] == 1000]) == 3 * 2 * 4
    assert len(res) == 3 * 2 * 4 * 2


def test_param_scan(tmp_path):
    params_to_zip = {1: {"a": [8, 9], "b": [88, 99]}}
    params_to_product = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
    simulation_set = SimulationSet(
        product_params=params_to_product,
        zip_params=params_to_zip,
        data_dir=tmp_path,
        validate=False,
    )
    simulation_set._base_params = {}
    simulation_set._update_parameter_combinations()
    res = set(iter(simulation_set))

    assert res == set(
        map(
            freeze_two_level_dict,
            (
                {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 1000}},
                {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 2000}},
                {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 1000}},
                {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 2000}},
                {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 1000}},
                {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 2000}},
                {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 1000}},
                {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 2000}},
            ),
        )
    )


def test_param_scan_equivalent_to_cartesian_product(tmp_path):
    param_scan_cartesian_product = lambda outer_dict: (
        {
            outer_key: inner_dict
            for outer_key, inner_dict in zip(outer_dict, inner_dicts)
        }
        for inner_dicts in it.product(
            *map(
                lambda inner_dict: map(
                    lambda inner_dict_values: dict(zip(inner_dict, inner_dict_values)),
                    it.product(*inner_dict.values()),
                ),
                outer_dict.values(),
            )
        )
    )
    params_to_product = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
    simulation_set = SimulationSet(
        product_params=params_to_product,
        data_dir=tmp_path,
        validate=False,
    )
    simulation_set._base_params = {}
    simulation_set._update_parameter_combinations()
    res = set(iter(simulation_set))

    assert res == set(
        map(freeze_two_level_dict, param_scan_cartesian_product(params_to_product))
    )


def test_param_scan_equivalent_to_pure_zip(tmp_path):
    params_to_zip = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}

    simulation_set = SimulationSet(
        zip_params=params_to_zip,
        data_dir=tmp_path,
        validate=False,
    )
    simulation_set._base_params = {}
    simulation_set._update_parameter_combinations()
    res = set(iter(simulation_set))
    assert res == set(
        map(
            freeze_two_level_dict,
            [
                {1: {"c": 100}, 2: {"z": 1000}},
                {1: {"c": 200}, 2: {"z": 2000}},
            ],
        )
    )


def test_param_scan_dry_run(tmp_path):
    get_simulation_set = lambda: SimulationSet(
        base_params={
            "general": {"n_vehicles": 1},
            "request_generator": {
                "max_pickup_delay": np.inf,
                "max_delivery_delay_rel": np.inf,
            },
        },
        product_params={"general": {"n_reqs": [5, 10]}},
        data_dir=tmp_path,
        debug=True,
    )

    simulation_set_dry_run = get_simulation_set()

    simulation_set_dry_run.run(dry_run=True)

    for i, (event_path, param_path) in enumerate(
        zip(simulation_set_dry_run.event_paths, simulation_set_dry_run.param_paths), 1
    ):
        assert not param_path.exists()
        assert not event_path.exists()

    simulation_set = get_simulation_set()

    simulation_set.run()

    for i, (event_path, param_path) in enumerate(
        zip(simulation_set.event_paths, simulation_set.param_paths), 1
    ):
        assert param_path.exists()
        assert event_path.exists()

        evs = read_events_json(event_path)
        params = read_params_json(param_path)

        stops, requests = get_stops_and_requests(
            space=params["general"]["space"], events=evs
        )
        assert len(stops) == params["general"]["n_reqs"] * 2 + 2
        assert len(requests) == params["general"]["n_reqs"]

    assert simulation_set.simulation_ids == simulation_set_dry_run.simulation_ids


def test_simulation_set_validate(tmp_path):
    ##################################
    # ZIP PARAMS
    ##################################

    SimulationSet(
        zip_params={
            "general": {"n_reqs": [100, 200, 300], "n_vehicles": [1000, 2000, 3000]}
        },
        data_dir=tmp_path,
        validate=True,
    )

    SimulationSet(
        zip_params={"general": {"n_vehicles": [1000, 2000, 3000]}},
        data_dir=tmp_path,
        validate=True,
    )

    SimulationSet(
        zip_params={"general": {"n_vehicles": []}},
        data_dir=tmp_path,
        validate=True,
    )

    SimulationSet(
        zip_params={"general": {}},
        data_dir=tmp_path,
        validate=True,
    )

    with pytest.raises(AssertionError, match=r"equal length"):
        SimulationSet(
            zip_params={
                "general": {"n_reqs": [100, 200], "n_vehicles": [1000, 2000, 3000]}
            },
            data_dir=tmp_path,
            validate=True,
        )

    ##################################
    # valid keys
    ##################################

    with pytest.raises(AssertionError, match=r"invalid.*='general'"):
        SimulationSet(
            base_params={
                "general": {"fizz": "baz"},
            },
            data_dir=tmp_path,
            validate=True,
        )

        SimulationSet(
            zip_params={
                "general": {"fizz": "baz"},
            },
            data_dir=tmp_path,
            validate=True,
        )

        SimulationSet(
            product_params={
                "general": {"fizz": "baz"},
            },
            data_dir=tmp_path,
            validate=True,
        )

    SimulationSet(
        base_params={
            "request_generator": {"fizz": "baz"},
        },
        data_dir=tmp_path,
        validate=True,
    )

    SimulationSet(
        zip_params={
            "request_generator": {"fizz": "baz"},
        },
        data_dir=tmp_path,
        validate=True,
    )

    SimulationSet(
        product_params={
            "request_generator": {"fizz": "baz"},
        },
        data_dir=tmp_path,
        validate=True,
    )
