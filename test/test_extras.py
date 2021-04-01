from thesimulator.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
)

from thesimulator.extras.simulate import simulate, get_default_conf


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


def test_simulate_py(tmp_path):
    conf = get_default_conf(cython=False)
    conf["general"]["n_reqs"] = [10]
    conf["general"]["n_vehicles"] = [10, 100]
    conf["general"]["seat_capacity"] = [2, 8]
    res = simulate(
        data_dir=tmp_path, conf=conf, cython=False, mpi=False, chunksize=1000
    )
    assert len(res) == 4
    for r in res:
        assert (tmp_path / f"{r}_params.json").exists()
        assert (tmp_path / f"{r}.jsonl").exists()


def test_simulate_cy(tmp_path):
    conf = get_default_conf(cython=True)
    conf["general"]["n_reqs"] = [10]
    conf["general"]["n_vehicles"] = [10, 100]
    conf["general"]["seat_capacity"] = [2, 8]
    res = simulate(data_dir=tmp_path, conf=conf, cython=True, mpi=False, chunksize=1000)
    assert len(res) == 4
    for r in res:
        assert (tmp_path / f"{r}_params.json").exists()
        assert (tmp_path / f"{r}.jsonl").exists()


def test_io_events():
    assert False


def test_io_params(tmp_path):
    param_path = tmp_path / f"params.json"
    conf = get_default_conf()


def test_io_space():
    assert False
