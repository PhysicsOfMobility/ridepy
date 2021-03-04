import random
import numpy as np

from typing import Union

from thesimulator.data_structures import TransportSpace, TransportationRequest
from thesimulator.cdata_structures import (
    TransportationRequest as CTransportationRequest,
)
from thesimulator.util.spaces import Euclidean


class RandomRequestGenerator:
    def __init__(
        self,
        *,
        space: TransportSpace,
        rate=1,
        seed=42,
        pickup_timewindow_start=0,
        pickup_timewindow_size=np.inf,
        dropoff_timewindow_start=0,
        dropoff_timewindow_size=np.inf,
        request_class=TransportationRequest,
    ):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.transport_space = space
        self.rate = rate
        self.pickup_timewindow_start = pickup_timewindow_start
        self.pickup_timewindow_size = pickup_timewindow_size
        self.dropoff_timewindow_start = dropoff_timewindow_start
        self.dropoff_timewindow_size = dropoff_timewindow_size
        self.request_class = request_class

    def __iter__(self):
        self.now = 0
        self.request_index = -1
        return self

    def __next__(self):
        self.now += np.random.exponential(1 / self.rate)
        self.request_index += 1
        return self.request_class(
            request_id=self.request_index,
            creation_timestamp=self.now,
            origin=self.transport_space.random_point(),
            destination=self.transport_space.random_point(),
            pickup_timewindow_min=self.now + self.pickup_timewindow_start,
            pickup_timewindow_max=self.now
            + self.pickup_timewindow_start
            + self.pickup_timewindow_size,
            delivery_timewindow_min=self.now + self.dropoff_timewindow_start,
            delivery_timewindow_max=self.now
            + self.dropoff_timewindow_start
            + self.dropoff_timewindow_size,
        )
