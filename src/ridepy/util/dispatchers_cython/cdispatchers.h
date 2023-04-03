#ifndef RIDEPY_CDISPATCHERS_H
#define RIDEPY_CDISPATCHERS_H

#include "../../data_structures_cython/cdata_structures.h"
#include "../spaces_cython/cspaces.h"
#include "cdispatchers_utils.h"
#include <climits>

using namespace std;

namespace ridepy {

template <typename Loc>
InsertionResult<Loc> brute_force_total_traveltime_minimizing_dispatcher(
    std::shared_ptr<TransportationRequest<Loc>> request,
    vector<Stop<Loc>> &stoplist, TransportSpace<Loc> &space, int seat_capacity,
    bool debug = false) {
  /*
  Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
  by minimizing the total driving time.

  Parameters
  ----------
  request
      request to be serviced
  stoplist
      stoplist of the vehicle, to be mapped to a new stoplist
  space
      transport space the vehicle is operating on
  debug
    Print debug info

  Returns
  -------

  */
  double min_cost = INFINITY;

  // Warning: i,j refers to the indices where the new stop would be inserted. So
  // i-1/j-1 is the index of the stop preceding the stop to be inserted.
  pair<int, int> best_insertion{0, 0};
  int i = -1;
  for (auto &stop_before_pickup : stoplist) {
    i++; // The first iteration of the loop: i = 0
    if (stop_before_pickup.occupancy_after_servicing == seat_capacity) {
      // inserting here will violate capacity constraint
      continue;
    }
    // (new stop would be inserted at idx=1). Insertion at idx=0 impossible.
    auto time_to_pickup = space.t(stop_before_pickup.location, request->origin);
    auto CPAT_pu = cpat_of_inserted_stop(stop_before_pickup, time_to_pickup);
    // check for request's pickup timewindow violation
    if (CPAT_pu > request->pickup_timewindow_max)
      continue;
    auto EAST_pu = request->pickup_timewindow_min;

    // dropoff immediately
    auto CPAT_do =
        max(EAST_pu, CPAT_pu) + space.t(request->origin, request->destination);
    auto EAST_do = request->delivery_timewindow_min;
    // check for request's dropoff timewindow violation
    if (CPAT_do > request->delivery_timewindow_max)
      continue;
    // compute the cost function
    auto time_to_dropoff = space.t(request->origin, request->destination);
    auto time_from_dropoff =
        time_to_stop_after_insertion(stoplist, request->destination, i, space);

    auto original_pickup_edge_length =
        time_from_current_stop_to_next(stoplist, i, space);
    auto total_cost = (time_to_pickup + time_to_dropoff + time_from_dropoff -
                       original_pickup_edge_length);
    if (total_cost < min_cost) {
      // check for constraint violations at later points
      auto cpat_at_next_stop =
          max(CPAT_do, request->delivery_timewindow_min) + time_from_dropoff;
      if (!(is_timewindow_violated_dueto_insertion(stoplist, i,
                                                   cpat_at_next_stop))) {
        best_insertion = {i, i};
        min_cost = total_cost;
      }
    }
    // Try dropoff not immediately after pickup
    auto time_from_pickup =
        time_to_stop_after_insertion(stoplist, request->origin, i, space);
    auto cpat_at_next_stop =
        (max(CPAT_pu, request->pickup_timewindow_min) + time_from_pickup);
    if (is_timewindow_violated_dueto_insertion(stoplist, i, cpat_at_next_stop))
      continue;
    auto pickup_cost =
        (time_to_pickup + time_from_pickup - original_pickup_edge_length);

    double delta_cpat = 0;
    if (i < static_cast<int>(stoplist.size() - 1))
      delta_cpat = cpat_at_next_stop - stoplist[i + 1].estimated_arrival_time;

    int j = i;
    //        BOOST_FOREACH(auto stop_before_dropoff,
    //        boost::make_iterator_range(stoplist.begin()+i, stoplist.end()))
    for (auto stop_before_dropoff = stoplist.begin() + i + 1;
         stop_before_dropoff != stoplist.end(); ++stop_before_dropoff) {
      j++; // first iteration: dropoff after j=(i+1)'th stop. pickup was after
           // i'th stop.
      // Need to check for seat capacity constraints. Note the loop: the
      // constraint was not violated after servicing the previous stop
      // (otherwise we wouldn't've reached this line). Need to check that the
      // constraint is not violated due to the action at this stop
      // (stop_before_dropoff)
      if (stop_before_dropoff->occupancy_after_servicing == seat_capacity) {
        // Capacity is violated. We need to break off this loop because no
        // insertion either here or at a later stop is permitted
        break;
      }
      time_to_dropoff =
          space.t(stop_before_dropoff->location, request->destination);
      CPAT_do = cpat_of_inserted_stop(*stop_before_dropoff, time_to_dropoff,
                                      delta_cpat);
      if (CPAT_do > request->delivery_timewindow_max)
        break;
      time_from_dropoff = time_to_stop_after_insertion(
          stoplist, request->destination, j, space);
      auto original_dropoff_edge_length =
          time_from_current_stop_to_next(stoplist, j, space);
      auto dropoff_cost =
          (time_to_dropoff + time_from_dropoff - original_dropoff_edge_length);

      total_cost = pickup_cost + dropoff_cost;

      if (total_cost < min_cost) {
        // cost has decreased. check for constraint violations at later stops
        cpat_at_next_stop = (max(CPAT_do, request->delivery_timewindow_min) +
                             time_from_dropoff);
        if (!(is_timewindow_violated_dueto_insertion(stoplist, j,
                                                     cpat_at_next_stop))) {
          best_insertion = {i, j};
          min_cost = total_cost;
        }
      }

      // we will try inserting the dropoff at a later stop
      // the delta_cpat is important to compute correctly for the next stop, it
      // may have changed if we had any slack time at this one
      auto new_departure_time =
          max(stop_before_dropoff->estimated_arrival_time + delta_cpat,
              stop_before_dropoff->time_window_min);
      delta_cpat =
          new_departure_time - stop_before_dropoff->estimated_departure_time();
    }
  }
  if (min_cost < INFINITY) {
    int best_pickup_idx = best_insertion.first;
    int best_dropoff_idx = best_insertion.second;

    //    if (request->request_id == 2.) {
    //        {
    //        cout << "C++ DEBUG: best insertion @ (" << best_pickup_idx << ", "
    //        << best_dropoff_idx << ")\n"; cout <<
    //        stoplist[0].estimated_arrival_time << endl; cout <<
    //        stoplist[0].location << endl; cout << request->creation_timestamp
    //        << endl << endl;
    //
    //        }

    auto new_stoplist = insert_request_to_stoplist_drive_first(
        stoplist, request, best_pickup_idx, best_dropoff_idx, space);
    if (debug) {
      std::cout << "Best insertion: " << best_pickup_idx << ", "
                << best_dropoff_idx << std::endl;
      std::cout << "Min cost: " << min_cost << std::endl;
    }
    auto EAST_pu = new_stoplist[best_pickup_idx + 1].time_window_min;
    auto LAST_pu = new_stoplist[best_pickup_idx + 1].time_window_max;

    auto EAST_do = new_stoplist[best_dropoff_idx + 2].time_window_min;
    auto LAST_do = new_stoplist[best_dropoff_idx + 2].time_window_max;
    return InsertionResult<Loc>{new_stoplist, min_cost, EAST_pu,
                                LAST_pu,      EAST_do,  LAST_do};
  } else {
    return InsertionResult<Loc>{{}, min_cost, NAN, NAN, NAN, NAN};
  }
}

template <typename Loc>
InsertionResult<Loc>
simple_ellipse_dispatcher(std::shared_ptr<TransportationRequest<Loc>> request,
                          vector<Stop<Loc>> &stoplist,
                          TransportSpace<Loc> &space, int seat_capacity,
                          double max_relative_detour = 0, bool debug = false) {
  /*
  Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
  according to the process described in https://arxiv.org/abs/2001.09711

  Note that this dispatcher disregards stops' and requests' time windows.
  Capacity constraints *are* honored.

  Insertions for which neither pickup nor dropoff are appended use no
  explicit cost function. The first insertion that violates no constraints will
  be chosen, and zero cost will be returned. In case either the dropoff or both
  pickup and dropoff have to be appended, the returned cost is the extra
  traveltime that is incurred, the time from the previous last stop to the
  dropoff.

  Parameters
  ----------
  request
      request to be serviced
  stoplist
      stoplist of the vehicle, to be mapped to a new stoplist
  space
      transport space the vehicle is operating on
  max_relative_detour

    For a single new stop ``x`` to be inserted between ``(u,v)``,
    the following constraint must be fulfilled:
    ``(d(u,x) + d(x, v)) / d(u,v) - 1 <= max_relative_detour``

    For an adjacent insertion of ``(x,y)`` in-between ``(u,v)`` the
    aforementioned criterion is applied successively:
    ``((d(u,x) + d(x, v)) / d(u,v) - 1 <= max_relative_detour) /\  ((d(x,y) +
  d(y, v)) / d(x,v) - 1 <= max_relative_detour)``

  Returns
  -------

  */
  double min_cost = INFINITY;
  bool insertion_found = false;

  auto relative_detour = [](auto absolute_detour,
                            auto original_edge_length) -> double {
    if (absolute_detour == 0)
      return 0;
    else if (original_edge_length == 0)
      INFINITY;
    else
      return absolute_detour / original_edge_length;
  };

  // Warning: i,j refers to the indices where the new stop would be inserted. So
  // i-1/j-1 is the index of the stop preceding the stop to be inserted.
  pair<int, int> best_insertion{0, 0};
  int i = -1;
  for (auto stop_before_pickup = stoplist.begin();
       stop_before_pickup != stoplist.end() - 1; ++stop_before_pickup) {
    i++; // The first iteration of the loop: i = 0
    // (new stop would be inserted at idx=1). Insertion at idx=0 impossible.

    if (stop_before_pickup->occupancy_after_servicing == seat_capacity) {
      // inserting here will violate capacity constraint
      continue;
    }

    auto time_to_pickup =
        space.t(stop_before_pickup->location, request->origin);
    auto time_from_pickup =
        time_to_stop_after_insertion(stoplist, request->origin, i, space);
    auto original_pickup_edge_length =
        time_from_current_stop_to_next(stoplist, i, space);

    auto pickup_absolute_detour =
        time_to_pickup + time_from_pickup - original_pickup_edge_length;

    if (relative_detour(pickup_absolute_detour, original_pickup_edge_length) >
        max_relative_detour)
      continue;

    // an valid pickup has been found
    // try dropoff immediately
    auto time_to_dropoff = space.t(request->origin, request->destination);
    auto time_from_dropoff =
        time_to_stop_after_insertion(stoplist, request->destination, i, space);

    auto dropoff_absolute_detour =
        time_to_dropoff + time_from_dropoff - time_from_pickup;

    if (relative_detour(dropoff_absolute_detour, time_from_pickup) <=
        max_relative_detour) {
      // found an insertion, stop looking
      best_insertion = {i, i};
      min_cost = 0;
      insertion_found = true;
      break;
    }
    // have to try dropoff not immediately after pickup
    int j = i;
    for (auto stop_before_dropoff = stoplist.begin() + i + 1;
         stop_before_dropoff != stoplist.end() - 1; ++stop_before_dropoff) {
      j++; // first iteration: dropoff after j=(i+1)'th stop. pickup was after
           // i'th stop.
      // Need to check for seat capacity constraints. Note the loop: the
      // constraint was not violated after servicing the previous stop
      // (otherwise we wouldn't've reached this line). Need to check that the
      // constraint is not violated due to the action at this stop
      // (stop_before_dropoff)

      if (stop_before_dropoff->occupancy_after_servicing == seat_capacity) {
        // Capacity is violated. We need to break off this loop because no
        // insertion either here or at a later stop is permitted
        break;
      }

      time_to_dropoff =
          space.t(stop_before_dropoff->location, request->destination);
      time_from_dropoff = time_to_stop_after_insertion(
          stoplist, request->destination, j, space);
      auto original_dropoff_edge_length =
          time_from_current_stop_to_next(stoplist, j, space);
      dropoff_absolute_detour =
          time_to_dropoff + time_from_dropoff - original_dropoff_edge_length;

      if (relative_detour(dropoff_absolute_detour,
                          original_dropoff_edge_length) > max_relative_detour)
        continue;
      else {
        best_insertion = {i, j};
        min_cost = 0;
        insertion_found = true;
        break;
      }
    }
    if (insertion_found == true)
      break;
    else {
      // dropoff has to be appended
      j = stoplist.size() - 1;
      time_to_dropoff = space.t(stoplist[j].location, request->destination);
      best_insertion = {i, j}; // will be inserted after LEN-1'th stop
      min_cost = time_to_dropoff;
      insertion_found = true;
      break;
    }
  }
  if (insertion_found == false) {
    // both pickup and dropoff have to be appended
    i = stoplist.size() - 1;
    min_cost = space.t(stoplist[i].location, request->origin) +
               space.t(request->origin, request->destination);
    best_insertion = {i, i}; // will be inserted after LEN-1'th stop
  }

  if (min_cost < INFINITY) {
    int best_pickup_idx = best_insertion.first;
    int best_dropoff_idx = best_insertion.second;
    auto new_stoplist = insert_request_to_stoplist_drive_first(
        stoplist, request, best_pickup_idx, best_dropoff_idx, space);
    if (debug) {
      std::cout << "Best insertion: " << best_pickup_idx << ", "
                << best_dropoff_idx << std::endl;
      std::cout << "Min cost: " << min_cost << std::endl;
    }
    auto EAST_pu = new_stoplist[best_pickup_idx + 1].time_window_min;
    auto LAST_pu = new_stoplist[best_pickup_idx + 1].time_window_max;

    auto EAST_do = new_stoplist[best_dropoff_idx + 2].time_window_min;
    auto LAST_do = new_stoplist[best_dropoff_idx + 2].time_window_max;
    return InsertionResult<Loc>{new_stoplist, min_cost, EAST_pu,
                                LAST_pu,      EAST_do,  LAST_do};
  } else {
    return InsertionResult<Loc>{{}, min_cost, NAN, NAN, NAN, NAN};
  }
}

template <typename Loc> class AbstractDispatcher {
public:
  virtual InsertionResult<Loc>
  operator()(std::shared_ptr<TransportationRequest<Loc>> request,
             vector<Stop<Loc>> &stoplist, TransportSpace<Loc> &space,
             int seat_capacity, bool debug = false) = 0;
  virtual ~AbstractDispatcher(){};
};

// Pattern motivated by: https://stackoverflow.com/a/2592270

template <typename Loc>
class BruteForceTotalTravelTimeMinimizingDispatcher
    : public AbstractDispatcher<Loc> {
public:
  InsertionResult<Loc>
  operator()(std::shared_ptr<TransportationRequest<Loc>> request,
             vector<Stop<Loc>> &stoplist, TransportSpace<Loc> &space,
             int seat_capacity, bool debug = false) {
    return brute_force_total_traveltime_minimizing_dispatcher(
        request, stoplist, space, seat_capacity, debug);
  }
};

template <typename Loc>
class SimpleEllipseDispatcher : public AbstractDispatcher<Loc> {
public:
  double max_relative_detour;
  SimpleEllipseDispatcher(double max_relative_detour = 0) {
    this->max_relative_detour = max_relative_detour;
  }
  InsertionResult<Loc>
  operator()(std::shared_ptr<TransportationRequest<Loc>> request,
             vector<Stop<Loc>> &stoplist, TransportSpace<Loc> &space,
             int seat_capacity, bool debug = false) {
    return simple_ellipse_dispatcher(request, stoplist, space, seat_capacity,
                                     max_relative_detour, debug);
  }
};

} // namespace ridepy

#endif // RIDEPY_CDISPATCHERS_H
