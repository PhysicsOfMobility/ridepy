from enum import Enum, auto
import numpy as np
import string
import random

from .data_structures import TransportationRequest
import scipy.spatial.distance as spd

from typing import Union, Iterable, Tuple
from abc import ABC, abstractmethod


class TransportSpace(ABC):
    @abstractmethod
    def d(self, u, v) -> Union[int, float]:
        ...

    @abstractmethod
    def random_point(self):
        ...


class Euclidean(TransportSpace):
    def __init__(
        self,
        n_dimensions: int = 1,
        coord_range: Iterable[Tuple[Union[int, float], Union[int, float]]] = None,
    ):
        self.n_dimensions = n_dimensions
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

    def random_point(self):
        return np.random.uniform(*zip(*self.coord_range))


def short_uuid():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


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
            else None,
            pickup_timewindow_max=self.now + self.pickup_timewindow_size
            if self.pickup_timewindow_size is not None
            else None,
            delivery_timewindow_min=self.now + self.dropoff_timewindow_start
            if self.dropoff_timewindow_start is not None
            else None,
            delivery_timewindow_max=self.now + self.dropoff_timewindow_size
            if self.dropoff_timewindow_size is not None
            else None,
        )
