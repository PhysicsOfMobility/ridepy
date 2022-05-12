from typing import Tuple

import numpy as np

from ridepy.data_structures import (
    TransportationRequest,
    Stoplist,
    TransportSpace,
    Stop,
    StopAction,
    SingleVehicleSolution,
)
from ridepy.util.dispatchers.helper_functions import (
    cpat_of_inserted_stop,
    time_to_stop_after_insertion,
    time_from_current_stop_to_next,
    is_timewindow_violated_or_violation_worsened_due_to_insertion,
    insert_request_to_stoplist_drive_first,
)

import logging

logger = logging.getLogger(__name__)


"""
This module contains pure python dispatchers. These are callable from python and should be used for testing purposes
and small scale simulations where computing performance is not of primary concern. 
For larger scale simulations, use Cython dispatchers. Note that these can not be called from python directly, but 
through the `.vehicle_state_cython.VehicleState` class.
"""


def dispatcherclass(f):
    """
    Use this decorator to create a callable Dispatcher class from a pure function. Use this to conveniently turn
    a pure function mapping a stoplist and a request to an updated stoplist into a dispatcher usable with ridepy.

    In principle, using dispatcher objects allow for easy configuration of dispatcher behavior. After instantiation
    of an object ``dispatcher`` the original dispatcher function is available
    as ``dispatcher(...)``. Currently on initiating a dispatcher object, ``loc_type`` can
    be supplied for interface compatibility with Cython dispatchers.

    Use like

    .. code-block:: python

        @dispatcherclass
        def MyFancyDispatcher(
            request: TransportationRequest,
            stoplist: Stoplist,
            space: TransportSpace,
            seat_capacity: int,
        ) -> SingleVehicleSolution:
            ...

    """

    class DispatcherClass:
        __name__ = f.__name__
        __qualname__ = f.__qualname__
        __doc__ = f.__doc__

        def __init__(self, loc_type=None):
            self.loc_type = loc_type

        def __call__(self, *args, **kwargs):
            return f(*args, **kwargs)

    return DispatcherClass


@dispatcherclass
def TaxicabDispatcherDriveFirst(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
    seat_capacity: int,
) -> SingleVehicleSolution:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.

    This pure function is turned into a callable class by the decorator `.dispatcherclass` whose __init__ accepts
    optional arguments, see the docstring of `.dispatcherclass` for details.

    See the dispatcher interface in :ref:`desc_dispatcher` for details.

    Parameters
    ----------
    request
        request to be serviced.
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist.
    space
        transport space the vehicle is operating on.
    seat_capacity
        the maximum number of `.TransportationRequest` s that can be in a vehicle at the same time.


    Returns
    -------
        The best solution as defined in `.SingleVehicleSolution`.
    """
    # TODO: When we have multi-passenger requests, this dispatcher needs to be changed and
    # include capacity constraints. Currently, taxi := single seat
    assert seat_capacity == 1
    CPAT_pu = max(
        stoplist[-1].estimated_arrival_time,
        stoplist[-1].time_window_min if stoplist[-1].time_window_min is not None else 0,
    ) + space.t(stoplist[-1].location, request.origin)
    EAST_pu = request.pickup_timewindow_min
    CPAT_do = max(EAST_pu, CPAT_pu) + space.t(request.origin, request.destination)
    LAST_pu = (
        CPAT_pu + request.delivery_timewindow_max
        if request.delivery_timewindow_max is not None
        else np.inf
    )
    EAST_do = EAST_pu
    LAST_do = np.inf

    cost = CPAT_do
    stoplist = stoplist + [
        Stop(
            location=request.origin,
            request=request,
            action=StopAction.pickup,
            estimated_arrival_time=CPAT_pu,
            occupancy_after_servicing=stoplist[-1].occupancy_after_servicing + 1,
            time_window_min=EAST_pu,
            time_window_max=LAST_pu,
        ),
        Stop(
            location=request.destination,
            request=request,
            action=StopAction.dropoff,
            estimated_arrival_time=CPAT_do,
            occupancy_after_servicing=0,
            time_window_min=EAST_do,
            time_window_max=LAST_do,
        ),
    ]
    return cost, stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)


@dispatcherclass
def BruteForceTotalTravelTimeMinimizingDispatcher(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
    seat_capacity: int,
) -> SingleVehicleSolution:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by minimizing the total driving time.

    This pure function is turned into a callable class by the decorator `.dispatcherclass` whose __init__ accepts
    optional arguments, see the docstring of `.dispatcherclass` for details.

    See the dispatcher interface in :ref:`desc_dispatcher` for details.


    Parameters
    ----------
    request
        request to be serviced.
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist.
    space
        transport space the vehicle is operating on.
    seat_capacity
            the maximum number of `.TransportationRequest` s that can be in a vehicle at the same time.

    Returns
    -------
        The best solution as defined in `.SingleVehicleSolution`.
    """
    min_cost = np.inf
    best_insertion = None
    for i, stop_before_pickup in enumerate(stoplist):
        if stop_before_pickup.occupancy_after_servicing == seat_capacity:
            # inserting here will violate capacity constraint
            continue
        time_to_pickup = space.t(stop_before_pickup.location, request.origin)
        CPAT_pu = cpat_of_inserted_stop(stop_before_pickup, time_to_pickup)
        # check for request's pickup timewindow violation
        if CPAT_pu > request.pickup_timewindow_max:
            continue
        EAST_pu = request.pickup_timewindow_min

        ######################
        # ADJACENT INSERTION #
        ######################
        CPAT_do = max(EAST_pu, CPAT_pu) + space.t(request.origin, request.destination)
        # check for request's dropoff timewindow violation
        if CPAT_do > request.delivery_timewindow_max:
            continue

        # compute the cost function
        time_to_dropoff = space.t(request.origin, request.destination)
        time_from_dropoff = time_to_stop_after_insertion(
            stoplist, request.destination, i, space
        )

        original_pickup_edge_length = time_from_current_stop_to_next(stoplist, i, space)
        total_cost = (
            time_to_pickup
            + time_to_dropoff
            + time_from_dropoff
            - original_pickup_edge_length
        )
        if total_cost < min_cost:
            # check for constraint violations at later points
            cpat_at_next_stop = (
                max(CPAT_do, request.delivery_timewindow_min) + time_from_dropoff
            )
            if not is_timewindow_violated_or_violation_worsened_due_to_insertion(
                stoplist, i, cpat_at_next_stop
            ):
                best_insertion = i, i
                min_cost = total_cost

        ##########################
        # NON-ADJACENT INSERTION #
        ##########################
        time_from_pickup = time_to_stop_after_insertion(
            stoplist, request.origin, i, space
        )
        cpat_at_next_stop = (
            max(CPAT_pu, request.pickup_timewindow_min) + time_from_pickup
        )
        if is_timewindow_violated_or_violation_worsened_due_to_insertion(
            stoplist, i, cpat_at_next_stop
        ):
            continue

        pickup_cost = time_to_pickup + time_from_pickup - original_pickup_edge_length

        if i < len(stoplist) - 1:
            delta_cpat = cpat_at_next_stop - stoplist[i + 1].estimated_arrival_time

        for j, stop_before_dropoff in enumerate(stoplist[i + 1 :], start=i + 1):
            # Need to check for seat capacity constraints. Note the loop: the constraint was not violated after
            # servicing the previous stop (otherwise we wouldn't've reached this line). Need to check that the
            # constraint is not violated due to the action at this stop (stop_before_dropoff)
            if stop_before_dropoff.occupancy_after_servicing == seat_capacity:
                # Capacity is violated. We need to break off this loop because no insertion either here or at a later
                # stop is permitted
                break
            time_to_dropoff = space.t(stop_before_dropoff.location, request.destination)
            CPAT_do = cpat_of_inserted_stop(
                stop_before_dropoff,
                time_to_dropoff,
                delta_cpat=delta_cpat,
            )
            # check for request's dropoff timewindow violation
            if CPAT_do > request.delivery_timewindow_max:
                break

            time_from_dropoff = time_to_stop_after_insertion(
                stoplist, request.destination, j, space
            )
            original_dropoff_edge_length = time_from_current_stop_to_next(
                stoplist, j, space
            )
            dropoff_cost = (
                time_to_dropoff + time_from_dropoff - original_dropoff_edge_length
            )
            total_cost = pickup_cost + dropoff_cost

            if total_cost < min_cost:
                # cost has decreased. check for constraint violations at later stops
                cpat_at_next_stop = (
                    max(CPAT_do, request.delivery_timewindow_min) + time_from_dropoff
                )
                if not is_timewindow_violated_or_violation_worsened_due_to_insertion(
                    stoplist, j, cpat_at_next_stop
                ):
                    best_insertion = i, j
                    min_cost = total_cost

            # we will try inserting the dropoff at a later stop
            # the delta_cpat is important to compute correctly for the next stop, it may have changed if
            # we had any slack time at this one
            new_departure_time = max(
                stop_before_dropoff.estimated_arrival_time + delta_cpat,
                stop_before_dropoff.time_window_min,
            )
            delta_cpat = (
                new_departure_time - stop_before_dropoff.estimated_departure_time
            )

    if min_cost < np.inf:
        best_pickup_idx, best_dropoff_idx = best_insertion
        # if request.request_id == 2:
        # print(f"Py DEBUG: best insertion @ {best_insertion}")
        # print(stoplist[0].estimated_arrival_time)
        # print(stoplist[0].location)
        # print(request.creation_timestamp)
        # print()

        logger.info(f"Best insertion: {best_insertion}")
        logger.info(f"Min cost: {min_cost}")

        new_stoplist = insert_request_to_stoplist_drive_first(
            stoplist=stoplist,
            request=request,
            pickup_idx=best_pickup_idx,
            dropoff_idx=best_dropoff_idx,
            space=space,
        )
        EAST_pu, LAST_pu = (
            new_stoplist[best_pickup_idx + 1].time_window_min,
            new_stoplist[best_pickup_idx + 1].time_window_max,
        )
        EAST_do, LAST_do = (
            new_stoplist[best_dropoff_idx + 2].time_window_min,
            new_stoplist[best_dropoff_idx + 2].time_window_max,
        )
        return min_cost, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
    else:
        return min_cost, None, (np.nan, np.nan, np.nan, np.nan)
