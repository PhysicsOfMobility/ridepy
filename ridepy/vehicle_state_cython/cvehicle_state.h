//
// Created by Debsankha Manik on 02.07.21.
//

#ifndef RIDEPY_CVEHICLE_STATE_H
#define RIDEPY_CVEHICLE_STATE_H

#include "../data_structures_cython/cdata_structures.h"
#include "../util/spaces_cython/cspaces.h"
#include "../util/dispatchers_cython/cdispatchers.h"
#include <functional>
#include <memory>
#include <optional>
#include <tuple>
#include <utility>

using namespace std;
namespace cstuff {

struct StopEventSpec {
  StopAction action;
  int request_id;
  int vehicle_id;
  double timestamp;
};


enum class AvailableDispatcher {
  brute_force_total_traveltime_minimizing_dispatcher,
  simple_ellipse_dispatcher
};


template <typename Loc> class VehicleState {
  // private:

public:
  int vehicle_id;
  vector<Stop<Loc>> stoplist;
  int seat_capacity;
  AvailableDispatcher dispatcher;
  TransportSpace<Loc> &space;

  VehicleState(int vehicle_id, vector<Stop<Loc>> initial_stoplist,
               TransportSpace<Loc> &space,
               AvailableDispatcher desired_dispatcher, int seat_capacity)
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
    // logger.debug(f"Fast forwarding vehicle {self._vehicle_id} from MPI rank
    // {rank}")
    vector<StopEventSpec> event_cache;

    Stop<Loc> last_stop;
    bool any_stop_serviced{false};
    // drop all non-future stops from the stoplist, except for the (outdated)
    // CPE
    for (int i = stoplist.size() - 1; i > 0; --i) {
      auto &stop = stoplist[i];
      // service the stop at its estimated arrival time
      if (stop.estimated_arrival_time <= t) {
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
            {stop.action, stop.request->request_id, vehicle_id,
             max(stop.estimated_arrival_time, stop.time_window_min)});
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
    if (stoplist.size() > 1) {
      if (last_stop.estimated_arrival_time > t) {
        // still mid-jump from last interpolation, no need to interpolate
        // again
        1 == 1;
      } else {
        auto [loc, jump_time] =
            space.interp_time(last_stop.location, stoplist[1].location,
                              stoplist[1].estimated_arrival_time - t);
        stoplist[0].location = loc;
        // set CPE time
        stoplist[0].estimated_arrival_time = t + jump_time;
      }
    } else {
      // stoplist is empty, only CPE is there. set CPE time to current time
      stoplist[0].estimated_arrival_time = t;
    }
    return event_cache;
  }

  pair<int, InsertionResult<Loc>> handle_transportation_request_single_vehicle(
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
    // Logging the following in this specific format is crucial for
    // `test / mpi_futures_fleet_state_test.py` to pass
    // logger.debug(f "Handling request #{request.request_id} with vehicle
    // {self._vehicle_id} from MPI rank {rank}")
    switch(dispatcher){
      case AvailableDispatcher::
        brute_force_total_traveltime_minimizing_dispatcher:
        return make_pair(vehicle_id, brute_force_total_traveltime_minimizing_dispatcher(
            request, stoplist, space, seat_capacity));
      case AvailableDispatcher::
        simple_ellipse_dispatcher:
        return make_pair(vehicle_id, simple_ellipse_dispatcher(
            request, stoplist, space, seat_capacity));
    }
  }
};
} // namespace cstuff

#endif // RIDEPY_CVEHICLE_STATE_H