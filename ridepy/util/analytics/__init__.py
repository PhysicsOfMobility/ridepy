import dataclasses
from collections import defaultdict

import operator as op
from typing import Iterable, List, Optional, Dict, Any

import numpy as np
import pandas as pd

from ridepy.data_structures import (
    TransportationRequest,
    ID,
    Stop,
    TransportSpace,
)
from ridepy.events import Event, VehicleStateEndEvent, VehicleStateBeginEvent


def _create_events_dataframe(events: Iterable[Event]) -> pd.DataFrame:
    """
    Create a DataFrame of all logged events with their properties at columns.

    The schema of the returned DataFrame is the following, where
    the index is an unnamed integer range index.
    ```
    Column                   Dtype
    ------                   -----
    request_id               int64
    timestamp                float64
    vehicle_id               float64
    event_type               object
    location                 Union[int, float64, Tuple[float64]]
    origin                   Union[int, float64, Tuple[float64]]
    destination              Union[int, float64, Tuple[float64]]
    pickup_timewindow_min    float64
    pickup_timewindow_max    float64
    delivery_timewindow_min  float64
    delivery_timewindow_max  float64
    ```

    Parameters
    ----------
    events

    Returns
    -------
    events DataFrame, indexed by integer range
    """

    #return pd.DataFrame(
    #    map(
    #        lambda ev: dict(dataclasses.asdict(ev), event_type=ev.__class__.__name__),
    #        events,
    #    )
    #)
    event_types, events = events
    return pd.DataFrame(index=event_types, data=events, ).rename_axis(index="event_type").reset_index()


def _create_stoplist_dataframe(*, evs: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a DataFrame containing the stoplists of the transporters.
    The location is only returned for the internal stops relating to
    VehicleStateBeginEvent and VehicleStateEndEvent. For the rest of
    the stops, location is nan.

    The schema of the returned DataFrame is the following, where
    `vehicle_id` and `timestamp` are MultiIndex levels.

    Column           Dtype
    ------           -----
    vehicle_id       float64
    timestamp        float64
    delta_occupancy  float64
    request_id       object
    state_duration   float64
    occupancy        float64
    location         Union[float64, int, Tuple[float64]]
    ```

    Parameters
    ----------
    evs
        events DataFrame

    Returns
    -------
    stoplist DataFrame indexed by `vehicle_id` and `timestamp`
    """
    # Create the initial dataframe: Select only events of type
    # `PickupEvent` and `DeliveryEvent`, along with their vehicle_id, timestamp,
    # and request_id
    stops = evs[
        evs["event_type"].isin(
            [
                "PickupEvent",
                "DeliveryEvent",
                "VehicleStateBeginEvent",
                "VehicleStateEndEvent",
            ]
        )
    ][["vehicle_id", "timestamp", "event_type", "request_id", "location"]]

    # Translate PickupEvent and DeliveryEvent into an occupancy delta.
    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/ridepy/issues/45)
    stops["delta_occupancy"] = stops["event_type"].map(
        defaultdict(float, PickupEvent=1, DeliveryEvent=-1)
    )

    # ... and drop the event_type as pickup/dropoff is now signified through delta_occupancy
    stops.drop("event_type", axis=1, inplace=True)

    stops.sort_values(["vehicle_id", "timestamp", "request_id"], inplace=True)

    # Fix the stop order. The begin and end stops have identical timestamps as
    # other stops, partially on the same vehicle. This is problematic as for
    # proper computation of the state durations BEGIN and END **must** be first
    # and last stops in every stoplist.
    def fix_start_stop_order(df):
        # get absolute current positions of the BEGIN/END stops
        i_start = (df["request_id"] == VehicleStateBeginEvent.request_id).argmax()
        i_stop = (df["request_id"] == VehicleStateEndEvent.request_id).argmax()

        # get dataframe's integer index values for the dummy stops
        idx = df.index.to_list()

        k_start = idx[i_start]
        k_stop = idx[i_stop]

        # delete the existing stops from the index list...
        if i_start < i_stop:
            i_stop -= 1
        else:
            i_start -= 1

        del idx[i_start]
        del idx[i_stop]

        # ...and insert them at the correct positions
        idx.insert(0, k_start)
        idx.append(k_stop)

        return df.loc[idx]

    stops = stops.groupby("vehicle_id", as_index=False).apply(fix_start_stop_order)

    # compute the durations of every state and add them as a columns to the dataframe
    stops["state_duration"] = (
        stops.groupby("vehicle_id")["timestamp"].diff().shift(-1).fillna(0)
    )
    # compute the occupancy as delta_occupancy cumsum
    stops["occupancy"] = stops.groupby("vehicle_id")["delta_occupancy"].cumsum()

    # set index to ('vehicle_id, 'stop_id'), where stop_id in 0...N for each vehicle
    stops = (
        stops.groupby("vehicle_id")
        .apply(lambda df: df.reset_index(drop=True))
        .drop("vehicle_id", axis=1)
    )
    stops.index.rename(names="stop_id", level=1, inplace=True)

    # check total operational times of all vehicles are almost identical
    iterator = iter(stops.groupby("vehicle_id")["state_duration"].sum())
    try:
        first = next(iterator)
    except StopIteration:
        pass
    else:
        assert all(np.isclose(first, x) for x in iterator)

    return stops


def _create_transportation_requests_dataframe(
    *, evs: pd.DataFrame, stops, space
) -> pd.DataFrame:
    """
    Create DataFrame containing all requests.
    This includes the *submitted* requests, the *accepted* requests and the *rejected* requests.
    For the accepted requests, additional *serviced* and subsequently *inferred* data is given,
    under the respectively named level-0 column index *source*. Level 1 specifying the actual
    kind data of data is named *quantity*.

    The schema of the returned DataFrame is the following,
    where `request_id` is the index.
    ```
    Column                               Dtype
    ------                               -----
    request_id                            int64
    (submitted, timestamp)                float64
    (submitted, origin)                   float64
    (submitted, destination)              float64
    (submitted, pickup_timewindow_min)    float64
    (submitted, pickup_timewindow_max)    float64
    (submitted, delivery_timewindow_min)  float64
    (submitted, delivery_timewindow_max)  float64
    (submitted, direct_travel_distance)   float64
    (submitted, direct_travel_time)       float64
    (accepted, timestamp)                 float64
    (accepted, origin)                    float64
    (accepted, destination)               float64
    (accepted, pickup_timewindow_min)     float64
    (accepted, pickup_timewindow_max)     float64
    (accepted, delivery_timewindow_min)   float64
    (accepted, delivery_timewindow_max)   float64
    (rejected, timestamp)                 float64
    (inferred, relative_travel_time)      float64
    (inferred, travel_time)               float64
    (inferred, waiting_time)              float64
    (serviced, timestamp_dropoff)         float64
    (serviced, timestamp_pickup)          float64
    (serviced, vehicle_id)                float64
    ```

    Parameters
    ----------
    evs
        events DataFrame
    stops
        stoplists DataFrame
    space
        TransportSpace the simulations were performed on

    Returns
    -------
    requests DataFrame indexed by `request_id`
    """

    # first turn all request submission, acceptance and rejection events into a dataframe
    reqs = (
        evs[
            evs["event_type"].isin(
                [
                    "RequestSubmissionEvent",
                    "RequestAcceptanceEvent",
                    "RequestRejectionEvent",
                ]
            )
        ]  # select only request events
        .drop(["vehicle_id", "location"], axis=1)  # drop now empty columns
        .set_index(
            ["request_id", "event_type"]
        )  # set index to be request_id and event_type
        .unstack()  # unstack so that remaining index is request_id and column index is MultiIndex event_type as level_1
        .reorder_levels(
            [1, 0], axis=1
        )  # switch column index order to have event_type as level_0
        .sort_index(axis=1)  # sort so that columns are grouped by event_type
        .drop(
            [
                ("RequestRejectionEvent", "pickup_timewindow_min"),
                ("RequestRejectionEvent", "pickup_timewindow_max"),
                ("RequestRejectionEvent", "delivery_timewindow_min"),
                ("RequestRejectionEvent", "delivery_timewindow_max"),
                ("RequestRejectionEvent", "origin"),
                ("RequestRejectionEvent", "destination"),
            ],
            axis=1,
            errors="ignore",
        )  # drop columns that are empty (nan) for rejections (errors=ignore b/c rejections may not have happened)
        .rename(
            {
                "RequestAcceptanceEvent": "accepted",
                "RequestSubmissionEvent": "submitted",
                "RequestRejectionEvent": "rejected",
            },
            axis=1,
            level=0,
        )  # rename event_types to the "data source" indicators "accepted", "submitted" and "rejected"
    )
    reqs.columns.rename(["source", "quantity"], inplace=True)

    # Get properties of serviced requests from the stops dataframe:
    stops_tmp = stops.reset_index()[
        ["request_id", "vehicle_id", "timestamp", "delta_occupancy"]
    ].set_index("request_id")

    # - vehicle ID of the vehicle that serviced the request
    reqs[("serviced", "vehicle_id")] = stops_tmp[stops_tmp["delta_occupancy"] > 0][
        "vehicle_id"
    ]

    # - timestamp of the pickup stop
    reqs[("serviced", "timestamp_pickup")] = stops_tmp[
        stops_tmp["delta_occupancy"] > 0
    ]["timestamp"]

    # - timestamp of the dropoff stop
    reqs[("serviced", "timestamp_dropoff")] = stops_tmp[
        stops_tmp["delta_occupancy"] < 0
    ]["timestamp"]

    # - travel time
    reqs[("inferred", "travel_time")] = (
        reqs[("serviced", "timestamp_dropoff")] - reqs[("serviced", "timestamp_pickup")]
    )

    # If transportation as submitted were submitted, calculate more properties.
    # NOTE that these properties might equally well be computed using the
    # inferred requests, but in case of differences between the requests
    # the resulting change in behavior might not intended. Therefore so far
    # we only compute these quantities if transportation_requests are submitted.

    # - direct travel time
    # `to_list()` is necessary as for dimensionality > 1 the `pd.Series` will contain tuples
    # which will not be understood as a dimension by `np.shape(...)` which subsequently confuses smartVectorize
    # see https://github.com/PhysicsOfMobility/ridepy/issues/85
    reqs[("submitted", "direct_travel_time")] = space.t(
        reqs[("submitted", "origin")].to_list(),
        reqs[("submitted", "destination")].to_list(),
    )

    # - direct travel distance
    # again: `to_list()` is necessary as for dimensionality > 1 the `pd.Series` will contain tuples
    # which will not be understood as a dimension by `np.shape(...)` which subsequently  confuses smartVectorize
    # see https://github.com/PhysicsOfMobility/ridepy/issues/85
    reqs[("submitted", "direct_travel_distance")] = space.d(
        reqs[("submitted", "origin")].to_list(),
        reqs[("submitted", "destination")].to_list(),
    )

    # - waiting time
    reqs[("inferred", "waiting_time")] = (
        reqs[("serviced", "timestamp_pickup")]
        - reqs[("submitted", "pickup_timewindow_min")]
    )

    # - relative travel time
    reqs[("inferred", "relative_travel_time")] = (
        reqs[("inferred", "travel_time")] / reqs[("submitted", "direct_travel_time")]
    )

    # TODO possibly add more properties to compute HERE

    # sort columns alphabetically
    # FIXME this is open for debate
    reqs.sort_values(["source", "quantity"], axis=1, inplace=True)
    return reqs


def _add_locations_to_stoplist_dataframe(*, reqs, stops, space) -> pd.DataFrame:
    """
    Add non-internal stops' locations to the stoplist DataFrame as inferred
    from the *accepted* requests.

    The schema of the returned DataFrame is the following, where
    `vehicle_id` and `timestamp` are MultiIndex levels.
    ```
    Column           Dtype
    ------           -----
    vehicle_id       float64
    timestamp        float64
    delta_occupancy  float64
    request_id       object
    state_duration   float64
    occupancy        float64
    location         Union[float64, int, Tuple[float64]]
    time_to_next     float64
    dist_to_next     float64
    ```

    Parameters
    ----------
    reqs
        requests  DataFrame
    stops
        stops DataFrame missing stop locations for non-internal stops

    Returns
    -------
    stoplist DataFrame with added stop locations indexed by `vehicle_id` and `timestamp`
    """

    # use the requests' locations and reshape them into a DateFrame indexed by
    # `request_id` and `delta_occupancy`
    locations = reqs.loc[:, ("accepted", ["origin", "destination"])]
    locations.columns = locations.columns.droplevel(0).rename("delta_occupancy")
    locations = locations.stack().rename("location")

    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/ridepy/issues/45)
    locations.index = locations.index.set_levels(
        locations.index.levels[1].map({"origin": 1.0, "destination": -1.0}),
        1,
    )

    # finally fill the locations missing in the stops dataframe by joining on request_id and delta_occupancy
    # and subsequently filling up nan from the now index-aligned "location_tmp" series
    stops["location"] = stops["location"].fillna(
        stops.join(locations, on=["request_id", "delta_occupancy"], rsuffix="_tmp")[
            "location_tmp"
        ],
    )

    def dist_time_to_next(df):
        locs = df["location"]

        dist_to_next = space.d(locs[:-1].to_list(), locs[1:].to_list())
        df["dist_to_next"] = pd.Series(dist_to_next, index=df.index[:-1])

        time_to_next = space.t(locs[:-1].to_list(), locs[1:].to_list())
        df["time_to_next"] = pd.Series(time_to_next, index=df.index[:-1])

        return df

    stops = stops.groupby("vehicle_id").apply(dist_time_to_next)

    return stops[
        [
            "timestamp",
            "delta_occupancy",
            "request_id",
            "state_duration",
            "occupancy",
            "location",
            "dist_to_next",
            "time_to_next",
        ]
    ]


def get_stops_and_requests(*, events: List[Event], space: TransportSpace):
    """
    Prepare two DataFrames, containing stops and requests.

    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/ridepy/issues/45)

    The `stops` DataFrame returned has the following schema:
    ```
    Column           Dtype
    ------           -----
    vehicle_id       float64
    timestamp        float64
    delta_occupancy  float64
    request_id       object
    state_duration   float64
    occupancy        float64
    location         Union[float64, int, Tuple[float64]]
    time_to_next     float64
    dist_to_next     float64
    ```

    The `requests` DataFrame returned has the following schema:

    ```
    Column                               Dtype
    ------                               -----
    (submitted, timestamp)                float64
    (submitted, origin)                   Union[float64, int, Tuple[float64]]
    (submitted, destination)              Union[float64, int, Tuple[float64]]
    (submitted, pickup_timewindow_min)    float64
    (submitted, pickup_timewindow_max)    float64
    (submitted, delivery_timewindow_min)  float64
    (submitted, delivery_timewindow_max)  float64
    (submitted, direct_travel_distance)   float64
    (submitted, direct_travel_time)       float64
    (accepted, timestamp)                 float64
    (accepted, origin)                    Union[float64, int, Tuple[float64]]
    (accepted, destination)               Union[float64, int, Tuple[float64]]
    (accepted, pickup_timewindow_min)     float64
    (accepted, pickup_timewindow_max)     float64
    (accepted, delivery_timewindow_min)   float64
    (accepted, delivery_timewindow_max)   float64
    (rejected, timestamp)                 float64
    (inferred, relative_travel_time)      float64
    (inferred, travel_time)               float64
    (inferred, waiting_time)              float64
    (serviced, timestamp_dropoff)         float64
    (serviced, timestamp_pickup)          float64
    (serviced, vehicle_id)                float64
    ```

    Parameters
    ----------
    events
        list of all the events returned by the simulation
    space
        transportation space that was used for the simulations

    Returns
    -------
    stops
        dataframe indexed by `[vehicle_id, timestamp]` containing all stops
    requests
        dataframe indexed by `request_id` containing all requests
    """

    events_df = _create_events_dataframe(events=events)
    stops_df = _create_stoplist_dataframe(evs=events_df)
    requests_df = _create_transportation_requests_dataframe(
        evs=events_df, stops=stops_df, space=space
    )

    try:
        stops_df = _add_locations_to_stoplist_dataframe(
            reqs=requests_df, stops=stops_df, space=space
        )
    except KeyError:
        pass

    return stops_df, requests_df
