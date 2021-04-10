import numpy as np
import pytest

import itertools as it

from numpy import inf, isclose

from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    TransportationRequest,
)
from thesimulator.events import (
    RequestRejectionEvent,
    RequestAcceptanceEvent,
    PickupEvent,
    DeliveryEvent,
)
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.testing_utils import stoplist_from_properties
from thesimulator.extras.spaces import make_nx_grid
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean2D, Manhattan2D, Graph
from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.vehicle_state import VehicleState


from thesimulator import data_structures_cython as cyds
from thesimulator import data_structures as pyds

from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as py_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)

from thesimulator.util import spaces as pyspaces
from thesimulator.util.spaces_cython import spaces as cyspaces


def _setup_insertion_data_structures_r2loc(
    stoplist_properties, request_properties, space_type, kind
):
    """

    Parameters
    ----------
    stoplist_properties
    request_properties
    kind
        'cython' or 'python'

    Returns
    -------
    """
    if kind == "python":
        # set up the space
        if space_type == "Euclidean2D":
            space = pyspaces.Euclidean2D()
        elif space_type == "Manhattan2D":
            space = pyspaces.Manhattan2D()
        else:
            raise ValueError(
                f"'space_type' must be either 'Euclidean2D' or 'Manhattan2D'"
            )
        # set up the request
        request = pyds.TransportationRequest(**request_properties)
        # set up the stoplist
        stoplist = stoplist_from_properties(
            stoplist_properties, data_structure_module=pyds
        )
        return (
            space,
            request,
            stoplist,
            py_brute_force_total_traveltime_minimizing_dispatcher,
        )
    elif kind == "cython":
        # set up the space
        if space_type == "Euclidean2D":
            space = cyspaces.Euclidean2D()
        elif space_type == "Manhattan2D":
            space = cyspaces.Manhattan2D()
        else:
            raise ValueError(
                f"'space_type' must be either 'Euclidean2D' or 'Manhattan2D'"
            )
        # set up the request
        request = cyds.TransportationRequest(**request_properties)
        # set up the stoplist
        stoplist = cyds.Stoplist(
            stoplist_from_properties(stoplist_properties, data_structure_module=cyds),
            cyds.LocType.R2LOC,
        )
        return (
            space,
            request,
            stoplist,
            cy_brute_force_total_traveltime_minimizing_dispatcher,
        )
    else:
        raise ValueError(f"'kind' must be either 'python' or 'cython'")


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_append_to_empty_stoplist(kind):
    space = Euclidean2D()
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0, 1),
        destination=(0, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )

    # location, cpat, tw_min, tw_max,
    stoplist_properties = [[(0, 0), 0, 0, inf]]
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[-2].location == request.origin
    assert new_stoplist[-1].location == request.destination


def test_no_solution_found():
    """Test that if no solution exists, none is returned"""
    assert False


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_append_due_to_timewindow(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 3, 3]
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 2),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert np.allclose(new_stoplist[-2].location, request.origin)
    assert np.allclose(new_stoplist[-1].location, request.destination)

    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 0, 1, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_timewindow_violation_at_dropoff_checked(kind):
    """
    The least traveltime insertion is not chosen because the delay
    dueto dropoff+pickup together would violate a tw_max. Although separately, these
    delays do not.
    """
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 2), 2, 2, 4],
        [(0, 6), 6, 6, 7]
    ]
    # fmt: on
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0.5, 1.5),
        destination=(0.5, 4.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    for kind in ["python", "cython"]:
        (
            space,
            request,
            stoplist,
            brute_force_total_traveltime_minimizing_dispatcher,
        ) = _setup_insertion_data_structures_r2loc(
            stoplist_properties=stoplist_properties,
            request_properties=request_properties,
            space_type="Manhattan2D",
            kind=kind,
        )

        min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
            request, stoplist, space, seat_capacity=10
        )
        assert new_stoplist[-2].location == request.origin
        assert new_stoplist[-1].location == request.destination

    # but the above should not have occured if the tw_max at the last stop were higher:
    stoplist_properties = [[(0, 1), 1, 0, inf], [(0, 2), 2, 2, 4], [(0, 6), 6, 6, 9]]
    # fmt: on
    for kind in ["python", "cython"]:
        (
            space,
            request,
            stoplist,
            brute_force_total_traveltime_minimizing_dispatcher,
        ) = _setup_insertion_data_structures_r2loc(
            stoplist_properties=stoplist_properties,
            request_properties=request_properties,
            space_type="Manhattan2D",
            kind=kind,
        )

        min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
            request, stoplist, space, seat_capacity=10
        )
        assert new_stoplist[1].location == request.origin
        assert new_stoplist[3].location == request.destination


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_timewindow_violation_at_pickup_checked(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 2), 2, 2, 2.5],
        [(0, 6), 6, 6, 9]
    ]
    # fmt: on
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(0.5, 1.5),
        destination=(0.5, 4.5),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Manhattan2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[2].location == request.origin
    assert new_stoplist[3].location == request.destination

    # but the above should not have occured if the tw_max at the last stop were higher:
    stoplist_properties = [[(0, 1), 1, 0, inf], [(0, 2), 2, 2, 4], [(0, 6), 6, 6, 9]]
    # fmt: on
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_inserted_at_the_middle(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_inserted_separately(kind):
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
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )
    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=10
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[3].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 1, 0, 0, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_not_inserted_separately_dueto_capacity_constraint(kind):
    """
    Forces the pickup and dropoff to be inserted together solely because
    of seat_capacity=1
    """
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
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 2),
        destination=(eps, 4),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    # the best insertion would be [s0, +, -, s1, s2, s3]
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    for s, cap in zip(stoplist, [0, 1, 0, 1]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[1].location == request.origin
    assert new_stoplist[2].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [0, 1, 0, 1, 0, 1]

    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
    )

    # the best insertion would be [s0, s1, s2, s3, +, -,]
    for s, cap in zip(stoplist, [1, 1, 1, 0]):
        s.occupancy_after_servicing = cap

    min_cost, new_stoplist, *_ = brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity=1
    )
    assert new_stoplist[4].location == request.origin
    assert new_stoplist[5].location == request.destination
    assert [s.occupancy_after_servicing for s in new_stoplist] == [1, 1, 1, 0, 1, 0]


@pytest.mark.parametrize("kind", ["python", "cython"])
def test_stoplist_not_modified_inplace(kind):
    # fmt: off
    # location, cpat, tw_min, tw_max,
    stoplist_properties = [
        [(0, 1), 1, 0, inf],
        [(0, 3), 3, 0, 6],
    ]
    # fmt: on
    eps = 1e-4
    request_properties = dict(
        request_id=42,
        creation_timestamp=1,
        origin=(eps, 1),
        destination=(eps, 3),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )
    (
        space,
        request,
        stoplist,
        brute_force_total_traveltime_minimizing_dispatcher,
    ) = _setup_insertion_data_structures_r2loc(
        stoplist_properties=stoplist_properties,
        request_properties=request_properties,
        space_type="Euclidean2D",
        kind=kind,
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


if __name__ == "__main__":
    pytest.main(args=[__file__])
