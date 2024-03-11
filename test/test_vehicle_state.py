import pytest
import random

import numpy as np

from ridepy.vehicle_state import VehicleState as PyVehicleState
from ridepy.data_structures import (
    Stop as PyStop,
    InternalRequest as PyInternalRequest,
    StopAction as PyStopAction,
    TransportationRequest as PyTransportationRequest,
)
from ridepy.util.spaces import Euclidean2D as PyEuclidean2D, Graph as PyGraph
from ridepy.util.dispatchers.ridepooling import (
    BruteForceTotalTravelTimeMinimizingDispatcher as PyBruteForceTotalTravelTimeMinimizingDispatcher,
)

from ridepy.vehicle_state_cython import VehicleState as CyVehicleState
from ridepy.data_structures_cython import (
    Stop as CyStop,
    InternalRequest as CyInternalRequest,
    StopAction as CyStopAction,
    TransportationRequest as CyTransportationRequest,
)
from ridepy.util.spaces_cython import Euclidean2D as CyEuclidean2D, Graph as CyGraph
from ridepy.util.dispatchers_cython import (
    BruteForceTotalTravelTimeMinimizingDispatcher as CyBruteForceTotalTravelTimeMinimizingDispatcher,
)

from ridepy.extras.spaces import (
    make_nx_cycle_graph,
    make_nx_grid,
    make_nx_star_graph,
)


@pytest.mark.parametrize("backend", ["python", "cython"])
@pytest.mark.parametrize("space", ["euclid1d", "euclid2d", "grid"])
def test_fast_forward_time(backend, space):
    random.seed(43)
    np.random.seed(43)

    if backend == "python":
        vehicle_state_cls = PyVehicleState
        stop_cls = PyStop
        stop_action_cls = PyStopAction
        request_cls = PyTransportationRequest
        internal_request_cls = PyInternalRequest
        dispatcher_cls = PyBruteForceTotalTravelTimeMinimizingDispatcher
        graph_cls = PyGraph
        euclid2d_cls = PyEuclidean2D
    elif backend == "cython":
        vehicle_state_cls = CyVehicleState
        stop_cls = CyStop
        stop_action_cls = CyStopAction
        request_cls = CyTransportationRequest
        internal_request_cls = CyInternalRequest
        dispatcher_cls = CyBruteForceTotalTravelTimeMinimizingDispatcher
        graph_cls = CyGraph
        euclid2d_cls = CyEuclidean2D
    else:
        raise ValueError

    if space == "euclid1d":
        space_cls = euclid2d_cls
        space = space_cls(coord_range=[(0, 1), (0, 0)])
    elif space == "euclid2d":
        space_cls = euclid2d_cls
        space = space_cls(coord_range=[(0, 1), (0, 1)])
    elif space == "grid":
        space = graph_cls.from_nx(make_nx_grid())
    else:
        raise ValueError

    initial_location = space.random_point()
    dispatcher = dispatcher_cls(loc_type=space.loc_type)

    get_vehicle_state = lambda: vehicle_state_cls(
        vehicle_id=0,
        initial_stoplist=[
            stop_cls(
                location=initial_location,
                request=internal_request_cls(
                    request_id=-1,
                    creation_timestamp=0,
                    location=initial_location,
                ),
                action=stop_action_cls.internal,
                estimated_arrival_time=0,
                occupancy_after_servicing=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ],
        space=space,
        dispatcher=dispatcher,
        seat_capacity=8,
    )

    pu_location = space.random_point()
    while pu_location == initial_location:
        pu_location = space.random_point()

    do_location = space.random_point()
    while do_location in [pu_location, initial_location]:
        do_location = space.random_point()

    t_il_pu = space.t(initial_location, pu_location)
    t_pu_do = space.t(pu_location, do_location)

    request = request_cls(
        request_id=0,
        creation_timestamp=0,
        origin=pu_location,
        destination=do_location,
        pickup_timewindow_min=0,
        pickup_timewindow_max=np.inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=np.inf,
    )

    ###########################################################################
    # Case 1: idling
    ###########################################################################

    vehicle_state = get_vehicle_state()

    assert len(vehicle_state.stoplist) == 1
    assert vehicle_state.stoplist[0].location == initial_location
    assert vehicle_state.stoplist[0].estimated_arrival_time == 0

    vehicle_state.fast_forward_time(10)

    assert len(vehicle_state.stoplist) == 1
    assert vehicle_state.stoplist[0].location == initial_location
    assert vehicle_state.stoplist[0].estimated_arrival_time == 10

    ###########################################################################
    # Case 2: [CPE, PU, DO], jump to in-between CPE and PU
    ###########################################################################

    vehicle_state = get_vehicle_state()

    vehicle_state.handle_transportation_request_single_vehicle(request)
    vehicle_state.select_new_stoplist()

    # between start and PU
    t = t_il_pu / 3
    vehicle_state.fast_forward_time(t)

    assert len(vehicle_state.stoplist) == 3
    loc, jump_time = space.interp_time(initial_location, pu_location, t_il_pu - t)
    assert np.isclose(vehicle_state.stoplist[0].location, loc).all()
    assert vehicle_state.stoplist[0].estimated_arrival_time == t + jump_time

    ###########################################################################
    # Case 3: [CPE, PU, DO], jump to in-between PU and DO
    ###########################################################################

    vehicle_state = get_vehicle_state()

    vehicle_state.handle_transportation_request_single_vehicle(request)
    vehicle_state.select_new_stoplist()

    # between PU and DO
    t = t_il_pu + t_pu_do / 3
    vehicle_state.fast_forward_time(t)

    assert len(vehicle_state.stoplist) == 2
    loc, jump_time = space.interp_time(pu_location, do_location, t_il_pu + t_pu_do - t)
    assert vehicle_state.stoplist[0].location == loc
    assert vehicle_state.stoplist[0].estimated_arrival_time == t + jump_time

    ###########################################################################
    # Case 4: [CPE, PU, DO], jump to after DO
    ###########################################################################

    vehicle_state = get_vehicle_state()

    vehicle_state.handle_transportation_request_single_vehicle(request)
    vehicle_state.select_new_stoplist()

    # after DO
    t = t_il_pu + t_pu_do + 1
    vehicle_state.fast_forward_time(t)

    assert len(vehicle_state.stoplist) == 1
    loc, jump_time = do_location, 0
    assert vehicle_state.stoplist[0].location == loc
    assert vehicle_state.stoplist[0].estimated_arrival_time == t + jump_time

    ###########################################################################
    # Case 4: [CPE, PU, DO], jump to in-betwen CPE/PU, to in-between PU/DO,
    # and to after DO successively
    ###########################################################################

    vehicle_state = get_vehicle_state()

    vehicle_state.handle_transportation_request_single_vehicle(request)
    vehicle_state.select_new_stoplist()

    # between start and PU
    t = t_il_pu / 3
    vehicle_state.fast_forward_time(t)

    # between PU and DO
    t = t_il_pu + t_pu_do / 3
    vehicle_state.fast_forward_time(t)

    assert len(vehicle_state.stoplist) == 2
    loc, jump_time = space.interp_time(pu_location, do_location, t_il_pu + t_pu_do - t)
    assert vehicle_state.stoplist[0].location == loc
    assert vehicle_state.stoplist[0].estimated_arrival_time == t + jump_time

    # AND after DO
    t = t_il_pu + t_pu_do + 1
    vehicle_state.fast_forward_time(t)

    assert len(vehicle_state.stoplist) == 1
    loc, jump_time = do_location, 0
    assert vehicle_state.stoplist[0].location == loc
    assert vehicle_state.stoplist[0].estimated_arrival_time == t + jump_time
