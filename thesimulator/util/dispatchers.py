from typing import Tuple

import numpy as np

from thesimulator.data_structures import (
    ID,
    TransportationRequest,
    Stoplist,
    Stop,
    StopAction,
    TransportSpace,
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


def insert_request_to_stoplist_drive_first(
    stoplist: Stoplist,
    request: TransportationRequest,
    pickup_idx: int,
    dropoff_idx: int,
    space: TransportSpace,
) -> Stoplist:
    """
    Inserts a request into  a stoplist. The pickup(dropoff) is inserted after pickup(dropoff)_idx.
    The estimated arrival times at all the stops are updated assuming a drive-first strategy.
    """
    # We don't want to modify stoplist in place. Make a copy.
    new_stoplist = stoplist[:]
    # Handle the pickup
    stop_before_pickup = stoplist[pickup_idx]
    cpat_at_pu = stop_before_pickup.estimated_departure_time + space.d(
        stop_before_pickup.location, request.origin
    )
    pickup_stop = Stop(
        location=request.origin,
        action=StopAction.pickup,
        estimated_arrival_time=cpat_at_pu,
        time_window_min=request.pickup_timewindow_min,
        time_window_max=request.pickup_timewindow_max,
    )

    insert_stop_to_stoplist_drive_first(new_stoplist, pickup_stop, pickup_idx, space)
    # Handle the dropoff
    dropoff_idx += 1
    stop_before_dropoff = stoplist[dropoff_idx]
    cpat_at_do = stop_before_dropoff.estimated_departure_time + space.d(
        stop_before_dropoff.location, request.destination
    )
    dropoff_stop = Stop(
        location=request.origin,
        action=StopAction.dropoff,
        estimated_arrival_time=cpat_at_do,
        time_window_min=request.delivery_timewindow_min,
        time_window_max=request.delivery_timewindow_max,
    )
    insert_stop_to_stoplist_drive_first(new_stoplist, dropoff_stop, dropoff_idx, space)
    return new_stoplist


def insert_stop_to_stoplist_drive_first(
    stoplist: Stoplist,
    stop: Stop,
    idx: int,
    space: TransportSpace,
) -> None:
    """
    Note: Modifies stoplist in-place. The passed stop has estimated_arrival_time set to None
    Args:
        stoplist:
        stop:
        idx:
        space:

    Returns:
    """
    stop_before_insertion = stoplist[idx]
    distance_to_new_stop = space.d(stop_before_insertion.location, stop.location)
    cpat_new_stop = cpat_of_inserted_stop(
        stop_before_insertion, distance_from_stop_before
    )
    stop.estimated_arrival_time = cpat_new_stop
    if idx < len(stoplist):
        # update cpats of later stops
        departure_previous_stop = stop.estimated_departure_time
        cpat_next_stop = departure_previous_stop + space.d(
            stop.location, stoplist[idx + 1].location
        )
        delta_cpat_next_stop = cpat_next_stop - stoplist[idx + 1].estimated_arrival_time
        for later_stop in stoplist[idx + 1 :]:
            old_departure = later_stop.estimated_departure_time
            later_stop.estimated_arrival_time += delta_cpat_next_stop
            new_departure = later_stop.estimated_departure_time

            delta_cpat_next_stop = new_departure - old_departure
            if delta_cpat_next_stop == 0:
                break


def cpat_of_inserted_stop(stop_before: Stop, distance_from_stop_before: float) -> float:
    """
    Note: Assumes drive first strategy.
    Args:
        stop_before:
        distance_from_stop_before:

    Returns:

    """
    return stop_before.estimated_departure_time + distance_from_stop_before


def distance_to_stop_after_insertion(
    stoplist: Stoplist, location, index: int, space: TransportSpace
) -> float:
    return (
        space.d(location, stoplist[index + 1].location) if index < len(stoplist) else 0
    )


def distance_from_current_stop_to_next(
    stoplist: Stoplist, i: int, space: TransportSpace
) -> float:
    return (
        space.d(stoplist[i].location, stoplist[i + 1].location)
        if i < len(stoplist)
        else 0
    )


def is_timewindow_violated_dueto_insertion(
    stoplist: Stoplist, idx: int, est_arrival_first_stop_after_insertion: float
) -> bool:
    """
    Assumes drive first strategy.
    Args:
        stoplist:
        idx:
        est_arrival_first_stop_after_insertion:

    Returns:

    """
    if not idx < len(stoplist):
        return False
    delta_cpat = (
        est_arrival_first_stop_after_insertion
        - stoplist[idx + 1].estimated_arrival_time
    )
    for stop in stoplist[idx + 1 :]:
        old_leeway = stop.time_window_max - stop.estimated_arrival_time
        new_leeway = old_leeway - delta_cpat

        if new_leeway < 0 < old_leeway:
            return True
        else:
            old_departure = max(stop.time_window_min, stop.estimated_arrival_time)
            new_departure = max(
                stop.time_window_min, stop.estimated_arrival_time + delta_cpat
            )
            delta_cpat = new_departure - old_departure
            if delta_cpat == 0:
                # no need to check next stops
                return False
    else:
        return False


def brute_force_distance_minimizing_dispatcher(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> Tuple[float, Stoplist, Tuple[float, float, float, float]]:
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

        # dropoff immediately
        CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request.origin, request.destination)
        EAST_do = request.delivery_timewindow_min
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
            if not is_timewindow_violated_dueto_insertion(
                stoplist, i, cpat_at_next_stop
            ):
                best_insertion = i, i
                min_cost = total_cost
        # dropoff not immediately after pickup
        distance_from_pickup = space.d(request.origin, stoplist[i + 1].location)
        cpat_at_next_stop = (
            max(CPAT_pu, request.pickup_timewindow_min) + distance_from_pickup
        )
        if is_timewindow_violated_dueto_insertion(stoplist, i, cpat_at_next_stop):
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
                +distance_to_dropoff,
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
            if total_cost > min_cost:
                continue
            else:
                # cost has decreased. check for constraint violations at later stops
                cpat_at_next_stop = (
                    max(CPAT_do, request.delivery_timewindow_min)
                    + distance_from_dropoff
                )
                if not is_timewindow_violated_dueto_insertion(
                    stoplist, j, cpat_at_next_stop
                ):
                    best_insertion = i, j
                    min_cost = total_cost
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
