import pytest

import numpy as np

from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
)


@pytest.fixture
def initial_stoplists(request):
    n_buses = (
        request.node.get_closest_marker("n_buses").args[0]
        if request.node.get_closest_marker("n_buses") is not None
        else 10
    )
    initial_location = (
        request.node.get_closest_marker("initial_location").args[0]
        if request.node.get_closest_marker("initial_location") is not None
        else 0
    )
    return {
        vehicle_id: [
            Stop(
                location=initial_location,
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=initial_location
                ),
                action=StopAction.internal,
                estimated_arrival_time=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ]
        for vehicle_id in range(n_buses)
    }
