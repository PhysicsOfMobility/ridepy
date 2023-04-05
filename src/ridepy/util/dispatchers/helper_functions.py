from typing import Optional
from copy import deepcopy

from ridepy.data_structures import (
    Stoplist,
    TransportationRequest,
    TransportSpace,
    Stop,
    StopAction,
)


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
