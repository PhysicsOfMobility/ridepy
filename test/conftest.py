import pytest

import numpy as np

from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
)

from thesimulator.data_structures_cython import (
    Stop as CyStop,
    InternalRequest as CyInternalRequest,
    StopAction as CyStopAction,
)


@pytest.fixture
def initial_stoplists(request):
    """
    Use like

    ```py
    @pytest.mark.n_buses(10)
    @pytest.mark.initial_location((0, 0))
    @pytest.mark.cython
    ```
    """
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
    if request.node.get_closest_marker("cython"):
        StopCls = CyStop
        InternalRequestCls = CyInternalRequest
        StopActionCls = CyStopAction

    else:
        StopCls = Stop
        InternalRequestCls = InternalRequest
        StopActionCls = StopAction

    return {
        vehicle_id: [
            StopCls(
                location=initial_location,
                request=InternalRequestCls(
                    request_id=-1, creation_timestamp=0, location=initial_location
                ),
                action=StopActionCls.internal,
                estimated_arrival_time=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ]
        for vehicle_id in range(n_buses)
    }
