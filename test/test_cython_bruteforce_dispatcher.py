import pytest
import numpy as np
from numpy import inf
from functools import reduce
from time import time
import itertools as it
from pandas.core.common import flatten

from thesimulator.cdata_structures import Stoplist as cyStoplist

from thesimulator import cdata_structures as cyds
from thesimulator import data_structures as pyds
from thesimulator.cdata_structures.data_structures import LocType
from thesimulator.util import spaces as pyspaces
from thesimulator.util.cspaces import spaces as cyspaces
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.dispatchers import (
    brute_force_distance_minimizing_dispatcher as py_brute_force_distance_minimizing_dispatcher,
)
from thesimulator.util.cdispatchers import (
    brute_force_distance_minimizing_dispatcher as cy_brute_force_distance_minimizing_dispatcher,
)
from thesimulator.vehicle_state import VehicleState as py_VehicleState
from thesimulator.cvehicle_state import VehicleState as cy_VehicleState

from thesimulator.fleet_state import SlowSimpleFleetState


def stoplist_from_properties(stoplist_properties, data_structure_module):
    return [
        data_structure_module.Stop(
            location=loc,
            request=None,
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=cpat,
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
        request, stoplist, pyspaces.Euclidean2D()
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
        request, stoplist, cyspaces.Euclidean2D(1)
    )
    cy_min_cost, _, cy_timewindows = cythonic_solution
    tock = time()
    print(
        f"Computing insertion into {len_stoplist}-element stoplist with cythonic dispatcher took: {tock-tick} seconds"
    )

    assert np.isclose(py_min_cost, cy_min_cost)
    assert np.allclose(py_timewindows, cy_timewindows)


def test_equivalence_cython_and_python_bruteforce_dispatcher_edge_case():
    """
    Tests that the pure pythonic and cythonic brute force dispatcher produces identical results in a specific edge case.
    """
    stop_locations = np.array([
        [0.11214248, 0.3257659],
        [0.05808361, 0.86617615],
        [0.60111501, 0.70807258],
        [0.96990985, 0.83244264],
        [0.95071431, 0.73199394],
        [0.59865848, 0.15601864],
        [0.21233911, 0.18182497]
    ])
    arrival_times = np.cumsum(
        [np.linalg.norm(x - y) for x, y in zip(stop_locations[:-1], stop_locations[1:])]
    )
    arrival_times = np.insert(arrival_times, 0, 0)
    # location, CPAT, tw_min, tw_max,
    stoplist_properties = [
        [stop_loc, CPAT, 0, inf]
        for stop_loc, CPAT in zip(stop_locations, arrival_times)
    ]
    origin = np.array([0.30424224, 0.52475643])
    destination = np.array([0.43194502, 0.29122914])

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

    # min_cost, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
    pythonic_solution = py_brute_force_distance_minimizing_dispatcher(
        request, stoplist, pyspaces.Euclidean2D()
    )
    py_min_cost, _, py_timewindows = pythonic_solution

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

    # vehicle_id, new_stoplist, (min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do)
    cythonic_solution = cy_brute_force_distance_minimizing_dispatcher(
        request, stoplist, cyspaces.Euclidean2D(1)
    )
    cy_min_cost, _, cy_timewindows = cythonic_solution

    assert np.isclose(py_min_cost, cy_min_cost)
    assert np.allclose(py_timewindows, cy_timewindows)



def test_equivalence_simulator_cython_and_python_bruteforce_dispatcher(seed=42):
    ir = pyds.InternalRequest(999, 0, (0, 0))
    s0 = pyds.Stop((0,0), ir, pyds.StopAction.internal, 0,0,0)
    sl = [s0]

    sfls = SlowSimpleFleetState(initial_stoplists={7: sl},
                                space=pyspaces.Euclidean2D(),
                                dispatcher=py_brute_force_distance_minimizing_dispatcher, vehicle_state_class=py_VehicleState)
    rg = RandomRequestGenerator(space=pyspaces.Euclidean2D(), request_class=pyds.TransportationRequest, )
    reqs = list(it.islice(rg, 10))
    py_events = list(sfls.simulate(reqs))


    ir = cyds.InternalRequest(999, 0, (0, 0))
    s0 = cyds.Stop((0,0), ir, cyds.StopAction.internal, 0,0,0)
    sl = [s0]

    sfls = SlowSimpleFleetState(initial_stoplists={7: sl},
                                space=cyspaces.Euclidean2D(),
                                dispatcher=cy_brute_force_distance_minimizing_dispatcher, vehicle_state_class=cy_VehicleState)
    # So far, cyspaces.Euclidean2D doesn't support random point generation. So we are using the hack of
    # Asking RandomRequestGenerator to use the python space to generate random points, but return cython
    # objects. This should be changed when the cython spaces support random sampling.
    rg = RandomRequestGenerator(space=pyspaces.Euclidean2D(), request_class=cyds.TransportationRequest)
    reqs = list(it.islice(rg, 10))
    cy_events = list(sfls.simulate(reqs))

    # assert that the returned events are the same
    assert len(cy_events) == len(py_events)
    for num, (cev, pev) in enumerate(zip(cy_events, py_events)):
        assert type(cev) == type(pev)
        np.allclose(list(flatten(list(pev.__dict__.values()))),
                    list(flatten(list(cev.__dict__.values()))))

