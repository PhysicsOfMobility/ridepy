//
// Created by dmanik on 04.06.21.
//

#ifndef DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H
#define DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H

#include "ortools/constraint_solver/routing.h"
#include "ortools/constraint_solver/routing_enums.pb.h"
#include "ortools/constraint_solver/routing_index_manager.h"
#include "ortools/constraint_solver/routing_parameters.h"

#include "../../data_structures_cython/cdata_structures.h"
#include "../spaces_cython/cspaces.h"
#include "cdispatchers_utils.h"
#include <climits>
#include <utility>      // std::pair
#include <map>
#include <algorithm>    // std::binary_search, std::sort

using namespace operations_research;
using namespace std;
namespace cstuff {

template <typename Loc>
vector<vector<Stop<Loc>>> optimize_stoplists(vector<vector<Stop<Loc>>> &stoplists,
                   TransportSpace<Loc> &space, vector<int> &vehicle_capacities_inp)
{
  int num_vehicles = stoplists.size();
  // We will create the data structures needed to initialize the ortools routing problem A flat list of all stops
  vector<Stop<Loc>> all_stops;
  // A list of all timewindows
  vector<pair<double, double>> time_windows;
  //  a list of all pickup/dropoff index pairs
  map<int, pair<int, int>> pudo_idxpairs;
  // list of indices for the start locations
  vector<int> start_loc_idxs;
  // list of lists, contains the indices for the dropoff stops of the onboard requests for each vehicle
  vector<vector<int>> onboard_requests_dropoff_idxs;
  // -1 for dropoffs, +1 for pickups
  vector<int> delta_load;
  vector<int64_t> vehicle_capacities(vehicle_capacities_inp.begin(), vehicle_capacities_inp.end());


  int flat_stop_idx{0};
  int vehicle_idx = 0;
  bool is_cpe_stop = false;
  for (auto &stoplist : stoplists) {
    is_cpe_stop = true;
    onboard_requests_dropoff_idxs.emplace_back(vector<int>(0));
    for (Stop<Loc> &stop : stoplist) {
      // note the index if cpe stop. ortools will need it soon
      all_stops.push_back(stop);
      if (is_cpe_stop) {
        start_loc_idxs.push_back(flat_stop_idx);
        // Set delta_load at CPE equal to the number of onboard requests.
        delta_load.push_back(stop.occupancy_after_servicing);
      }
      is_cpe_stop = false;
      // record the time windows
      time_windows.push_back(
          make_pair(stop.time_window_min, stop.time_window_max));
      // construct pu/do pairs
      if (stop.action == StopAction::pickup) {
        pudo_idxpairs[stop.request->request_id] =
            make_pair(int{flat_stop_idx}, int{-1});
        delta_load.push_back(1);
      } else {
        if (stop.action == StopAction::dropoff) {
          delta_load.push_back(-1);
          if (pudo_idxpairs.count(stop.request->request_id) == 0) {
            // this is an onboard request's dropoff
            onboard_requests_dropoff_idxs[vehicle_idx].push_back(flat_stop_idx);
          }
          // this dropoff is part of a PU/DO pair
          else
            pudo_idxpairs[stop.request->request_id].second = int{flat_stop_idx};
        } else
          delta_load.push_back(0);
      }
      flat_stop_idx++;
    }
    vehicle_idx++;
  }

  // We do not explicitly create dummy end node. Just imagine it's there
  int end_loc_idx = flat_stop_idx;

  // Create Routing Index Manager
  RoutingIndexManager manager(
      all_stops.size() + 1, // number of all the stops in the system: We need one extra for the dummy end stop
      num_vehicles,     // number of vehicles
      vector<RoutingIndexManager::NodeIndex>(start_loc_idxs.begin(),
                                             start_loc_idxs.end()),
      vector<RoutingIndexManager::NodeIndex>(
          num_vehicles, RoutingIndexManager::NodeIndex{end_loc_idx}));

  // Create Routing Model.
  RoutingModel routing(manager);

  // Define a distance callback that returns 0 for the dummy end node.
  const int transit_callback_index = routing.RegisterTransitCallback(
      [&all_stops, &space, &end_loc_idx,
       &manager](int64_t from_index, int64_t to_index) -> int64_t {
        auto from_idx = manager.IndexToNode(from_index).value();
        auto to_idx = manager.IndexToNode(to_index).value();
        if ((from_idx == end_loc_idx) or (to_idx == end_loc_idx))
          return 0;
        // Convert from routing variable Index to time matrix NodeIndex
        return space.t(all_stops[from_idx].location,
                       all_stops[to_idx].location);
      });

  // Define cost of each arc.
  routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index);

  // Add Time constraint.
  std::string time{"Time"};
  routing.AddDimension(transit_callback_index, // transit callback index
                       int64_t{3000000},       // allow waiting time
                       int64_t{3000000},       // maximum time per vehicle
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

  // Force the dropoffs of the onboard requests to be served by the correct vehicle.
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

  // Now construct new stoplists from the solution
  vector<vector<Stop<Loc>>> new_stoplists(num_vehicles);
  for (int vehicle_idx = 0; vehicle_idx < num_vehicles; ++vehicle_idx) {
    int64_t index = routing.Start(vehicle_idx);
    while (routing.IsEnd(index) == false) {
      new_stoplists[vehicle_idx].push_back(all_stops[manager.IndexToNode(index).value()]);
      int64_t previous_index = index;
      index = solution->Value(routing.NextVar(index));
    }
  }
  return new_stoplists;
}
}// end ns cstuff

#endif // DEVEL_SIMULATOR_ORTOOLS_OPTIMIZER_H