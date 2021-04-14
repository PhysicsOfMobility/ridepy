import os
import re

import logging
import pytest

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
    simulate_parameter_space,
    get_default_conf,
    param_scan,
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
    log = logging.getLogger("thesimulator")
    log.setLevel(logging.INFO)
    log.handlers[0].setLevel(logging.INFO)

    conf = get_default_conf(cython=cython)
    conf["general"]["n_reqs"] = [10]
    conf["general"]["n_vehicles"] = [10, 100]
    conf["general"]["seat_capacity"] = [2, 8]
    res = simulate_parameter_space(data_dir=tmp_path, conf=conf, chunksize=1000)

    # evaluate multiprocessing
    _, err = capfd.readouterr()
    pids = re.findall(r"Simulating run on process (\d+) @", err)
    assert 1 < len(set(pids)) <= os.cpu_count()

    assert len(res) == 4
    for r in res:
        assert (tmp_path / f"{r}_params.json").exists()
        assert (tmp_path / f"{r}.jsonl").exists()


def test_io_simulate(tmp_path, capfd):
    log = logging.getLogger("thesimulator")
    log.setLevel(logging.INFO)
    log.handlers[0].setLevel(logging.INFO)

    conf = get_default_conf(cython=True)
    conf["general"]["n_reqs"] = [100]
    res = simulate_parameter_space(data_dir=tmp_path, conf=conf, chunksize=1000)

    # evaluate multiprocessing
    _, err = capfd.readouterr()
    pids = re.findall(r"Simulating run on process (\d+) @", err)
    assert 1 < len(set(pids)) <= os.cpu_count()

    evs = read_events_json(tmp_path / f"{res[0]}.jsonl")
    params = read_params_json(param_path=tmp_path / f"{res[0]}_params.json")
    stops, requests = get_stops_and_requests(
        space=params["general"]["space"], events=evs
    )
    print(stops)


def test_io_params(tmp_path):
    param_path = tmp_path / f"params.json"

    for cython in [False, True]:
        params = next(param_scan(get_default_conf(cython=cython)))

        save_params_json(param_path=param_path, params=params)
        restored_params = read_params_json(param_path=param_path)
        print()
        print(params)
        print(restored_params)

        assert params == restored_params
