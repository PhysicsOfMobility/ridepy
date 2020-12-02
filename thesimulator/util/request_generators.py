import random

import numpy as np
import pandas as pd

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


class DeterministicRequestGenerator:
    """
    Generates TransportationRequests from a csv file. The csv file must contain the following columns
    named (case sensitive) in the header:
    ID : The unique identifier of a request
    time : The creation time of a request

    Moreover the csv file must contain either:

    origin_location,
    destination_location,

    for 1D topologies and graphs, or

    origin_location_x,
    origin_location_y,
    destination_location_x
    destination_location_y,

    for 2D topologies.

    The csv file may contain the following columns:

    pickup_timewindow_min,
    pickup_timewindow_max,
    delivery_timewindow_min,
    delivery_timewindow_max,

    if these columns are not present, values will be calculated from the default values. The default values
    can be defined in the initialization of DeterministicRequestGenerator.

    Example csv file:

    '''
    ID,time,origin_location_x,origin_location_y,destination_location_x,destination_location_y,pickup_timewindow_min,pickup_timewindow_max
    0,1,0.2,0,0.8,0,1.2,10.0
    1,1.1,0,0,0.1,0,1.1,1.2
    2,1.2,0,0,0.8,0,1.2,10
    3,1.3,0,0,0.8,0,1.3,10
    4,1.4,0,0,0.8,0,1.4,10
    5,1.5,0,0,0.8,0,2.0,10
    '''
    """

    def __init__(
        self,
        file_name: str,
        chunksize: int = 10000,
        transport_space: TransportSpace = Euclidean(n_dimensions=2),
        pickup_timewindow_start=0,
        pickup_timewindow_size=np.inf,
        delivery_timewindow_start=0,
        delivery_timewindow_size=np.inf,
    ):

        self.transport_space = transport_space
        self.file_name = file_name
        self.chunksize = chunksize
        self.pickup_timewindow_start = pickup_timewindow_start
        self.pickup_timewindow_size = pickup_timewindow_size
        self.delivery_timewindow_start = delivery_timewindow_start
        self.delivery_timewindow_size = delivery_timewindow_size
        self.header = self.parse_header()
        self.chunks = pd.read_csv(self.file_name, chunksize=self.chunksize, header=0)

    def __iter__(self):
        self.now = 0
        self.row_index = 0
        try:
            self.current_chunk = next(self.chunks)
            self.request_iterator = self.current_chunk.itertuples(name="Request")
        except StopIteration:
            raise IOError(f"Failed to read file: {self.file_name}")
        return self

    def __next__(self):
        # get next request from this chunk
        try:
            next_request = next(self.request_iterator)
        # if chunk is empty get the next chunk
        except StopIteration:
            # this raises StopIteration if it is empty, which will not be caught on purpose
            self.current_chunk = next(self.chunks)
            self.request_iterator = self.current_chunk.itertuples(name="Request")
            next_request = next(self.request_iterator)

        pickup_timewindow_min = (
            next_request.pickup_timewindow_min
            if "pickup_timewindow_min" in self.header
            else next_request.time + self.pickup_timewindow_start
        )
        pickup_timewindow_max = (
            next_request.pickup_timewindow_max
            if "pickup_timewindow_max" in self.header
            else pickup_timewindow_min + self.pickup_timewindow_size
        )
        delivery_timewindow_min = (
            next_request.delivery_timewindow_min
            if "delivery_timewindow_min" in self.header
            else next_request.time + self.delivery_timewindow_start
        )
        delivery_timewindow_max = (
            next_request.delivery_timewindow_max
            if "delivery_timewindow_max" in self.header
            else delivery_timewindow_min + self.delivery_timewindow_size
        )

        origin = (
            [next_request.origin_location_x, next_request.origin_location_y]
            if "origin_location_x" in self.header and "origin_location_y" in self.header
            else next_request.origin_location
        )

        destination = (
            [next_request.destination_location_x, next_request.destination_location_y]
            if "destination_location_x" in self.header
            and "destination_location_y" in self.header
            else next_request.destination_location
        )

        return TransportationRequest(
            request_id=next_request.ID,
            creation_timestamp=next_request.time,
            origin=origin,
            destination=destination,
            pickup_timewindow_min=pickup_timewindow_min,
            pickup_timewindow_max=pickup_timewindow_max,
            delivery_timewindow_min=delivery_timewindow_min,
            delivery_timewindow_max=delivery_timewindow_max,
        )

    def parse_header(self):
        file = open(self.file_name, "r")
        header_string = file.readline()
        header = header_string.strip().split(",")
        assert "ID" in header, "'ID' column missing"
        assert "origin_location" in header or (
            "origin_location_x" in header and "origin_location_y" in header
        ), "'origin_location' column(s) missing"
        assert "destination_location" in header or (
            "destination_location_x" in header and "destination_location_y" in header
        ), "'destination_location' column(s) missing"
        assert "time" in header, "'time' column missing"

        return header
