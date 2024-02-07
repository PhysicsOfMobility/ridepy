import random
import copy
import warnings

from typing import List, Tuple, Union, Any, Iterator, Sequence

import numpy as np
import operator as op
import math as m
import networkx as nx
import itertools as it
from scipy.spatial import distance as spd

from ridepy.data_structures import TransportSpace, ID, LocType
from ridepy.util import smartVectorize, make_repr


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
        if self.n_dim == 1:
            return abs(v - u)
        else:
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
        return tuple(random.uniform(a, b) for a, b in self.coord_range)

    def asdict(self):
        return dict(
            n_dim=self.n_dim, coord_range=self.coord_range, velocity=self.velocity
        )

    def __repr__(self):
        return make_repr("Euclidean", self.asdict())


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
        return random.uniform(self.coord_range[0][0], self.coord_range[0][1])

    def asdict(self):
        return dict(coord_range=self.coord_range, velocity=self.velocity)

    def __repr__(self):
        return make_repr("Euclidean1D", self.asdict())


class Euclidean2D(Euclidean):
    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        super().__init__(n_dim=2, coord_range=coord_range, velocity=velocity)
        self.loc_type = LocType.R2LOC

    def _coord_sub(self, u, v):
        return u[0] - v[0], u[1] - v[1]

    def _coord_mul(self, u, k):
        return u[0] * k, u[1] * k

    @smartVectorize
    def d(self, u, v):
        return m.sqrt(m.pow(v[0] - u[0], 2) + m.pow(v[1] - u[1], 2))

    def asdict(self):
        return dict(coord_range=self.coord_range, velocity=self.velocity)

    def __repr__(self):
        return make_repr("Euclidean2D", self.asdict())


class Manhattan2D(TransportSpace):
    """
    :math:`\mathbb{R}^2` with :math:`L_1`-induced metric (Manhattan).
    """

    def __init__(
        self,
        coord_range: List[Tuple[Union[int, float], Union[int, float]]] = None,
        velocity: float = 1,
    ):
        """
        Parameters
        ----------
        coord_range
            coordinate range of the space as a list of 2-tuples (x_i,min, x_i,max)
            where x_i represents the ith dimension.
        velocity
            constant scaling factor as discriminator between distance and travel time
        """
        self.n_dim = 2
        self.velocity = velocity
        self.loc_type = LocType.R2LOC

        if coord_range is not None:
            assert len(coord_range) == 2, (
                "Number of desired dimensions must "
                "match the number of coord range pairs given"
            )
            self.coord_range = coord_range
        else:
            self.coord_range = [(0, 1)] * 2

    @smartVectorize
    def d(self, u, v):
        return abs(u[0] - v[0]) + abs(u[1] - v[1])

    def t(self, u, v):
        return self.d(u, v) / self.velocity

    def _coord_sub(self, u, v):
        return map(op.sub, u, v)

    def _coord_mul(self, u, k):
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
        return tuple(random.uniform(a, b) for a, b in self.coord_range)

    def asdict(self):
        return dict(coord_range=self.coord_range, velocity=self.velocity)

    def __repr__(self):
        return make_repr("Manhattan", self.asdict())


class Graph(TransportSpace):
    """
    A location is identified with a one-dimensional coordinate, namely the node index.
    """

    n_dim = 1
    loc_type = LocType.INT

    def _update_distance_cache(self):
        (
            self._predecessors,
            self._distances,
        ) = nx.floyd_warshall_predecessor_and_distance(self.G, "distance")

    def __init__(
        self,
        vertices: Sequence[int],
        edges: Sequence[Tuple[int, int]],
        weights: Union[None, float, Sequence[float]] = None,
        velocity: float = 1,
    ):
        """
        Weighted undirected graph with integer vertex labels

        Parameters
        ----------
        vertices
            sequence of vertices
        edges
            sequence of edge tuples
        weights
            Edge weights.
            - if None is supplied, the resulting graph is unweighted (unit edge length)
            - if a single float is supplied, every edge length will be equal to this number
            - if a sequence is supplied, this will be mapped onto the edge sequence
        velocity
            constant velocity to compute travel time, optional.
        """
        self.G = nx.Graph()
        self.G.add_nodes_from(vertices)

        if weights is None:
            weights = 1

        if isinstance(weights, (int, float)):
            weights = it.repeat(float(weights))

        self.G.add_edges_from(
            (u, v, {"distance": w}) for (u, v), w in zip(edges, weights)
        )

        self.loc_type = LocType.INT
        self.velocity = velocity
        self._update_distance_cache()

    @staticmethod
    def _prepare_copy_of_nx_graph(*, G, make_attribute_distance, directed=False):
        if not directed:
            graph_class = nx.Graph
        else:
            graph_class = nx.DiGraph

        if not all(
            isinstance(u, int) for u in random.sample(list(G.nodes()), k=min(5, len(G)))
        ):
            warnings.warn(
                "Heuristic determined non-int node labels. Converting to int, "
                "keeping original labels as attribute.",
                UserWarning,
            )

            G = nx.relabel.convert_node_labels_to_integers(
                G, label_attribute="original_label"
            )
        else:
            # create a copy as we don't want to modify the original graph
            G = copy.deepcopy(G)

        # as we are keeping the graph instance, make sure it's right
        if not isinstance(G, graph_class):
            raise TypeError(f"Must supply {graph_class.__name__}, not {type(G)}")
        elif (directed and not G.is_directed()) or (not directed and G.is_directed()):
            raise TypeError(f"Must supply {'' if directed else 'un'}directed graph")

        # making another attribute the distance
        if make_attribute_distance is None:
            nx.set_edge_attributes(G, 1, name="distance")
        elif make_attribute_distance != "distance":
            # if 'distance' already exists, we raise
            if nx.get_edge_attributes(G, "distance"):
                raise ValueError(
                    "'distance' already exists as edge attribute, won't overwrite"
                )
            # otherwise rename
            else:
                nx.set_edge_attributes(
                    G,
                    nx.get_edge_attributes(G, make_attribute_distance),
                    name="distance",
                )
        else:
            if len(nx.get_edge_attributes(G, "distance")) != G.number_of_edges():
                raise ValueError(
                    "Was told to use 'distance' as distance edge attribute. "
                    "All edges must have the distance weight specified."
                )

        return G

    @classmethod
    def from_nx(
        cls,
        G: nx.Graph,
        velocity: float = 1,
        make_attribute_distance: str = "distance",
    ):
        """
        Create a graph space from NetworkX graph.

        Parameters
        ----------
        G
            the networkx.Graph instance, will be deepcopied
        velocity
            velocity to use for travel time computation
        make_attribute_distance
            attribute to rename to "distance" and use as such
            If None is supplied, the resulting graph is unweighted (unit edge length).

        Returns
        -------
        graph space instance
        """
        self = cls.__new__(cls)
        self.G = cls._prepare_copy_of_nx_graph(
            G=G, make_attribute_distance=make_attribute_distance, directed=False
        )
        self.velocity = velocity
        self._update_distance_cache()
        return self

    @smartVectorize
    def d(self, u, v):
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

    @property
    def vertices(self):
        return list(self.G.nodes)

    @property
    def edges(self):
        return list(self.G.edges)

    @property
    def weights(self):
        return list(nx.get_edge_attributes(self.G, "distance").values())

    def random_point(self):
        return random.choice(self.vertices)

    def __repr__(self):
        return f"Graph(..., velocity={self.velocity})"

    def asdict(self):
        return dict(
            vertices=self.vertices,
            edges=self.edges,
            weights=self.weights,
            velocity=self.velocity,
        )

    def __reduce__(self):
        return self.__class__, (
            self.vertices,
            self.edges,
            self.weights,
            self.velocity,
        )


class DiGraph(Graph):
    def __init__(
        self,
        vertices: Sequence[int],
        edges: Sequence[Tuple[int, int]],
        weights: Union[None, float, Sequence[float]],
        velocity: float = 1,
    ):
        """
        Weighted directed graph with integer vertex labels

        Parameters
        ----------
        vertices
            sequence of vertices
        edges
            sequence of edge tuples
        weights
            Edge weights.
            - if None is supplied, the resulting graph is unweighted (unit edge length)
            - if a single float is supplied, every edge length will be equal to this number
            - if a sequence is supplied, this will be mapped onto the edge sequence
        velocity
            constant velocity to compute travel time, optional.
        """
        self.G = nx.DiGraph()
        self.G.add_nodes_from(vertices)
        self.G.add_edges_from(
            (u, v, {"distance": w}) for (u, v), w in zip(edges, weights)
        )

        self.velocity = velocity
        self._update_distance_cache()

    @classmethod
    def from_nx(
        cls,
        G: nx.Graph,
        velocity: float = 1,
        make_attribute_distance: str = "distance",
    ):
        """
        Create a graph space from networkx directed graph
        Parameters
        ----------
        G
            the networkx.DiGraph instance, will be deepcopied
        velocity
            velocity to use for travel time computation
        make_attribute_distance
            attribute to rename to "distance" and use as such
            If None is supplied, the resulting graph is unweighted (unit edge length).

        Returns
        -------
        graph space instance
        """
        self = cls.__new__(cls)
        self.G = cls._prepare_copy_of_nx_graph(
            G=G, make_attribute_distance=make_attribute_distance, directed=True
        )
        self.velocity = velocity
        self._update_distance_cache()
        return self

    def __repr__(self):
        return f"DiGraph(..., velocity={self.velocity})"


class ContinuousGraph(Graph):
    def __init__(self):
        raise NotImplementedError

    @smartVectorize
    def d(self, u, v):
        """coordinates shall consist of triples (u, v, dist_to_dest)"""
        ...

    def t(self, u, v): ...

    def interp_dist(self, u, w, time_to_dest): ...

    def interp_time(self, u, v, time_to_dest): ...

    def random_point(self): ...
