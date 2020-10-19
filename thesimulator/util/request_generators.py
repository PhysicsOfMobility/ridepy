import random

import numpy as np

from thesimulator.data_structures import TransportSpace, TransportationRequest
from thesimulator.util.spaces import Euclidean


class RandomRequestGenerator:
    def __init__(
        self,
        transport_space: TransportSpace = Euclidean(n_dimensions=2),
        rate=1,
        seed=42,
        pickup_timewindow_start=0,
        pickup_timewindow_size=20,
        dropoff_timewindow_start=None,
        dropoff_timewindow_size=None,
    ):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.transport_space = transport_space
        self.rate = rate
        self.pickup_timewindow_start = pickup_timewindow_start
        self.pickup_timewindow_size = pickup_timewindow_size
        self.dropoff_timewindow_start = dropoff_timewindow_start
        self.dropoff_timewindow_size = dropoff_timewindow_size

    def __iter__(self):
        self.now = 0
        self.request_index = -1
        return self

    def __next__(self):
        self.now = self.now + np.random.exponential(1 / self.rate)
        self.request_index += 1
        return TransportationRequest(
            request_id=self.request_index,
            creation_timestamp=self.now,
            origin=self.transport_space.random_point(),
            destination=self.transport_space.random_point(),
            pickup_timewindow_min=self.now + self.pickup_timewindow_start
            if self.pickup_timewindow_start is not None
            else 0,
            pickup_timewindow_max=self.now + self.pickup_timewindow_size
            if self.pickup_timewindow_size is not None
            else np.inf,
            delivery_timewindow_min=self.now + self.dropoff_timewindow_start
            if self.dropoff_timewindow_start is not None
            else 0,
            delivery_timewindow_max=self.now + self.dropoff_timewindow_size
            if self.dropoff_timewindow_size is not None
            else np.inf,
        )
