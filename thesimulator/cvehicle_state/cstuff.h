//
// Created by dmanik on 29.11.20.
//

#ifndef THESIMULATOR_CSTUFF_H
#define THESIMULATOR_CSTUFF_H

#include <utility> // for pair
#include <tuple>
#include <vector>
#include <algorithm>  // for max()
#include <cmath>
//#include <boost/foreach.hpp>
//#include <boost/range/iterator_range.hpp>
#include <random>
#include <chrono> // for benchmarking
#include <iostream>

using namespace std;

namespace cstuff {
    typedef pair<double, double> R2loc;


    enum class StopAction : uint32_t {
        pickup = 0,
        dropoff = 1,
        internal = 2
    };

    class Euclidean2D {
    public:
        double d(R2loc u, R2loc v) const;

        Euclidean2D();
    };

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

    void insert_stop_to_stoplist_drive_first(
            Stoplist &stoplist,
            Stop &stop,
            int idx,
            const Euclidean2D &space
    );

    Stoplist insert_request_to_stoplist_drive_first(
            Stoplist &stoplist,
            const Request &request,
            int pickup_idx,
            int dropoff_idx,
            const Euclidean2D &space
    );

    double cpat_of_inserted_stop(Stop &stop_before, double distance_from_stop_before);

    double distance_to_stop_after_insertion(
            const Stoplist &stoplist, const R2loc location, int index, const Euclidean2D &space
    );

    double distance_from_current_stop_to_next(
            const Stoplist &stoplist, int i, const Euclidean2D &space
    );

    int is_timewindow_violated_dueto_insertion(
            const Stoplist &stoplist, int idx, double est_arrival_first_stop_after_insertion
    );

    InsertionResult
    brute_force_distance_minimizing_dispatcher(
            const Request &request,
            Stoplist &stoplist,
            const Euclidean2D &space);

}
#endif
//THESIMULATOR_CSTUFF_H
