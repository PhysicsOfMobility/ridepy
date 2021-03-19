import pytest
import numpy as np
from numpy import inf
from functools import reduce
from time import time
import itertools as it
from pandas.core.common import flatten

from thesimulator.data_structures_cython import Stoplist as cyStoplist

from thesimulator import data_structures_cython as cyds
from thesimulator import data_structures as pyds
from thesimulator.data_structures_cython.data_structures import LocType
from thesimulator.util import spaces as pyspaces
from thesimulator.util.spaces_cython import spaces as cyspaces
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.dispatchers import (
    brute_force_distance_minimizing_dispatcher as py_brute_force_distance_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_distance_minimizing_dispatcher as cy_brute_force_distance_minimizing_dispatcher,
)
from thesimulator.vehicle_state import VehicleState as py_VehicleState
from thesimulator.vehicle_state_cython import VehicleState as cy_VehicleState

from thesimulator.fleet_state import SlowSimpleFleetState


def stoplist_from_properties(stoplist_properties, data_structure_module):
    return [
        data_structure_module.Stop(
            location=loc,
            request=data_structure_module.InternalRequest(
                request_id=999, creation_timestamp=0, location=loc
            ),
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=cpat,
            occupancy_after_servicing=0,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]


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

    stoplist = stoplist_from_properties(stoplist_properties, data_structure_module=pyds)

    tick = time()
    # min_cost, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
    pythonic_solution = py_brute_force_distance_minimizing_dispatcher(
        request, stoplist, pyspaces.Euclidean2D(), seat_capacity
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

    # Note: we need to create a Cythonic stoplist object here because we cannot pass a python list to cy_brute_force_distance_minimizing_dispatcher
    stoplist = cyStoplist(
        stoplist_from_properties(stoplist_properties, data_structure_module=cyds),
        loc_type=LocType.R2LOC,
    )

    tick = time()
    # vehicle_id, new_stoplist, (min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do)
    cythonic_solution = cy_brute_force_distance_minimizing_dispatcher(
        request, stoplist, cyspaces.Euclidean2D(1), seat_capacity
    )
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
    n_reqs = 100
    ir = pyds.InternalRequest(request_id=999, creation_timestamp=0, location=(0, 0))
    s0 = pyds.Stop(
        location=(0, 0),
        request=ir,
        action=pyds.StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=0,
    )
    sl = [s0]

    ssfs = SlowSimpleFleetState(
        initial_stoplists={7: sl},
        seat_capacities=[10],
        space=pyspaces.Euclidean2D(),
        dispatcher=py_brute_force_distance_minimizing_dispatcher,
        vehicle_state_class=py_VehicleState,
    )
    rg = RandomRequestGenerator(
        space=pyspaces.Euclidean2D(),
        request_class=pyds.TransportationRequest,
    )
    reqs = list(it.islice(rg, n_reqs))
    py_events = list(ssfs.simulate(reqs))

    ir = cyds.InternalRequest(request_id=999, creation_timestamp=0, location=(0, 0))
    s0 = cyds.Stop(
        location=(0, 0),
        request=ir,
        action=cyds.StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=0,
    )
    sl = [s0]

    space = cyspaces.Euclidean2D()
    ssfs = SlowSimpleFleetState(
        initial_stoplists={7: sl},
        seat_capacities=[10],
        space=space,
        dispatcher=cy_brute_force_distance_minimizing_dispatcher,
        vehicle_state_class=cy_VehicleState,
    )
    rg = RandomRequestGenerator(space=space, request_class=cyds.TransportationRequest)
    reqs = list(it.islice(rg, n_reqs))
    cy_events = list(ssfs.simulate(reqs))

    # assert that the returned events are the same
    assert len(cy_events) == len(py_events)
    for num, (cev, pev) in enumerate(zip(cy_events, py_events)):
        assert type(cev) == type(pev)
        np.allclose(
            list(flatten(list(pev.__dict__.values()))),
            list(flatten(list(cev.__dict__.values()))),
        )
