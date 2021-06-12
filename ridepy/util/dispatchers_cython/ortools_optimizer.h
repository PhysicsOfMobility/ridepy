//
// Created by dmanik on 04.06.21.
//

#ifndef DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H
#define DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H

#include "../../data_structures_cython/cdata_structures.h"
#include "../spaces_cython/cspaces.h"
#include "cdispatchers_utils.h"

#include "ortools/constraint_solver/routing.h"
#include "ortools/constraint_solver/routing_enums.pb.h"
#include "ortools/constraint_solver/routing_index_manager.h"
#include "ortools/constraint_solver/routing_parameters.h"

#include <algorithm> // std::binary_search, std::sort
#include <climits>
#include <limits>
#include <map>
#include <string>
#include <utility> // std::pair

using namespace operations_research;
using namespace std;
namespace cstuff {

int64_t rescale_time(double time, double resolution, double min_time) {
  if (isinf(time))
    return INT64_MAX;

  if (time - min_time > resolution * INT64_MAX)
    throw std::invalid_argument("cannot rescale time " + to_string(time));

  int64_t res = (time - min_time) / resolution;
  if ((time > 0) and (res == 0))
    throw std::invalid_argument("cannot rescale time " + to_string(time));
  return res;
}

template <typename Loc>
vector<vector<Stop<Loc>>>
optimize_stoplists(vector<vector<Stop<Loc>>> &stoplists,
                   TransportSpace<Loc> &space,
                   vector<int> &vehicle_capacities_inp, double current_time = 0,
                   double time_resolution = 1e-8) {
  if (stoplists.size() != vehicle_capacities_inp.size())
    throw std::invalid_argument(
        "stoplists and vehicle_capacities do not match in size");
  int num_vehicles = stoplists.size();
  // We will create the data structures needed to initialize the ortools routing
  // problem A flat list of all stops
  vector<Stop<Loc> *> all_stops;
  // A list of all timewindows
  vector<pair<int64_t, int64_t>> time_windows;
  //  a list of all pickup/dropoff index pairs
  map<int, pair<int, int>> pudo_idxpairs;
  // list of indices for the start locations
  vector<int> start_loc_idxs;
  // list of lists, contains the indices for the dropoff stops of the onboard
  // requests for each vehicle
  vector<vector<int>> onboard_requests_dropoff_idxs;
  // -1 for dropoffs, +1 for pickups
  vector<int> delta_load;
  vector<int64_t> vehicle_capacities(vehicle_capacities_inp.begin(),
                                     vehicle_capacities_inp.end());

  int flat_stop_idx{0};
  int vehicle_idx = 0;
  bool is_cpe_stop = false;
  bool delta_load_pushed_back = false;
  for (auto &stoplist : stoplists) {
    is_cpe_stop = true;
    onboard_requests_dropoff_idxs.emplace_back(vector<int>(0));
    for (Stop<Loc> &stop : stoplist) {
      delta_load_pushed_back = false;
      // note the index if cpe stop. ortools will need it soon
      all_stops.push_back(&stop);
      if (is_cpe_stop) {
        start_loc_idxs.push_back(flat_stop_idx);
        // Set delta_load at CPE equal to the number of onboard requests.
        delta_load.push_back(stop.occupancy_after_servicing);
        delta_load_pushed_back = true;
      }
      // record the time windows
      if (is_cpe_stop) {
        time_windows.push_back(
            make_pair(rescale_time(stop.estimated_arrival_time, time_resolution,
                                   current_time),
                      rescale_time(stop.estimated_arrival_time, time_resolution,
                                   current_time)));
      } else {
        time_windows.push_back(make_pair(
            rescale_time(stop.time_window_min, time_resolution, current_time),
            rescale_time(stop.time_window_max, time_resolution, current_time)));
      }
      // construct pu/do pairs
      if (stop.action == StopAction::pickup) {
        pudo_idxpairs[stop.request->request_id] =
            make_pair(int{flat_stop_idx}, int{-1});
        if (!delta_load_pushed_back)
          delta_load.push_back(1);
      } else {
        if (stop.action == StopAction::dropoff) {
          if (!delta_load_pushed_back)
            delta_load.push_back(-1);
          if (pudo_idxpairs.count(stop.request->request_id) == 0) {
            // this is an onboard request's dropoff
            onboard_requests_dropoff_idxs[vehicle_idx].push_back(flat_stop_idx);
          }
          // this dropoff is part of a PU/DO pair
          else
            pudo_idxpairs[stop.request->request_id].second = int{flat_stop_idx};
        } else if (!delta_load_pushed_back)
          delta_load.push_back(0);
      }
      flat_stop_idx++;
      is_cpe_stop = false;
    }
    vehicle_idx++;
  }

  // We do not explicitly create dummy end node. Just imagine it's there
  int end_loc_idx = flat_stop_idx;

  // Create Routing Index Manager
  RoutingIndexManager manager(
      all_stops.size() + 1, // number of all the stops in the system: We need
                            // one extra for the dummy end stop
      num_vehicles,         // number of vehicles
      vector<RoutingIndexManager::NodeIndex>(start_loc_idxs.begin(),
                                             start_loc_idxs.end()),
      vector<RoutingIndexManager::NodeIndex>(
          num_vehicles, RoutingIndexManager::NodeIndex{end_loc_idx}));

  // Create Routing Model.
  RoutingModel routing(manager);

  // Define a distance callback that returns 0 for the dummy end node.
  const int transit_callback_index = routing.RegisterTransitCallback(
      [&all_stops, &space, &end_loc_idx, &time_resolution, &current_time,
       &manager](int64_t from_index, int64_t to_index) -> int64_t {
        auto from_idx = manager.IndexToNode(from_index).value();
        auto to_idx = manager.IndexToNode(to_index).value();
        if ((from_idx == end_loc_idx) or (to_idx == end_loc_idx))
          return 0;
        // Convert from routing variable Index to time matrix NodeIndex
        return rescale_time(
            space.t(all_stops[from_idx]->location, all_stops[to_idx]->location),
            time_resolution, current_time);
      });

  // Define cost of each arc.
  routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index);

  // Add Time constraint.
  std::string time{"Time"};
  routing.AddDimension(transit_callback_index, // transit callback index
                       int64_t{INT64_MAX},     // allow waiting time
                       int64_t{INT64_MAX},     // maximum time per vehicle
                       false, // Don't force start cumul to zero
                       time);
  const RoutingDimension &time_dimension = routing.GetDimensionOrDie(time);

  // Add the time window constraints
  // - Maximum slack has to be chosen.
  // - Somehow tw constraints for the start node *must* be specified at the end.
  // Add time window constraints for each location except depot.
  for (int i = 1; i < all_stops.size(); ++i) {
    if (i == end_loc_idx or
        (binary_search(start_loc_idxs.begin(), start_loc_idxs.end(), i)))
      continue;
    int64_t index = manager.NodeToIndex(RoutingIndexManager::NodeIndex(i));
    time_dimension.CumulVar(index)->SetRange(time_windows[i].first,
                                             time_windows[i].second);
  }
  // Add time window constraints for each vehicle start node.
  for (int vehicle_idx = 0; vehicle_idx < num_vehicles; ++vehicle_idx) {
    int64_t index = routing.Start(vehicle_idx);
    auto start_loc_idx = start_loc_idxs[vehicle_idx];
    time_dimension.CumulVar(index)->SetRange(
        time_windows[start_loc_idx].first, time_windows[start_loc_idx].second);
  }

  // Force the dropoffs of the onboard requests to be served by the correct
  // vehicle.
  vehicle_idx = 0;
  for (auto onboard_requests_dropoff_idxs_one_vehicle =
           onboard_requests_dropoff_idxs.begin();
       onboard_requests_dropoff_idxs_one_vehicle !=
       onboard_requests_dropoff_idxs.end();
       ++onboard_requests_dropoff_idxs_one_vehicle, ++vehicle_idx) {
    for (auto &onboard_request_dropoff_idx :
         *onboard_requests_dropoff_idxs_one_vehicle) {
      int64_t index = manager.NodeToIndex(
          RoutingIndexManager::NodeIndex(onboard_request_dropoff_idx));
      routing.SetAllowedVehiclesForIndex(vector<int>(1, vehicle_idx), index);
    }
  }

  // Specify that dropoffs follow pickups.
  Solver *const solver = routing.solver();
  for (const auto &[request_id, pudo] : pudo_idxpairs) {
    int64_t pickup_index =
        manager.NodeToIndex(RoutingIndexManager::NodeIndex{pudo.first});
    int64_t delivery_index =
        manager.NodeToIndex(RoutingIndexManager::NodeIndex{pudo.second});
    routing.AddPickupAndDelivery(pickup_index, delivery_index);
    solver->AddConstraint(solver->MakeEquality(
        routing.VehicleVar(pickup_index), routing.VehicleVar(delivery_index)));
    solver->AddConstraint(
        solver->MakeLessOrEqual(time_dimension.CumulVar(pickup_index),
                                time_dimension.CumulVar(delivery_index)));
  }

  // Add Capacity constraints
  const int demand_callback_index = routing.RegisterUnaryTransitCallback(
      [&delta_load, &manager](int64_t from_index) -> int64_t {
        // Convert from routing variable Index to demand NodeIndex.
        int from_node = manager.IndexToNode(from_index).value();
        return delta_load[from_node];
      });
  routing.AddDimensionWithVehicleCapacity(
      demand_callback_index, // transit callback index
      int64_t{0},            // null capacity slack
      vehicle_capacities,    // vehicle maximum capacities
      true,                  // start cumul to zero
      "Capacity");

  // Instantiate route start and end times to produce feasible times.
  for (int i = 0; i < num_vehicles; ++i) {
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.Start(i)));
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.End(i)));
  }

  // Setting first solution heuristic.
  RoutingSearchParameters searchParameters = DefaultRoutingSearchParameters();
  searchParameters.set_first_solution_strategy(
      FirstSolutionStrategy::PATH_CHEAPEST_ARC);

  // Optional stuff: specify initial solution
  const Assignment *solution = routing.SolveWithParameters(searchParameters);

  if (solution == nullptr)
    throw std::runtime_error("ortools found no solution");

  // Now construct new stoplists from the solution
  vector<vector<Stop<Loc>>> new_stoplists(num_vehicles);
  for (vehicle_idx = 0; vehicle_idx < num_vehicles; ++vehicle_idx) {
    int64_t index = routing.Start(vehicle_idx);
    Stop<Loc> old_stop;
    is_cpe_stop = true;
    while (routing.IsEnd(index) == false) {
      int new_stop_idx_in_flat_vec = manager.IndexToNode(index).value();
      Stop<Loc> new_stop = *all_stops[new_stop_idx_in_flat_vec];

      if (not is_cpe_stop) {
        double traveltime_from_old_stop =
            space.t(old_stop.location, new_stop.location);
        new_stop.estimated_arrival_time =
            old_stop.estimated_departure_time() + traveltime_from_old_stop;
        new_stop.occupancy_after_servicing =
            old_stop.occupancy_after_servicing +
            delta_load[new_stop_idx_in_flat_vec];
      }

      new_stoplists[vehicle_idx].push_back(new_stop);
      index = solution->Value(routing.NextVar(index));
      is_cpe_stop = false;
      old_stop = new_stop;
    }
  }
  return new_stoplists;
}
} // namespace cstuff

#endif // DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H