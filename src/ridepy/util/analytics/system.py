import pandas as pd

from typing import Optional, Any, Union


def get_system_quantities(
    stops: pd.DataFrame,
    requests: pd.DataFrame,
    params: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Union[int, float]]:
    """
    Compute various quantities aggregated for the entire simulation.

    Currently, the following observables are returned (quantities in parentheses may not
    be returned if ``params`` is not given/``stops`` does not contain the respective
    quantities):

    - **(n_vehicles)** -- number of vehicles (simulation parameter)
    - **(request_rate)** -- request rate (simulation parameter)
    - **(velocity)** -- vehicle velocity (simulation parameter)
    - **(load_requested)** -- load requested (derived from request rate, velocity, and number of vehicles as input parameters and the spaces' average distance)
    - **(load_serviced)** -- load requested (derived from request rate times (1-rejection ratio), velocity, and number of vehicles as input parameters and the spaces' average distance)
    - **(avg_direct_dist_space)** -- average direct distance in space, computed by taking 1e5 random samples
    - **avg_occupancy**
    - **avg_segment_dist**
    - **avg_segment_time**
    - **total_dist_driven**
    - **total_time_driven**
    - **avg_direct_dist**
    - **avg_direct_time**
    - **total_direct_dist**
    - **total_direct_time**
    - **efficiency_dist**
    - **efficiency_time**
    - **avg_waiting_time**
    - **rejection_ratio**
    - **median_stoplist_length** -- median per-vehicle stoplist length, taken over all "stoplist states" (vehicles x time)
    - **median_stoplist_length** -- median per-vehicle stoplist length, taken over all "stoplist states" (vehicles x time)
    - **mean_system_stoplist_length** -- arithmetic mean system-wide stoplist length, taken over all "stoplist states" (time)
    - **mean_system_stoplist_length** -- arithmetic mean system-wide stoplist length, taken over all "stoplist states" (time)
    - **avg_detour**
    - **(avg_system_stoplist_length_service_time)**
    - **(avg_system_stoplist_length_submission_time)**
    - **(avg_stoplist_length_service_time)**
    - **(avg_stoplist_length_submission_time)**

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
    system_quantities
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
    stoplist_length_ensemble = (
        event_log["event_type"]
        .map(dict(submission=2, pickup=-1, dropoff=-1))
        .fillna(0)  # internal stops remain, incur no stoplist length delta
        .groupby(["vehicle_id", "timestamp"])
        .sum()  # merge state changes at same time
        .groupby("vehicle_id")
        .cumsum()  # integrate over stoplist length changes for each vehicle
    )

    median_stoplist_length = stoplist_length_ensemble.median()
    mean_stoplist_length = stoplist_length_ensemble.mean()

    system_stoplist_length_ensemble = (
        event_log.reset_index("vehicle_id", drop=True)
        .loc[:, "event_type"]
        .map(dict(submission=2, pickup=-1, dropoff=-1))
        .fillna(0)
        .sort_index()
        .groupby("timestamp")
        .sum()
        .cumsum()
    )

    median_system_stoplist_length = system_stoplist_length_ensemble.median()
    mean_system_stoplist_length = system_stoplist_length_ensemble.mean()

    avg_detour = requests["inferred", "relative_travel_time"].mean()

    res = {}

    if params:
        n_vehicles = params["general"]["n_vehicles"] or len(
            params["general"]["initial_locations"]
        )
        space = params["general"]["space"]
        request_rate = params["request_generator"].get("rate")
        velocity = space.velocity
        d_avg = (
            sum(
                [
                    space.d(space.random_point(), space.random_point())
                    for _ in range(100_000)
                ]
            )
            / 100_000
        )

        load_requested = d_avg * request_rate / (velocity * n_vehicles)
        load_serviced = (
            d_avg * request_rate * (1 - rejection_ratio) / (velocity * n_vehicles)
        )

        res |= dict(
            n_vehicles=n_vehicles,
            request_rate=request_rate,
            velocity=velocity,
            load_requested=load_requested,
            load_serviced=load_serviced,
            avg_direct_dist_space=d_avg,
        )

    res |= dict(
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
        mean_stoplist_length=mean_stoplist_length,
        median_system_stoplist_length=median_system_stoplist_length,
        mean_system_stoplist_length=mean_system_stoplist_length,
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

    return res
