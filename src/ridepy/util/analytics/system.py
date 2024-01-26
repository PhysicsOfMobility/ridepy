from typing import Optional, Any, Dict

import pandas as pd


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
            stops.reset_index().set_index(["vehicle_id", "timestamp"])[
                ["event_type", "request_id"]
            ],
            submission_events,
        ],
        axis="index",
    ).sort_index()

    # This computes the median stoplist length. The median is taken over all states
    # of all vehicles, all states weighted equally. State changes are incurred by
    # submission events, pickup stops, delivery stops and internal stops
    # (initial and final stops). State changes at the same timestamp are merged.
    # It assumes that the stoplist is ordered by timestamp.
    median_stoplist_length = (
        event_log["event_type"]
        .map(dict(submission=2, pickup=-1, dropoff=-1))
        .fillna(0)  # internal stops remain, incur no stoplist length delta
        .groupby(["vehicle_id", "timestamp"])
        .sum()  # merge state changes at same time
        .groupby("vehicle_id")
        .cumsum()  # integrate over stoplist length changes for each vehicle
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
        avg_waiting_time=avg_waiting_time,
        rejection_ratio=rejection_ratio,
        median_stoplist_length=median_stoplist_length,
        avg_detour=avg_detour,
    )

    _stops = stops.dropna(
        subset=[
            *(
                {
                    "system_stoplist_length_service_time",
                    "system_stoplist_length_submission_time",
                    "stoplist_length_service_time",
                    "stoplist_length_submission_time",
                }
                & set(stops)
            )
        ]
    )
    if "system_stoplist_length_service_time" in _stops:
        res["avg_system_stoplist_length_service_time"] = (
            _stops["system_stoplist_length_service_time"] * _stops["state_duration"]
        ).sum() / _stops["state_duration"].sum()

    if "system_stoplist_length_submission_time" in _stops:
        res["avg_system_stoplist_length_submission_time"] = (
            _stops["system_stoplist_length_submission_time"] * _stops["state_duration"]
        ).sum() / _stops["state_duration"].sum()

    if "stoplist_length_submission_time" in _stops:
        res["avg_stoplist_length_submission_time"] = (
            _stops["stoplist_length_submission_time"] * _stops["state_duration"]
        ).sum() / _stops["state_duration"].sum()

    if "stoplist_length_service_time" in _stops:
        res["avg_stoplist_length_service_time"] = (
            _stops["stoplist_length_service_time"] * _stops["state_duration"]
        ).sum() / _stops["state_duration"].sum()

    if params:
        res |= dict(
            n_vehicles=params["general"]["n_vehicles"]
            or len(params["general"]["initial_locations"]),
            request_rate=params["request_generator"].get("rate"),
            velocity=params["general"]["space"].velocity,
        )

    return res
