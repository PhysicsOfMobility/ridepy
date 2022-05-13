//
// Created by Debsankha Manik on 02.07.21.
//

#ifndef RIDEPY_CVEHICLE_STATE_H
#define RIDEPY_CVEHICLE_STATE_H

#include "../data_structures_cython/cdata_structures.h"
#include "../util/dispatchers_cython/cdispatchers.h"
#include "../util/spaces_cython/cspaces.h"
#include <functional>
#include <memory>
#include <optional>
#include <tuple>
#include <utility>

using namespace std;

namespace ridepy {

struct StopEventSpec {
  StopAction action;
  int request_id;
  int vehicle_id;
  double timestamp;
};

template <typename Loc> class VehicleState {
  // private:

public:
  int vehicle_id;
  vector<Stop<Loc>> stoplist;
  vector<Stop<Loc>> stoplist_new;
  int seat_capacity;
  AbstractDispatcher<Loc> &dispatcher;
  TransportSpace<Loc> &space;

  VehicleState(int vehicle_id, vector<Stop<Loc>> initial_stoplist,
               TransportSpace<Loc> &space,
               AbstractDispatcher<Loc> &desired_dispatcher, int seat_capacity)
      : vehicle_id{vehicle_id}, stoplist{initial_stoplist},
        seat_capacity{seat_capacity}, space{space}, dispatcher{
                                                        desired_dispatcher} {}

  ~VehicleState() {}

  vector<StopEventSpec> fast_forward_time(double t) {
    /*
    Update the vehicle_state to the simulator time `t`.

    Parameters
    ----------
    t
        time to be updated to

    Returns
    -------
    events
        List of stop events emitted through servicing stops upto time=t
    new_stoplist
        Stoplist remaining after servicing the stops upto time=t
    */
    // TODO assert that the CPATs are updated and the stops sorted accordingly
    // TODO optionally validate the travel time velocity constraints
    vector<StopEventSpec> event_cache;

    // Here, last_stop refers to the stop with the largest departure time value
    // smaller or equal than t. This can either be the last stop in the stoplist
    // that is serviced here, or it can be the (possibly outdated) CPE stop, of
    // no other stop is serviced.
    Stop<Loc> last_stop;

    bool any_stop_serviced{false};
    // drop all non-future stops from the stoplist, except for the (outdated)
    // CPE
    for (int i = stoplist.size() - 1; i > 0; --i) {
      auto &stop = stoplist[i];
      auto service_time =
          max(stop.estimated_arrival_time, stop.time_window_min);

      // service the stop at its estimated arrival time
      if (service_time <= t) {
        // as we are iterating backwards, the first stop iterated over is the
        // last one serviced
        if (not any_stop_serviced) {
          // this deepcopy is necessary because otherwise after removing
          // elements from stoplist, last_stop will point to the wrong
          // element. See the failing test as well:
          // test.test_data_structures_cython.test_stoplist_getitem_and_elem_removal_consistent
          last_stop = stop;
          any_stop_serviced = true;
        }
        event_cache.push_back(
            {stop.action, stop.request->request_id, vehicle_id, service_time});
        stoplist.erase(stoplist.begin() + i);
      }
    }

    // fix event cache order
    reverse(event_cache.begin(), event_cache.end());

    // if no stop was serviced, the last stop is the outdated CPE
    if (not any_stop_serviced)
      last_stop = stoplist[0];

    // set the occupancy at CPE
    stoplist[0].occupancy_after_servicing = last_stop.occupancy_after_servicing;

    // set CPE location to current location as inferred from the time delta to
    // the upcoming stop's CPAT
    // still mid-jump from last interpolation, no need to interpolate
    // again
    if (stoplist[0].estimated_arrival_time <= t) {
      if (stoplist.size() > 1) {
        auto [loc, jump_time] =
            space.interp_time(last_stop.location, stoplist[1].location,
                              stoplist[1].estimated_arrival_time - t);
        stoplist[0].location = loc;
        // set CPE time
        stoplist[0].estimated_arrival_time = t + jump_time;
      } else {
        // Stoplist is (now) empty, only CPE is there. Set CPE time to
        // current time and move CPE to last_stop's location (which is
        // identical to CPE, if we haven't served anything.
        stoplist[0].location = last_stop.location;
        stoplist[0].estimated_arrival_time = t;
      }
    }
    return event_cache;
  }

  SingleVehicleSolution handle_transportation_request_single_vehicle(
      std::shared_ptr<TransportationRequest<Loc>> request) {
    /*
    The computational bottleneck. An efficient simulator could:
    1. Parallelize this over all vehicles. This function being without any side
    effects, it should be easy to do.

    Parameters
    ----------
    request
      Request to be handled.

    Returns
    -------
    The `SingleVehicleSolution` for the respective vehicle.
    */
    InsertionResult<Loc> insertion_result =
        dispatcher(request, stoplist, space, seat_capacity);
    stoplist_new = insertion_result.new_stoplist;
    SingleVehicleSolution single_vehicle_solution{vehicle_id,
                                                  insertion_result.min_cost,
                                                  insertion_result.EAST_pu,
                                                  insertion_result.LAST_pu,
                                                  insertion_result.EAST_do,
                                                  insertion_result.LAST_do};
    return single_vehicle_solution;
  }

  void select_new_stoplist() { stoplist = stoplist_new; }
};

} // namespace ridepy

#endif // RIDEPY_CVEHICLE_STATE_H
