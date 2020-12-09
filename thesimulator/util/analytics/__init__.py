import dataclasses
from typing import Iterable, List, Optional, Dict, Any

import numpy as np
import pandas as pd

from thesimulator.data_structures import (
    TransportationRequest,
    Event,
    ID,
    Stop,
    TransportSpace,
)


def _create_events_dataframe(events: Iterable) -> pd.DataFrame:
    return pd.DataFrame(
        map(
            lambda ev: dict(dataclasses.asdict(ev), event_type=ev.__class__.__name__),
            events,
        )
    )


def _create_stoplist_without_locations_dataframe(
    *, evs: pd.DataFrame, vehicle_ids
) -> pd.DataFrame:
    stops = evs[
        (evs["event_type"] == "PickupEvent") | (evs["event_type"] == "DeliveryEvent")
    ][["vehicle_id", "timestamp", "event_type", "request_id"]]

    stops["delta_occupancy"] = stops.apply(
        lambda t: {"PickupEvent": 1, "DeliveryEvent": -1}[t["event_type"]], axis=1
    ).astype("float64")

    stops.drop("event_type", axis=1, inplace=True)

    begin_stops = pd.DataFrame(
        np.r_[
            "-1,2,0",
            vehicle_ids,
            np.zeros(len(vehicle_ids)),
            np.zeros(len(vehicle_ids)),
        ],
        columns=["vehicle_id", "timestamp", "delta_occupancy"],
    )

    # NOTE this could/should use the cutoff time, if applicable
    # https://github.com/PhysicsOfMobility/theSimulator/issues/47
    end_time = stops["timestamp"].max()

    end_stops = pd.DataFrame(
        np.r_[
            "-1,2,0",
            vehicle_ids,
            np.full(len(vehicle_ids), end_time),
            np.zeros(len(vehicle_ids)),
        ],
        columns=["vehicle_id", "timestamp", "delta_occupancy"],
    )

    begin_stops["request_id"] = "START"
    end_stops["request_id"] = "STOP"
    stops = pd.concat((begin_stops, stops, end_stops), ignore_index=True)

    stops.sort_values(["vehicle_id", "timestamp", "request_id"], inplace=True)

    def fix_start_stop_order(df):
        i_start = (df["request_id"] == "START").argmax()
        i_stop = (df["request_id"] == "STOP").argmax()

        idx = df.index.to_list()

        k_start = idx[i_start]
        k_stop = idx[i_stop]

        if i_start < i_stop:
            i_stop -= 1
        else:
            i_start -= 1

        del idx[i_start]
        del idx[i_stop]

        idx.insert(0, k_start)
        idx.append(k_stop)

        return df.loc[idx]

    stops = stops.groupby("vehicle_id", as_index=False).apply(fix_start_stop_order)

    stops["state_duration"] = (
        stops.groupby("vehicle_id")["timestamp"].diff().shift(-1).fillna(0)
    )
    stops["occupancy"] = stops.groupby("vehicle_id")["delta_occupancy"].cumsum()

    stops.set_index(["vehicle_id", "timestamp"], inplace=True)

    # check total operational times of all vehicles are identical
    assert len(stops.groupby("vehicle_id")["state_duration"].sum().unique()) == 1
    return stops


def _create_requests_dataframe(
    *,
    evs: pd.DataFrame,
    stops,
    space,
    transportation_requests: Optional[List[TransportationRequest]] = None,
) -> pd.DataFrame:
    reqs_as_accepted = (
        evs[
            (evs["event_type"] == "RequestAcceptanceEvent")
            | (evs["event_type"] == "RequestRejectionEvent")
        ]
        .drop(["event_type", "vehicle_id"], axis=1)
        .set_index("request_id")
    )
    if transportation_requests is not None:
        reqs_as_supplied = (
            pd.DataFrame(map(dataclasses.asdict, transportation_requests))
            .set_index("request_id")
            .rename({"creation_timestamp": "timestamp"}, axis=1)
        )

        reqs = pd.concat(
            (reqs_as_supplied, reqs_as_accepted),
            axis=1,
            keys=["supplied", "accepted"],
            names=["source", "quantity"],
        )
    else:
        reqs = pd.concat(
            (reqs_as_accepted,), keys=["accepted"], names=["source", "quantity"], axis=1
        )

    stops_tmp = stops.reset_index()[
        ["request_id", "vehicle_id", "timestamp", "delta_occupancy"]
    ].set_index("request_id")

    reqs[("serviced", "vehicle_id")] = stops_tmp[stops_tmp["delta_occupancy"] == 1][
        "vehicle_id"
    ]
    reqs[("serviced", "timestamp_pickup")] = stops_tmp[
        stops_tmp["delta_occupancy"] == 1
    ]["timestamp"]
    reqs[("serviced", "timestamp_dropoff")] = stops_tmp[
        stops_tmp["delta_occupancy"] == -1
    ]["timestamp"]

    if "supplied" in reqs.columns:
        reqs[("supplied", "direct_travel_time")] = space.t(
            reqs[("supplied", "origin")], reqs[("supplied", "destination")]
        )

        reqs[("supplied", "direct_travel_distance")] = space.d(
            reqs[("supplied", "origin")], reqs[("supplied", "destination")]
        )

        reqs[("inferred", "waiting_time")] = (
            reqs[("serviced", "timestamp_pickup")]
            - reqs[("supplied", "pickup_timewindow_min")]
        )

    reqs[("inferred", "travel_time")] = (
        reqs[("serviced", "timestamp_dropoff")] - reqs[("serviced", "timestamp_pickup")]
    )

    if "supplied" in reqs.columns:
        reqs[("inferred", "relative_travel_time")] = (
            reqs[("inferred", "travel_time")] / reqs[("supplied", "direct_travel_time")]
        )

    reqs.sort_values(["source", "quantity"], axis=1, inplace=True)
    return reqs


def _add_locations_to_stoplist_dataframe(
    *, reqs, stops, initial_stoplists, vehicle_ids
) -> pd.DataFrame:
    breakpoint()
    locations = reqs.loc[:, ("accepted", ["origin", "destination"])]
    locations.columns = locations.columns.droplevel(0).rename("delta_occupancy")
    locations = locations.stack().rename("location")
    locations.index.set_levels(
        locations.index.levels[1]
        .astype("category")
        .rename_categories({"origin": 1.0, "destination": -1.0}),
        1,
        inplace=True,
    )

    stops = stops.join(locations, on=["request_id", "delta_occupancy"])

    begin_locations = pd.Series(
        [stoplist[0].location for stoplist in initial_stoplists.values()],
        index=pd.MultiIndex.from_product(
            [["START"], vehicle_ids], names=["request_id", "vehicle_id"]
        ),
        name="location",
    )
    stops["location"] = stops["location"].fillna(
        stops.join(begin_locations, on=["request_id", "vehicle_id"], lsuffix="_")[
            "location"
        ]
    )

    return stops


def get_stops_and_requests(
    *,
    events: List[Event],
    initial_stoplists: Dict[ID, List[Stop]],
    space: TransportSpace,
    transportation_requests: Optional[List[TransportationRequest]] = None,
):
    """
    Prepare two dataframes, containing stops and requests.

    Parameters
    ----------
    events
        list of all the events returned by the simulation
    initial_stoplists
        fleet state dictionary containing the initial stoplists indexed by their vehicle IDs
    transportation_requests
        list of the transportation requests, optional
    space
        transportation space that was used for the simulations

    Returns
    -------
    stops
        dataframe indexed by `[vehicle_id, timestamp]` containing all stops
    requests
        dataframe indexed by `request_id` containing all requests
    """
    vehicle_ids = list(initial_stoplists)
    events_df = _create_events_dataframe(events=events)

    stops = _create_stoplist_without_locations_dataframe(
        evs=events_df, vehicle_ids=vehicle_ids
    )

    requests = _create_requests_dataframe(
        evs=events_df,
        transportation_requests=transportation_requests,
        stops=stops,
        space=space,
    )

    stops = _add_locations_to_stoplist_dataframe(
        stops=stops,
        initial_stoplists=initial_stoplists,
        reqs=requests,
        vehicle_ids=vehicle_ids,
    )

    return stops, requests