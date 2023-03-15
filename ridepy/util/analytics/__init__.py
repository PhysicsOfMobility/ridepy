from collections import defaultdict

from typing import Iterable, List, Optional, Dict, Any

import functools as ft
import numpy as np
import pandas as pd

from ridepy.data_structures import (
    TransportSpace,
)
from ridepy.events import VehicleStateEndEvent, VehicleStateBeginEvent


def _create_events_dataframe(events: Iterable[dict]) -> pd.DataFrame:
    """
    Create a DataFrame of all logged events with their properties at columns.

    The schema of the returned DataFrame is the following, where
    the index is an unnamed integer range index.

    .. code-block::

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

    Parameters
    ----------
    events

    Returns
    -------
    events DataFrame, indexed by integer range
    """
    return pd.DataFrame(events)


def _create_stoplist_dataframe(*, evs: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a DataFrame containing the stoplists of the transporters.
    The location is only returned for the internal stops relating to
    VehicleStateBeginEvent and VehicleStateEndEvent. For the rest of
    the stops, location is nan.

    The schema of the returned DataFrame is the following, where
    `vehicle_id` and `timestamp` are MultiIndex levels.

    .. code-block::

        Column           Dtype
        ------           -----
        vehicle_id       float64
        timestamp        float64
        delta_occupancy  float64
        request_id       object
        state_duration   float64
        occupancy        float64
        location         Union[float64, int, Tuple[float64]]

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
        i_start = (df["request_id"] == -100).argmax()
        i_stop = (df["request_id"] == -200).argmax()

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

    .. code-block::

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

    The schema of the returned DataFrame is a superset of the following, where
    `vehicle_id` and `timestamp` are MultiIndex levels.

    .. code-block::

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
        levels=locations.index.levels[1].map({"origin": 1.0, "destination": -1.0}),
        level=1,
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

    stops = stops.groupby("vehicle_id", group_keys=False).apply(dist_time_to_next)

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


def _add_insertion_stats_to_stoplist_dataframe(*, reqs, stops, space) -> pd.DataFrame:
    """

    The schema of the returned DataFrame is a superset of the following, where
    `vehicle_id` and `timestamp` are MultiIndex levels.

    .. code-block::

        Column                                       Dtype
        ------                                       -----
        vehicle_id                                 float64
        stop_id                                      int64
        timestamp                                  float64
        delta_occupancy                            float64
        request_id                                   int64
        state_duration                             float64
        occupancy                                  float64
        location                                    object
        dist_to_next                               float64
        time_to_next                               float64
        timestamp_submitted                        float64
        insertion_index                            float64
        leg_1_dist_service_time                    float64
        leg_2_dist_service_time                    float64
        leg_direct_dist_service_time               float64
        detour_dist_service_time                   float64
        leg_1_dist_submission_time                 float64
        leg_2_dist_submission_time                 float64
        leg_direct_dist_submission_time            float64
        detour_dist_submission_time                float64
        stoplist_length_submission_time            float64
        stoplist_length_service_time               float64
        avg_segment_dist_submission_time           float64
        avg_segment_time_submission_time           float64
        avg_segment_dist_service_time              float64
        avg_segment_time_service_time              float64
        system_stoplist_length_submission_time     float64
        system_stoplist_length_service_time        float64
        avg_system_segment_dist_submission_time    float64
        avg_system_segment_time_submission_time    float64
        avg_system_segment_dist_service_time       float64
        avg_system_segment_time_service_time       float64
        relative_insertion_position                float64



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

    stops = pd.merge(
        stops,
        reqs.submitted.timestamp,
        how="left",
        left_on="request_id",
        right_index=True,
        suffixes=(None, "_submitted"),
    )
    actual_stops = stops.dropna(subset=("timestamp_submitted",))

    def _properties_at_time(stop, full_sl, scope):
        t = stop["timestamp"]
        ts = stop["timestamp_submitted"]
        pu = True if stop["delta_occupancy"] > 0 else False

        get_i_pu = lambda _sl, stop: (_sl["request_id"] == stop["request_id"]).argmax()
        get_i_do = (
            lambda _sl, stop: len(_sl)
            - (_sl["request_id"] == stop["request_id"])[::-1].argmax()
            - 1
        )

        sl = full_sl[
            (full_sl["timestamp_submitted"] <= t) & (t <= full_sl["timestamp"])
        ]

        sl_s = full_sl[
            (full_sl["timestamp_submitted"] <= ts) & (ts <= full_sl["timestamp"])
        ]

        if pu:
            i_pu_sl = get_i_pu(sl, stop)
            i_pu_sl_s = get_i_pu(sl_s, stop)
            i_do_sl_s = get_i_do(sl_s, stop)

            idx_pu = sl_s.iloc[i_pu_sl_s].name
            idx_do = sl_s.iloc[i_do_sl_s].name
            assert idx_pu == stop.name

            i_stop_sl = i_pu_sl
            i_stop_sl_s = i_pu_sl_s
        else:
            i_do_sl = get_i_do(sl, stop)

            i_pu_sl_s = get_i_pu(sl_s, stop)
            i_do_sl_s = get_i_do(sl_s, stop)

            idx_pu = sl_s.iloc[i_pu_sl_s].name
            idx_do = sl_s.iloc[i_do_sl_s].name
            assert idx_do == stop.name

            i_stop_sl = i_do_sl
            i_stop_sl_s = i_do_sl_s

        res = {}

        if scope != "system":
            res["insertion_index"] = len(sl_s[sl_s["timestamp"] < t])

            def _get_legs(i_stop, _sl, time_desc):
                l_sl = len(_sl)
                if i_stop == 0 == l_sl - 1:
                    stop_leg_1 = 0
                    stop_leg_2 = 0
                    stop_leg_d = 0
                elif i_stop == 0:
                    stop_leg_1 = 0
                    stop_leg_2 = space.d(
                        stop["location"], _sl.iloc[i_stop + 1]["location"]
                    )
                    stop_leg_d = stop_leg_1
                elif i_stop == l_sl - 1:
                    stop_leg_1 = space.d(
                        _sl.iloc[i_stop - 1]["location"], stop["location"]
                    )
                    stop_leg_2 = 0
                    stop_leg_d = stop_leg_2
                else:
                    stop_leg_1 = space.d(
                        _sl.iloc[i_stop - 1]["location"], stop["location"]
                    )
                    stop_leg_2 = space.d(
                        stop["location"], _sl.iloc[i_stop + 1]["location"]
                    )
                    stop_leg_d = space.d(
                        _sl.iloc[i_stop - 1]["location"],
                        _sl.iloc[i_stop + 1]["location"],
                    )

                stop_detour = stop_leg_1 + stop_leg_2 - stop_leg_d

                return {
                    f"leg_1_dist_{time_desc}_time": stop_leg_1,
                    f"leg_2_dist_{time_desc}_time": stop_leg_2,
                    f"leg_direct_dist_{time_desc}_time": stop_leg_d,
                    f"detour_dist_{time_desc}_time": stop_detour,
                }

            res |= _get_legs(i_stop_sl, sl, "service")
            res |= _get_legs(i_stop_sl_s, sl_s, "submission")

        if pu:
            sl.drop([idx_pu, idx_do], inplace=True)
            sl_s.drop([idx_pu, idx_do], inplace=True)
        else:
            sl.drop(idx_do, inplace=True)
            sl_s.drop([idx_pu, idx_do], inplace=True)

        res[
            f"{'system_' if scope=='system' else ''}stoplist_length_submission_time"
        ] = len(sl_s)
        res[
            f"{'system_' if scope=='system' else ''}stoplist_length_service_time"
        ] = len(sl)

        res[
            f"avg_{'system_' if scope=='system' else ''}segment_dist_submission_time"
        ] = sl_s["dist_to_next"].mean()
        res[
            f"avg_{'system_' if scope=='system' else ''}segment_time_submission_time"
        ] = sl_s["time_to_next"].mean()

        res[
            f"avg_{'system_' if scope=='system' else ''}segment_dist_service_time"
        ] = sl["dist_to_next"].mean()
        res[
            f"avg_{'system_' if scope=='system' else ''}segment_time_service_time"
        ] = sl["time_to_next"].mean()

        return res

    stops = stops.merge(
        actual_stops.groupby("vehicle_id").apply(
            lambda df: df.apply(
                ft.partial(_properties_at_time, full_sl=df, scope="vehicle"),
                axis=1,
                result_type="expand",
            )
        ),
        left_index=True,
        right_index=True,
        how="left",
    )

    stops = stops.merge(
        actual_stops.apply(
            ft.partial(_properties_at_time, full_sl=stops, scope="system"),
            axis=1,
            result_type="expand",
        ),
        left_index=True,
        right_index=True,
        how="left",
    )

    with pd.option_context("mode.use_inf_as_na", True):
        stops["relative_insertion_position"] = (
            stops["insertion_index"] / stops["stoplist_length_submission_time"]
        ).fillna(1)

    return stops


def get_stops_and_requests_from_events_dataframe(
    *, events_df: pd.DataFrame, space: TransportSpace
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare stops and requests dataframes from an events dataframe.
    For details on the returned dataframes see doc on outside-facing `get_stops_and_requests`.

    Parameters
    ----------
    events_df
        DataFrame indexed
    space

    Returns
    -------
    stops
        dataframe indexed by `[vehicle_id, timestamp]` containing all stops
    requests
        dataframe indexed by `request_id` containing all requests
    """
    stops_df = _create_stoplist_dataframe(evs=events_df)
    requests_df = _create_transportation_requests_dataframe(
        evs=events_df, stops=stops_df, space=space
    )

    try:
        stops_df = _add_locations_to_stoplist_dataframe(
            reqs=requests_df, stops=stops_df, space=space
        )
    except KeyError:  # TODO document this
        pass

    return stops_df, requests_df


def get_stops_and_requests(
    *, events: List[dict], space: TransportSpace
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare two DataFrames, containing stops and requests.

    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/ridepy/issues/45)

    The `stops` DataFrame returned has the following schema:

    .. code-block::

        Column                                       Dtype
        ------                                       -----
        vehicle_id                                 float64
        stop_id                                      int64
        timestamp                                  float64
        delta_occupancy                            float64
        request_id                                   int64
        state_duration                             float64
        occupancy                                  float64
        location                                    object
        dist_to_next                               float64
        time_to_next                               float64
        timestamp_submitted                        float64
        insertion_index                            float64
        leg_1_dist_service_time                    float64
        leg_2_dist_service_time                    float64
        leg_direct_dist_service_time               float64
        detour_dist_service_time                   float64
        leg_1_dist_submission_time                 float64
        leg_2_dist_submission_time                 float64
        leg_direct_dist_submission_time            float64
        detour_dist_submission_time                float64
        stoplist_length_submission_time            float64
        stoplist_length_service_time               float64
        avg_segment_dist_submission_time           float64
        avg_segment_time_submission_time           float64
        avg_segment_dist_service_time              float64
        avg_segment_time_service_time              float64
        system_stoplist_length_submission_time     float64
        system_stoplist_length_service_time        float64
        avg_system_segment_dist_submission_time    float64
        avg_system_segment_time_submission_time    float64
        avg_system_segment_dist_service_time       float64
        avg_system_segment_time_service_time       float64
        relative_insertion_position                float6


    The `requests` DataFrame returned has the following schema:

    .. code-block::

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

    return get_stops_and_requests_from_events_dataframe(
        events_df=_create_events_dataframe(events=events), space=space
    )


def get_vehicle_quantities(stops: pd.DataFrame, requests: pd.DataFrame) -> pd.DataFrame:
    """
    Compute various quantities aggregated **per vehicle**.

    Currently the following observables are returned:

    - avg_occupancy
    - avg_segment_dist
    - avg_segment_time
    - total_dist_driven
    - total_time_driven
    - avg_direct_dist
    - avg_direct_time
    - total_direct_dist
    - total_direct_time
    - efficiency_dist
    - efficiency_time
    - avg_system_stoplist_length_service_time
    - avg_system_stoplist_length_submission_time
    - avg_stoplist_length_service_time
    - avg_stoplist_length_submission_time

    Parameters
    ----------
    stops
        Stops dataframe
    requests
        Requests dataframe

    Returns
    -------
    ``pd.DataFrame`` containing the aforementioned observables as columns, indexed by ``vehicle_id``
    """
    serviced_requests = (
        requests[requests[("rejected", "timestamp")].isna()]
        if ("rejected", "timestamp") in requests
        else requests
    )

    avg_occupancy = stops.groupby("vehicle_id").apply(
        lambda gdf: (gdf["occupancy"] * gdf["state_duration"]).sum()
        / gdf["state_duration"].sum()
    )

    avg_segment_dist = stops.groupby("vehicle_id")["dist_to_next"].mean()
    avg_segment_time = stops.groupby("vehicle_id")["time_to_next"].mean()

    total_dist_driven = stops.groupby("vehicle_id")["dist_to_next"].sum()
    total_time_driven = stops.groupby("vehicle_id")["time_to_next"].sum()

    avg_direct_dist = serviced_requests.groupby(("serviced", "vehicle_id")).apply(
        lambda gdf: gdf.submitted.direct_travel_distance.mean()
    )

    avg_direct_time = serviced_requests.groupby(("serviced", "vehicle_id")).apply(
        lambda gdf: gdf.submitted.direct_travel_time.mean()
    )

    total_direct_dist = serviced_requests.groupby(("serviced", "vehicle_id")).apply(
        lambda gdf: gdf.submitted.direct_travel_distance.sum()
    )

    total_direct_time = serviced_requests.groupby(("serviced", "vehicle_id")).apply(
        lambda gdf: gdf.submitted.direct_travel_time.sum()
    )

    efficiency_dist = total_direct_dist / total_dist_driven
    efficiency_time = total_direct_time / total_time_driven

    avg_system_stoplist_length_service_time = stops.groupby("vehicle_id").apply(
        lambda gdf: (
            gdf["system_stoplist_length_service_time"] * gdf["state_duration"]
        ).sum()
        / gdf["state_duration"].sum()
    )
    avg_system_stoplist_length_submission_time = stops.groupby("vehicle_id").apply(
        lambda gdf: (
            gdf["system_stoplist_length_submission_time"] * gdf["state_duration"]
        ).sum()
        / gdf["state_duration"].sum()
    )

    avg_stoplist_length_service_time = stops.groupby("vehicle_id").apply(
        lambda gdf: (gdf["stoplist_length_service_time"] * gdf["state_duration"]).sum()
        / gdf["state_duration"].sum()
    )
    avg_stoplist_length_submission_time = stops.groupby("vehicle_id").apply(
        lambda gdf: (
            gdf["stoplist_length_submission_time"] * gdf["state_duration"]
        ).sum()
        / gdf["state_duration"].sum()
    )

    return pd.DataFrame(
        dict(
            avg_occupancy=avg_occupancy,
            avg_segment_dist=avg_segment_dist,
            avg_segment_time=avg_segment_time,
            total_dist_driven=total_dist_driven,
            total_time_driven=total_time_driven,
            avg_direct_dist=avg_direct_dist,
            avg_direct_time=avg_direct_time,
            total_direct_dist=total_direct_dist,
            total_direct_time=total_direct_time,
            efficiency_dist=efficiency_dist,
            efficiency_time=efficiency_time,
            avg_system_stoplist_length_service_time=avg_system_stoplist_length_service_time,
            avg_system_stoplist_length_submission_time=avg_system_stoplist_length_submission_time,
            avg_stoplist_length_service_time=avg_stoplist_length_service_time,
            avg_stoplist_length_submission_time=avg_stoplist_length_submission_time,
        )
    ).rename_axis("vehicle_id")


def get_system_quantities(
    stops: pd.DataFrame,
    requests: pd.DataFrame,
    params: Optional[dict[str, dict[str, Any]]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Compute various quantities aggregated for the entire simulation.

    Currently the following observables are returned:

    - avg_occupancy
    - avg_segment_dist
    - avg_segment_time
    - total_dist_driven
    - total_time_driven
    - avg_direct_dist
    - avg_direct_time
    - total_direct_dist
    - total_direct_time
    - efficiency_dist
    - efficiency_time
    - avg_system_stoplist_length_service_time
    - avg_system_stoplist_length_submission_time
    - avg_stoplist_length_service_time
    - avg_stoplist_length_submission_time
    - avg_waiting_time
    - rejection_ratio
    - median_stoplist_length
    - avg_detour
    - (n_vehicles)
    - (request_rate)
    - (velocity)

    Parameters
    ----------
    stops
        Stops dataframe
    requests
        Requests dataframe
    params
        Optional, adds more data (the fields in parentheses) to the result for convenience purposes

    Returns
    -------
    dict containing the aforementioned observables

    Parameters
    ----------
    stops
        Stops dataframe
    requests
        Requests dataframe

    Returns
    -------
    dict containing the aforementioned observables
    """
    serviced_requests = (
        requests[requests[("rejected", "timestamp")].isna()]
        if ("rejected", "timestamp") in requests
        else requests
    )

    avg_occupancy = (stops["occupancy"] * stops["state_duration"]).sum() / stops[
        "state_duration"
    ].sum()

    avg_segment_dist = stops["dist_to_next"].mean()
    avg_segment_time = stops["time_to_next"].mean()

    total_dist_driven = stops["dist_to_next"].sum()
    total_time_driven = stops["time_to_next"].sum()

    avg_direct_dist = serviced_requests[("submitted", "direct_travel_distance")].mean()
    avg_direct_time = serviced_requests[("submitted", "direct_travel_time")].mean()

    total_direct_dist = serviced_requests[("submitted", "direct_travel_distance")].sum()
    total_direct_time = serviced_requests[("submitted", "direct_travel_time")].sum()

    efficiency_dist = total_direct_dist / total_dist_driven
    efficiency_time = total_direct_time / total_time_driven

    avg_waiting_time = serviced_requests.inferred.waiting_time.mean()

    rejection_ratio = 1 - len(serviced_requests) / len(requests)

    _stops = stops.dropna(
        subset=(
            "system_stoplist_length_service_time",
            "system_stoplist_length_submission_time",
        )
    )
    avg_system_stoplist_length_service_time = (
        _stops["system_stoplist_length_service_time"] * _stops["state_duration"]
    ).sum() / _stops["state_duration"].sum()

    avg_system_stoplist_length_submission_time = (
        _stops["system_stoplist_length_submission_time"] * _stops["state_duration"]
    ).sum() / _stops["state_duration"].sum()

    # not sure if it is necessary to do it again...
    _stops = stops.dropna(
        subset=("stoplist_length_service_time", "stoplist_length_submission_time")
    )

    avg_stoplist_length_submission_time = (
        _stops["stoplist_length_submission_time"] * _stops["state_duration"]
    ).sum() / _stops["state_duration"].sum()

    avg_stoplist_length_service_time = (
        _stops["stoplist_length_service_time"] * _stops["state_duration"]
    ).sum() / _stops["state_duration"].sum()

    stops["event_type"] = stops["delta_occupancy"].map({1.0: "pickup", -1.0: "dropoff"})

    submission_events = requests.loc[
        :, [("submitted", "timestamp"), ("serviced", "vehicle_id")]
    ].dropna()
    submission_events.columns = ["timestamp", "vehicle_id"]
    submission_events = (
        submission_events.reset_index()
        .set_index(["vehicle_id", "timestamp"])
        .sort_index()
        .assign(event_type="submission")
    )

    event_log = pd.concat(
        [
            stops[["event_type", "request_id"]],
            submission_events,
        ],
        axis="index",
    ).sort_index()

    median_stoplist_length = (
        event_log["event_type"]
        .map(dict(submission=2, pickup=-1, dropoff=-1))
        .cumsum()
        .median()
    )

    avg_detour = requests["inferred", "relative_travel_time"].mean()

    res = dict(
        avg_occupancy=avg_occupancy,
        avg_segment_dist=avg_segment_dist,
        avg_segment_time=avg_segment_time,
        total_dist_driven=total_dist_driven,
        total_time_driven=total_time_driven,
        avg_direct_dist=avg_direct_dist,
        avg_direct_time=avg_direct_time,
        total_direct_dist=total_direct_dist,
        total_direct_time=total_direct_time,
        efficiency_dist=efficiency_dist,
        efficiency_time=efficiency_time,
        avg_system_stoplist_length_service_time=avg_system_stoplist_length_service_time,
        avg_system_stoplist_length_submission_time=avg_system_stoplist_length_submission_time,
        avg_stoplist_length_service_time=avg_stoplist_length_service_time,
        avg_stoplist_length_submission_time=avg_stoplist_length_submission_time,
        avg_waiting_time=avg_waiting_time,
        rejection_ratio=rejection_ratio,
        median_stoplist_length=median_stoplist_length,
        avg_detour=avg_detour,
    )

    if params:
        res |= dict(
            n_vehicles=params["general"]["n_vehicles"],
            request_rate=params["request_generator"]["rate"],
            velocity=params["general"]["space"].velocity,
        )

    return res
