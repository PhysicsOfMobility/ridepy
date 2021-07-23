# distutils: language = c++
# cython: linetrace=True


import numpy as np
cimport numpy as np
from ridepy.data_structures_cython import LocType

DTYPE = np.float
ctypedef np.float_t DTYPE_t

from ridepy.util.spaces_cython.spaces cimport TransportSpace
from ridepy.data_structures_cython.cdata_structures cimport R2loc


cdef np.ndarray _get_legs(int i_stop, np.ndarray lo, np.ndarray _loc, TransportSpace space):
    res = np.full(4, np.nan)
    [
        LEG1,
        LEG2,
        DIRECT,
        DETOUR,
    ] = range(4)

    l_sl = len(_loc)
    if i_stop == 0 == l_sl - 1:
        res[LEG1] = 0
        res[LEG2] = 0
        res[DIRECT] = 0
    elif i_stop == 0:
        res[LEG1] = 0
        if space.loc_type == LocType.R2LOC:
            res[LEG2] = space.d(lo, _loc[i_stop + 1])
        else:
            res[LEG2] = space.d(lo, _loc[i_stop + 1])
        res[DIRECT] = res[LEG1]
    elif i_stop == l_sl - 1:
        if space.loc_type == LocType.R2LOC:
            res[LEG1] = space.d(_loc[i_stop - 1], lo)
        else:
            res[LEG1] = space.d(_loc[i_stop - 1], lo)
        res[LEG2] = 0
        res[DIRECT] = res[LEG2]
    else:
        if space.loc_type == LocType.R2LOC:
            res[LEG1] = space.d(_loc[i_stop - 1], lo)
            res[LEG2] = space.d(lo, _loc[i_stop + 1])
        else:
            res[LEG1] = space.d(_loc[i_stop - 1], lo)
            res[LEG2] = space.d(lo, _loc[i_stop + 1])

        res[DIRECT] = space.d(
            _loc[i_stop - 1],
            _loc[i_stop + 1],
        )

    res[DETOUR] = res[LEG1] + res[LEG2] - res[DIRECT]

    return res


cdef int get_i_pu(np.ndarray sl, int rid):
    cdef int i = 0
    cdef int sl_len = len(sl)

    for i in range(sl_len):
        if sl[i] == rid:
            return i

    return -1


cdef int get_i_do(np.ndarray sl, int rid):
    cdef int i = 0
    cdef int sl_len = len(sl)

    for i in range(sl_len-1,-1,-1):
        if sl[i] == rid:
            return i

    return -1


cdef np.ndarray properties_at_stop(
        DTYPE_t t,
        DTYPE_t ts,
        bint pu,
        int rid,
        np.ndarray lo,
        np.ndarray stoplist,
        np.ndarray locations,
        TransportSpace space,
        bint system
):
    [
        VEHICLE_ID,
        STOP_ID,
        TIMESTAMP,
        DELTA_OCCUPANCY,
        REQUEST_ID,
        STATE_DURATION,
        OCCUPANCY,
        DIST_TO_NEXT,
        TIME_TO_NEXT,
        TIMESTAMP_SUBMITTED,
    ] = range(10)

    cdef int i = 0, j = 0, k = 0
    cdef int sl_len = len(stoplist)

    sl = np.empty((sl_len, 10))
    loc = np.empty((sl_len, 2)) # TODO loc type

    sl_s = np.empty((sl_len, 10))
    loc_s = np.empty((sl_len, 2)) # TODO loc type

    cdef double t_, ts_
    for i in range(sl_len):
        t_ = stoplist[i, TIMESTAMP]
        ts_ = stoplist[i, TIMESTAMP_SUBMITTED]

        if ts_ <= t <= t_:
            sl[j] = stoplist[i]
            loc[j] = locations[i]
            j += 1

        if ts_ <= ts <= t_:
            sl_s[k] = stoplist[i]
            loc_s[k] = locations[i]
            k += 1


    sl = sl[:j]
    loc = loc[:j]

    sl_s = sl_s[:k]
    loc_s = loc_s[:k]

    if pu:
        i_pu_sl = get_i_pu(sl[:, REQUEST_ID], rid)
        i_do_sl = get_i_do(sl[:, REQUEST_ID], rid)
        i_pu_sl_s = get_i_pu(sl_s[:, REQUEST_ID], rid)
        i_do_sl_s = get_i_do(sl_s[:, REQUEST_ID], rid)

        i_stop_sl = i_pu_sl
        i_stop_sl_s = i_pu_sl_s
    else:
        i_do_sl = get_i_do(sl[:, REQUEST_ID], rid)

        i_pu_sl_s = get_i_pu(sl_s[:, REQUEST_ID], rid)
        i_do_sl_s = get_i_do(sl_s[:, REQUEST_ID], rid)

        i_stop_sl = i_do_sl
        i_stop_sl_s = i_do_sl_s

    res = np.full(15, np.nan)

    [
        SL_LEN_S,
        SL_LEN,
        SEG_DIST_S,
        SEG_TIME_S,
        SEG_DIST,
        SEG_TIME,
        LEG1_S,
        LEG2_S,
        DIRECT_S,
        DETOUR_S,
        LEG1,
        LEG2,
        DIRECT,
        DETOUR,
        INSERTION_INDEX,
    ] = range(15)

    if not system:
        res[INSERTION_INDEX] = len(sl_s[sl_s[:, TIMESTAMP] < t])
        res[[LEG1, LEG2, DIRECT, DETOUR]] = _get_legs(i_stop_sl,lo, loc,  space)
        res[[LEG1_S, LEG2_S, DIRECT_S, DETOUR_S]] = _get_legs(i_stop_sl_s, lo, loc_s, space)

    if pu:
        sl = np.delete(sl, [i_pu_sl, i_do_sl], axis=0)
    else:
        sl = np.delete(sl, i_do_sl, axis=0)

    sl_s = np.delete(sl_s, [i_pu_sl_s, i_do_sl_s], axis=0)

    res[SL_LEN_S] = len(sl_s)
    res[SL_LEN] = len(sl)

    res[SEG_DIST_S] = np.mean(sl_s[:, DIST_TO_NEXT])
    res[SEG_TIME_S] = np.mean(sl_s[:, TIME_TO_NEXT])

    res[SEG_DIST] = np.mean(sl[:, DIST_TO_NEXT])
    res[SEG_TIME] = np.mean(sl[:, TIME_TO_NEXT])

    return res

cpdef np.ndarray stop_properties(
        np.ndarray stoplist,
        np.ndarray locations,
        TransportSpace space,
):

    [
        VEHICLE_ID,
        STOP_ID,
        TIMESTAMP,
        DELTA_OCCUPANCY,
        REQUEST_ID,
        STATE_DURATION,
        OCCUPANCY,
        DIST_TO_NEXT,
        TIME_TO_NEXT,
        TIMESTAMP_SUBMITTED,
    ] = range(10)

    cdef int n = len(stoplist)
    cdef np.ndarray res = np.full((n, 21), np.nan)
    cdef int i
    for i in range(n):
        res[i, :6] = properties_at_stop(
            stoplist[i, TIMESTAMP],
            stoplist[i, TIMESTAMP_SUBMITTED],
            stoplist[i, DELTA_OCCUPANCY] > 0,
            stoplist[i, REQUEST_ID],
            locations[i],
            stoplist,
            locations,
            space,
            True
        )[:6]

    cdef int vid
    for vid in np.unique(stoplist[:, VEHICLE_ID]):
        vehicle_mask = stoplist[:, VEHICLE_ID] == vid
        vsl = stoplist[vehicle_mask]
        vlc = locations[vehicle_mask]
        vres = np.full((len(vsl), 15), np.nan)
        for i in range(len(vsl)):
            vres[i] = properties_at_stop(
                vsl[i, TIMESTAMP],
                vsl[i, TIMESTAMP_SUBMITTED],
                vsl[i, DELTA_OCCUPANCY] > 0,
                vsl[i, REQUEST_ID],
                vlc[i],
                vsl,
                vlc,
                space,
                False
            )
        res[vehicle_mask, 6:] = vres

    return res













