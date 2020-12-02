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


def ridesharing_dispatcher_min_route_length(
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

    """
    objective = np.infty
    scheduled_end_epoch = stoplist[-1].estimated_arrival_time

    best_pickup_index = None
    best_dropoff_rel_index = None

    exit_stops = stoplist[:-1]
    reentry_stops = stoplist[1:]

    def _calculate_detour(exit_stop: Stop, entry_stop: Stop, stop):
        return space.d(exit_stop.location, stop) \
               + space.d(stop, entry_stop.location) - space.d(exit_stop.location, entry_stop.location)

    def _check_timeframe_constraints(request: TransportationRequest,
                                     pickup_index: int,
                                     dropoff_rel_index: int,
                                     stoplist: Stoplist):
        estimated_pickup_time = stoplist[pickup_index].estimated_arrival_time+space.d(stoplist[pickup_index].location, request.origin)
        satisfied = True
        if request.pickup_timewindow_min is not None:
            satisfied *= (request.pickup_timewindow_min<=estimated_pickup_time)
        if request.pickup_timewindow_max is not None:
            satisfied *= (request.pickup_timewindow_max>=estimated_pickup_time)
        if dropoff_rel_index is not None:
            estimated_dropoff_time = None
            if dropoff_rel_index==0:
                estimated_dropoff_time = estimated_pickup_time + space.d(request.origin,request.destination)
            else:
                estimated_dropoff_time = stoplist[dropoff_rel_index].estimated_arrival_time \
                                       + space.d(stoplist[pickup_index].location, request.origin) \
                                       + space.d(request.origin,stoplist[pickup_index+1].location) \
                                       - space.d(stoplist[pickup_index].location,stoplist[pickup_index+1].location) \
                                       + space.d(stoplist[pickup_index+dropoff_rel_index].location,request.destination)

            if request.delivery_timewindow_min is not None:
                satisfied *= (request.delivery_timewindow_min<=estimated_dropoff_time)
            if request.delivery_timewindow_max is not None:
                satisfied *= (request.delivery_timewindow_max>=estimated_dropoff_time)
        return satisfied

    pickup_detours = list(map(_calculate_detour, exit_stops, reentry_stops, (len(stoplist) - 1) * request.origin)) + [
        space.d(stoplist[-1].location, request.origin)]

    dropoff_detours = list(
        map(_calculate_detour, exit_stops, reentry_stops, (len(stoplist) - 1) * request.destination)) + [
                          space.d(stoplist[-1].location, request.destination)]

    for pickup_index, pickup_detour in enumerate(pickup_detours):
        if pickup_detour + scheduled_end_epoch > objective:
            continue
        elif pickup_index == len(stoplist) - 1:
            append_both_objective = scheduled_end_epoch \
                                    + pickup_detour \
                                    + space.d(request.origin, request.destination)
            if append_both_objective < objective and _check_timeframe_constraints(request,pickup_index,None,stoplist):
                objective = append_both_objective
                best_pickup_index = pickup_index
                best_dropoff_rel_index = 0
        else:
            for dropoff_rel_index, dropoff_detour in enumerate(dropoff_detours[pickup_index:]):
                if pickup_detour + dropoff_detour + scheduled_end_epoch > objective or not _check_timeframe_constraints(request,pickup_index,dropoff_rel_index,stoplist):
                    continue
                else:
                    if dropoff_rel_index == 0:
                        chained_insert_objective = scheduled_end_epoch \
                                                   + pickup_detour \
                                                   + space.d(request.origin, request.destination) \
                                                   + space.d(request.destination, reentry_stops[pickup_index].location)\
                                                   - space.d(request.origin, reentry_stops[pickup_index].location)
                        if chained_insert_objective < objective:
                            objective = chained_insert_objective
                            best_pickup_index = pickup_index
                            best_dropoff_rel_index = dropoff_rel_index
                    else:
                        separate_insert_objective = scheduled_end_epoch + pickup_detour + dropoff_detour
                        if separate_insert_objective < objective:
                            objective = separate_insert_objective
                            best_pickup_index = pickup_index
                            best_dropoff_rel_index = dropoff_rel_index

    CPAT_pu = stoplist[best_pickup_index].estimated_arrival_time \
        + space.d(stoplist[best_pickup_index].location, request.origin)

    EAST_pu = 0
    CPAT_do = (
        stoplist[best_pickup_index + best_dropoff_rel_index].estimated_arrival_time
        + space.d(request.origin, request.destination)
        if best_dropoff_rel_index != 0
        else
        stoplist[best_pickup_index].estimated_arrival_time
        + space.d(stoplist[best_pickup_index].location, request.origin)
        + space.d(request.origin, request.destination)
    )
    LAST_pu = np.inf
    EAST_do = EAST_pu
    LAST_do = np.inf

    pickup_stop = Stop(location=request.origin,
                       request=request,
                       action=StopAction.pickup,
                       estimated_arrival_time=CPAT_pu,
                       time_window_min=EAST_pu,
                       time_window_max=LAST_pu, )
    dropoff_stop = Stop(location=request.destination,
                        request=request,
                        action=StopAction.dropoff,
                        estimated_arrival_time=CPAT_do,
                        time_window_min=EAST_do,
                        time_window_max=LAST_do, )
    new_stoplist = []
    if best_pickup_index != len(stoplist) - 1 and best_dropoff_rel_index != 0:
        pre_pickup_stoplist = stoplist[:best_pickup_index + 1]
        post_pickup_stoplist = stoplist[best_pickup_index + 1:best_pickup_index + best_dropoff_rel_index + 1]
        for i, x in enumerate(post_pickup_stoplist):
            post_pickup_stoplist[i].estimated_arrival_time += pickup_detours[best_pickup_index]
        post_dropoff_stoplist = stoplist[best_pickup_index + best_dropoff_rel_index + 1:]
        for i, x in enumerate(post_dropoff_stoplist):
            post_dropoff_stoplist[i].estimated_arrival_time += pickup_detours[best_pickup_index] \
                                                               + dropoff_detours[
                                                                   best_pickup_index + best_dropoff_rel_index]
        new_stoplist = pre_pickup_stoplist + [pickup_stop] + post_pickup_stoplist + [
            dropoff_stop] + post_dropoff_stoplist
    elif best_pickup_index == len(stoplist) - 1:
        new_stoplist = stoplist + [pickup_stop] + [dropoff_stop]
    elif best_dropoff_rel_index == 0:
        pre_pickup_stoplist = stoplist[:best_pickup_index + 1]
        detour = space.d(stoplist[best_pickup_index].location, request.origin) \
            + space.d(request.origin, request.destination) \
            + space.d(request.destination, stoplist[best_pickup_index + 1].location) \
            - space.d(stoplist[best_pickup_index].location, stoplist[best_pickup_index + 1].location)
        post_pickup_stoplist = stoplist[best_pickup_index + 1:]
        for i, x in enumerate(post_pickup_stoplist):
            post_pickup_stoplist[i].estimated_arrival_time += detour
        new_stoplist = pre_pickup_stoplist + [pickup_stop, dropoff_stop] + post_pickup_stoplist
    return objective, new_stoplist, (EAST_pu, LAST_pu, EAST_do, LAST_do)
