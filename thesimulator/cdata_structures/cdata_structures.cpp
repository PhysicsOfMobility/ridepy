//
// Created by Debsankha Manik on 13.12.20.
//

#include "cdata_structures.h"
namespace cstuff {
    template<typename Loc>
    Request<Loc>::Request() = default;

    template<typename Loc>
    Stop<Loc>::Stop() = default;

    template<typename Loc>
    Request<Loc>::Request(
            int request_id,
            double creation_timestamp,
            Loc origin,
            Loc destination,
            double pickup_timewindow_min,
            double pickup_timewindow_max,
            double delivery_timewindow_min,
            double delivery_timewindow_max
    ) :
            request_id{request_id},
            creation_timestamp{creation_timestamp},
            origin{origin},
            destination{destination},
            pickup_timewindow_min{pickup_timewindow_min},
            pickup_timewindow_max{pickup_timewindow_max},
            delivery_timewindow_min{delivery_timewindow_min},
            delivery_timewindow_max{delivery_timewindow_max} {}

    template<typename Loc>
    Stop<Loc>::Stop(
            Loc loc, Request<Loc> req, StopAction action, double estimated_arrival_time,
            double time_window_min, double time_window_max) :
            location{loc},
            request{req},
            action{action},
            estimated_arrival_time{estimated_arrival_time},
            time_window_min{time_window_min},
            time_window_max{time_window_max} {}

    template<typename Loc>
    double Stop<Loc>::estimated_departure_time() {
        return max(estimated_arrival_time, time_window_min);
    }
}