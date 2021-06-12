import numpy as np
from numpy import inf
from itertools import chain

from typing import Iterable
from ridepy.data_structures_cython import (
    StopAction,
    TransportationRequest,
    InternalRequest,
    Stop,
    Stoplist,
    LocType,
)
from ridepy.util.spaces_cython import Manhattan2D
from ridepy.util.dispatchers_cython import optimize_stoplists

create_request_from_properties = lambda req_id, orig, dest: TransportationRequest(
    request_id=req_id, creation_timestamp=0, origin=orig, destination=dest
)

pu = StopAction.pickup
do = StopAction.dropoff


def create_stoplist_from_properties(
    actions: Iterable[tuple[TransportationRequest, StopAction]],
    initial_location,
    initial_time=0,
    initial_load=0,
    space=Manhattan2D(),
):
    sl = []
    t = initial_time
    load = initial_load
    ir = InternalRequest(request_id=-1, creation_timestamp=0, location=initial_location)
    cpe_stop = Stop(
        location=initial_location,
        request=ir,
        action=StopAction.internal,
        occupancy_after_servicing=load,
        estimated_arrival_time=t,
        time_window_min=0,
        time_window_max=inf,
    )
    sl.append(cpe_stop)
    prev_loc = cpe_stop.location
    for req, action in actions:
        if action == StopAction.pickup:
            loc = req.origin
            load += 1
        elif action == StopAction.dropoff:
            loc = req.destination
            load -= 1
        else:
            raise ValueError(f"Do not understand action {action}")
        t += space.t(prev_loc, loc)
        s = Stop(
            location=loc,
            request=req,
            action=action,
            estimated_arrival_time=t,
            occupancy_after_servicing=load,
            time_window_min=0,
            time_window_max=inf,
        )
        sl.append(s)
        prev_loc = loc
    return Stoplist(sl, LocType.R2LOC)


def test_ortools_optimization_honours_capacity_constraints():
    r1 = create_request_from_properties(req_id=1, orig=(2, 0), dest=(4, 0))
    r2 = create_request_from_properties(req_id=2, orig=(3, 0), dest=(5, 0))

    old_stoplist = create_stoplist_from_properties(
        initial_location=(0, 0),
        initial_load=0,
        actions=[(r1, pu), (r2, pu), (r1, do), (r2, do)],
        space=Manhattan2D(),
    )
    # If the capacity is >1, pooling should occur
    (new_stoplist,) = optimize_stoplists(
        [old_stoplist], Manhattan2D(), [10], current_time=0, time_resolution=1e-10
    )
    assert [s.location[0] for s in new_stoplist] == [0, 2, 3, 4, 5]
    # If the capacity is 1, no pooling can occur
    (new_stoplist,) = optimize_stoplists(
        [old_stoplist], Manhattan2D(), [1], current_time=0, time_resolution=1e-10
    )
    assert [s.location[0] for s in new_stoplist] == [0, 2, 4, 3, 5]


def test_ortools_optimization_honours_capacity_constraints_with_onboard_requests():
    r1 = create_request_from_properties(req_id=1, orig=(2, 0), dest=(4, 0))
    r2 = create_request_from_properties(req_id=2, orig=(3, 0), dest=(5, 0))

    old_stoplist = create_stoplist_from_properties(
        initial_location=(0, 0),
        initial_load=1,
        actions=[(r1, do), (r2, pu), (r2, do)],
        space=Manhattan2D(),
    )
    # If the capacity is >1, pooling should occur
    (new_stoplist,) = optimize_stoplists(
        [old_stoplist], Manhattan2D(), [10], current_time=0, time_resolution=1e-10
    )
    assert [s.location[0] for s in new_stoplist] == [0, 3, 4, 5]

    # If the capacity is 1, no pooling can occur
    (new_stoplist,) = optimize_stoplists(
        [old_stoplist], Manhattan2D(), [1], current_time=0, time_resolution=1e-10
    )
    assert [s.location[0] for s in new_stoplist] == [0, 4, 3, 5]


def test_ortools_optimization_delivers_onboard_requests_with_correct_vehicle():
    r1 = create_request_from_properties(req_id=1, orig=(2, 100), dest=(4, 100))
    r2 = create_request_from_properties(req_id=2, orig=(3, -100), dest=(5, -100))
    r3 = create_request_from_properties(req_id=3, orig=(2, -100), dest=(4, -100))
    r4 = create_request_from_properties(req_id=4, orig=(3, 100), dest=(5, 100))

    old_stoplist_1 = create_stoplist_from_properties(
        initial_location=(0, 0),
        initial_load=1,
        actions=[(r1, do), (r2, pu), (r2, do)],
        space=Manhattan2D(),
    )
    old_stoplist_2 = create_stoplist_from_properties(
        initial_location=(0, 0),
        initial_load=1,
        actions=[(r3, do), (r4, pu), (r4, do)],
        space=Manhattan2D(),
    )

    new_stoplists = optimize_stoplists(
        [old_stoplist_1, old_stoplist_2],
        Manhattan2D(),
        [10, 10],
        current_time=0,
        time_resolution=1e-10,
    )
    # while testing, let's not check for CPE
    assert [[(s.request, s.action) for s in sl][1:] for sl in new_stoplists] == [
        [(r4, pu), (r1, do), (r4, do)],
        [(r2, pu), (r3, do), (r2, do)],
    ]


def test_ortools_optimization_pickups_before_dropoffs():
    r1 = create_request_from_properties(req_id=1, orig=(10, 0), dest=(4, 0))

    old_stoplist = create_stoplist_from_properties(
        initial_location=(0, 0),
        initial_load=0,
        actions=[(r1, pu), (r1, do)],
        space=Manhattan2D(),
    )
    (new_stoplist,) = optimize_stoplists(
        [old_stoplist], Manhattan2D(), [10], current_time=0, time_resolution=1e-10
    )
    assert [s.location[0] for s in new_stoplist] == [0, 10, 4]


def test_ortools_prouces_sane_solutions():
    """
    Runs the optimizer on a bunch of stops, half being in the y>0 place, half in the y<0 one, with
    2 vehicles.
    Checks that in the returned solution, one vehicle services all the upper stops and the other the
    lower ones.
    """
    requests = []
    for i in range(20):
        orig_x = np.random.uniform(-10, 10)
        dest_x = np.random.uniform(-10, 10)

        y = np.random.choice([-100, 100])

        req = create_request_from_properties(
            req_id=i, orig=(orig_x, y), dest=(dest_x, y)
        )
        requests.append(req)

    actions_1 = list(
        chain.from_iterable(
            [[(req, pu), (req, do)] for req in requests[: len(requests) // 2]]
        )
    )
    actions_2 = list(
        chain.from_iterable(
            [[(req, pu), (req, do)] for req in requests[len(requests) // 2 :]]
        )
    )

    old_stoplist_1 = create_stoplist_from_properties(
        initial_location=(0, 10), # initialize one vehicle in the upper half-plane
        initial_load=0,
        actions=actions_1,
        space=Manhattan2D(),
    )

    old_stoplist_2 = create_stoplist_from_properties(
        initial_location=(0, -10), # initialize one vehicle in the lower half-plane
        initial_load=0,
        actions=actions_2,
        space=Manhattan2D(),
    )

    new_stoplist_1, new_stoplist_2 = optimize_stoplists(
        [old_stoplist_1, old_stoplist_2],
        Manhattan2D(),
        [10, 10],
        current_time=0,
        time_resolution=1e-10,
    )

    assert all(s.location[1] > 0 for s in new_stoplist_1)
    assert all(s.location[1] < 0 for s in new_stoplist_2)
