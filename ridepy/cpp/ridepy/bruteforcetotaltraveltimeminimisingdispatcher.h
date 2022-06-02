#ifndef BRUTEFORCETOTALTRAVELTIMEMINIMISINGDISPATCHER_H
#define BRUTEFORCETOTALTRAVELTIMEMINIMISINGDISPATCHER_H

#include "abstractdispatcher.h"
#include <cmath>
using std::max;

namespace ridepy {

template<typename Loc>
class BruteForceTotalTravelTimeMinimizingDispatcher : public AbstractDispatcher<Loc>
{
public:
    InsertionResult<Loc> operator ()(const TransportationRequest<Loc> &request, const StopList<Loc> &stoplist, TransportSpace<Loc> &space, int seat_capacity){
        double min_cost = INFINITY;
        std::pair<int, int> best_insertion = {0, 0};

        const int n_stops = stoplist.size();
        for (int i = 0; i< n_stops; i++){
            const Stop<Loc> &stop_before_pickup = stoplist.at(i);

            // skip this stop if vehicle is already fully occupied
            if (stop_before_pickup.occupancy_after_servicing == seat_capacity)
                continue;

            // determine driving time from this stop to the pickup location
            const double time_to_pickup = space.t(stop_before_pickup.location,request.origin);
            const double cpat_pu = stop_before_pickup.estimated_departure_time() + time_to_pickup;

            // skip vehicle if it can't make it in time to pickup location
            if (cpat_pu > request.pickup_timewindow.max)
                continue;

            const double east_pu = request.pickup_timewindow.min;

            // dropoff immediately
            const double time_to_dropoff = space.t(request.origin,request.destination);
            const double cpat_do = max(east_pu,cpat_pu) + time_to_dropoff;

            // skip vehicle if it can't deliver in time even when it drops off immediately
            if (cpat_do > request.delivery_timewindow.max)
                continue;

            // compute travel time from dropoff point to next stop in list
            const double time_from_dropoff = i<n_stops-1 ? space.t(request.destination,stoplist.at(i+1).location) : 0;

            // calculate cost
            const double time_after_insertion  = time_to_pickup + time_to_dropoff + time_from_dropoff;
            const double time_before_insertion = i<n_stops-1 ? space.t(stoplist.at(i).location,stoplist.at(i+1).location) : 0;
            const double total_cost = time_after_insertion - time_before_insertion;

            if (total_cost < min_cost){
                double cpat_at_next_stop = max(cpat_do, request.delivery_timewindow.min) + time_from_dropoff;
                if (!does_insertion_violates_any_timewindow(stoplist,i,cpat_at_next_stop)){
                    best_insertion = {i,i};
                    min_cost = total_cost;
                }
            }

            // try dropoff not immediately
            const double time_from_pickup = i<n_stops-1 ? space.t(request.origin,stoplist.at(i+1).location) : 0;
            const double cpat_at_next_stop = (max(cpat_pu, request.pickup_timewindow.min) + time_from_pickup);

            if (does_insertion_violates_any_timewindow(stoplist,i,cpat_at_next_stop))
                continue;

            const double pickup_cost = (time_to_pickup + time_from_pickup - time_before_insertion);

            double delay = i<n_stops-1 ? cpat_at_next_stop - stoplist.at(i+1).estimated_arrival_time : 0;

            // try all remaining stop intervals for inserting the new dropoff
            for (int j=i+1; j<n_stops; j++){
                const Stop<Loc> &stop_before_dropoff = stoplist.at(j);

                // skip all further stops if vehicle is already fully occupied here
                if (stop_before_dropoff.occupancy_after_servicing == seat_capacity)
                    break;

                // compute travel time to dropoff point
                const double time_to_dropoff = space.t(stop_before_dropoff.location,request.destination);
                const double cpat_do = max(stop_before_dropoff.estimated_arrival_time + delay, stop_before_dropoff.time_window.min) + time_to_dropoff;

                // skip all further stops if it can't deliver in time
                if (cpat_do > request.delivery_timewindow.max)
                    break;

                // compute travel time from dropoff point to next stop in list
                const double time_from_dropoff = i<n_stops-1 ? space.t(request.destination,stoplist.at(i+1).location) : 0;

                // calculate cost
                const double time_after_insertion  = time_to_dropoff + time_from_dropoff;
                const double time_before_insertion = j<n_stops-1 ? space.t(stoplist.at(j).location,stoplist.at(j+1).location) : 0;
                const double dropoff_cost = time_after_insertion - time_before_insertion;

                const double total_cost = pickup_cost + dropoff_cost;

                if (total_cost < min_cost){
                    const double cpat_at_next_stop = max(cpat_do, request.delivery_timewindow.min) + time_from_dropoff;
                    if (!does_insertion_violates_any_timewindow(stoplist,j,cpat_at_next_stop)){
                        best_insertion = {i,j};
                        min_cost = total_cost;
                    }
                }

                const double new_departure_time = max(stop_before_dropoff.estimated_arrival_time + delay, stop_before_dropoff.time_window.min);
                delay = new_departure_time - stop_before_dropoff.estimated_departure_time();
            }
        }

        // if no valid solution was found, return a result with min_cost == INFINITY
        if (min_cost >= INFINITY)
            return InsertionResult<Loc>();

        const int pickup  = best_insertion.first;

        // build new stoplist
        StopList<Loc> new_stoplist(stoplist);
        const Stop<Loc> &stop_before_pickup = new_stoplist.at(pickup);

        // push new pickup stop to new list
        const double cpat_at_pu = stop_before_pickup.estimated_departure_time() + space.t(stop_before_pickup.location,request.origin);
        const Stop<Loc> pickup_stop(request.origin, request, StopAction::PICKUP, cpat_at_pu, stop_before_pickup.occupancy_after_servicing + 1, request.pickup_timewindow);
        new_stoplist.insert(new_stoplist.begin()+pickup+1,pickup_stop);

        // update estimated_arrival_times for all following stops
        if (pickup < n_stops-1){
            const double cpat_after_pickup = pickup_stop.estimated_departure_time() + space.t(pickup_stop.location,new_stoplist.at(pickup+2).location);
            double delay = cpat_after_pickup - new_stoplist.at(pickup+2).estimated_arrival_time;

            for (auto it = new_stoplist.begin()+pickup+2; it != new_stoplist.end(); ++it){
                if (delay <= 0)
                    break;

                const double old_departure = it->estimated_departure_time();
                it->estimated_arrival_time += delay;
                const double new_departure = it->estimated_departure_time();
                delay = new_departure - old_departure;
            }
        }

        // insert new dropoff stop to list
        const int dropoff = best_insertion.second + 1;
        const Stop<Loc> stop_before_dropoff = new_stoplist.at(dropoff);
        const double cpat_at_do = stop_before_dropoff.estimated_departure_time() + space.t(stop_before_dropoff.location,request.destination);
        const Stop<Loc> dropoff_stop(request.destination, request, StopAction::DROPOFF, cpat_at_do, stop_before_dropoff.occupancy_after_servicing + 1, request.delivery_timewindow);
        new_stoplist.insert(new_stoplist.begin()+dropoff+1,pickup_stop);

        // update estimated_arrival_times for all following stops
        if (dropoff < n_stops-1){
            const double cpat_after_dropoff = dropoff_stop.estimated_departure_time() + space.t(dropoff_stop.location,new_stoplist.at(dropoff+2).location);
            double delay = cpat_after_dropoff - new_stoplist.at(dropoff+2).estimated_arrival_time;

            for (auto it = new_stoplist.begin()+dropoff+2; it != new_stoplist.end(); ++it){
                if (delay <= 0)
                    break;

                const double old_departure = it->estimated_departure_time();
                it->estimated_arrival_time += delay;
                const double new_departure = it->estimated_departure_time();
                delay = new_departure - old_departure;
            }
        }

        return InsertionResult<Loc>(new_stoplist,min_cost,new_stoplist.at(pickup+1).time_window,new_stoplist.at(dropoff+1).time_window);
    }
private:
    bool does_insertion_violates_any_timewindow(const StopList<Loc> &stoplist, const int i, const double est_arrival){
        if (i > stoplist.size()-2)
            return false;

        double delay = est_arrival - stoplist.at(i+1).estimated_arrival_time;

        // check each stop after the insertion
        for(auto it = stoplist.begin() + i+1; it != stoplist.end(); ++it){
            const double old_leeway = it->time_window.max - it->estimated_arrival_time;
            const double new_leeway = old_leeway - delay;

            if (new_leeway < 0 && (new_leeway < old_leeway)) // second condition neccessary?
                return true;

            // compute delay for next stop if not at end
            if (it+1 != stoplist.end()){
                // if the delay vanished, no need for further efforts
                if (it->estimated_arrival_time + delay <= it->time_window.min)
                    return false;

                const double new_departure = max(it->time_window.min, it->estimated_arrival_time + delay);
                delay = new_departure - it->estimated_departure_time();
            }
        }

        return true;
    }
};

} // namespace ridepy

#endif // BRUTEFORCETOTALTRAVELTIMEMINIMISINGDISPATCHER_H
