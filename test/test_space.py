import pytest
import random

import itertools as it
import math as m
import numpy as np
import networkx as nx
from hypothesis import given
import hypothesis.strategies as st
from time import time

np.random.seed(0)
import pandas as pd

from ridepy.util.spaces import (
    Euclidean,
    Euclidean1D,
    Euclidean2D,
    Graph,
    DiGraph,
    Manhattan2D,
)
from ridepy.util.spaces_cython import (
    Euclidean2D as CyEuclidean2D,
    Manhattan2D as CyManhattan2D,
    Graph as CyGraph,
    Grid2D as CyGrid2D,
    Grid2D_QM as CyGrid2D_QM,
)

from ridepy.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
)


def test_Euclidean():
    space = Euclidean(n_dim=1)
    assert space.d(0, 1) == 1.0
    assert space.d(0, 0) == 0.0

    space = Euclidean(n_dim=2)
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


def test_Manhattan2D():
    space = Manhattan2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == 2


def test_Euclidean2D_smart_vectorize():
    space = Euclidean2D()
    df1 = pd.DataFrame(
        [
            {"a": (0, 0), "b": (0, 1)},
            {"a": (0, 0), "b": (0, 0)},
            {"a": (0, 0), "b": (1, 1)},
        ]
    )

    df2 = pd.DataFrame(
        [
            {"a": [0, 0], "b": [0, 1]},
            {"a": [0, 0], "b": [0, 0]},
            {"a": [0, 0], "b": [1, 1]},
        ]
    )

    for df in [df1, df2]:
        np.testing.assert_array_equal(
            space.d(df.a.to_list(), df.b.to_list()), np.array([1, 0, m.sqrt(2)])
        )


# @pytest.mark.skip
def test_grid():
    space = Graph.from_nx(make_nx_grid())

    assert space.d(0, 0) == 0
    assert space.d(0, 1) == 1
    assert space.d(1, 2) == 1
    assert space.d(0, 2) == 2
    assert space.d(0, 5) == 3
    assert space.d(0, 8) == 4
    with pytest.raises(KeyError):
        assert space.d(-1, 8) == 4

    for dist_to_dest, (next_node, jump_time) in zip(
        [2, 1.1, 1, 0.1, 0],
        [(0, 0), (1, 0.1), (1, 0), (2, 0.1), (2, 0)],
    ):
        next_node_interp, jump_time_interp = space.interp_dist(0, 2, dist_to_dest)
        assert next_node_interp == next_node
        assert np.isclose(jump_time_interp, jump_time)

    assert space.interp_dist(0, 0, 0) == (0, 0)


def test_cyclic_graph():
    space = Graph.from_nx(make_nx_cycle_graph(order=4))

    assert space.d(0, 0) == 0
    assert space.d(0, 1) == 1
    assert space.d(0, 2) == 2
    assert space.d(0, 3) == 1
    assert space.d(0, 4) == np.inf

    x = pd.Series(np.zeros(5, dtype="i8"))
    y = pd.Series(np.arange(5, dtype="i8"))
    d = space.d(x, y)

    assert np.array_equal(d, [0, 1, 2, 1, np.inf])


def test_star_graph():
    space = Graph.from_nx(make_nx_star_graph(order=5))

    for u in range(5):
        assert space.d(u, u) == 0

    for u, v in it.product([0], range(1, 5)):
        assert space.d(u, v) == 1
        assert space.d(v, u) == 1

    for u, v in it.permutations(range(1, 5), 2):
        assert space.d(u, v) == 2

    x = pd.Series(np.zeros(5, dtype="i8"))
    y = pd.Series(np.arange(5, dtype="i8"))
    d = space.d(x, y)

    assert np.array_equal(d, pd.Series([0, 1, 1, 1, 1]))


def test_CyEuclidean2D():
    space = CyEuclidean2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == m.sqrt(2)


def test_CyManhattan2D():
    space = CyManhattan2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == 2


def test_CyGrid2D():
    space = CyGrid2D()

    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == 2
    assert space.d((0, 0), (0, 0.1)) == 0.1


def test_CyGrid2D_QM():
    space = CyGrid2D_QM()

    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == 2
    assert space.d((0, 0), (0, 0.1)) == 0.1


def test_CyGrid2D_velocity():
    space = CyGrid2D()

    assert space.t((0, 0), (0, 1)) == 1.0
    assert space.t((0, 0), (0, 0)) == 0.0
    assert space.t((0, 0), (1, 1)) == 2
    assert space.t((0, 0), (0, 0.1)) == 0.1

    space = CyGrid2D(velocity=2)

    assert space.t((0, 0), (0, 1)) == 0.5
    assert space.t((0, 0), (0, 0)) == 0.0
    assert space.t((0, 0), (1, 1)) == 1
    assert space.t((0, 0), (0, 0.1)) == 0.05


def test_CyGrid2D_QM_velocity():
    space = CyGrid2D_QM()

    assert space.t((0, 0), (0, 1)) == 1.0
    assert space.t((0, 0), (0, 0)) == 0.0
    assert space.t((0, 0), (1, 1)) == 2
    assert space.t((0, 0), (0, 0.1)) == 0.1

    space = CyGrid2D_QM(velocity=2)

    assert space.t((0, 0), (0, 1)) == 0.5
    assert space.t((0, 0), (0, 0)) == 0.0
    assert space.t((0, 0), (1, 1)) == 1
    assert space.t((0, 0), (0, 0.1)) == 0.05


def test_CyGrid2D_interpolation():

    def assert_interpolation_equal(a, b):
        # TODO this should not be necessary anymore, as we want exact values
        assert a[0][0] == pytest.approx(b[0][0])
        assert a[0][1] == pytest.approx(b[0][1])
        assert a[1] == pytest.approx(b[1])

    space = CyGrid2D()

    assert_interpolation_equal(space.interp_dist((0, 0), (0, 1), 1.0), ((0, 0), 0))
    # assert space.interp_dist((0, 1), (0, 1), 1.0) == ((1, 0), 0) # this is undefined behavior

    # ========================================

    # X---X   X   X   X
    #     V
    # X   X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 0), (1, 1), 1.0), ((0, 1), 0))

    # X   X   X   X   X
    # A
    # X---X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((1, 1), (0, 0), 1.0), ((1, 0), 0))

    # ========================================

    # X---X   X   X   X
    #     |
    # X   X   X   X   X
    #     V
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 0.6), ((2, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 1.0), ((1, 1), 0))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 1.6), ((1, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 2.6), ((0, 1), 0.6))

    # X   X   X   X   X
    # A
    # X   X   X   X   X
    # |
    # X---X   X   X   X

    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 0.6), ((0, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 1.0), ((1, 0), 0))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 1.6), ((1, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 2.6), ((2, 0), 0.6))

    # ========================================

    # X---X   X   X   X
    # V
    # X   X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((1, 0), (0, 1), 1.0), ((0, 0), 0))

    # X   X   X   X   X
    #     A
    # X---X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 1), (1, 0), 1.0), ((1, 1), 0))

    # ========================================

    # X-->X   X   X   X
    # |
    # X   X   X   X   X
    # |
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 0.6), ((0, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 1.0), ((0, 0), 0))
    assert_interpolation_equal(
        space.interp_dist((2, 0), (0, 1), 1.6), ((0, 0), 0.6)
    )  # this is broken (returns ((1, 1), 0.6), which is incompatible with the previous result)
    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 2.6), ((1, 0), 0.6))

    # X   X   X   X   X
    #     |
    # X   X   X   X   X
    #     |
    # X<--X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 0.6), ((2, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 1.0), ((2, 1), 0))
    assert_interpolation_equal(
        space.interp_dist((0, 1), (2, 0), 1.6), ((2, 1), 0.6)
    )  # this is broken
    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 2.6), ((1, 1), 0.6))


@pytest.mark.xfail
def test_CyGrid2D_QM_interpolation():

    def assert_interpolation_equal(a, b):
        # TODO this should not be necessary anymore, as we want exact values
        assert a[0][0] == pytest.approx(b[0][0])
        assert a[0][1] == pytest.approx(b[0][1])
        assert a[1] == pytest.approx(b[1])

    space = CyGrid2D_QM()

    assert_interpolation_equal(space.interp_dist((0, 0), (0, 1), 1.0), ((0, 0), 0))
    # assert space.interp_dist((0, 1), (0, 1), 1.0) == ((1, 0), 0) # this is undefined behavior

    # ========================================

    # X---X   X   X   X
    #     V
    # X   X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 0), (1, 1), 1.0), ((0, 1), 0))

    # X   X   X   X   X
    # A
    # X---X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((1, 1), (0, 0), 1.0), ((1, 0), 0))

    # ========================================

    # X---X   X   X   X
    #     |
    # X   X   X   X   X
    #     V
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 0.6), ((2, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 1.0), ((1, 1), 0))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 1.6), ((1, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 0), (2, 1), 2.6), ((0, 1), 0.6))

    # X   X   X   X   X
    # A
    # X   X   X   X   X
    # |
    # X---X   X   X   X

    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 0.6), ((0, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 1.0), ((1, 0), 0))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 1.6), ((1, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 1), (0, 0), 2.6), ((2, 0), 0.6))

    # ========================================

    # X---X   X   X   X
    # V
    # X   X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((1, 0), (0, 1), 1.0), ((0, 0), 0))

    # X   X   X   X   X
    #     A
    # X---X   X   X   X
    #
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 1), (1, 0), 1.0), ((1, 1), 0))

    # ========================================

    # X-->X   X   X   X
    # |
    # X   X   X   X   X
    # |
    # X   X   X   X   X

    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 0.6), ((0, 1), 0.6))
    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 1.0), ((0, 0), 0))
    assert_interpolation_equal(
        space.interp_dist((2, 0), (0, 1), 1.6), ((0, 0), 0.6)
    )  # this is broken (returns ((1, 1), 0.6), which is incompatible with the previous result)
    assert_interpolation_equal(space.interp_dist((2, 0), (0, 1), 2.6), ((1, 0), 0.6))

    # X   X   X   X   X
    #     |
    # X   X   X   X   X
    #     |
    # X<--X   X   X   X

    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 0.6), ((2, 0), 0.6))
    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 1.0), ((2, 1), 0))
    assert_interpolation_equal(
        space.interp_dist((0, 1), (2, 0), 1.6), ((2, 1), 0.6)
    )  # this is broken
    assert_interpolation_equal(space.interp_dist((0, 1), (2, 0), 2.6), ((1, 1), 0.6))


def test_CyGrid2D_random_points_discrete():
    space = CyGrid2D()
    random_points = [space.random_point() for _ in range(1000)]
    for random_point in random_points:
        assert 0 <= random_point[0] <= 10
        assert 0 <= random_point[1] <= 10
        assert random_point[0] % 1 == 0
        assert random_point[1] % 1 == 0


def test_CyGrid2D_QM_random_points_discrete():
    space = CyGrid2D_QM()
    random_points = [space.random_point() for _ in range(1000)]
    for random_point in random_points:
        assert 0 <= random_point[0] <= 10
        assert 0 <= random_point[1] <= 10
        assert random_point[0] % 1 == 0
        assert random_point[1] % 1 == 0


@given(edge_weight=st.floats(0.00001, 10))
def test_CyGraph_distance(edge_weight):
    G = nx.binomial_tree(n=4)
    velocity = 0.17
    for u, v in G.edges():
        G[u][v]["distance"] = edge_weight
    pyG = Graph.from_nx(G, velocity=velocity)

    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [edge_weight] * len(edges)
    CyG = CyGraph(vertices=vertices, edges=edges, weights=weights, velocity=velocity)

    for u in G.nodes():
        for v in G.nodes():
            if u >= v:
                py_dist = pyG.d(u, v)
                cy_dist = CyG.d(u, v)
                assert py_dist == cy_dist


def test_CyGraph_interpolate():
    G = nx.Graph()
    G.add_weighted_edges_from([(1, 2, 10.5), (2, 3, 3.5)])
    velocity = 0.17
    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    CyG = CyGraph(vertices=vertices, edges=edges, weights=weights, velocity=velocity)

    def true_interp_1_to_3(dist_to_dest):
        """
        dist_to_dest  | node | jump_dist
         0            | 3    | 0
         1            | 3    | 1
         3            | 3    | 3
         3.5          | 2    | 0
         4            | 2    | 0.5
         5            | 2    | 1.5
         13           | 2    | 9.5
         14           | 1    | 0
        """
        if dist_to_dest < 0:
            return None, None
        elif dist_to_dest < 3.5:
            return 3, dist_to_dest
        elif dist_to_dest < 14:
            return 2, dist_to_dest - 3.5
        elif dist_to_dest == 14:
            return 1, 0
        else:
            return None, None

    for d in np.linspace(0.001, 13.999, 100):
        assert np.allclose(CyG.interp_dist(1, 3, d), true_interp_1_to_3(d))


@given(velocity=st.floats(0.00001, 10))
def test_CyGraph_interp_d_vs_t(velocity):
    G = nx.Graph()
    G.add_weighted_edges_from([(1, 2, 10), (2, 3, 4)])
    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    CyG = CyGraph(vertices=vertices, edges=edges, weights=weights, velocity=velocity)
    for d in np.linspace(0.001, 13.999, 100):
        v1, dist = CyG.interp_dist(1, 3, d)
        v2, time = CyG.interp_time(1, 3, d / velocity)

        assert v1 == v2
        assert np.isclose(dist, time * velocity)


@given(velocity=st.floats(0.00001, 10))
def test_CyGraph_d_vs_t(velocity):
    G = nx.cycle_graph(10)

    for u, v in G.edges():
        G[u][v]["weight"] = np.random.random()

    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    CyG = CyGraph(vertices=vertices, edges=edges, weights=weights, velocity=velocity)
    ds = np.array([CyG.d(u, v) for u in G.nodes() for v in G.nodes()])
    ts = np.array([CyG.t(u, v) for u in G.nodes() for v in G.nodes()])

    assert np.allclose(ds, ts * velocity)


@given(rest_frac=st.floats(0, 1))
def test_interpolation_in_2D_continuous_spaces(rest_frac):
    for space in [Euclidean2D(), CyEuclidean2D(), CyManhattan2D()]:
        u = (0, 0)
        v = (3, 8)

        dist = space.d(u, v)
        rest_dist = dist * rest_frac

        interpolated_pt, jump_time = space.interp_dist(u, v, rest_dist)
        assert jump_time == 0
        assert np.isclose(space.d(interpolated_pt, v), rest_dist)


def test_repr():
    velocity = 42

    G = nx.cycle_graph(10)

    for u, v in G.edges():
        G[u][v]["weight"] = np.random.random()

    graph = CyGraph.from_nx(G, velocity=velocity, make_attribute_distance="weight")
    R2L1 = CyManhattan2D(velocity=velocity)
    R2L2 = CyEuclidean2D(velocity=velocity)

    assert repr(graph) == f"Graph(velocity={float(velocity)})"
    assert repr(R2L1) == f"Manhattan2D(velocity={float(velocity)})"
    assert repr(R2L2) == f"Euclidean2D(velocity={float(velocity)})"


def test_py_cy_init():
    velocity = 42

    G = nx.cycle_graph(10)
    for u, v in G.edges():
        G[u][v]["weight"] = np.random.random()

    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    const_weight = 13.37

    for kwargs in [
        dict(
            vertices=vertices,
            edges=edges,
            velocity=velocity,
        ),
        dict(
            vertices=vertices,
            edges=edges,
            weights=const_weight,
            velocity=velocity,
        ),
        dict(
            vertices=vertices,
            edges=edges,
            weights=weights,
            velocity=velocity,
        ),
    ]:
        cy_graph = CyGraph(**kwargs)
        py_graph = Graph(**kwargs)

        assert cy_graph.velocity == py_graph.velocity == velocity

        for u in G.nodes():
            for v in G.nodes():
                if u >= v:
                    assert cy_graph.d(u, v) == pytest.approx(py_graph.d(u, v))
                    assert cy_graph.t(u, v) == pytest.approx(py_graph.t(u, v))


def test_py_cy_from_nx():
    velocity = 42

    G = nx.cycle_graph(10)
    for u, v in G.edges():
        G[u][v]["weight"] = np.random.random()

    for kwargs in [
        dict(G=G, velocity=velocity, make_attribute_distance=None),
        dict(G=G, velocity=velocity, make_attribute_distance="weight"),
    ]:
        cy_graph = CyGraph.from_nx(**kwargs)
        py_graph = Graph.from_nx(**kwargs)

        assert cy_graph.velocity == py_graph.velocity == velocity

        for u in G.nodes():
            for v in G.nodes():
                if u >= v:
                    assert cy_graph.d(u, v) == pytest.approx(py_graph.d(u, v))
                    assert cy_graph.t(u, v) == pytest.approx(py_graph.t(u, v))


def test_py_cy_from_nx_graph_type():
    G_u = nx.cycle_graph(10, create_using=nx.Graph)
    G = nx.cycle_graph(10, create_using=nx.DiGraph)

    CyGraph.from_nx(G=G_u, make_attribute_distance=None)
    Graph.from_nx(G=G_u, make_attribute_distance=None)
    DiGraph.from_nx(G=G, make_attribute_distance=None)

    with pytest.raises(TypeError, match=" undirected "):
        CyGraph.from_nx(G=G, make_attribute_distance=None)

    with pytest.raises(TypeError, match=" undirected "):
        Graph.from_nx(G=G, make_attribute_distance=None)

    with pytest.raises(TypeError, match=" supply DiGraph"):
        DiGraph.from_nx(G=G_u, make_attribute_distance=None)


def test_digraph():
    velocity = 42

    G = nx.cycle_graph(10, create_using=nx.DiGraph)
    G_u = G.to_undirected()

    get_kwargs = lambda graph: dict(
        G=graph, velocity=velocity, make_attribute_distance=None
    )

    py_graph = Graph.from_nx(**get_kwargs(G_u))
    py_digraph = DiGraph.from_nx(**get_kwargs(G))
    cy_graph = CyGraph.from_nx(**get_kwargs(G_u))

    assert py_graph.velocity == py_digraph.velocity == cy_graph.velocity == velocity

    for u in G.nodes():
        for v in G.nodes():
            if u >= v:
                assert py_graph.d(u, v) == nx.shortest_path_length(G_u, u, v)
                assert cy_graph.d(u, v) == nx.shortest_path_length(G_u, u, v)
                assert py_digraph.d(u, v) == nx.shortest_path_length(G, u, v)


def test_graph_relabeling_deepcopy():
    # without relabeling
    G = nx.cycle_graph(10, create_using=nx.DiGraph)
    G_u = G.to_undirected()
    get_kwargs = lambda graph: dict(G=graph, velocity=42, make_attribute_distance=None)

    py_graph = Graph.from_nx(**get_kwargs(G_u))
    py_digraph = DiGraph.from_nx(**get_kwargs(G))

    G_u.nodes[0]["garbl"] = 42
    G.nodes[0]["garbl"] = 42

    assert G_u.nodes[0]["garbl"] == 42
    assert G.nodes[0]["garbl"] == 42

    with pytest.raises(KeyError, match="garbl"):
        py_graph.G.nodes[0]["garbl"]

    with pytest.raises(KeyError, match="garbl"):
        py_digraph.G.nodes[0]["garbl"]

    # with relabeling
    G_u = nx.grid_graph((10, 10))
    G = G_u.to_directed()
    get_kwargs = lambda graph: dict(G=graph, velocity=42, make_attribute_distance=None)

    with pytest.warns(UserWarning, match="non-int node labels"):
        py_graph = Graph.from_nx(**get_kwargs(G_u))

    with pytest.warns(UserWarning, match="non-int node labels"):
        py_digraph = DiGraph.from_nx(**get_kwargs(G))

    with pytest.warns(UserWarning, match="non-int node labels"):
        CyGraph.from_nx(**get_kwargs(G_u))

    G_u.nodes[(0, 0)]["garbl"] = 42
    G.nodes[(0, 0)]["garbl"] = 42

    assert G_u.nodes[(0, 0)]["garbl"] == 42
    assert G.nodes[(0, 0)]["garbl"] == 42

    with pytest.raises(KeyError, match="garbl"):
        py_graph.G.nodes[0]["garbl"]

    with pytest.raises(KeyError, match="garbl"):
        py_digraph.G.nodes[0]["garbl"]


def test_random_point_generation():
    ### DEFINE SPACES ###
    py_graph = Graph.from_nx(make_nx_star_graph())
    cy_graph = CyGraph.from_nx(make_nx_star_graph())

    py_R1L2 = Euclidean1D()

    py_R2L2 = Euclidean2D()
    cy_R2L2 = CyEuclidean2D()

    cy_R2L1 = CyManhattan2D()

    py_R3L2 = Euclidean(n_dim=3)

    ### GENERATE ###
    random.seed(42)
    py_graph_loc = py_graph.random_point()
    random.seed(42)
    cy_graph_loc = cy_graph.random_point()
    assert py_graph_loc == cy_graph_loc

    random.seed(42)
    py_R1L2_loc = py_R1L2.random_point()

    random.seed(42)
    py_R2L2_loc = py_R2L2.random_point()
    random.seed(42)
    cy_R2L2_loc = cy_R2L2.random_point()
    assert py_R2L2_loc == cy_R2L2_loc

    random.seed(42)
    cy_R2L1_loc = cy_R2L1.random_point()

    random.seed(42)
    py_R3L2_loc = py_R3L2.random_point()

    ### TEST FORMAT ###
    assert isinstance(py_graph_loc, int)
    assert isinstance(cy_graph_loc, int)

    assert isinstance(py_R1L2_loc, float)

    assert np.shape(py_R2L2_loc) == (2,)
    assert all(isinstance(x, float) for x in cy_R2L2_loc)

    assert np.shape(cy_R2L1_loc) == (2,)
    assert all(isinstance(x, float) for x in cy_R2L1_loc)

    assert np.shape(py_R3L2_loc) == (3,)
    assert all(isinstance(x, float) for x in py_R3L2_loc)

    ### TEST SEED ###
    random.seed(42)
    assert py_graph_loc == py_graph.random_point()

    random.seed(42)
    assert cy_graph_loc == cy_graph.random_point()

    random.seed(42)
    assert py_R1L2_loc == py_R1L2.random_point()

    random.seed(42)
    assert py_R2L2_loc == py_R2L2.random_point()

    random.seed(42)
    assert cy_R2L2_loc == cy_R2L2.random_point()

    random.seed(42)
    assert cy_R2L1_loc == cy_R2L1.random_point()

    random.seed(42)
    assert py_R3L2_loc == py_R3L2.random_point()


def test_caching_in_boost_graph_space():
    cy_graph = CyGraph.from_nx(make_nx_grid((100, 100)))

    vertices = cy_graph.vertices
    src, dest = min(vertices), max(vertices)

    compute_times = []
    results = []

    for i in range(2):
        tick = time()
        res = cy_graph.d(src, dest)
        tock = time()

        compute_times.append(tock - tick)
        results.append(res)

    assert (np.array(results) == results[0]).all()
    assert compute_times[0] > compute_times[1]


@pytest.mark.xfail()
# DO NOT test this for now, as we use different methods for computing the shortest path
# (floyd-warshall in Python and dijkstra in C++. Therefore differences in interpolation arise.)
def test_python_cython_graph_interpolation_equivalence():
    pyspace = Graph.from_nx(make_nx_grid())
    cyspace = CyGraph.from_nx(make_nx_grid())

    py_loc, py_jump_time = pyspace.interp_time(0, 4, 1.5)
    cy_loc, cy_jump_time = cyspace.interp_time(0, 4, 1.5)

    assert py_loc == cy_loc
    assert py_jump_time == cy_jump_time
