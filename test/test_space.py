import pytest
import math as m
import numpy as np

from thesimulator.util.spaces import (
    Euclidean,
    Euclidean1D,
    Euclidean2D,
    Graph,
    ContinuousGraph,
)


def test_Euclidean():
    space = Euclidean(n_dimensions=1)
    assert space.d(0, 1) == 1.0
    assert space.d(0, 0) == 0.0

    space = Euclidean(n_dimensions=2)
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == m.sqrt(2)


def test_Euclidean1D():
    space = Euclidean1D()
    assert space.d(0, 1) == 1.0
    assert space.d(0, 0) == 0.0


def test_Euclidean2D():
    space = Euclidean2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == m.sqrt(2)


def test_Grid():
    space = Graph.create_grid()
    # breakpoint()
    assert space.d((0, 0), (0, 0)) == 0
    assert space.d((0, 0), (0, 1)) == 1
    assert space.d((0, 1), (0, 2)) == 1
    assert space.d((0, 0), (0, 2)) == 2
    assert space.d((0, 0), (1, 2)) == 3
    assert space.d((0, 0), (2, 2)) == 4
    with pytest.raises(KeyError):
        assert space.d((0, -1), (2, 2)) == 4

    for dist_to_dest, (next_node, jump_time) in zip(
        [2, 1.1, 1, 0.1, 0],
        [((0, 0), 0), ((0, 1), 0.1), ((0, 1), 0), ((0, 2), 0.1), ((0, 2), 0)],
    ):
        next_node_interp, jump_time_interp = space.interp_dist(
            (0, 0), (0, 2), dist_to_dest
        )
        assert next_node_interp == next_node
        assert np.isclose(jump_time_interp, jump_time)

    assert space.interp_dist((0, 0), (0, 0), 0) == ((0, 0), 0)
