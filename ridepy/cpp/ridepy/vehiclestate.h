#ifndef VEHICLESTATE_H
#define VEHICLESTATE_H

#include <vector>
#include <deque>
#include <algorithm>

#include "stop.h"
#include "abstractdispatcher.h"
#include "transportspace.h"
#include "singlevehiclesolution.h"

namespace ridepy {

template <typename Loc>
class VehicleState
{
public:
    int vehicle_id = -1;
    int seat_capacity = 1;
    // use deque instead of vector here for efficient pop_front()
    std::deque<Stop<Loc>> stoplist;

    VehicleState(const int vehicle_id, const int seat_capacity, const std::deque<Stop<Loc>> &initial_stoplist, AbstractDispatcher<Loc> &dispatcher, TransportSpace<Loc> &space)
        : vehicle_id(vehicle_id), seat_capacity(seat_capacity), stoplist(initial_stoplist), m_dispatcher(dispatcher), m_space(space)
    {}

    // this function was rewritten
    std::vector<StopEvent> fast_forward_time(double new_time){
        std::vector<StopEvent> stopEvents;

        // iterate over stops in list to gather all stops that will be serviced until new_time
        bool first = true;
        for (const Stop<Loc> &stop : stoplist) {
            // skip first element in stoplist as this stop was already served at last fast_forward_time
            if (first){
                first = false;
                continue;
            }

            double service_time = std::max(stop.estimated_arrival_time,stop.time_window.min);
            if (service_time <= new_time)
                stopEvents.push_back({stop.action,service_time,stop.request.request_id,vehicle_id});
            else
                break;
        }

        // remove all serviced stops from list
        const int serviced_stops = stopEvents.size();
        stoplist.erase(stoplist.begin(), stoplist.begin() + serviced_stops);

        // compute exact position at new_time
        if (stoplist[0].estimated_arrival_time < new_time){
            if (stoplist.size() > 1){
                auto nextLocTravelTime = m_space.interp_time(stoplist[0].location,stoplist[1].location,stoplist[1].estimated_arrival_time - new_time);
                stoplist[0].location = nextLocTravelTime.location;
                stoplist[0].estimated_arrival_time = new_time + nextLocTravelTime.distance;
            } else {
                // wait at last serviced stop until new_time if stoplist is empty
                stoplist[0].estimated_arrival_time = new_time;
            }
        }

        return stopEvents;
    }

    SingleVehicleSolution handle_transportation_request_single_vehicle(const TransportationRequest<Loc> &request) {
        InsertionResult<Loc> insertion_result = m_dispatcher(request, stoplist, m_space, seat_capacity);
        m_stoplist_new = insertion_result.new_stoplist;
        return insertion_result.toSingleVehicleSolution(vehicle_id);
    }

    void select_new_stoplist() {
        stoplist.swap(m_stoplist_new);
        m_stoplist_new.clear();;
    }

    TimeWindow estimate_travel_time(const TransportationRequest<Loc> &request, const bool useNewList = true) const{
        TimeWindow invehicle_time = {INFINITY,INFINITY};

        const std::deque<Stop<Loc>> &stoplistRef = useNewList ? m_stoplist_new : stoplist;
        for (const Stop<Loc> &stop : stoplistRef){
            if (stop.request.request_id == request.request_id){
                if (stop.action == StopAction::PICKUP)
                    invehicle_time.min = stop.estimated_arrival_time;
                else if (stop.action == StopAction::DROPOFF)
                    invehicle_time.max = stop.estimated_arrival_time;
            }
        }

        return invehicle_time;
    }

private:
    std::deque<Stop<Loc>> m_stoplist_new;
    AbstractDispatcher<Loc> &m_dispatcher;
    TransportSpace<Loc> &m_space;
};

} // namespace ridepy

#endif // VEHICLESTATE_H
