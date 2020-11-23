from thesimulator.data_structures import (
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
) -> Stoplist:
    """
    Inserts a request into  a stoplist. The pickup (dropoff) is inserted after pickup_idx (dropoff_idx).
    The estimated arrival times at all the stops are updated assuming a drive-first strategy.
    """
    # We don't want to modify stoplist in place. Make a copy.
    new_stoplist = stoplist[:]

    # Handle the pickup
    stop_before_pickup = new_stoplist[pickup_idx]
    cpat_at_pu = stop_before_pickup.estimated_departure_time + space.d(
        stop_before_pickup.location, request.origin
    )
    pickup_stop = Stop(
        location=request.origin,
        action=StopAction.pickup,
        estimated_arrival_time=cpat_at_pu,
        time_window_min=request.pickup_timewindow_min,
        time_window_max=request.pickup_timewindow_max,
        request=request,
    )

    insert_stop_to_stoplist_drive_first(new_stoplist, pickup_stop, pickup_idx, space)

    # Handle the dropoff
    dropoff_idx += 1
    stop_before_dropoff = new_stoplist[dropoff_idx]
    cpat_at_do = stop_before_dropoff.estimated_departure_time + space.d(
        stop_before_dropoff.location, request.destination
    )
    dropoff_stop = Stop(
        location=request.destination,
        action=StopAction.dropoff,
        estimated_arrival_time=cpat_at_do,
        time_window_min=request.delivery_timewindow_min,
        time_window_max=request.delivery_timewindow_max,
        request=request,
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
        stop_before=stop_before_insertion,
        distance_from_stop_before=distance_to_new_stop,
    )
    stop.estimated_arrival_time = cpat_new_stop

    if idx < len(stoplist) - 1:
        # update CPATs of later stops
        delta_CPAT_next_stop = (
            stop.estimated_departure_time
            + space.d(stop.location, stoplist[idx + 1].location)
            - stoplist[idx + 1].estimated_arrival_time
        )

        for later_stop in stoplist[idx + 1 :]:
            old_departure = later_stop.estimated_departure_time
            later_stop.estimated_arrival_time += delta_CPAT_next_stop
            new_departure = later_stop.estimated_departure_time

            delta_CPAT_next_stop = new_departure - old_departure

            if delta_CPAT_next_stop == 0:
                break

    stoplist.insert(idx + 1, stop)


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
        space.d(location, stoplist[index + 1].location)
        if index < len(stoplist) - 1
        else 0
    )


def distance_from_current_stop_to_next(
    stoplist: Stoplist, i: int, space: TransportSpace
) -> float:
    return (
        space.d(stoplist[i].location, stoplist[i + 1].location)
        if i < len(stoplist) - 1
        else 0
    )


def is_timewindow_violated_due_to_insertion(
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
    if idx > len(stoplist) - 2:
        return False

    delta_cpat = (
        est_arrival_first_stop_after_insertion
        - stoplist[idx + 1].estimated_arrival_time
    )

    if delta_cpat == 0:
        return False

    for stop in stoplist[idx + 1 :]:
        old_leeway = stop.time_window_max - stop.estimated_arrival_time
        new_leeway = old_leeway - delta_cpat

        if new_leeway < 0 <= old_leeway:
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
