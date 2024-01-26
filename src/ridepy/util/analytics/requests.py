import pandas as pd


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
