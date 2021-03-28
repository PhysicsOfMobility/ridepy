import pytest
import signal

import numpy as np
import itertools as it

from thesimulator.data_structures import Stop, InternalRequest, StopAction
from thesimulator.data_structures_cython import (
    Stop as CyStop,
    InternalRequest as CyInternalRequest,
    StopAction as CyStopAction,
)
from thesimulator.vehicle_state import VehicleState
from thesimulator.vehicle_state_cython import VehicleState as CyVehicleState

from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)

from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.util.spaces import Euclidean2D
from thesimulator.util.spaces_cython import Euclidean2D as CyEuclidean2D


def test_slow_simple_fleet_state_initialization():
    test_space = [
        [Euclidean2D(), CyEuclidean2D()],
        [
            brute_force_total_traveltime_minimizing_dispatcher,
            cy_brute_force_total_traveltime_minimizing_dispatcher,
        ],
        [VehicleState, CyVehicleState],
    ]
    for i, (space, dispatcher, VehicleStateCls) in enumerate(it.product(*test_space)):

        testable = lambda: SlowSimpleFleetState(
            initial_locations={0: (0, 0), 1: (1, 1)},
            space=space,
            dispatcher=dispatcher,
            seat_capacities=8,
            vehicle_state_class=VehicleStateCls,
        )

        # if we have all python or all cython types (first and last combination), assert that it works
        if i == 0 or i == 2 ** len(test_space) - 1:
            testable()
        # in all other cases it should break
        else:
            with pytest.raises((TypeError, AssertionError)):
                testable()


# TODO: see https://github.com/PhysicsOfMobility/theSimulator/issues/120
@pytest.mark.skip("Currently, not everything is validated, this is why this segfaults")
def test_slow_simple_fleet_state_from_fleet():
    py_space = Euclidean2D()
    cy_space = CyEuclidean2D()
    initial_location = 0, 0

    make_fleet = lambda space, dispatcher, VehicleStateCls, StopCls, InternalRequestCls, StopActionCls: {
        vehicle_id: VehicleStateCls(
            vehicle_id=vehicle_id,
            space=space,
            dispatcher=dispatcher,
            seat_capacity=8,
            initial_stoplist=[
                StopCls(
                    location=initial_location,
                    request=InternalRequestCls(
                        request_id=-1,
                        creation_timestamp=0,
                        location=initial_location,
                    ),
                    action=StopActionCls.internal,
                    estimated_arrival_time=0,
                    occupancy_after_servicing=0,
                    time_window_min=0,
                    time_window_max=np.inf,
                )
            ],
        )
        for vehicle_id in range(50)
    }

    test_space = [
        [py_space, cy_space],
        [
            brute_force_total_traveltime_minimizing_dispatcher,
            cy_brute_force_total_traveltime_minimizing_dispatcher,
        ],
        [VehicleState, CyVehicleState],
        [Stop, CyStop],
        [InternalRequest, CyInternalRequest],
        [StopAction, CyStopAction],
    ]

    for i, (
        space,
        dispatcher,
        VehicleStateCls,
        StopCls,
        InternalRequestCls,
        StopActionCls,
    ) in enumerate(it.product(*test_space)):

        testable = lambda: SlowSimpleFleetState.from_fleet(
            fleet=make_fleet(
                space=space,
                dispatcher=dispatcher,
                VehicleStateCls=VehicleStateCls,
                StopCls=StopCls,
                InternalRequestCls=InternalRequestCls,
                StopActionCls=StopActionCls,
            ),
            space=space,
            dispatcher=dispatcher,
        )

        print(
            dict(
                space=space,
                dispatcher=dispatcher,
                VehicleStateCls=VehicleStateCls,
                StopCls=StopCls,
                InternalRequestCls=InternalRequestCls,
                StopActionCls=StopActionCls,
            )
        )
        # if we have all python or all cython types (first and last combination), assert that it works
        if i == 0 or i == 2 ** len(test_space) - 1:
            testable()
        # in all other cases it should break
        else:
            with pytest.raises((TypeError, AssertionError)):
                testable()
