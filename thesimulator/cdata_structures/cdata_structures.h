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

    class Request {
    public:
        int request_id;
        double creation_timestamp;
        R2loc origin;
        R2loc destination;
        double pickup_timewindow_min;
        double pickup_timewindow_max;
        double delivery_timewindow_min;
        double delivery_timewindow_max;

        Request();

        Request(
                int request_id,
                double creation_timestamp,
                R2loc origin,
                R2loc destination,
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

    class Stop {
    public:
        R2loc location;
        Request request;
        StopAction action;
        double estimated_arrival_time;
        double time_window_min;
        double time_window_max;

        Stop();

        Stop(
                R2loc loc, Request req, StopAction action, double estimated_arrival_time,
                double time_window_min, double time_window_max);

        double estimated_departure_time();
    };

    typedef vector<Stop> Stoplist;

    struct InsertionResult {
        Stoplist new_stoplist;
        double min_cost;
        double EAST_pu;
        double LAST_pu;
        double EAST_do;
        double LAST_do;
    };

}

#endif //THESIMULATOR_CDATA_STRUCTURES_H
