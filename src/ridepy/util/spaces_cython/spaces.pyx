# distutils: language = c++

import random
import warnings
import itertools as it
import networkx as nx

from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.memory cimport dynamic_pointer_cast

from ridepy.util import smartVectorize
from .cspaces cimport(
    R2loc,
    Euclidean2D as CEuclidean2D,
    Manhattan2D as CManhattan2D,
    GraphSpace as CGraphSpace
)

from typing import List, Tuple, Optional

from ridepy.data_structures_cython.data_structures cimport LocType, R2loc
from ridepy.util.spaces import Euclidean2D as pyEuclidean2D

from cython.operator cimport dereference

"""
Note: We are duplicating the C++ class hierarchy in ./spaces_cython.h. In short, our C++ transport spaces
all inherit from the abstract base class TransportSpace. Here, we will create a cdef class also called
TransportSpace and other cdef classes will inherit from that. There are a few caveats, which were described
in great length at https://stackoverflow.com/a/28727488. Basically:

1. Virtual functions that are later overridden in a child class **must be declared only for the base class**.
   That is, we must *not* declare Euclidean2D.d/t/... here, only in TransportSpace.
   Doing so will result in an *ambiguous overridden function* error from cython.
2. When allocating/deallocating c pointers in __cinit__/__dealloc__ of a cdef class ClassLaterSubclassedFrom 
   that has been subclassed, a check like `if type(self) == ClassLaterSubclassedFrom` must be used. Otherwise
   double free occurs. 
"""
cdef class TransportSpace:
    """
    Base class for extension types wrapping C++ TransportSpace class template. Since there's no elegant way of
    wrapping templates in cython and exposing them to python, we will use the [Explicit Run-Time Dispatch approach]
    (https://martinralbrecht.wordpress.com/2017/07/23/adventures-in-cython-templating/). See the docstring of
    ridepy/data_structures_cython/data_structures.pyx for details.
    """
    def __init__(self, loc_type):
        if loc_type == LocType.INT:
            self.loc_type = LocType.INT
            self.n_dim = 1
        elif loc_type == LocType.R2LOC:
            self.loc_type = LocType.R2LOC
            self.n_dim = 2
        else:
            raise ValueError("This line should never have been reached")

    @smartVectorize
    def d(self, u, v):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).d(<R2loc>u, <R2loc>v)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).d(<int>u, <int>v)
        else:
            raise ValueError("This line should never have been reached")

    @smartVectorize # TODO: check if the smartVectorize works for this cdef class
    def t(self, u, v):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).t(<R2loc>u, <R2loc>v)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).t(<int>u, <int>v)

    def interp_dist(self, u, v, double dist_to_dest):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).interp_dist(<R2loc>u, <R2loc>v, dist_to_dest)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).interp_dist(<int>u, <int>v, dist_to_dest)
        else:
            raise ValueError("This line should never have been reached")

    def interp_time(self, u, v, double time_to_dest):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).interp_time(<R2loc>u, <R2loc>v, time_to_dest)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).interp_time(<int>u, <int>v, time_to_dest)
        else:
            raise ValueError("This line should never have been reached")

    def asdict(self):
        return dict(loc_type=self.loc_type)

    def __dealloc__(self):
        """
        Since this is a base class that will never be instantiated, we do not need to free any pointer here.
        Take care to do so in the derived classes though.
        """
        ...

    def __eq__(self, other: TransportSpace):
        return type(self) == type(other) and self.asdict() == other.asdict()


cdef class Euclidean2D(TransportSpace):
    """
    :math:`\mathbb{R}^2` with :math:`L_2`-induced metric (Euclidean).
    """
    def __cinit__(self, double velocity=1, *args, **kwargs):
        self.loc_type = LocType.R2LOC
        self.derived_ptr = self.u_space.space_r2loc_ptr = new CEuclidean2D(velocity)

    def __init__(self, *args, **kwargs): # remember both __cinit__ and __init__ gets the same arguments passed
        """
        Parameters
        ----------
        velocity
            constant velocity to compute travel time, optional. default: 1
        """
        TransportSpace.__init__(self, loc_type=LocType.R2LOC)
        coord_range = kwargs.get('coord_range') or (args[1] if len(args) > 1 else None)

        if coord_range is not None:
            assert len(coord_range) == self.n_dim, (
                "Number of desired dimensions must "
                "match the number of coord range pairs given"
            )
            self.coord_range = coord_range
        else:
            self.coord_range = [(0, 1)] * self.n_dim

    def __dealloc__(self):
        del self.derived_ptr

    def __repr__(self):
        return f"Euclidean2D(velocity={self.velocity})"

    @property
    def velocity(self):
        return dereference(self.derived_ptr).velocity

    def random_point(self):
        return tuple(random.uniform(a, b) for a, b in self.coord_range)

    def asdict(self):
        return dict(velocity=self.velocity, coord_range=self.coord_range)

    def __reduce__(self):
        return self.__class__, (self.velocity, self.coord_range)


cdef class Manhattan2D(TransportSpace):
    """
    :math:`\mathbb{R}^2` with :math:`L_1`-induced metric (Manhattan).
    """
    def __cinit__(self, double velocity=1, *args, **kwargs):
        self.loc_type = LocType.R2LOC
        self.derived_ptr = self.u_space.space_r2loc_ptr = new CManhattan2D(velocity)

    def __init__(self, *args, **kwargs): # remember both __cinit__ and __init__ gets the same arguments passed
        """
        Parameters
        ----------
        velocity
            constant velocity to compute travel time, optional. default: 1
        """
        TransportSpace.__init__(self, loc_type=LocType.R2LOC)

        coord_range = kwargs.get('coord_range') or (args[1] if len(args) > 1 else None)
        if coord_range is not None:
            assert len(coord_range) == self.n_dim, (
                "Number of desired dimensions must "
                "match the number of coord range pairs given"
            )
            self.coord_range = coord_range
        else:
            self.coord_range = [(0, 1)] * self.n_dim

    def __dealloc__(self):
        del self.derived_ptr

    def __repr__(self):
        return f"Manhattan2D(velocity={self.velocity})"

    @property
    def velocity(self):
        return dereference(self.derived_ptr).velocity

    def random_point(self):
        return tuple(random.uniform(a, b) for a, b in self.coord_range)

    def asdict(self):
        return dict(velocity=self.velocity, coord_range=self.coord_range)

    def __reduce__(self):
        return self.__class__, (self.velocity, self.coord_range)


cdef class Graph(TransportSpace):
    """
    Weighted directed graph with integer node labels.
    """
    def __cinit__(self, vertices, edges, weights=None, double velocity=1):
        self.loc_type = LocType.INT

        if weights is None:
            self.derived_ptr = self.u_space.space_int_ptr = new CGraphSpace[int](
                velocity, <vector[int]>vertices, <vector[pair[int, int]]>edges
            )
        else:
            if isinstance(weights, (int, float)):
                weights = it.repeat(float(weights), len(edges))

            self.derived_ptr = self.u_space.space_int_ptr = new CGraphSpace[int](
                velocity, <vector[int]>vertices, <vector[pair[int, int]]>edges, <vector[double]>weights
            )

    def __init__(self, *args, **kwargs): # remember both __cinit__ and __init__ gets the same arguments passed
        """
        Parameters
        ----------
        vertices : Sequence[int]
            sequence of vertices
        edges : Sequence[Tuple[int, int]]
            sequence of edge tuples
        weights : Union[None, float, Sequence[float]]
            Edge weights.
            - if None is supplied, the resulting graph is unweighted (unit edge length)
            - if a single float is supplied, every edge length will be equal to this number
            - if a sequence is supplied, this will be mapped onto the edge sequence
        velocity
            constant velocity to compute travel time, optional. default: 1
        """
        TransportSpace.__init__(self, loc_type=LocType.INT)

    def __dealloc__(self):
        del self.derived_ptr

    def __repr__(self):
        return f"Graph(velocity={self.velocity})"

    @property
    def velocity(self):
        return dereference(self.derived_ptr).velocity

    @property
    def vertices(self):
        return dereference(self.derived_ptr).get_vertices()

    @property
    def edges(self):
        return dereference(self.derived_ptr).get_edges()

    @property
    def weights(self):
        return dereference(self.derived_ptr).get_weights()

    @classmethod
    def from_nx(
            cls, G, velocity: float = 1.0, make_attribute_distance: Optional[str] = "distance"
    ):
        """
        Create a Graph from a networkx.Graph with a mandatory distance edge attribute.

        Parameters
        ----------
        G : networkx.Graph
            networkx graph
        velocity
            velocity used for travel time computation
        make_attribute_distance
            name of the nx.DiGraph edge attribute used as distance between nodes.
            If None is supplied, the resulting graph is unweighted (unit edge length).

        Returns
        -------
        Graph instance
        """
        if not isinstance(G, nx.Graph):
            raise TypeError(f"Must supply nx.Graph, not {type(G)}")
        elif G.is_directed():
            raise TypeError(f"Must supply undirected graph")

        if not all(isinstance(u, int) for u in random.sample(list(G.nodes()), k=min(5, len(G)))):
            warnings.warn("Heuristic determined non-int node labels. Converting to int", UserWarning)
            G = nx.relabel.convert_node_labels_to_integers(G)

        if make_attribute_distance is None:
            weights = None
        else:
            weights = [G[u][v][make_attribute_distance] for u, v in G.edges()]

        return cls(
            vertices=list(G.nodes()),
            edges=list(G.edges()),
            weights=weights,
            velocity=velocity
        )

    def random_point(self):
        return random.choice(self.vertices)


    def __reduce__(self):
        return self.__class__, \
            (
                 self.vertices,
                 self.edges,
                 self.weights,
                 self.velocity,
            )

    def asdict(self):
        return dict(
            vertices=self.vertices,
            edges=self.edges,
            weights=self.weights,
            velocity=self.velocity,
        )
