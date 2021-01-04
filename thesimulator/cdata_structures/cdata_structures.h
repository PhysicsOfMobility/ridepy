//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef THESIMULATOR_CDATA_STRUCTURES_H
#define THESIMULATOR_CDATA_STRUCTURES_H

#include <utility> // for pair
#include <tuple>
#include <vector>
#include <cmath>
#include <iostream>
#include "../util/cspaces/cspaces.h"

using namespace std;
namespace cstuff {
    typedef pair<double, double> R2loc;

    template<typename Loc>
    class Request {
    public:
        int request_id;
        double creation_timestamp;
        Loc origin;
        Loc destination;
        double pickup_timewindow_min;
        double pickup_timewindow_max;
        double delivery_timewindow_min;
        double delivery_timewindow_max;

        Request();

        Request(
                int request_id,
                double creation_timestamp,
                Loc origin,
                Loc destination,
                double pickup_timewindow_min,
                double pickup_timewindow_max,
                double delivery_timewindow_min,
                double delivery_timewindow_max
        );
    };

    enum class StopAction : uint32_t {
        pickup = 0,
        dropoff = 1,
        internal = 2
    };

    template<typename Loc>
    class Stop {
    public:
        Loc location;
        Request<Loc> request;
        StopAction action;
        double estimated_arrival_time;
        double time_window_min;
        double time_window_max;

        Stop();

        Stop(
                Loc loc, Request<Loc> req, StopAction action, double estimated_arrival_time,
                double time_window_min, double time_window_max);

        double estimated_departure_time();
    };

    template<typename Loc>
    struct InsertionResult {
        using Stoplist = vector<Stop<Loc>>;
        Stoplist new_stoplist=vector<Stop<Loc>>(0) ;
        double min_cost=0;
        double EAST_pu=0;
        double LAST_pu=0;
        double EAST_do=0;
        double LAST_do=0;
    };
    //////////////////////////////////////////////////////
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

#endif //THESIMULATOR_CDATA_STRUCTURES_H
