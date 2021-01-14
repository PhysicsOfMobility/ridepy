from typing import Tuple

import numpy as np

from thesimulator.data_structures import (
    TransportationRequest,
    Stoplist,
    TransportSpace,
    Stop,
    StopAction,
    SingleVehicleSolution,
)
from thesimulator.util.dispatchers.helper_functions import (
    cpat_of_inserted_stop,
    distance_to_stop_after_insertion,
    distance_from_current_stop_to_next,
    is_timewindow_violated_or_violation_worsened_due_to_insertion,
    insert_request_to_stoplist_drive_first,
)


def taxicab_dispatcher_drive_first(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> Tuple[float, Stoplist, Tuple[float, float, float, float]]:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.

    Parameters
    ----------
    request
        request to be serviced
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist
    space
        transport space the vehicle is operating on

    Returns
    -------


    """
    CPAT_pu = (
        max(
            stoplist[-1].estimated_arrival_time,
            stoplist[-1].time_window_min
            if stoplist[-1].time_window_min is not None
            else 0,
        )
        + space.d(stoplist[-1].location, request.origin)
    )
    EAST_pu = request.pickup_timewindow_min
    CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request.origin, request.destination)
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
            time_window_min=EAST_pu,
            time_window_max=LAST_pu,
        ),
        Stop(
            location=request.destination,
            request=request,
            action=StopAction.dropoff,
            estimated_arrival_time=CPAT_do,
            time_window_min=EAST_do,
            time_window_max=LAST_do,
        ),
    ]
    return cost, stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)


def brute_force_distance_minimizing_dispatcher(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> SingleVehicleSolution:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by minimizing the total driving distance.

    Parameters
    ----------
    request
        request to be serviced
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist
    space
        transport space the vehicle is operating on

    Returns
    -------


    """
    min_cost = np.inf
    best_insertion = None
    for i, stop_before_pickup in enumerate(stoplist):
        distance_to_pickup = space.d(stop_before_pickup.location, request.origin)
        CPAT_pu = cpat_of_inserted_stop(stop_before_pickup, distance_to_pickup)
        # check for request's pickup timewindow violation
        if CPAT_pu > request.pickup_timewindow_max:
            continue
        EAST_pu = request.pickup_timewindow_min

        ######################
        # ADJACENT INSERTION #
        ######################
        CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request.origin, request.destination)
        # check for request's dropoff timewindow violation
        if CPAT_do > request.delivery_timewindow_max:
            continue

        # compute the cost function
        distance_to_dropoff = space.d(request.origin, request.destination)
        distance_from_dropoff = distance_to_stop_after_insertion(
            stoplist, request.destination, i, space
        )

        original_pickup_edge_length = distance_from_current_stop_to_next(
            stoplist, i, space
        )
        total_cost = (
            distance_to_pickup
            + distance_to_dropoff
            + distance_from_dropoff
            - original_pickup_edge_length
        )
        if total_cost < min_cost:
            # check for constraint violations at later points
            cpat_at_next_stop = (
                max(CPAT_do, request.delivery_timewindow_min) + distance_from_dropoff
            )
            if not is_timewindow_violated_or_violation_worsened_due_to_insertion(
                stoplist, i, cpat_at_next_stop
            ):
                best_insertion = i, i
                min_cost = total_cost

        ##########################
        # NON-ADJACENT INSERTION #
        ##########################
        distance_from_pickup = distance_to_stop_after_insertion(
            stoplist, request.origin, i, space
        )
        cpat_at_next_stop = (
            max(CPAT_pu, request.pickup_timewindow_min) + distance_from_pickup
        )
        if is_timewindow_violated_or_violation_worsened_due_to_insertion(
            stoplist, i, cpat_at_next_stop
        ):
            continue

        pickup_cost = (
            distance_to_pickup + distance_from_pickup - original_pickup_edge_length
        )

        for j, stop_before_dropoff in enumerate(stoplist[i + 1 :], start=i + 1):
            distance_to_dropoff = space.d(
                stop_before_dropoff.location, request.destination
            )
            CPAT_do = cpat_of_inserted_stop(
                stop_before_dropoff,
                distance_to_dropoff,
            )
            if CPAT_do > request.delivery_timewindow_max:
                continue

            distance_from_dropoff = distance_to_stop_after_insertion(
                stoplist, request.destination, j, space
            )
            original_dropoff_edge_length = distance_from_current_stop_to_next(
                stoplist, j, space
            )
            dropoff_cost = (
                distance_to_dropoff
                + distance_from_dropoff
                - original_dropoff_edge_length
            )
            total_cost = pickup_cost + dropoff_cost

            if total_cost >= min_cost:
                continue
            else:
                # cost has decreased. check for constraint violations at later stops
                cpat_at_next_stop = (
                    max(CPAT_do, request.delivery_timewindow_min)
                    + distance_from_dropoff
                )
                if not is_timewindow_violated_or_violation_worsened_due_to_insertion(
                    stoplist, j, cpat_at_next_stop
                ):
                    best_insertion = i, j
                    min_cost = total_cost


    if min_cost < np.inf:
        best_pickup_idx, best_dropoff_idx = best_insertion
        print(f"Best insertion: {best_insertion}")
        print(f"Min cost: {min_cost}")
        
        best_pickup_idx, best_dropoff_idx = best_insertion

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
