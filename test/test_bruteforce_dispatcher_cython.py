import random
import pytest

import numpy as np
import itertools as it

from numpy import inf, isclose
from time import time
from pandas.core.common import flatten

from ridepy.data_structures_cython import Stoplist as CyStoplist

from ridepy import data_structures_cython as cyds
from ridepy import data_structures as pyds

from ridepy.events import (
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)

from ridepy.data_structures_cython.data_structures import LocType
from ridepy.util import spaces as pyspaces
from ridepy.util.spaces_cython import spaces as cyspaces
from ridepy.util.request_generators import RandomRequestGenerator

from ridepy.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)
from ridepy.util.testing_utils_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from ridepy.util.dispatchers_cython import BruteForceTotalTravelTimeMinimizingDispatcher
from ridepy.util.testing_utils import stoplist_from_properties
from ridepy.vehicle_state import VehicleState as py_VehicleState
from ridepy.vehicle_state_cython import VehicleState as cy_VehicleState

from ridepy.fleet_state import SlowSimpleFleetState
from ridepy.extras.spaces import make_nx_grid


def test_equivalence_cython_and_python_bruteforce_dispatcher(seed=42):
    """
    Tests that the pure pythonic and cythonic brute force dispatcher produces identical results.
    """
    len_stoplist = 100
    seat_capacity = 4
    rnd = np.random.RandomState(seed)
    stop_locations = rnd.uniform(low=0, high=100, size=(len_stoplist, 2))
    arrival_times = np.cumsum(
        [np.linalg.norm(x - y) for x, y in zip(stop_locations[:-1], stop_locations[1:])]
    )
    arrival_times = np.insert(arrival_times, 0, 0)
    # location, CPAT, tw_min, tw_max,
    stoplist_properties = [
        [stop_loc, CPAT, 0, inf]
        for stop_loc, CPAT in zip(stop_locations, arrival_times)
    ]
    origin = list(rnd.uniform(low=0, high=100, size=2))
    destination = list(rnd.uniform(low=0, high=100, size=2))

    # first call the pure pythonic dispatcher
    request = pyds.TransportationRequest(
        request_id=100,
        creation_timestamp=1,
        origin=origin,
        destination=destination,
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    space = pyspaces.Euclidean2D()
    stoplist = stoplist_from_properties(
        stoplist_properties=stoplist_properties, kind="python", space=space
    )

    tick = time()
    # min_cost, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
    pythonic_solution = py_brute_force_total_traveltime_minimizing_dispatcher()(
        request, stoplist, space, seat_capacity
    )
    py_min_cost, _, py_timewindows = pythonic_solution
    tock = time()
    print(
        f"Computing insertion into {len_stoplist}-element stoplist with pure pythonic dispatcher took: {tock - tick} seconds"
    )

    # then call the cythonic dispatcher
    request = cyds.TransportationRequest(
        request_id=100,
        creation_timestamp=1,
        origin=origin,
        destination=destination,
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )

    # Note: we need to create a Cythonic stoplist object here because we cannot pass a python list to
    # cy_brute_force_total_traveltime_minimizing_dispatcher
    space = cyspaces.Euclidean2D()
    stoplist = stoplist_from_properties(
        stoplist_properties=stoplist_properties, kind="cython", space=space
    )
    tick = time()
    # vehicle_id, new_stoplist, (min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do)
    cythonic_solution = cy_brute_force_total_traveltime_minimizing_dispatcher(
        LocType.R2LOC
    )(request, stoplist, space, seat_capacity)
    cy_min_cost, _, cy_timewindows = cythonic_solution
    tock = time()
    print(
        f"Computing insertion into {len_stoplist}-element stoplist with cythonic dispatcher took: {tock-tick} seconds"
    )

    assert np.isclose(py_min_cost, cy_min_cost)
    assert np.allclose(py_timewindows, cy_timewindows)


def test_equivalence_simulator_cython_and_python_bruteforce_dispatcher(seed=42):
    """
    Tests that the simulation runs with pure pythonic and cythonic brute force dispatcher produces identical events.
    """
    for py_space, cy_space in (
        (pyspaces.Euclidean2D(), cyspaces.Euclidean2D()),
        (
            pyspaces.Graph.from_nx(make_nx_grid()),
            cyspaces.Graph.from_nx(make_nx_grid()),
        ),
    ):

        n_reqs = 100

        random.seed(seed)
        init_loc = py_space.random_point()
        random.seed(seed)
        assert init_loc == cy_space.random_point()

        ######################################################
        # PYTHON
        ######################################################

        ssfs = SlowSimpleFleetState(
            initial_locations={7: init_loc},
            seat_capacities=10,
            space=py_space,
            dispatcher=py_brute_force_total_traveltime_minimizing_dispatcher(),
            vehicle_state_class=py_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=py_space,
            request_class=pyds.TransportationRequest,
            seed=seed,
            rate=1.5,
        )
        py_reqs = list(it.islice(rg, n_reqs))
        py_events = list(ssfs.simulate(py_reqs))

        ######################################################
        # CYTHON
        ######################################################

        ssfs = SlowSimpleFleetState(
            initial_locations={7: init_loc},
            seat_capacities=10,
            space=cy_space,
            dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(
                loc_type=cy_space.loc_type
            ),
            vehicle_state_class=cy_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=cy_space,
            request_class=cyds.TransportationRequest,
            seed=seed,
            rate=1.5,
        )
        cy_reqs = list(it.islice(rg, n_reqs))
        cy_events = list(ssfs.simulate(cy_reqs))

        ######################################################
        # COMPARE
        ######################################################
        # assert that the returned events are the same
        assert len(cy_events) == len(py_events)
        for num, (cev, pev) in enumerate(zip(cy_events, py_events)):
            assert type(cev) == type(pev)
            assert np.allclose(
                list(flatten(list(pev.__dict__.values()))),
                list(flatten(list(cev.__dict__.values()))),
                rtol=1e-4,
            )


def test_sanity_in_graph():
    """
    Insert a request, note delivery time.
    Handle more requests so that there's no pooling.
    Assert that the delivery time is not changed.

    Or more simply, assert that the vehicle moves at either the space's velocity or 0.
    """

    for velocity in [0.9, 1, 1.1]:
        space = cyspaces.Graph.from_nx(make_nx_grid(), velocity=velocity)

        rg = RandomRequestGenerator(
            rate=10,
            space=space,
            max_pickup_delay=0,
            max_delivery_delay_abs=0,
            request_class=cyds.TransportationRequest,
        )

        transportation_requests = list(it.islice(rg, 1000))

        fs = SlowSimpleFleetState(
            initial_locations={k: 0 for k in range(50)},
            seat_capacities=10,
            space=space,
            dispatcher=BruteForceTotalTravelTimeMinimizingDispatcher(LocType.INT),
            vehicle_state_class=cy_VehicleState,
        )

        events = list(fs.simulate(transportation_requests))

        rejections = set(
            ev.request_id for ev in events if isinstance(ev, RequestRejectionEvent)
        )
        pickup_times = {
            ev.request_id: ev.timestamp for ev in events if isinstance(ev, PickupEvent)
        }
        delivery_times = {
            ev.request_id: ev.timestamp
            for ev in events
            if isinstance(ev, DeliveryEvent)
        }

        for req in transportation_requests:

            if (rid := req.request_id) not in rejections:
                assert isclose(req.delivery_timewindow_max, delivery_times[rid])
                assert isclose(
                    delivery_times[rid] - pickup_times[rid],
                    space.t(req.origin, req.destination),
                )
