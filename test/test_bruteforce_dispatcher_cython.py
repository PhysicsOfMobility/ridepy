import random

import numpy as np
from numpy import inf, isclose
from time import time
import itertools as it
from pandas.core.common import flatten

from thesimulator.data_structures_cython import Stoplist as CyStoplist

from thesimulator import data_structures_cython as cyds
from thesimulator import data_structures as pyds

from thesimulator.events import (
    RequestRejectionEvent,
    PickupEvent,
    DeliveryEvent,
)

from thesimulator.data_structures_cython.data_structures import LocType
from thesimulator.util import spaces as pyspaces
from thesimulator.util.spaces_cython import spaces as cyspaces
from thesimulator.util.request_generators import RandomRequestGenerator

from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.testing_utils import stoplist_from_properties
from thesimulator.vehicle_state import VehicleState as py_VehicleState
from thesimulator.vehicle_state_cython import VehicleState as cy_VehicleState

from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.extras.spaces import make_nx_grid


def test_append_to_empty_stoplist():
    space = cyspaces.Euclidean2D()
    request = cyds.TransportationRequest(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1),
        destination=(0, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    cpestop = cyds.Stop(
        location=(0, 0),
        request=cyds.InternalRequest(
            request_id=-1, creation_timestamp=0, location=(0, 0)
        ),
        action=cyds.StopAction.internal,
        estimated_arrival_time=0,
        time_window_min=0,
        time_window_max=inf,
        occupancy_after_servicing=0,
    )
    stoplist = [cpestop]
    min_cost, new_stoplist, *_ = cy_brute_force_total_traveltime_minimizing_dispatcher(
        request, cyds.Stoplist(stoplist, cyds.LocType.R2LOC), space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


def test_append_due_to_timewindow():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 3, 3]
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination

    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 1, 0]


def test_timewindow_violation_at_dropoff_checked():
    """
    The least traveltime insertion is not chosen because the delay
    dueto dropoff+pickup together would violate a tw_max. Although separately, these
    delays do not.
    """
    space = Manhattan2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 2), 2, 2, 4],
        [(0, 6), 6, 6, 7]
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(0.5, 1.5),
        destination=(0.5, 4.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination

    # but the above should not have occured if the tw_max at the last stop were higher:
    stoplist_properties = [[(0, 1), 1, 0, inf], [(0, 2), 2, 2, 4], [(0, 6), 6, 6, 9]]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination


def test_timewindow_violation_at_pickup_checked():
    space = Manhattan2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 2), 2, 2, 2.5],
        [(0, 6), 6, 6, 9]
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(0.5, 1.5),
        destination=(0.5, 4.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[2].location == request.origin
    assert new_stoplist[3].location == request.destination

    # but the above should not have occured if the tw_max at the last stop were higher:
    stoplist_properties = [[(0, 1), 1, 0, inf], [(0, 2), 2, 2, 4], [(0, 6), 6, 6, 9]]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination


def test_inserted_at_the_middle():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]


def test_inserted_separately():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]


def test_not_inserted_separately_dueto_capacity_constraint():
    """
    Forces the pickup and dropoff to be inserted together solely because
    of seat_capacity=1
    """
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, inf],
        [(0, 5), 5, 0, inf],
        [(0, 7), 7, 0, inf],
    ]
    # fmt: on
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    # the best insertion would be [s0, +, -, s1, s2, s3]
    stoplist = stoplist_from_properties(stoplist_properties)
    for s, cap in zip(stoplist, [0, 1, 0, 1]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 1, 0, 1]

    stoplist = stoplist_from_properties(stoplist_properties)
    # the best insertion would be [s0, s1, s2, s3, +, -,]
    for s, cap in zip(stoplist, [1, 1, 1, 0]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[4].location == request.origin
    assert new_stoplist[5].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [1, 1, 1, 0, 1, 0]


def test_stoplist_not_modified_inplace():
    space = Euclidean2D()
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    stoplist = stoplist_from_properties(stoplist_properties)
    eps = 1e-4
    request = TransportationRequest(
        request_id="a",
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert new_stoplist[3].estimated_arrival_time == 3 + 2 * eps
    assert stoplist[1].estimated_arrival_time == 3


def test_sanity_in_graph():
    """
    Insert a request, note delivery time.
    Handle more requests so that there's no pooling.
    Assert that the delivery time is not changed.

    Or more simply, assert that the vehicle moves at either the space's velocity or 0.
    """

    for velocity in [0.9, 1, 1.1]:
        space = Graph.from_nx(make_nx_grid(), velocity=velocity)

        rg = RandomRequestGenerator(
            rate=10,
            space=space,
            max_delivery_delay_abs=0,
        )

        transportation_requests = list(it.islice(rg, 1000))

        fs = SlowSimpleFleetState(
            initial_locations={k: 0 for k in range(50)},
            seat_capacities=10,
            space=space,
            dispatcher=brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=VehicleState,
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

        assert len(transportation_requests) > len(rejections)
        for req in transportation_requests:
            if (rid := req.request_id) not in rejections:
                assert isclose(req.delivery_timewindow_max, delivery_times[rid])
                assert isclose(
                    delivery_times[rid] - pickup_times[rid],
                    space.t(req.origin, req.destination),
                )


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
    pythonic_solution = py_brute_force_total_traveltime_minimizing_dispatcher(
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

    # Note: we need to create a Cythonic stoplist object here because we cannot pass a python list to
    # cy_brute_force_total_traveltime_minimizing_dispatcher
    stoplist = CyStoplist(
        stoplist_from_properties(stoplist_properties, data_structure_module=cyds),
        loc_type=LocType.R2LOC,
    )

    tick = time()
    # vehicle_id, new_stoplist, (min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do)
    cythonic_solution = cy_brute_force_total_traveltime_minimizing_dispatcher(
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
            dispatcher=py_brute_force_total_traveltime_minimizing_dispatcher,
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
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
            vehicle_state_class=cy_VehicleState,
        )
        rg = RandomRequestGenerator(
            space=cy_space, request_class=cyds.TransportationRequest, seed=seed
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
            dispatcher=cy_brute_force_total_traveltime_minimizing_dispatcher,
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
