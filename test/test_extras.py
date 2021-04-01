from thesimulator.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
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
