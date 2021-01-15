import pytest
import math as m
import numpy as np

from hypothesis import given
import hypothesis.strategies as st

from thesimulator.util.spaces import (
    Euclidean,
    Euclidean1D,
    Euclidean2D,
    Graph,
    ContinuousGraph,
)
from thesimulator.util.cspaces import (
    Euclidean2D as CyEuclidean2D, Manhattan2D as CyManhattan2D
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


def test_grid():
    space = Graph.create_grid()

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


def test_cyclic_graph():
    space = Graph.create_cycle_graph(n_nodes=4)

    assert space.d(0, 0) == 0
    assert space.d(0, 1) == 1
    assert space.d(0, 2) == 2
    assert space.d(0, 3) == 1
    assert space.d(0, 4) == np.inf


def test_CyEuclidean2D():
    space = CyEuclidean2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == m.sqrt(2)


def test_Manhattan2D():
    space = CyManhattan2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == 2

@given(rest_frac=st.floats(0,1))
def test_interpolation_in_2D_continuous_spaces(rest_frac):
    for space in [Euclidean2D(), CyEuclidean2D(), CyManhattan2D()]:
        u = (0,0)
        v = (3,8)

        dist = space.d(u, v)
        rest_dist = dist*rest_frac

        interpolated_pt, jump_time = space.interp_dist(u, v, rest_dist)
        assert jump_time == 0
        assert np.isclose(space.d(interpolated_pt, v), rest_dist)



