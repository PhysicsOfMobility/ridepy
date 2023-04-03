//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef RIDEPY_CDATA_STRUCTURES_H
#define RIDEPY_CDATA_STRUCTURES_H

#include <cmath>
#include <iostream>
#include <memory>
#include <tuple>
#include <utility> // for pair
#include <vector>

using namespace std;

namespace ridepy {

typedef pair<double, double> R2loc;

template <typename Loc> class Request {
public:
  int request_id;
  double creation_timestamp;

  Request(int request_id, double creation_timestamp)
      : request_id{request_id}, creation_timestamp{creation_timestamp} {};

  virtual ~Request() = default;
};

template <typename Loc> class TransportationRequest : public Request<Loc> {
public:
  Loc origin;
  Loc destination;
  double pickup_timewindow_min = 0;
  double pickup_timewindow_max = INFINITY;
  double delivery_timewindow_min = 0;
  double delivery_timewindow_max = INFINITY;

  TransportationRequest() = default;
  TransportationRequest(int request_id, double creation_timestamp, Loc origin,
                        Loc destination, double pickup_timewindow_min = 0,
                        double pickup_timewindow_max = INFINITY,
                        double delivery_timewindow_min = 0,
                        double delivery_timewindow_max = INFINITY)
      : Request<Loc>{request_id, creation_timestamp}, origin{origin},
        destination{destination}, pickup_timewindow_min{pickup_timewindow_min},
        pickup_timewindow_max{pickup_timewindow_max},
        delivery_timewindow_min{delivery_timewindow_min},
        delivery_timewindow_max{delivery_timewindow_max} {}
};

template <typename Loc> class InternalRequest : public Request<Loc> {
public:
  Loc location;

  InternalRequest() = default;
  InternalRequest(int request_id, double creation_timestamp, Loc location)
      : Request<Loc>{request_id, creation_timestamp}, location{location} {};
};

enum class StopAction : uint32_t { pickup = 0, dropoff = 1, internal = 2 };

template <typename Loc> class Stop {
public:
  Loc location;
  std::shared_ptr<Request<Loc>> request;
  StopAction action;
  double estimated_arrival_time;
  int occupancy_after_servicing;
  double time_window_min = 0;
  double time_window_max = INFINITY;

  Stop() = default;
  Stop(Loc loc, const std::shared_ptr<Request<Loc>> &req, StopAction action,
       double estimated_arrival_time, int occupancy_after_servicing,
       double time_window_min = 0, double time_window_max = INFINITY)
      : location{loc}, request{req}, action{action},
        estimated_arrival_time{estimated_arrival_time},
        occupancy_after_servicing{occupancy_after_servicing},
        time_window_min{time_window_min}, time_window_max{time_window_max} {}

  double estimated_departure_time() {
    return max(estimated_arrival_time, time_window_min);
  }
};

template <typename Loc> struct InsertionResult {
  using Stoplist = vector<Stop<Loc>>;
  Stoplist new_stoplist = vector<Stop<Loc>>(0);
  double min_cost = 0;
  double EAST_pu = 0;
  double LAST_pu = INFINITY;
  double EAST_do = 0;
  double LAST_do = INFINITY;
};

struct SingleVehicleSolution {
  int vehicle_id = 0;
  double min_cost = 0;
  double EAST_pu = 0;
  double LAST_pu = INFINITY;
  double EAST_do = 0;
  double LAST_do = INFINITY;
};

} // namespace ridepy

#endif // RIDEPY_CDATA_STRUCTURES_H
