from typing import List, Tuple, Union

import numpy as np
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
        return spd.euclidean(u, v)

    def t(self, u, v):
        return self.d(u, v) / self.velocity

    def interp_dist(self, u, v, dist_to_dest):
        return v - (v - u) * dist_to_dest / self.d(u, v)

    def interp_time(self, u, v, time_to_dest):
        return v - (v - u) * time_to_dest / self.t(u, v)

    def random_point(self):
        return np.random.uniform(*zip(*self.coord_range))
