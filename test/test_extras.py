import pytest
import os
import re
import logging

import itertools as it

from thesimulator.extras.io import (
    save_params_json,
    read_params_json,
    read_events_json,
)
from thesimulator.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
)

from thesimulator.extras.parameter_spaces import (
    simulate_parameter_combinations,
    simulate_parameter_space,
    get_default_conf,
    param_scan,
    param_scan_cartesian_product,
)
from thesimulator.util.analytics import get_stops_and_requests


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


@pytest.mark.parametrize("cython", [True, False])
def test_simulate(cython, tmp_path, capfd):
    conf = get_default_conf(cython=cython)
    conf["general"]["n_reqs"] = [10]
    conf["general"]["n_vehicles"] = [10, 100]
    conf["general"]["seat_capacity"] = [2, 8]
    res = simulate_parameter_space(
        data_dir=tmp_path, param_space_to_product=conf, chunksize=1000, debug=True
    )

    # evaluate multiprocessing
    out, _ = capfd.readouterr()
    pids = re.findall(r"Simulating run on process (\d+) @", out)
    assert 1 < len(set(pids)) <= os.cpu_count()

    assert len(res) == 4
    for r in res:
        assert (tmp_path / f"{r}_params.json").exists()
        assert (tmp_path / f"{r}.jsonl").exists()


def test_io_simulate(tmp_path, capfd):
    conf = get_default_conf(cython=True)
    conf["general"]["n_reqs"] = [100]
    res = simulate_parameter_space(
        data_dir=tmp_path,
        param_space_to_product=conf,
        chunksize=1000,
    )

    evs = read_events_json(tmp_path / f"{res[0]}.jsonl")
    params = read_params_json(param_path=tmp_path / f"{res[0]}_params.json")
    stops, requests = get_stops_and_requests(
        space=params["general"]["space"], events=evs
    )
    print(stops)


def test_io_params(tmp_path):
    param_path = tmp_path / f"params.json"

    for cython in [False, True]:
        params = next(param_scan_cartesian_product(get_default_conf(cython=cython)))

        save_params_json(param_path=param_path, params=params)
        restored_params = read_params_json(param_path=param_path)
        print()
        print(params)
        print(restored_params)

        assert params == restored_params


def test_param_scan_length():
    params_tozip = {
        1: {"a": [10, 20, 30], "c": [33, 44, 55]},
        2: {"z": [100, 200, 300]},
    }
    params_toproduct = {
        1: {"b": [21, 22], "d": [66, 67, 67, 68]},
        2: {"w": [1000, 2000]},
    }
    res = list(
        param_scan(params_to_zip=params_tozip, params_to_product=params_toproduct)
    )

    assert len(res) == 3 * 2 * 4 * 2
    assert len([i for i in res if i[1]["a"] == 10]) == 2 * 4 * 2
    assert len([i for i in res if i[2]["w"] == 1000]) == 3 * 2 * 4


def test_param_scan():
    params_to_zip = {1: {"a": [8, 9], "b": [88, 99]}}
    params_to_product = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
    assert tuple(
        param_scan(params_to_zip=params_to_zip, params_to_product=params_to_product)
    ) == (
        {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 1000}},
        {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 2000}},
        {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 1000}},
        {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 2000}},
        {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 1000}},
        {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 2000}},
        {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 1000}},
        {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 2000}},
    )


def test_param_scan_equivalent_to_cartesian_product():
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
    assert list(
        param_scan(params_to_product=params_to_product, params_to_zip=dict())
    ) == list(param_scan_cartesian_product(params_to_product))


def test_param_scan_equivalent_to_pure_zip():
    params_to_zip = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
    assert list(param_scan(params_to_zip=params_to_zip, params_to_product=dict())) == [
        {1: {"c": 100}, 2: {"z": 1000}},
        {1: {"c": 200}, 2: {"z": 2000}},
    ]
