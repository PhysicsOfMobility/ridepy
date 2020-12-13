//
// Created by Debsankha Manik on 13.12.20.
//

#include "cdata_structures.h"
namespace cstuff {
    Request::Request() = default;

    Stop::Stop() = default;

    Request::Request(
            int request_id,
            double creation_timestamp,
            pair<double, double> origin,
            pair<double, double> destination,
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

    Stop::Stop(
            R2loc loc, Request req, StopAction action, double estimated_arrival_time,
            double time_window_min, double time_window_max) :
            location{loc},
            request{req},
            action{action},
            estimated_arrival_time{estimated_arrival_time},
            time_window_min{time_window_min},
            time_window_max{time_window_max} {}

    double Stop::estimated_departure_time() {
        return max(estimated_arrival_time, time_window_min);
    }
}