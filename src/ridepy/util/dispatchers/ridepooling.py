from copy import deepcopy

import numpy as np

from ridepy.data_structures import (
    TransportationRequest,
    Stoplist,
    TransportSpace,
    DispatcherSolution,
    Stop,
    StopAction,
)
from ridepy.util.dispatchers.dispatcher_class import dispatcherclass

import logging

logger = logging.getLogger(__name__)


def insert_request_to_stoplist_drive_first(
    stoplist: Stoplist,
    request: TransportationRequest,
    pickup_idx: int,
    dropoff_idx: int,
    space: TransportSpace,
    n_passengers: int = 1,  # future proofing when we have requests with multiple passengers
) -> Stoplist:
    """
    Inserts a request into  a stoplist. The pickup (dropoff) is inserted after pickup_idx (dropoff_idx).
    The estimated arrival times at all the stops are updated assuming a drive-first strategy.
    """
    # We don't want to modify stoplist in place. Make a copy.
    new_stoplist = deepcopy(stoplist)

    # Handle the pickup
    stop_before_pickup = new_stoplist[pickup_idx]
    cpat_at_pu = stop_before_pickup.estimated_departure_time + space.t(
        stop_before_pickup.location, request.origin
    )
    pickup_stop = Stop(
        location=request.origin,
        action=StopAction.pickup,
        estimated_arrival_time=cpat_at_pu,
        time_window_min=request.pickup_timewindow_min,
        time_window_max=request.pickup_timewindow_max,
        request=request,
        occupancy_after_servicing=stop_before_pickup.occupancy_after_servicing
        + n_passengers,
    )
    # increase the occupancies of all the stops between pickup and dropoff
    # remember, the indices are as follows:
    # 0,1,...,pickup_idx,(pickup_not_yet_inserted),...,dropoff_idx,(dropoff_not_yet_inserted), ...
    for s in new_stoplist[pickup_idx + 1 : dropoff_idx + 1]:
        s.occupancy_after_servicing += n_passengers

    insert_stop_to_stoplist_drive_first(new_stoplist, pickup_stop, pickup_idx, space)

    # Handle the dropoff
    dropoff_idx += 1
    stop_before_dropoff = new_stoplist[dropoff_idx]
    cpat_at_do = stop_before_dropoff.estimated_departure_time + space.t(
        stop_before_dropoff.location, request.destination
    )
    dropoff_stop = Stop(
        location=request.destination,
        action=StopAction.dropoff,
        estimated_arrival_time=cpat_at_do,
        time_window_min=request.delivery_timewindow_min,
        time_window_max=request.delivery_timewindow_max,
        request=request,
        occupancy_after_servicing=stop_before_dropoff.occupancy_after_servicing
        - n_passengers,
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
    stop.estimated_arrival_time = cpat_of_inserted_stop(
        stop_before=stop_before_insertion,
        time_from_stop_before=space.t(stop_before_insertion.location, stop.location),
    )

    if idx < len(stoplist) - 1:
        # update CPATs of later stops
        delta_CPAT_next_stop = (
            stop.estimated_departure_time
            + space.t(stop.location, stoplist[idx + 1].location)
            - stoplist[idx + 1].estimated_arrival_time
        )

        for later_stop in stoplist[idx + 1 :]:
            old_departure = later_stop.estimated_departure_time
            later_stop.estimated_arrival_time += delta_CPAT_next_stop
            delta_CPAT_next_stop = later_stop.estimated_departure_time - old_departure

            if delta_CPAT_next_stop == 0:
                break

    stoplist.insert(idx + 1, stop)


def cpat_of_inserted_stop(
    stop_before: Stop, time_from_stop_before: float, delta_cpat: float = 0
) -> float:
    """
    Computes the cpat of the inserted stop, assuming drive first strategy.
    """
    return (
        max(
            stop_before.estimated_arrival_time + delta_cpat,
            stop_before.time_window_min,
        )
        + time_from_stop_before
    )


def time_to_stop_after_insertion(
    stoplist: Stoplist, location, index: int, space: TransportSpace
) -> float:
    """
    If a stop with `location` will have been inserted at `index`, computes the time
    from `location` to the stop after the insertion.

    Note: If the insertion is at the end of the stoplist, returns 0. Insertion at idx means after the idx'th stop.
    """

    return (
        space.t(location, stoplist[index + 1].location)
        if index < len(stoplist) - 1
        else 0
    )


def time_from_current_stop_to_next(
    stoplist: Stoplist, i: int, space: TransportSpace
) -> float:
    """
    Returns the time from the i'th stop in `stoplist` to the next stop.

    Note: If the insertion is at the end of the stoplist, returns 0
    """
    return (
        space.t(stoplist[i].location, stoplist[i + 1].location)
        if i < len(stoplist) - 1
        else 0
    )


def is_timewindow_violated_or_violation_worsened_due_to_insertion(
    stoplist: Stoplist, idx: int, est_arrival_first_stop_after_insertion: float
) -> bool:
    """
    If a stop is inserted at idx, so that the estimated_arrival_time at the stop after the inserted stop is
    est_arrival_first_stop_after_insertion, then checks for time window violations in the stoplist.

    Note: Assumes drive first strategy. Insertion at idx means after the idx'th stop.
    """

    # we are inserting at the end of the stoplist, nothing to check
    if idx > len(stoplist) - 2:
        return False

    # inserted stop incurs zero detour, and we don't have to wait
    if (
        est_arrival_first_stop_after_insertion
        <= stoplist[idx + 1].estimated_arrival_time
    ):
        return False

    delta_cpat = (
        est_arrival_first_stop_after_insertion
        - stoplist[idx + 1].estimated_arrival_time
    )

    for stop in stoplist[idx + 1 :]:
        old_leeway = stop.time_window_max - stop.estimated_arrival_time
        new_leeway = old_leeway - delta_cpat

        if new_leeway < 0 and new_leeway < old_leeway:
            return True
        elif stop.time_window_min >= stop.estimated_arrival_time + delta_cpat:
            # We have to wait or arrive just on time, thus no need to check next stops
            return False
        else:
            # Otherwise we are incurring additional delay. Compute the remaining delay:
            delta_cpat = (
                max(stop.time_window_min, stop.estimated_arrival_time + delta_cpat)
                - stop.estimated_departure_time
            )

    return False


@dispatcherclass
def BruteForceTotalTravelTimeMinimizingDispatcher(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
    seat_capacity: int,
) -> DispatcherSolution:
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
