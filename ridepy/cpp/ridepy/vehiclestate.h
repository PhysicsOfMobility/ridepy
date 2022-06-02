#ifndef VEHICLESTATE_H
#define VEHICLESTATE_H

#include <vector>
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
    StopList<Loc> stoplist;

    VehicleState(const int vehicle_id, const int seat_capacity, const StopList<Loc> &initial_stoplist, AbstractDispatcher<Loc> &dispatcher, TransportSpace<Loc> &space, const double initialTime = 0.)
        : vehicle_id(vehicle_id), seat_capacity(seat_capacity), stoplist(initial_stoplist), m_dispatcher(dispatcher), m_space(space), m_currentTime(initialTime)
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
                NextLocationDistance<Loc> nextLocTravelTime = m_space.interp_time(stoplist[0].location,stoplist[1].location,stoplist[1].estimated_arrival_time - new_time);
                stoplist[0].location = nextLocTravelTime.location;
                stoplist[0].estimated_arrival_time = new_time + nextLocTravelTime.distance;
            } else {
                // wait at last serviced stop until new_time if stoplist is empty
                stoplist[0].estimated_arrival_time = new_time;
            }
        }

        m_currentTime = new_time;
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

        const StopList<Loc> &stoplistRef = useNewList ? m_stoplist_new : stoplist;
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

    /*!
     * \brief Returns the current position of the vehicle
     * \todo Currently, the next location that will be reached is returned. However, for visualisations it would be better to return the exact, interpolated position
     */
    Loc currentPosition() const{
        if (stoplist.size() > 1){
            // vehicle is driving from stoplist[0] to stoplist[1]
            const double time_to_next_stop = stoplist.at(1).estimated_arrival_time - m_currentTime;
            // get next location, that will be reached
            NextLocationDistance<Loc> next = m_space.interp_time(stoplist.at(0).location,stoplist.at(1).location,time_to_next_stop);

            // return the next location that will be reached
            return next.location;
        } else {
            // vehicle is waiting at stop
            return stoplist.at(0).location;
        }
    }

private:
    StopList<Loc> m_stoplist_new;
    AbstractDispatcher<Loc> &m_dispatcher;
    TransportSpace<Loc> &m_space;

    double m_currentTime = 0;
};

} // namespace ridepy

#endif // VEHICLESTATE_H
