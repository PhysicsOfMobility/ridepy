//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef THESIMULATOR_CDISPATCHERS_UTILS_H
#define THESIMULATOR_CDISPATCHERS_UTILS_H

#include "../../cdata_structures/cdata_structures.h"

namespace cstuff {
    template<typename Loc>
    std::vector<Stop<Loc>> insert_request_to_stoplist_drive_first(
            std::vector<Stop<Loc>> &stoplist,
            const Request<Loc> &request,
            int pickup_idx,
            int dropoff_idx,
            const TransportSpace<Loc> &space
    );

    template<typename Loc>
    void insert_stop_to_stoplist_drive_first(
            std::vector<Stop<Loc>> &stoplist,
            Stop<Loc> &stop,
            int idx,
            const TransportSpace<Loc> &space
    );

    template<typename Loc>
    double cpat_of_inserted_stop(Stop<Loc> &stop_before, double distance_from_stop_before);

    template<typename Loc>
    double distance_to_stop_after_insertion(
            const std::vector<Stop<Loc>> &stoplist, const Loc location, int index,
            const TransportSpace<Loc> &space
    );

    template<typename Loc>
    double distance_from_current_stop_to_next(
            const std::vector<Stop<Loc>> &stoplist, int i, const TransportSpace<Loc> &space
    );

    template<typename Loc>
    int is_timewindow_violated_dueto_insertion(
            const std::vector<Stop<Loc>> &stoplist, int idx, double est_arrival_first_stop_after_insertion
    );

    /* Now the implementations */
    template<typename Loc>
    std::vector<Stop<Loc>> insert_request_to_stoplist_drive_first(
            std::vector<Stop<Loc>> &stoplist,
            const Request<Loc> &request,
            int pickup_idx,
            int dropoff_idx,
            const TransportSpace<Loc> &space
    ) {
        /*
        Inserts a request into  a stoplist. The pickup(dropoff) is inserted *after* pickup(dropoff)_idx.
        The estimated arrival times at all the stops are updated assuming a drive-first strategy.
        */

        // We don't want to modify stoplist in place. Make a copy.
        std::vector<Stop<Loc>> new_stoplist{stoplist}; // TODO: NEED TO copy?
        // Handle the pickup
        auto &stop_before_pickup = new_stoplist[pickup_idx];
        auto cpat_at_pu = stop_before_pickup.estimated_departure_time() + space.d(
                stop_before_pickup.location, request.origin
        );
        Stop<Loc> pickup_stop(request.origin, request, StopAction::pickup, cpat_at_pu, request.pickup_timewindow_min,
                              request.pickup_timewindow_max);

        insert_stop_to_stoplist_drive_first(new_stoplist, pickup_stop, pickup_idx, space);
        // Handle the dropoff
        dropoff_idx += 1;
        auto &stop_before_dropoff = new_stoplist[dropoff_idx];
        auto cpat_at_do = stop_before_dropoff.estimated_departure_time() + space.d(
                stop_before_dropoff.location, request.destination
        );
        Stop<Loc> dropoff_stop(
                request.destination,
                request,
                StopAction::dropoff,
                cpat_at_do,
                request.delivery_timewindow_min,
                request.delivery_timewindow_max);
        insert_stop_to_stoplist_drive_first(new_stoplist, dropoff_stop, dropoff_idx, space);
        return new_stoplist;
    }

    template<typename Loc>
    void insert_stop_to_stoplist_drive_first(
            std::vector<Stop<Loc>> &stoplist,
            Stop<Loc> &stop,
            int idx,
            const TransportSpace<Loc> &space
    ) {
        /*
        Note: Modifies stoplist in-place. The passed stop has estimated_arrival_time set to None
        Args:
            stoplist:
            stop:
            idx:
            space:

        Returns:
        */
        auto &stop_before_insertion = stoplist[idx];
        // Stop later_stop
        // cdef double departure_previous_stop, cpat_next_stop,  delta_cpat_next_stop, old_departure, new_departure
        double distance_to_new_stop = space.d(stop_before_insertion.location, stop.location);
        double cpat_new_stop = cpat_of_inserted_stop(
                stop_before_insertion,
                distance_to_new_stop
        );
        stop.estimated_arrival_time = cpat_new_stop;
        if (idx < stoplist.size() - 1) {
            // update cpats of later stops
            auto departure_previous_stop = stop.estimated_departure_time();
            auto cpat_next_stop = departure_previous_stop + space.d(
                    stop.location, stoplist[idx + 1].location
            );
            auto delta_cpat_next_stop = cpat_next_stop - stoplist[idx + 1].estimated_arrival_time;
//        BOOST_FOREACH(auto later_stop, boost::make_iterator_range(stoplist.begin()+idx + 1, stoplist.end()))
            for (auto later_stop = stoplist.begin() + idx + 1; later_stop != stoplist.end(); ++later_stop) {
                auto old_departure = later_stop->estimated_departure_time();
                later_stop->estimated_arrival_time += delta_cpat_next_stop;
                auto new_departure = later_stop->estimated_departure_time();

                auto delta_cpat_next_stop = new_departure - old_departure;
                if (delta_cpat_next_stop == 0) break;
            }
        }
        stoplist.insert(stoplist.begin() + idx + 1, stop);
    }

    template<typename Loc>
    double cpat_of_inserted_stop(Stop<Loc> &stop_before, double distance_from_stop_before) {
        /*
        Note: Assumes drive first strategy.
        Args:
            stop_before:
            distance_from_stop_before:

        Returns:

        */
        return stop_before.estimated_departure_time() + distance_from_stop_before;
    }

    template<typename Loc>
    double distance_to_stop_after_insertion(
            const std::vector<Stop<Loc>> &stoplist, const Loc location, int index,
            const TransportSpace<Loc> &space
    ) {
        // note that index is *after which* the new stop will be inserted.
        // So index+1 is where the next stop is
        if (index < stoplist.size() - 1) return space.d(location, stoplist[index + 1].location);
        else return 0;
    }

    template<typename Loc>
    double distance_from_current_stop_to_next(
            const std::vector<Stop<Loc>> &stoplist, int i, const TransportSpace<Loc> &space
    ) {
        if (i < stoplist.size() - 1) return space.d(stoplist[i].location, stoplist[i + 1].location);
        else return 0;
    }

    template<typename Loc>
    int is_timewindow_violated_dueto_insertion(
            const std::vector<Stop<Loc>> &stoplist, int idx, double est_arrival_first_stop_after_insertion
    ) {
        /*
        Assumes drive first strategy.
        Args:
            stoplist:
            idx:
            est_arrival_first_stop_after_insertion:

        Returns:

        */
        // double delta_cpat, old_leeway, new_leeway, old_departure, new_departure
        if (idx >= stoplist.size() - 1) return false;
        auto delta_cpat = (
                est_arrival_first_stop_after_insertion
                - stoplist[idx].estimated_arrival_time
        );
//    BOOST_FOREACH(auto& stop, boost::make_iterator_range(stoplist.begin()+idx, stoplist.end()))
        for (auto stop = stoplist.begin() + idx; stop != stoplist.end(); ++stop) {
            auto old_leeway = stop->time_window_max - stop->estimated_arrival_time;
            auto new_leeway = old_leeway - delta_cpat;

            if ((new_leeway < 0) & (new_leeway < old_leeway)) return true;
            else {
                auto old_departure = max(stop->time_window_min, stop->estimated_arrival_time);
                auto new_departure = max(
                        stop->time_window_min, stop->estimated_arrival_time + delta_cpat
                );
                auto delta_cpat = new_departure - old_departure;
                if (delta_cpat == 0) {
                    // no need to check next stops
                    return false;
                }
            }
        }
        return false;
    }
}


#endif //THESIMULATOR_CDISPATCHERS_UTILS_H