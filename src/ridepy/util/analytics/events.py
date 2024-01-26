from typing import Iterable, List

import pandas as pd

from ridepy.data_structures import TransportSpace
from ridepy.util.analytics.stops import (
    _create_stoplist_dataframe,
    _add_locations_to_stoplist_dataframe,
)
from ridepy.util.analytics.requests import _create_transportation_requests_dataframe


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

    # try:
    stops_df = _add_locations_to_stoplist_dataframe(
        reqs=requests_df, stops=stops_df, space=space
    )
    # stops_df = _add_insertion_stats_to_stoplist_dataframe(
    #     reqs=requests_df, stops=stops_df, space=space
    # )
    # except KeyError:  # TODO document this

    # pass

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
