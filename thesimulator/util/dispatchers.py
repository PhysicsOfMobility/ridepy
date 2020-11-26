from typing import Tuple, Any, Union

import numpy as np
import functools as ft

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


def calculate_detour(
    last_stop: Stop, next_stop: Stop, location: Any, space: TransportSpace
) -> float:
    """
    Return detour for inserting a new location
    Parameters
    ----------
    last_stop
        stop before the location to insert
    next_stop
        stop after the location to insert
    location
        location of the stop to be inserted
    space
        transport space used for distance calculation

    Returns
    -------
    detour
        The excess in distance introduced by inserting the new
        location between the two existing stops.
    """
    return (
        space.d(last_stop.location, location)
        + space.d(location, next_stop.location)
        - space.d(last_stop.location, next_stop.location)
    )


def check_timeframe_constraints(
    *,
    request: TransportationRequest,
    pickup_idx: int,
    dropoff_rel_idx: Union[None, int],
    stoplist: Stoplist,
    space: TransportSpace,
):
    estimated_pickup_time = stoplist[pickup_idx].estimated_arrival_time + space.d(
        stoplist[pickup_idx].location, request.origin
    )
    satisfied = True
    if request.pickup_timewindow_min is not None:
        satisfied *= request.pickup_timewindow_min <= estimated_pickup_time
    if request.pickup_timewindow_max is not None:
        satisfied *= request.pickup_timewindow_max >= estimated_pickup_time
    if dropoff_rel_idx is not None:
        if dropoff_rel_idx == 0:
            estimated_dropoff_time = estimated_pickup_time + space.d(
                request.origin, request.destination
            )
        else:
            estimated_dropoff_time = (
                stoplist[dropoff_rel_idx].estimated_arrival_time
                + space.d(stoplist[pickup_idx].location, request.origin)
                + space.d(request.origin, stoplist[pickup_idx + 1].location)
                - space.d(
                    stoplist[pickup_idx].location,
                    stoplist[pickup_idx + 1].location,
                )
                + space.d(
                    stoplist[pickup_idx + dropoff_rel_idx].location,
                    request.destination,
                )
            )
        if request.delivery_timewindow_min is not None:
            satisfied *= request.delivery_timewindow_min <= estimated_dropoff_time
        if request.delivery_timewindow_max is not None:
            satisfied *= request.delivery_timewindow_max >= estimated_dropoff_time
    return satisfied


def ridepooling_dispatcher_min_route_length(
    request: TransportationRequest,
    stoplist: Stoplist,
    space: TransportSpace,
) -> Tuple[float, Stoplist, Tuple[float, float, float, float]]:
    """
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by simply appending the necessary stops to the existing stoplist.
    The objective function minimized is the finishing time of the scheduled route.

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
    cost
    new_stoplist
    (
        EAST_pu,
        LAST_pu,
        EAST_do,
        LAST_do
    )
    """

    exit_stops = stoplist[:-1]
    reentry_stops = stoplist[1:]

    pickup_detours, dropoff_detours = (
        list(
            map(
                ft.partial(calculate_detour, location=location, space=space),
                exit_stops,
                reentry_stops,
            )
        )
        + [space.d(stoplist[-1].location, request.origin)]
        for location in (request.origin, request.destination)
    )

    objective = np.inf

    for pickup_idx, pickup_detour in enumerate(pickup_detours[:-1]):
        # iterate over distances incurred at pickup
        if pickup_detour <= objective:
            # pickup is only viable if pickup_detour does not already exceed the objective
            for dropoff_rel_idx, dropoff_detour in enumerate(
                dropoff_detours[pickup_idx:]
            ):
                # now iterate over all possible dropoffs
                if (
                    pickup_detour + dropoff_detour <= objective
                    and check_timeframe_constraints(
                        request=request,
                        pickup_idx=pickup_idx,
                        dropoff_rel_idx=dropoff_rel_idx,
                        stoplist=stoplist,
                        space=space,
                    )
                ):
                    if dropoff_rel_idx == 0:
                        # adjacent insertion
                        chained_insert_objective = (
                            pickup_detour
                            + space.d(request.origin, request.destination)
                            + space.d(
                                request.destination,
                                reentry_stops[pickup_idx].location,
                            )
                            - space.d(
                                request.origin, reentry_stops[pickup_idx].location
                            )
                        )
                        if chained_insert_objective < objective:
                            objective = chained_insert_objective
                            best_pickup_idx = pickup_idx
                            best_dropoff_rel_idx = dropoff_rel_idx
                    else:
                        # non-adjacent insertion
                        separate_insert_objective = pickup_detour + dropoff_detour
                        if separate_insert_objective < objective:
                            objective = separate_insert_objective
                            best_pickup_idx = pickup_idx
                            best_dropoff_rel_idx = dropoff_rel_idx
    else:
        pickup_idx = len(stoplist) - 1
        append_both_objective = pickup_detours[pickup_idx] + space.d(
            request.origin, request.destination
        )
        if append_both_objective < objective and check_timeframe_constraints(
            request=request,
            pickup_idx=pickup_idx,
            dropoff_rel_idx=None,
            stoplist=stoplist,
            space=space,
        ):
            objective = append_both_objective
            best_pickup_idx = pickup_idx
            best_dropoff_rel_idx = 0

    CPAT_pu = stoplist[best_pickup_idx].estimated_arrival_time + space.d(
        stoplist[best_pickup_idx].location, request.origin
    )
    EAST_pu = 0
    LAST_pu = np.inf

    CPAT_do = (
        stoplist[best_pickup_idx + best_dropoff_rel_idx].estimated_arrival_time
        + space.d(request.origin, request.destination)
        if best_dropoff_rel_idx != 0
        else stoplist[best_pickup_idx].estimated_arrival_time
        + space.d(stoplist[best_pickup_idx].location, request.origin)
        + space.d(request.origin, request.destination)
    )
    EAST_do = EAST_pu
    LAST_do = np.inf

    pickup_stop = Stop(
        location=request.origin,
        request=request,
        action=StopAction.pickup,
        estimated_arrival_time=CPAT_pu,
        time_window_min=EAST_pu,
        time_window_max=LAST_pu,
    )

    dropoff_stop = Stop(
        location=request.destination,
        request=request,
        action=StopAction.dropoff,
        estimated_arrival_time=CPAT_do,
        time_window_min=EAST_do,
        time_window_max=LAST_do,
    )

    new_stoplist = []
    if best_pickup_idx != len(stoplist) - 1 and best_dropoff_rel_idx != 0:
        pre_pickup_stoplist = stoplist[: best_pickup_idx + 1]
        post_pickup_stoplist = stoplist[
            best_pickup_idx + 1 : best_pickup_idx + best_dropoff_rel_idx + 1
        ]
        for i, x in enumerate(post_pickup_stoplist):
            post_pickup_stoplist[i].estimated_arrival_time += pickup_detours[
                best_pickup_idx
            ]
        post_dropoff_stoplist = stoplist[best_pickup_idx + best_dropoff_rel_idx + 1 :]
        for i, x in enumerate(post_dropoff_stoplist):
            post_dropoff_stoplist[i].estimated_arrival_time += (
                pickup_detours[best_pickup_idx]
                + dropoff_detours[best_pickup_idx + best_dropoff_rel_idx]
            )
        new_stoplist = (
            pre_pickup_stoplist
            + [pickup_stop]
            + post_pickup_stoplist
            + [dropoff_stop]
            + post_dropoff_stoplist
        )
    elif best_pickup_idx == len(stoplist) - 1:
        new_stoplist = stoplist + [pickup_stop] + [dropoff_stop]
    elif best_dropoff_rel_idx == 0:
        pre_pickup_stoplist = stoplist[: best_pickup_idx + 1]
        detour = (
            space.d(stoplist[best_pickup_idx].location, request.origin)
            + space.d(request.origin, request.destination)
            + space.d(request.destination, stoplist[best_pickup_idx + 1].location)
            - space.d(
                stoplist[best_pickup_idx].location,
                stoplist[best_pickup_idx + 1].location,
            )
        )
        post_pickup_stoplist = stoplist[best_pickup_idx + 1 :]
        for i, x in enumerate(post_pickup_stoplist):
            post_pickup_stoplist[i].estimated_arrival_time += detour
        new_stoplist = (
            pre_pickup_stoplist + [pickup_stop, dropoff_stop] + post_pickup_stoplist
        )

    return (
        objective + stoplist[-1].estimated_arrival_time,
        new_stoplist,
        (EAST_pu, LAST_pu, EAST_do, LAST_do),
    )
