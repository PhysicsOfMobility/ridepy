import pytest
import numpy as np
from numpy import inf
from functools import reduce
from time import time


from thesimulator import cdata_structures as cds
from thesimulator import data_structures as pyds
from thesimulator.util import spaces as pyspaces

from thesimulator import cvehicle_state as cvs
from thesimulator import vehicle_state as pyvs


from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher

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
    pythonic_solution = brute_force_distance_minimizing_dispatcher(request, stoplist, pyspaces.Euclidean2D())
    py_min_cost, _, py_timewindows = pythonic_solution
    tock = time()
    print(f"Computing insertion into {len_stoplist}-element stoplist with pure pythonic dispatcher took: {tock - tick} seconds")

    # then call the cythonic dispatcher
    request = cds.TransportationRequest(
        request_id=100,
        creation_timestamp=1,
        origin=origin,
        destination=destination,
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )

    stoplist = stoplist_from_properties(stoplist_properties, data_structure_module=cds)
    vstate = cvs.VehicleState(vehicle_id=12, initial_stoplist=stoplist)

    tick = time()
    # vehicle_id, (min_cost, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do))
    cythonic_solution = vstate.handle_transportation_request_single_vehicle(request)
    _, (cy_min_cost, _, cy_timewindows) = cythonic_solution
    tock = time()
    print(f"Computing insertion into {len_stoplist}-element stoplist with cythonic dispatcher took: {tock-tick} seconds")

    assert np.isclose(py_min_cost, cy_min_cost)
    assert np.allclose(py_timewindows, cy_timewindows)

