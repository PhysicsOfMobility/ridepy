import random
import numpy as np

from ridepy.data_structures import TransportSpace, TransportationRequest


class RandomRequestGenerator:
    """
    Generates random requests in the chosen transport space with a certain rate.
    The timewindows for the request are configurable.

    Note:
        The pickup and dropoff timewindows are calculated as follows:
            1. request_pickup_time < request.creation_timestamp + max_pickup_delay
            2. request_delivery_time < request.creation_timestamp + direct_travel_time \
                + max_delivery_delay_abs
            3. request_delivery_time < request.creation_timestamp + direct_travel_time*(1+max_delivery_delay_rel)
    """

    def __init__(
        self,
        *,
        space: TransportSpace,
        rate=1,
        seed=42,
        pickup_timewindow_offset=0,
        request_class=TransportationRequest,
        max_pickup_delay: float = np.inf,
        max_delivery_delay_abs: float = np.inf,
        max_delivery_delay_rel: float = np.inf,
    ):
        """

        Parameters
        ----------
        space
            the TransportSpace in which the requests will be generated.
        rate
            the rate of requests per time unit
        seed
            the random seed
        pickup_timewindow_offset
            each request's pickup_timewindow_min will be this much from the creation timestamp
        request_class
            the generated requests will be instances of this class. Needed to generate pythonic or cythonic requests at will.
        max_pickup_delay
            see class docstring
        max_delivery_delay_abs
            see class docstring
        max_delivery_delay_rel
            see class docstring
        """
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.transport_space = space
        self.rate = rate
        self.request_class = request_class
        self.pickup_timewindow_offset = pickup_timewindow_offset
        self.max_pickup_delay = max_pickup_delay
        self.max_delivery_delay_abs = max_delivery_delay_abs
        self.max_delivery_delay_rel = max_delivery_delay_rel

    def __iter__(self):
        self.now = 0
        self.request_index = -1
        return self

    def __next__(self):
        self.now += np.random.exponential(1 / self.rate)
        self.request_index += 1

        while True:
            origin = self.transport_space.random_point()
            destination = self.transport_space.random_point()
            if origin != destination:
                break

        direct_travel_time = self.transport_space.t(origin, destination)
        pickup_lbound = self.now + self.pickup_timewindow_offset
        pickup_ubound = pickup_lbound + self.max_pickup_delay
        delivery_ubound = (
            pickup_lbound
            + direct_travel_time
            + min(
                self.max_delivery_delay_abs,
                self.max_delivery_delay_rel * direct_travel_time,
            )
        )

        return self.request_class(
            request_id=self.request_index,
            creation_timestamp=self.now,
            origin=origin,
            destination=destination,
            pickup_timewindow_min=pickup_lbound,
            pickup_timewindow_max=pickup_ubound,
            delivery_timewindow_min=pickup_lbound,
            delivery_timewindow_max=delivery_ubound,
        )
