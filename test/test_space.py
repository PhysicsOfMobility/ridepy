import pytest
import math as m
import numpy as np
import networkx as nx
from hypothesis import given
import hypothesis.strategies as st

np.random.seed(0)

from thesimulator.util.spaces import (
    Euclidean,
    Euclidean1D,
    Euclidean2D,
    Graph,
    ContinuousGraph,
)
from thesimulator.util.cspaces import (
    Euclidean2D as CyEuclidean2D,
    Manhattan2D as CyManhattan2D,
    Graph as CyGraph
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


@given(edge_weight=st.floats(0.00001,10))
def test_cyGraph_distance(edge_weight):
    G = nx.binomial_tree(n=4)
    velocity = 0.17
    for u, v in G.edges():
        G[u][v]['distance'] = edge_weight
    pyG = Graph(G, distance_attribute='distance', velocity=velocity)

    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [edge_weight]*len(edges)
    cyG = CyGraph(vertices, edges, weights, velocity=velocity)

    for u in G.nodes():
        for v in G.nodes():
            if u >= v:
                py_dist = pyG.d(u, v)
                cy_dist = cyG.d(u, v)
                assert py_dist == cy_dist


def test_cyGraph_interpolate():
    G = nx.Graph()
    G.add_weighted_edges_from([(1,2,10.5), (2,3,3.5)])
    velocity = 0.17
    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]['weight'] for u,v in G.edges()]
    cyG = CyGraph(vertices, edges, weights, velocity=velocity)

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
        assert np.allclose(cyG.interp_dist(1,3,d), true_interp_1_to_3(d))


@given(velocity=st.floats(0.00001,10))
def test_cyGraph_interp_d_vs_t(velocity):
    G = nx.Graph()
    G.add_weighted_edges_from([(1,2,10), (2,3,4)])
    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]['weight'] for u,v in G.edges()]
    cyG = CyGraph(vertices, edges, weights, velocity=velocity)

    for d in np.linspace(0.001, 13.999, 100):
        v1, dist = cyG.interp_dist(1,3,d)
        v2, time = cyG.interp_time(1,3,d/velocity)

        assert v1 == v2
        assert np.isclose(dist, time*velocity)


@given(velocity=st.floats(0.00001,10))
def test_cyGraph_d_vs_t(velocity):
    G = nx.cycle_graph(10)

    for u, v in G.edges():
        G[u][v]['weight'] = np.random.random()

    vertices = list(G.nodes())
    edges = list(G.edges())
    weights = [G[u][v]['weight'] for u,v in G.edges()]
    cyG = CyGraph(vertices, edges, weights, velocity=velocity)

    ds = np.array([cyG.d(u, v) for u in G.nodes() for v in G.nodes()])
    ts = np.array([cyG.t(u, v) for u in G.nodes() for v in G.nodes()])

    assert np.allclose(ds, ts*velocity)



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



