import random

from typing import List, Tuple, Union

import numpy as np
import math as m
import networkx as nx
from scipy.spatial import distance as spd

from thesimulator.data_structures import TransportSpace


class Euclidean(TransportSpace):
    """
    n-dimensional Euclidean space with constant velocity.
    """

    def __init__(
        self,
        n_dimensions: int = 1,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        """
        Initialize n-dimensional Euclidean space with constant velocity.

        Parameters
        ----------
        n_dimensions
            number of dimensions
        coord_range
            coordinate range of the space as a list of 2-tuples (x_i,min, x_i,max)
            where x_i represents the ith dimension.
        velocity
            constant scaling factor as discriminator between distance and travel time
        """
        self.n_dimensions = n_dimensions
        self.velocity = velocity

        if coord_range is not None:
            assert len(coord_range) == n_dimensions, (
                "Number of desired dimensions must "
                "match the number of coord range pairs given"
            )
            self.coord_range = coord_range
        else:
            self.coord_range = [(0, 1)] * n_dimensions

    def d(self, u, v):
        assert len(u) == len(v) == self.n_dimensions, "Dimensions of vectors must match"
        return spd.euclidean(u, v)

    def t(self, u, v):
        return self.d(u, v) / self.velocity

    def interp_dist(self, u, v, dist_to_dest):
        return v - (v - u) * dist_to_dest / self.d(u, v)

    def interp_time(self, u, v, time_to_dest):
        return v - (v - u) * time_to_dest / self.t(u, v)

    def random_point(self):
        return np.random.uniform(*zip(*self.coord_range))


class Euclidean1D(Euclidean):
    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        super().__init__(n_dimensions=1, coord_range=coord_range, velocity=velocity)

    def d(self, u, v):
        return abs(v - u)


class Euclidean2D(Euclidean):
    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        super().__init__(n_dimensions=2, coord_range=coord_range, velocity=velocity)

    def d(self, u, v):
        return m.sqrt(m.pow(v[0] - u[0], 2) + m.pow(v[1] - u[1], 2))


class Graph(TransportSpace):
    def __init__(
        self, graph: nx.Graph, distance_attribute="distance", velocity: float = 1
    ):
        self.G = graph
        self.distance_attribute = distance_attribute
        (
            self._predecessors,
            self._distances,
        ) = nx.floyd_warshall_predecessor_and_distance(self.G, self.distance_attribute)
        self.velocity = velocity

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
        )

    def d(self, u, v):
        return self._distances[u][v]

    def t(self, u, v) -> Union[int, float]:
        return self.d(u, v) / self.velocity

    def interp_dist(self, u, v, dist_to_dest):
        dist_w_to_dest = self.d(u, v)
        w = v

        while w is not u:
            w = self._predecessors[u][w]
            dist_w_to_dest = self.d(w, v)
            if dist_w_to_dest >= dist_to_dest:
                break

        if dist_w_to_dest > dist_to_dest:
            # we are between parent vertex and v vertex
            return w
        else:
            # we are at parent vertex
            return w

    def interp_time(self, u, v, time_to_dest):
        node = self.interp_dist(u, v, dist_to_dest=time_to_dest * self.velocity)
        return node

    def random_point(self):
        return random.choice(list(self.G.nodes))


class ContinuousGraph(Graph):
    def d(self, u, v):
        """coordinates shall consist of triples (u, v, dist_to_dest)"""
        ...

    def t(self, u, v):
        ...

    def interp_dist(self, u, v, time_to_dest):
        ...

    def interp_time(self, u, v, time_to_dest):
        ...

    def random_point(self):
        ...
