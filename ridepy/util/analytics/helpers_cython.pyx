import numpy as np

cpdef stop_properties(stop, full_sl, scope):
    lo = stop["location"]

    stop = stop[
        [
            "timestamp",
            "delta_occupancy",
            "request_id",
            "state_duration",
            "occupancy",
            "dist_to_next",
            "time_to_next",
            "timestamp_submitted",
        ]
    ].to_numpy(dtype="f8")

    locations = np.array(full_sl["location"].to_list())

    full_sl = full_sl[
        [
            "timestamp",
            "delta_occupancy",
            "request_id",
            "state_duration",
            "occupancy",
            "dist_to_next",
            "time_to_next",
            "timestamp_submitted",
        ]
    ].to_numpy(dtype="f8")

    [
        TIMESTAMP,
        DELTA_OCCUPANCY,
        REQUEST_ID,
        STATE_DURATION,
        OCCUPANCY,
        DIST_TO_NEXT,
        TIME_TO_NEXT,
        TIMESTAMP_SUBMITTED,
    ] = range(8)

    t = stop[TIMESTAMP]
    ts = stop[TIMESTAMP_SUBMITTED]
    pu = True if stop[DELTA_OCCUPANCY] > 0 else False
    rid = stop[REQUEST_ID]

    get_i_pu = lambda _sl, rid: np.argmax(_sl[:, REQUEST_ID] == rid)
    get_i_do = (
        lambda _sl, rid: len(_sl) - np.argmax((_sl[:, REQUEST_ID] == rid)[::-1]) - 1
    )

    mask = (full_sl[:, TIMESTAMP_SUBMITTED] <= t) & (t <= full_sl[:, TIMESTAMP])
    sl = full_sl[mask]
    loc = locations[mask]

    mask_s = (full_sl[:, TIMESTAMP_SUBMITTED] <= ts) & (ts <= full_sl[:, TIMESTAMP])
    sl_s = full_sl[mask_s]
    loc_s = locations[mask_s]

    if pu:
        i_pu_sl = get_i_pu(sl, rid)
        i_do_sl = get_i_do(sl, rid)
        i_pu_sl_s = get_i_pu(sl_s, rid)
        i_do_sl_s = get_i_do(sl_s, rid)

        i_stop_sl = i_pu_sl
        i_stop_sl_s = i_pu_sl_s
    else:
        i_do_sl = get_i_do(sl, rid)

        i_pu_sl_s = get_i_pu(sl_s, rid)
        i_do_sl_s = get_i_do(sl_s, rid)

        i_stop_sl = i_do_sl
        i_stop_sl_s = i_do_sl_s

    res = {}

    if scope != "system":
        res["insertion_index"] = len(sl_s[sl_s[:, TIMESTAMP] < t])

        def _get_legs(i_stop, _loc, time_desc):
            l_sl = len(_loc)
            if i_stop == 0 == l_sl - 1:
                stop_leg_1 = 0
                stop_leg_2 = 0
                stop_leg_d = 0
            elif i_stop == 0:
                stop_leg_1 = 0
                stop_leg_2 = space.d(lo, _loc[i_stop + 1])
                stop_leg_d = stop_leg_1
            elif i_stop == l_sl - 1:
                stop_leg_1 = space.d(_loc[i_stop - 1], lo)
                stop_leg_2 = 0
                stop_leg_d = stop_leg_2
            else:
                stop_leg_1 = space.d(_loc[i_stop - 1], lo)
                stop_leg_2 = space.d(lo, _loc[i_stop + 1])
                stop_leg_d = space.d(
                    _loc[i_stop - 1],
                    _loc[i_stop + 1],
                )

            stop_detour = stop_leg_1 + stop_leg_2 - stop_leg_d

            return {
                f"leg_1_dist_{time_desc}_time": stop_leg_1,
                f"leg_2_dist_{time_desc}_time": stop_leg_2,
                f"leg_direct_dist_{time_desc}_time": stop_leg_d,
                f"detour_dist_{time_desc}_time": stop_detour,
            }

        res |= _get_legs(i_stop_sl, loc, "service")
        res |= _get_legs(i_stop_sl_s, loc_s, "submission")

    if pu:
        sl = np.delete(sl, [i_pu_sl, i_do_sl], axis=0)
    else:
        sl = np.delete(sl, i_do_sl, axis=0)

    sl_s = np.delete(sl_s, [i_pu_sl_s, i_do_sl_s], axis=0)

    res[
        f"{'system_' if scope=='system' else ''}stoplist_length_submission_time"
    ] = len(sl_s)
    res[
        f"{'system_' if scope=='system' else ''}stoplist_length_service_time"
    ] = len(sl)

    res[
        f"avg_{'system_' if scope=='system' else ''}segment_dist_submission_time"
    ] = np.mean(sl_s[:, DIST_TO_NEXT])
    res[
        f"avg_{'system_' if scope=='system' else ''}segment_time_submission_time"
    ] = np.mean(sl_s[:, TIME_TO_NEXT])

    res[
        f"avg_{'system_' if scope=='system' else ''}segment_dist_service_time"
    ] = np.mean(sl[:, DIST_TO_NEXT])
    res[
        f"avg_{'system_' if scope=='system' else ''}segment_time_service_time"
    ] = np.mean(sl[:, TIME_TO_NEXT])

    return res
