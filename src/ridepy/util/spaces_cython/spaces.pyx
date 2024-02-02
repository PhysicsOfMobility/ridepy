# distutils: language = c++

import random
import warnings
import itertools as it
import networkx as nx
import math as m

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


cdef class Grid2D(Manhattan2D):
    """
    Fast 2D grid network space, realized as a discrete 2D space with Manhattan metric.

    Note that this space does not enforce the discrete integer coordinate pairs it is
    supposed to be used with. This means that you have to take care yourself to only
    introduce integer coordinate pairs. This implies that the distance and time functions
    ``Grid2D.d`` and ``Grid2D.t`` will in fact as if the space were continuous.
    The discrete/graph characteristic of the space is encoded in the interpolation and
    random point generation functions.

    The interpolation function will always assume the shortest path with no turns or a
    single right turn.
    """
    def __cinit__(self, int n=10, int m=10, double dn=1, double dm=1, double velocity=1):
        self.loc_type = LocType.R2LOC
        self.derived_ptr = self.u_space.space_r2loc_ptr = new CManhattan2D(velocity)

    def __init__(self, n=10, m=10, dn=1, dm=1, velocity=1):
        """
        Parameters
        ----------
        velocity
            constant velocity to compute travel time, optional. default: 1
        """
        TransportSpace.__init__(self, loc_type=LocType.R2LOC)

        self.n = n
        self.m = m
        self.dn = dn
        self.dm = dm
        self.velocity = velocity

    def d(self, u, v):
        return abs(u[0] - v[0]) * self.dn + abs(u[1] - v[1]) * self.dm

    def t(self, u, v):
        return self.d(u, v) / self.velocity

    def interp_dist(self, u, v, double dist_to_dest):
        d_r = dist_to_dest # Remaining distance
        d_t = self.d(u, v) # Total distance
        d_e = d_t - d_r # Elapsed distance
        d_n = self.dn # Vertical grid spacing
        d_m = self.dm # Horizontal grid spacing


        if d_r == d_t:
            # We are still at the origin
            # print("We are still at the origin")
            i = u[0]
            j = u[1]
            d_j = 0
        elif d_r == 0:
            # We have reached the destination
            # print("We have reached the destination")
            i = v[0]
            j = v[1]
            d_j = 0
        else:
            # We are under way
            # print("We are under way")
            w = (v[0] - u[0], v[1] - u[1])

            d_vert = abs(w[0]) * d_n
            d_hori = abs(w[1]) * d_m

            if (w[0] < 0 < w[1]) or (w[0] > 0 > w[1]) or (w[1] == 0):
                # Going vertically, first
                # print("Going vertically, first")
                if d_e <= d_vert:
                    # We have not made the turn.
                    # print("We have not made the turn")
                    j = u[1]
                    # Determine next node:
                    if w[0] < 0:
                        # Going upwards
                        # print("Going upwards")
                        d_e_d = d_e
                        k_d_e_d = m.ceil(d_e_d / d_n)
                        i = u[0] - k_d_e_d
                        d_j = k_d_e_d * d_n - d_e_d
                    else:
                        # Going downwards
                        # print("Going downwards")
                        d_e_d = d_e
                        k_d_e_d = m.ceil(d_e_d / d_n)
                        i = u[0] + k_d_e_d
                        d_j = k_d_e_d * d_n - d_e_d
                else:
                    # We have made the turn.
                    # print("We have made the turn")
                    i = v[0]
                    # Determine next node:
                    if w[1] < 0:
                        # Going left
                        # print("Going left")
                        d_e_d = d_e - d_vert
                        k_d_e_d = m.ceil(d_e_d / d_m)
                        j = u[1] - k_d_e_d
                        d_j =  k_d_e_d * d_m - d_e_d
                    else:
                        # Going right
                        # print("Going right")
                        d_e_d = d_e - d_vert
                        k_d_e_d = m.ceil(d_e_d / d_m)
                        j = u[1] + k_d_e_d
                        d_j =  k_d_e_d * d_m - d_e_d
            else:
                # Going horizontally, first
                # print("Going horizontally, first")
                if d_e <= d_hori:
                    # We have not made the turn
                    # print("We have not made the turn")
                    i = u[0]
                    # Determine the next node:
                    if w[1] < 0:
                        # Going left
                        # print("Going left")
                        d_e_d = d_e
                        k_d_e_d = m.ceil(d_e_d / d_m)
                        j = u[1] - k_d_e_d
                        d_j =  k_d_e_d * d_m - d_e_d
                    else:
                        # Going right
                        # print("Going right")
                        d_e_d = d_e
                        k_d_e_d = m.ceil(d_e_d / d_m)
                        j = u[1] + k_d_e_d
                        d_j =  k_d_e_d * d_m - d_e_d
                else:
                    # We have made the turn
                    # print("We have made the turn")
                    j = v[1]
                    # Determine the next node:
                    if w[0] < 0:
                        # Going upwards
                        # print("Going upwards")
                        d_e_d = d_e - d_hori
                        k_d_e_d = m.ceil(d_e_d / d_n)
                        i = u[0] - k_d_e_d
                        d_j = k_d_e_d * d_n - d_e_d
                    else:
                        # Going downwards
                        # print("Going downwards")
                        d_e_d = d_e - d_hori
                        k_d_e_d = m.ceil(d_e_d / d_n)
                        i = u[0] + k_d_e_d
                        d_j = k_d_e_d * d_n - d_e_d

            print(f"d_r = {d_r}, d_t = {d_t}, d_e = {d_e}, d_n = {d_n}, d_m = {d_m}, w = {w}, d_vert = {d_vert}, "
                  f"d_hori = {d_hori}, d_e_d = {d_e_d}, k_d_e_d = {k_d_e_d}, i = {i}, j = {j}, d_j = {d_j}")
        return (round(i), round(j)), d_j


    def interp_time(self, u, v, double time_to_dest):
        nn, d_j = self.interp_dist(u, v, time_to_dest * self.velocity)
        t_j = d_j / self.velocity
        return nn, t_j

    def random_point(self):
        i = random.randint(0, self.n - 1)
        j = random.randint(0, self.m - 1)
        return i, j

    def __repr__(self):
        return f"Grid2D(n={self.n}, m={self.m}, dn={self.dn}, dm={self.dm}, velocity={self.velocity})"

    def asdict(self):
        return dict(n=self.n, m=self.m, dn=self.dn, dm=self.dm, velocity=self.velocity)
    def __reduce__(self):
        return self.__class__, (self.n, self.m, self.dn, self.dm, self.velocity)

cdef class Grid2D_QM(Grid2D):
    """
    Same as Grid2D, except that the bus routes are nonunique. This means that the choice of the
    (non-unique) shortest path on the grid will only be made at the time of interpolation ("measurement").
    This has the benefit that buses tend to move along the Euclidean shortest path. The drawback is that
    interpolating multiple times along the route will produce inconsistent paths taken.
    """

    def interp_dist(self, u, v, double dist_to_dest):
        d_r = dist_to_dest
        d_n = self.dn
        d_m = self.dm

        if d_r == 0:
            nn = v
            d_j = 0
        else:
            frac = d_r / self.d(u, v)
            x = (u[0] * frac + (1 - frac) * v[0]) * d_n, (u[1] * frac + (1 - frac) * v[1]) * d_m
            # print(x)

            # determine grid cell target node:
            if u[0] < v[0]:
                # going downwards
                # print('going down')
                i = m.ceil(x[0] / d_n)
            elif u[0] > v[0]:
                # going upwards
                # print('going up')
                i = m.floor(x[0] / d_n)
            else:
                # going horizontally
                i = u[0] / d_n

            if u[1] < v[1]:
                # going right
                # print('going right')
                j = m.ceil(x[1] / d_m)
            elif u[1] > v[1]:
                # going left
                # print('going left')
                j = m.floor(x[1] / d_m)
            else:
                # going vertically
                j = u[1] / d_m

            # distance remaining from grid cell target node
            d_r_p = abs(v[0] - i) * d_n + abs(v[1] - j) * d_m

            # distance within grid cell to grid cell target node
            d_g = d_r - d_r_p

            # assumption: we always deviate to the left
            if (u[0] >= v[0] and u[1] < v[1]) or (u[0] <= v[0] and u[1] > v[1]):
                # coming in horizontally
                # print('coming in horizontally')
                horizontal = True
                d_gref = d_m
            else:
                # coming in vertically
                # print('coming in vertically')
                horizontal = False
                d_gref = d_n

            if d_g < d_gref:
                # next node is grid cell target node,
                # jump distance is grid cell distance
                nn = (i, j)
                d_j = d_g
            else:
                d_j = d_g - d_gref
                if horizontal:
                    # coming in horizontally
                    if u[1] < v[1]:
                        # coming in from the left
                        # print('coming in from the left')
                        nn = (i, j - 1)
                    else:
                        # coming in from the right
                        # print('coming in from the right')
                        nn = (i, j + 1)
                else:
                    # coming in vertically
                    if u[0] < v[0]:
                        # coming in from above
                        # print('coming in from above')
                        nn = (i - 1, j)
                    else:
                        # coming in from below
                        # print('coming in from below')
                        nn = (i + 1, j)

        return (round(nn[0]), round(nn[1])), d_j


    def __repr__(self):
        return f"Grid2D_QM(n={self.n}, m={self.m}, dn={self.dn}, dm={self.dm}, velocity={self.velocity})"

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
