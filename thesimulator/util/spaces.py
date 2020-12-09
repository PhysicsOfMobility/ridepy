import random

from typing import List, Tuple, Union, Any, Iterator

import numpy as np
import operator as op
import math as m
import pandas as pd
import networkx as nx
import itertools as it
from scipy.spatial import distance as spd

from thesimulator.data_structures import TransportSpace, ID
from thesimulator.util import smartVectorize


class Euclidean(TransportSpace):
    """
    n-dimensional Euclidean space with constant velocity.
    """

    def __init__(
        self,
        n_dim: int = 1,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        """
        Initialize n-dimensional Euclidean space with constant velocity.

        Parameters
        ----------
        n_dim
            number of dimensions
        coord_range
            coordinate range of the space as a list of 2-tuples (x_i,min, x_i,max)
            where x_i represents the ith dimension.
        velocity
            constant scaling factor as discriminator between distance and travel time
        """
        self.n_dim = n_dim
        self.velocity = velocity

        if coord_range is not None:
            assert len(coord_range) == n_dim, (
                "Number of desired dimensions must "
                "match the number of coord range pairs given"
            )
            self.coord_range = coord_range
        else:
            self.coord_range = [(0, 1)] * n_dim

    @smartVectorize
    def d(self, u, v):
        return spd.euclidean(u, v)

    def t(self, u, v):
        return self.d(u, v) / self.velocity

    def _coord_sub(self, u, v):
        if self.n_dim == 1:
            return u - v
        else:
            return map(op.sub, u, v)

    def _coord_mul(self, u, k):
        if self.n_dim == 1:
            return u * k
        else:
            return map(op.mul, u, it.repeat(k))

    def interp_dist(self, u, v, dist_to_dest):
        return (
            self._coord_sub(
                v, self._coord_mul(self._coord_sub(v, u), dist_to_dest / self.d(u, v))
            ),
            0,
        )

    def interp_time(self, u, v, time_to_dest):
        return (
            self._coord_sub(
                v, self._coord_mul(self._coord_sub(v, u), time_to_dest / self.t(u, v))
            ),
            0,
        )

    def random_point(self):
        return np.random.uniform(*zip(*self.coord_range))


class Euclidean1D(Euclidean):
    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        super().__init__(n_dim=1, coord_range=coord_range, velocity=velocity)

    def interp_dist(self, u, v, dist_to_dest):
        return v - (v - u) * dist_to_dest / self.d(u, v), 0

    def interp_time(self, u, v, time_to_dest):
        return v - (v - u) * time_to_dest / self.t(u, v), 0

    @smartVectorize
    def d(self, u, v):
        return abs(v - u)

    def random_point(self):
        return random.uniform(*self.coord_range[0])


class Euclidean2D(Euclidean):
    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        super().__init__(n_dim=2, coord_range=coord_range, velocity=velocity)

    def _coord_sub(self, u, v):
        return u[0] - v[0], u[1] - v[1]

    def _coord_mul(self, u, k):
        return u[0] * k, u[1] * k

    @smartVectorize
    def d(self, u, v):
        return m.sqrt(m.pow(v[0] - u[0], 2) + m.pow(v[1] - u[1], 2))


class Graph(TransportSpace):
    """
    A location is identified with a one-dimensional coordinate, namely the node index.
    """

    def __init__(
        self,
        graph: nx.Graph,
        distance_attribute="distance",
        velocity: float = 1,
        n_dim=1,
    ):
        self.G = graph
        self.distance_attribute = distance_attribute
        (
            self._predecessors,
            self._distances,
        ) = nx.floyd_warshall_predecessor_and_distance(self.G, self.distance_attribute)
        self.velocity = velocity
        self.n_dim = n_dim

    @classmethod
    def create_random(cls):
        ...

    @classmethod
    def create_grid(
        cls,
        dim=(3, 3),
        periodic=False,
        velocity: float = 1,
        edge_distance=1,
        distance_attribute="distance",
    ):
        graph = nx.grid_graph(dim=dim, periodic=periodic)
        nx.set_edge_attributes(graph, edge_distance, distance_attribute)

        return Graph(
            graph=graph,
            velocity=velocity,
            distance_attribute=distance_attribute,
            n_dim=2,
        )

    @classmethod
    def create_cycle_graph(
        cls,
        n_nodes=10,
        velocity: float = 1,
        edge_distance=1,
        distance_attribute="distance",
    ):
        graph = nx.generators.classic.cycle_graph(n=n_nodes)
        nx.set_edge_attributes(graph, edge_distance, distance_attribute)

        return Graph(
            graph=graph,
            velocity=velocity,
            distance_attribute=distance_attribute,
        )

    @smartVectorize
    def d(self, u, v):
        if isinstance(u, pd.Series) and isinstance(v, pd.Series):
            return pd.DataFrame((u, v)).apply(lambda r: self._distances[r[0]][r[1]])
        else:
            return self._distances[u][v]

    def t(self, u, v) -> Union[int, float]:
        return self.d(u, v) / self.velocity

    def interp_dist(self, u, v, dist_to_dest):
        """

        Parameters
        ----------
        u
        v
        dist_to_dest

        Returns
        -------
        next_node
        jump_distance

        """

        if u == v:
            return v, 0

        next_node = v
        while next_node is not u:
            predecessor = self._predecessors[u][next_node]
            predecessor_dist = self.d(predecessor, v)
            if predecessor_dist >= dist_to_dest:
                break
            next_node = predecessor

        if predecessor_dist > dist_to_dest:
            return next_node, dist_to_dest - self.d(next_node, v)
        else:
            return predecessor, 0

    def interp_time(self, u, v, time_to_dest):
        """

        Parameters
        ----------
        u
        v
        time_to_dest

        Returns
        -------
        next_node
        jump_time

        """
        next_node, jump_dist = self.interp_dist(
            u, v, dist_to_dest=time_to_dest * self.velocity
        )
        return next_node, jump_dist / self.velocity

    def shortest_path_vertex_sequence(self, u, v) -> List[ID]:
        seq = [v]
        if u != v:
            next_node = v
            while next_node is not u:
                next_node = self._predecessors[u][next_node]
                seq.append(next_node)
            seq.append(u)
        return seq[::-1]

    def random_point(self):
        return random.choice(list(self.G.nodes))


class ContinuousGraph(Graph):
    @smartVectorize
    def d(self, u, v):
        """coordinates shall consist of triples (u, v, dist_to_dest)"""
        ...

    def t(self, u, v):
        ...

    def interp_dist(self, u, w, time_to_dest):
        ...

    def interp_time(self, u, v, time_to_dest):
        ...

    def random_point(self):
        ...
