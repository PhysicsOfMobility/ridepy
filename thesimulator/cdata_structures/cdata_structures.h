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
#include <memory>
#include "../util/cspaces/cspaces.h"

using namespace std;
namespace cstuff {
    typedef pair<double, double> R2loc;

    template<typename Loc>
    class Request {
    public:
        int request_id;
        double creation_timestamp;

        Request(
            int request_id,
            double creation_timestamp
            ) :
            request_id{request_id},
            creation_timestamp{creation_timestamp} {};

        virtual ~Request()=default;
    };

    template<typename Loc>
    class TransportationRequest: public Request<Loc> {
    public:
        Loc origin;
        Loc destination;
        double pickup_timewindow_min;
        double pickup_timewindow_max;
        double delivery_timewindow_min;
        double delivery_timewindow_max;

        TransportationRequest() = default;
        TransportationRequest(
            int request_id,
            double creation_timestamp,
            Loc origin,
            Loc destination,
            double pickup_timewindow_min,
            double pickup_timewindow_max,
            double delivery_timewindow_min,
            double delivery_timewindow_max
            ) :
            Request<Loc>{request_id, creation_timestamp},
            origin{origin},
            destination{destination},
            pickup_timewindow_min{pickup_timewindow_min},
            pickup_timewindow_max{pickup_timewindow_max},
            delivery_timewindow_min{delivery_timewindow_min},
            delivery_timewindow_max{delivery_timewindow_max} {}
    };

    template<typename Loc>
    class InternalRequest: public Request<Loc> {
    public:
        Loc location;

        InternalRequest() = default;
        InternalRequest(
            int request_id,
            double creation_timestamp,
            Loc location
            ) :
            Request<Loc>{request_id, creation_timestamp},
            location{location} {};
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
        std::shared_ptr<Request<Loc>> request;
        StopAction action;
        double estimated_arrival_time;
        double time_window_min;
        double time_window_max;

        Stop() = default;
        Stop(
            Loc loc, const std::shared_ptr<Request<Loc>>& req, StopAction action, double estimated_arrival_time,
            double time_window_min, double time_window_max) :
            location{loc},
            request{req},
            action{action},
            estimated_arrival_time{estimated_arrival_time},
            time_window_min{time_window_min},
            time_window_max{time_window_max} {}

        Stop(const Stop& a) :
            location{a.location},
            request{a.request},
            action{a.action},
            estimated_arrival_time{a.estimated_arrival_time},
            time_window_min{a.time_window_min},
            time_window_max{a.time_window_max}{}

        Stop& operator=(const Stop &other) {
            location = other.location;
            request.reset();
            request = other.request;
            action = other.action;
            estimated_arrival_time = other.estimated_arrival_time;
            time_window_min = other.time_window_min;
            time_window_max = other.time_window_max;

            return *this;
        }

        Stop(Stop&& a) :
            location{a.location},
            request{a.request},
            action{a.action},
            estimated_arrival_time{a.estimated_arrival_time},
            time_window_min{a.time_window_min},
            time_window_max{a.time_window_max}{
               a.request.reset();
        }

        Stop& operator=(Stop&& other){
            location = other.location;
            request.reset();
            request = other.request;
            other.request.reset();
            action = other.action;
            estimated_arrival_time = other.estimated_arrival_time;
            time_window_min = other.time_window_min;
            time_window_max = other.time_window_max;
            return *this;
        }

// "grab the elements" from a // now a has no elements

        double estimated_departure_time() {
            return max(estimated_arrival_time, time_window_min);
        }
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
}

#endif //THESIMULATOR_CDATA_STRUCTURES_H
