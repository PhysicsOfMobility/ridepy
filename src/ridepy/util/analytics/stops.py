import functools as ft
from collections import defaultdict

import numpy as np
import pandas as pd


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

    stops = stops.groupby("vehicle_id", as_index=False, group_keys=False).apply(
        fix_start_stop_order
    )

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
        stops DataFrame

    Returns
    -------
    stoplist DataFrame
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
        res[f"{'system_' if scope=='system' else ''}stoplist_length_service_time"] = (
            len(sl)
        )

        res[
            f"avg_{'system_' if scope=='system' else ''}segment_dist_submission_time"
        ] = sl_s["dist_to_next"].mean()
        res[
            f"avg_{'system_' if scope=='system' else ''}segment_time_submission_time"
        ] = sl_s["time_to_next"].mean()

        res[f"avg_{'system_' if scope=='system' else ''}segment_dist_service_time"] = (
            sl["dist_to_next"].mean()
        )
        res[f"avg_{'system_' if scope=='system' else ''}segment_time_service_time"] = (
            sl["time_to_next"].mean()
        )

        return res

    stops = stops.merge(
        actual_stops.groupby("vehicle_id", group_keys=False).apply(
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
