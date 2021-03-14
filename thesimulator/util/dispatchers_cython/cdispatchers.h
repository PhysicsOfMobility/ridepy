//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef THESIMULATOR_CDISPATCHERS_H
#define THESIMULATOR_CDISPATCHERS_H

#include "../spaces_cython/cspaces.h"
#include "../../data_structures_cython/cdata_structures.h"
#include "cdispatchers_utils.h"
#include <climits>

using namespace std;
namespace cstuff {
    template<typename Loc>
    InsertionResult<Loc> brute_force_distance_minimizing_dispatcher(
            std::shared_ptr<TransportationRequest<Loc>> request,
            vector<Stop<Loc>> &stoplist,
            TransportSpace<Loc> &space,
            int seat_capacity
    ) {
        /*
        Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
        by minimizing the total driving distance.

        Parameters
        ----------
        request
            request to be serviced
        stoplist
            stoplist of the vehicle, to be mapped to a new stoplist
        space
            transport space the vehicle is operating on

        Returns
        -------

        */
        double min_cost = INFINITY;

        // Warning: i,j refers to the indices where the new stop would be inserted. So i-1/j-1 is the index of
        // the stop preceding the stop to be inserted.
        pair<int, int> best_insertion{0, 0};
        int i = -1;
        for (auto &stop_before_pickup: stoplist) {
            i++; // The first iteration of the loop: i = 0
            if (stop_before_pickup.occupancy_after_servicing == seat_capacity){
                // inserting here will violate capacity constraint
                continue;
            }
            // (new stop would be inserted at idx=1). Insertion at idx=0 impossible.
            auto distance_to_pickup = space.d(stop_before_pickup.location, request->origin);
            auto CPAT_pu = cpat_of_inserted_stop(stop_before_pickup, distance_to_pickup);
            // check for request's pickup timewindow violation
            if (CPAT_pu > request->pickup_timewindow_max) continue;
            auto EAST_pu = request->pickup_timewindow_min;

            // dropoff immediately
            auto CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request->origin, request->destination);
            auto EAST_do = request->delivery_timewindow_min;
            // check for request's dropoff timewindow violation
            if (CPAT_do > request->delivery_timewindow_max) continue;
            // compute the cost function
            auto distance_to_dropoff = space.d(request->origin, request->destination);
            auto distance_from_dropoff = distance_to_stop_after_insertion(
                    stoplist, request->destination, i, space
            );

            auto original_pickup_edge_length = distance_from_current_stop_to_next(
                    stoplist, i, space
            );
            auto total_cost = (
                    distance_to_pickup
                    + distance_to_dropoff
                    + distance_from_dropoff
                    - original_pickup_edge_length
            );
            if (total_cost < min_cost) {
                // check for constraint violations at later points
                auto cpat_at_next_stop =
                        max(CPAT_do, request->delivery_timewindow_min) + distance_from_dropoff;
                if (~is_timewindow_violated_dueto_insertion(
                        stoplist, i, cpat_at_next_stop)) {
                    best_insertion = {i, i};
                    min_cost = total_cost;
                }
            }
            // Try dropoff not immediately after pickup
            auto distance_from_pickup = distance_to_stop_after_insertion(
                    stoplist, request->origin, i, space);
            auto cpat_at_next_stop = (
                    max(CPAT_pu, request->pickup_timewindow_min) + distance_from_pickup
            );
            if (is_timewindow_violated_dueto_insertion(stoplist, i, cpat_at_next_stop)) continue;
            auto pickup_cost = (
                    distance_to_pickup + distance_from_pickup - original_pickup_edge_length
            );
            int j = i;
//        BOOST_FOREACH(auto stop_before_dropoff, boost::make_iterator_range(stoplist.begin()+i, stoplist.end()))
            for (auto stop_before_dropoff = stoplist.begin() + i + 1;
                 stop_before_dropoff != stoplist.end(); ++stop_before_dropoff) {
                j++; // first iteration: dropoff after j=(i+1)'th stop. pickup was after i'th stop.
                // Need to check for seat capacity constraints. Note the loop: the constraint was not violated after
                // servicing the previous stop (otherwise we wouldn't've reached this line). Need to check that the
                // constraint is not violated due to the action at this stop (stop_before_dropoff)
                if (stop_before_dropoff->occupancy_after_servicing == seat_capacity){
                    // Capacity is violated. We need to break off this loop because no insertion either here or at a later
                    // stop is permitted
                    break;
                }
                distance_to_dropoff = space.d(
                        stop_before_dropoff->location, request->destination
                );
                CPAT_do = cpat_of_inserted_stop(
                        *stop_before_dropoff,
                        +distance_to_dropoff
                );
                if (CPAT_do > request->delivery_timewindow_max) continue;
                distance_from_dropoff = distance_to_stop_after_insertion(
                        stoplist, request->destination, j, space
                );
                auto original_dropoff_edge_length = distance_from_current_stop_to_next(
                        stoplist, j, space
                );
                auto dropoff_cost = (
                        distance_to_dropoff
                        + distance_from_dropoff
                        - original_dropoff_edge_length
                );

                total_cost = pickup_cost + dropoff_cost;

                if (total_cost >= min_cost) continue;
                else {
                    // cost has decreased. check for constraint violations at later stops
                    cpat_at_next_stop = (
                            max(CPAT_do, request->delivery_timewindow_min)
                            + distance_from_dropoff
                    );
                    if (~is_timewindow_violated_dueto_insertion(
                            stoplist, j, cpat_at_next_stop)) {
                        best_insertion = {i, j};
                        min_cost = total_cost;
                    }
                }
            }
        }
        int best_pickup_idx = best_insertion.first;
        int best_dropoff_idx = best_insertion.second;
        // TODO: Compute occupancies in both new and old stops
        auto new_stoplist = insert_request_to_stoplist_drive_first(
                stoplist,
                request,
                best_pickup_idx,
                best_dropoff_idx,
                space
        );
        std::cout << "Best insertion: " << best_pickup_idx << ", " << best_dropoff_idx << std::endl;
        std::cout << "Min cost: " << min_cost << std::endl;
        auto EAST_pu = new_stoplist[best_pickup_idx + 1].time_window_min;
        auto LAST_pu = new_stoplist[best_pickup_idx + 1].time_window_max;

        auto EAST_do = new_stoplist[best_dropoff_idx + 2].time_window_min;
        auto LAST_do = new_stoplist[best_dropoff_idx + 2].time_window_max;
        return InsertionResult<Loc>{new_stoplist, min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do};
    }
}
#endif //THESIMULATOR_CDISPATCHERS_H
