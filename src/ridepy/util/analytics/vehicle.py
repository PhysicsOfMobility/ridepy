import pandas as pd


def get_vehicle_quantities(stops: pd.DataFrame, requests: pd.DataFrame) -> pd.DataFrame:
    """
    Compute various quantities aggregated **per vehicle**.

    Currently, the following observables are returned:

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

    res = pd.DataFrame(
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
        )
    ).rename_axis("vehicle_id")

    if "system_stoplist_length_service_time" in stops:
        res["avg_system_stoplist_length_service_time"] = stops.groupby(
            "vehicle_id"
        ).apply(
            lambda gdf: (
                gdf["system_stoplist_length_service_time"] * gdf["state_duration"]
            ).sum()
            / gdf["state_duration"].sum()
        )
    if "system_stoplist_length_submission_time" in stops:
        res["avg_system_stoplist_length_submission_time"] = stops.groupby(
            "vehicle_id"
        ).apply(
            lambda gdf: (
                gdf["system_stoplist_length_submission_time"] * gdf["state_duration"]
            ).sum()
            / gdf["state_duration"].sum()
        )

    if "stoplist_length_service_time" in stops:
        res["avg_stoplist_length_service_time"] = stops.groupby("vehicle_id").apply(
            lambda gdf: (
                gdf["stoplist_length_service_time"] * gdf["state_duration"]
            ).sum()
            / gdf["state_duration"].sum()
        )

    if "stoplist_length_submission_time" in stops:
        res["avg_stoplist_length_submission_time"] = stops.groupby("vehicle_id").apply(
            lambda gdf: (
                gdf["stoplist_length_submission_time"] * gdf["state_duration"]
            ).sum()
            / gdf["state_duration"].sum()
        )

    return res
