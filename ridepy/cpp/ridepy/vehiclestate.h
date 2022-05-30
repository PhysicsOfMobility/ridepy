#ifndef VEHICLESTATE_H
#define VEHICLESTATE_H

#include <vector>
#include <list>
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
    // note that StopList is a std::list compared to std::vector in the original implementation
    std::list<Stop<Loc>> stoplist;

    VehicleState(const int vehicle_id, const int seat_capacity, const std::list<Stop<Loc>> &initial_stoplist, AbstractDispatcher<Loc> &dispatcher, TransportSpace<Loc> &space)
        : vehicle_id(vehicle_id), seat_capacity(seat_capacity), stoplist(initial_stoplist), m_dispatcher(dispatcher), m_space(space)
    {}

    // this function was rewritten
    std::vector<StopEvent> fast_forward_time(double new_time){
        std::vector<StopEvent> stopEvents;

        // iterate over stops in list to gather all stops that will be serviced until new_time
        for (const Stop<Loc> &stop : stoplist) {
            double service_time = std::max(stop.estimated_arrival_time,stop.time_window.min);
            if (service_time <= new_time)
                stopEvents.push_back({stop.action,stop.request->request_id,vehicle_id,service_time});
            else
                break;
        }

        // remove all serviced stops from list
        const int serviced_stops = stopEvents.size() < stoplist.size() ? stopEvents.size() : stoplist.size()-1;
        for (int i=0; i<serviced_stops; i++)
            stoplist.pop_front();

        // compute exact position at new_time
        if (stoplist[0].estimated_arrival_time < new_time){
            if (stoplist.size() > 1){
                auto nextLocTravelTime = m_space.interp_time(stoplist[0].location,stoplist[1].location,stoplist[1].estimated_arrival_time - new_time);
                stoplist[0].location = nextLocTravelTime.location;
                stoplist[0].estimated_arrival_time = new_time + nextLocTravelTime.distance;
                stoplist[0].action = StopAction::INTERNAL; // was this forgotten in the original implementation?
            } else {
                // wait at last serviced stop until new_time if stoplist is empty
                stoplist[0].estimated_arrival_time = new_time;
                stoplist[0].action = StopAction::INTERNAL; // was this forgotten in the original implementation?
            }
        }

        return stopEvents;
    }

    SingleVehicleSolution handle_transportation_request_single_vehicle(const TransportationRequest<Loc> &request) {
        InsertionResult<Loc> insertion_result = dispatcher(request, stoplist, m_space, seat_capacity);
        m_stoplist_new = insertion_result.new_stoplist;
        return insertion_result.toSingleVehicleSolution(vehicle_id);
    }

    void select_new_stoplist() {
        stoplist.swap(m_stoplist_new);
        m_stoplist_new.clear();;
    }

private:
    std::list<Stop<Loc>> m_stoplist_new;
    AbstractDispatcher<Loc> &m_dispatcher;
    TransportSpace<Loc> &m_space;
};

} // namespace ridepy

#endif // VEHICLESTATE_H
