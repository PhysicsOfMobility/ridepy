import dataclasses
import operator as op
from typing import Iterable, List, Optional, Dict, Any

import numpy as np
import pandas as pd

from thesimulator.data_structures import (
    TransportationRequest,
    ID,
    Stop,
    TransportSpace,
)
from thesimulator.events import Event, VehicleStateEndEvent, VehicleStateBeginEvent

from thesimulator.util import make_dict


def _create_events_dataframe(events: Iterable) -> pd.DataFrame:
    """
    Create a DataFrame of all logged events with their properties at columns.

    The schema of the returned DataFrame is the following:
    ```
     #   Column                   Dtype
    ---  ------                   -----
     0   request_id               int64
     1   timestamp                float64
     2   origin                   float64
     3   destination              float64
     4   pickup_timewindow_min    float64
     5   pickup_timewindow_max    float64
     6   delivery_timewindow_min  float64
     7   delivery_timewindow_max  float64
     8   event_type               object
     9   vehicle_id               float64
    ```

    Parameters
    ----------
    events

    Returns
    -------
    events DataFrame
    """

    return pd.DataFrame(
        map(
            lambda ev: dict(dataclasses.asdict(ev), event_type=ev.__class__.__name__),
            events,
        )
    )


def _create_stoplist_dataframe(*, evs: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a DataFrame containing the stoplists of the transporters
    (though still without the stops' locations attached)

    The schema of the returned DataFrame is the following:
    ```
     #   Column           Non-Null Count  Dtype
    ---  ------           --------------  -----
     0   delta_occupancy  12 non-null     float64
     1   request_id       12 non-null     object
     2   state_duration   12 non-null     float64
     3   occupancy        12 non-null     float64
    ```

    Parameters
    ----------
    evs
        events DataFrame

    Returns
    -------
    stoplist DataFrame
    """
    # Create the initial dataframe: Select only events of type
    # `PickupEvent` and `DeliveryEvent`, along with their vehicle_id, timestamp,
    # and request_id
    stops = evs[
        (evs["event_type"] == "PickupEvent")
        | (evs["event_type"] == "DeliveryEvent")
        | (evs["event_type"] == "VehicleStateBeginEvent")
        | (evs["event_type"] == "VehicleStateEndEvent")
    ][["vehicle_id", "timestamp", "event_type", "request_id", "location"]]

    # Translate PickupEvent and DeliveryEvent into an occupancy delta.
    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/theSimulator/issues/45)
    stops["delta_occupancy"] = stops.apply(
        lambda t: {"PickupEvent": 1, "DeliveryEvent": -1}.get(t["event_type"], 0),
        axis=1,
    ).astype("f8")

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

    # and change index to hierarchical (vehicle_id, timestamp). Note that this is
    # non-unique as multiply stops on the same vehicle may have identical timestamps.
    stops.set_index(["vehicle_id", "timestamp"], inplace=True)

    # check total operational times of all vehicles are identical
    assert len(stops.groupby("vehicle_id")["state_duration"].sum().unique()) == 1
    return stops


def _create_transportation_requests_dataframe(
    *,
    evs: pd.DataFrame,
    stops,
    space,
    transportation_requests: Optional[List[TransportationRequest]] = None,
) -> pd.DataFrame:
    """
    Create DataFrame containing all requests. If desired, the filed
    requests may be supplied as an optional argument. This allows for treatment
    of differences in the properties of supplied and logged/accepted/rejected requests,
    such as modified stop locations etc.

    The schema of the returned DataFrame is the following:
    ```
     #   Column                               Dtype
    ---  ------                               -----
     0   (accepted, delivery_timewindow_max)  float64
     1   (accepted, delivery_timewindow_min)  float64
     2   (accepted, destination)              float64
     3   (accepted, origin)                   float64
     4   (accepted, pickup_timewindow_max)    float64
     5   (accepted, pickup_timewindow_min)    float64
     6   (accepted, timestamp)                float64
     7   (inferred, relative_travel_time)     float64
     8   (inferred, travel_time)              float64
     9   (inferred, waiting_time)             float64
     10  (serviced, timestamp_dropoff)        float64
     11  (serviced, timestamp_pickup)         float64
     12  (serviced, vehicle_id)               float64
     13  (supplied, delivery_timewindow_max)  float64
     14  (supplied, delivery_timewindow_min)  int64
     15  (supplied, destination)              float64
     16  (supplied, direct_travel_distance)   float64
     17  (supplied, direct_travel_time)       float64
     18  (supplied, origin)                   float64
     19  (supplied, pickup_timewindow_max)    float64
     20  (supplied, pickup_timewindow_min)    int64
     21  (supplied, timestamp)                int64
    ```
    If transportation_requests are not supplied, the (supplied, .*)
    columns are not present.

    Parameters
    ----------
    evs
        events DataFrame
    stops
        stoplists DataFrame
    space
        TransportSpace the simulations were performed on
    transportation_requests
        Transportation Requests (optional). If not supplied,
        infer the requests.

    Returns
    -------
    requests DataFrame
    """

    # first turn all request acceptance and rejection events into a dataframe
    reqs_as_logged = (
        evs[
            (evs["event_type"] == "RequestAcceptanceEvent")
            | (evs["event_type"] == "RequestRejectionEvent")
        ]
        .drop(["event_type", "vehicle_id", "location"], axis=1)
        .set_index("request_id")
    )

    if transportation_requests is None:
        # if no transportation requests are supplied, just use the logged ones.
        reqs = pd.concat(
            (reqs_as_logged,), keys=["accepted"], names=["source", "quantity"], axis=1
        )
    else:
        # otherwise, create an additional dataframe containing the supplied requests
        # which possibly may have different properties and join it to the logged ones.
        reqs_as_supplied = (
            pd.DataFrame(map(make_dict, transportation_requests))
            .set_index("request_id")
            .rename({"creation_timestamp": "timestamp"}, axis=1)
        )

        reqs = pd.concat(
            (reqs_as_supplied, reqs_as_logged),
            axis=1,
            keys=["supplied", "accepted"],
            names=["source", "quantity"],
        )

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

    if "supplied" in reqs.columns:
        # If transportation as supplied were supplied, calculate more properties.
        # NOTE that these properties might equally well be computed using the
        # inferred requests, but in case of differences between the requests
        # the resulting change in behavior might not intended. Therefore so far
        # we only compute these quantities if transportation_requests are supplied.

        # - direct travel time
        # `to_list()` is necessary as for dimensionality > 1 the `pd.Series` will contain tuples
        # which will not be understood as a dimension by `np.shape(...)` which subsequently confuses smartVectorize
        # see https://github.com/PhysicsOfMobility/theSimulator/issues/85
        reqs[("supplied", "direct_travel_time")] = space.t(
            reqs[("supplied", "origin")].to_list(),
            reqs[("supplied", "destination")].to_list(),
        )

        # - direct travel distance
        # again: `to_list()` is necessary as for dimensionality > 1 the `pd.Series` will contain tuples
        # which will not be understood as a dimension by `np.shape(...)` which subsequently  confuses smartVectorize
        # see https://github.com/PhysicsOfMobility/theSimulator/issues/85
        reqs[("supplied", "direct_travel_distance")] = space.d(
            reqs[("supplied", "origin")].to_list(),
            reqs[("supplied", "destination")].to_list(),
        )

        # - waiting time
        reqs[("inferred", "waiting_time")] = (
            reqs[("serviced", "timestamp_pickup")]
            - reqs[("supplied", "pickup_timewindow_min")]
        )

        # - relative travel time
        reqs[("inferred", "relative_travel_time")] = (
            reqs[("inferred", "travel_time")] / reqs[("supplied", "direct_travel_time")]
        )

    # TODO possibly add more properties to compute HERE

    # sort columns alphabetically
    # FIXME this is open for debate
    reqs.sort_values(["source", "quantity"], axis=1, inplace=True)
    return reqs


def _add_locations_to_stoplist_dataframe(*, reqs, stops) -> pd.DataFrame:
    """
    Add stops' locations to the stoplist DataFrame.

    The schema of the returned DataFrame is the following:
    ```
     #        Column           Dtype
    ---       ------           -----
     index_0  vehicle_id       float64
     index_1  timestamp        float64
     0        delta_occupancy  float64
     1        request_id       object
     2        state_duration   float64
     3        occupancy        float64
     4        location         Union[float64, int, Tuple[float64]]
    ```

    Parameters
    ----------
    reqs
        requests  DataFrame
    stops
        stops DataFrame missing stop locations

    Returns
    -------
    stoplist DataFrame with added stop locations
    """

    # use the requests' locations and reshape them into a DateFrame indexed by
    # `request_id` and `delta_occupancy`
    locations = reqs.loc[:, ("accepted", ["origin", "destination"])]
    locations.columns = locations.columns.droplevel(0).rename("delta_occupancy")
    locations = locations.stack().rename("location")

    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/theSimulator/issues/45)
    locations.index.set_levels(
        locations.index.levels[1].map({"origin": 1.0, "destination": -1.0}),
        1,
        inplace=True,
    )

    stops["location"] = stops["location"].fillna(
        stops.join(locations, on=["request_id", "delta_occupancy"], rsuffix="_tmp")[
            "location_tmp"
        ],
    )
    return stops[
        ["delta_occupancy", "request_id", "state_duration", "occupancy", "location"]
    ]


def get_stops_and_requests(
    *,
    events: List[Event],
    space: TransportSpace,
    transportation_requests: Optional[List[TransportationRequest]] = None,
    end_time: Optional[float] = None,
):
    """
    Prepare two DataFrames, containing stops and requests.

    # NOTE: This assumes occupancy delta of +1/-1, i.e. only single-customer requests.
    #       If the simulator should allow for multi-customer requests in the future,
    #       this must be changed.
    #       See also [issue #45](https://github.com/PhysicsOfMobility/theSimulator/issues/45)

    The `stops` DataFrame returned has the following schema:
    ```
     #   Column           Dtype
    ---  ------           -----
     0   delta_occupancy  float64
     1   request_id       object
     2   state_duration   float64
     3   occupancy        float64
     4   location         float64
    ```

    The `requests` DataFrame returned has the following schema:

    ```
     #   Column                               Dtype
    ---  ------                               -----
     0   (accepted, delivery_timewindow_max)  float64
     1   (accepted, delivery_timewindow_min)  float64
     2   (accepted, destination)              float64
     3   (accepted, origin)                   float64
     4   (accepted, pickup_timewindow_max)    float64
     5   (accepted, pickup_timewindow_min)    float64
     6   (accepted, timestamp)                float64
     7   (inferred, relative_travel_time)     float64
     8   (inferred, travel_time)              float64
     9   (inferred, waiting_time)             float64
     10  (serviced, timestamp_dropoff)        float64
     11  (serviced, timestamp_pickup)         float64
     12  (serviced, vehicle_id)               float64
     13  (supplied, delivery_timewindow_max)  float64
     14  (supplied, delivery_timewindow_min)  int64
     15  (supplied, destination)              float64
     16  (supplied, direct_travel_distance)   float64
     17  (supplied, direct_travel_time)       float64
     18  (supplied, origin)                   float64
     19  (supplied, pickup_timewindow_max)    float64
     20  (supplied, pickup_timewindow_min)    int64
     21  (supplied, timestamp)                int64
    ```

    Parameters
    ----------
    events
        list of all the events returned by the simulation
    transportation_requests
        list of the transportation requests, optional
    space
        transportation space that was used for the simulations
    end_time
        time at which to presume the simulation has ended. currently this must
        not be smaller than the time at which the last stop was serviced, i.e. all
        stops and requests that were treated during the simulation are incorporated
        into the resulting dataframes. In the future there might be an option to discard
        everything that happened after a certain time, or even to select a specific time
        interval of the simulations for analytics.

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
        evs=events_df,
        transportation_requests=transportation_requests,
        stops=stops_df,
        space=space,
    )

    stops_df = _add_locations_to_stoplist_dataframe(reqs=requests_df, stops=stops_df)

    return stops_df, requests_df
