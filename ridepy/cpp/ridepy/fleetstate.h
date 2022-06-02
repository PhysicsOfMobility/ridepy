#ifndef FLEETSTATE_H
#define FLEETSTATE_H

#include <sstream>
#include <vector>
#include <deque>
#include <list>

#include "vehiclestate.h"
#include "transportationrequest.h"
#include "events.h"

namespace ridepy {

/*!
 * \brief The FleetState class holds
 * \tparam Loc The type used to identify locations in the underlying TransportSpace. It has at least to provide a proper implementation of the operator==
 *
 */
template <typename Loc>
class FleetState
{
public:
    /*!
     * \brief Contructs an FleetState with \p numVehicles vehicles in the fleet, all having the same capacity \p seatCapacity
     * \param numVehicles The number of vehicles in the fleet
     * \param seatCapacity The number of passenger a single vehicle can carry at the same time
     */
    FleetState(const int numVehicles, const int seatCapacity, const Loc &startLocation, TransportSpace<Loc> *transportSpace, AbstractDispatcher<Loc> *dispatcher, double startTime = 0.)
        : m_transportSpace(transportSpace), m_dispatcher(dispatcher){

        // initial stoplist only contains the startLocation, that is reached immediately
        StopList<Loc> initialStopList = {Stop<Loc>(startLocation,Request(-1,startTime),StopAction::INTERNAL,startTime)};

        m_vehicles.reserve(numVehicles);
        for (int i=0; i<numVehicles; i++)
            m_vehicles.push_back(VehicleState<Loc>(i,seatCapacity,initialStopList,*m_dispatcher,*m_transportSpace,startTime));
    }

    /*!
     * \brief Returns the VehicleState of the vehicle with \p vehicleId.
     * \param vehicleId The id of the vehicle that should be accessed
     * \return A reference to the requested vehicle
     * \throws std::out_of_range If \p vehicleId is not in [0, numVehicles()-1]
     */
    VehicleState<Loc> &operator[](const int vehicleId){
        return m_vehicles[vehicleId];
    }

    /*!
     * \overload
     */
    const VehicleState<Loc> &operator[](const int vehicleId) const{
        return m_vehicles[vehicleId];
    }

    /*!
     * \brief Returns a read-only reference to the vehicle vector
     */
    const std::vector<VehicleState<Loc>> &vehicles() const{
        return m_vehicles;
    }

    /*!
     * \brief Returns the number of vehicles in the fleet
     */
    int numVehicles() const{
        return m_vehicles.size();
    }

    virtual std::vector<StopEvent> fast_forward(const double t){
        std::list<StopEvent> sortedEvents;

        // fast forward each vehicle
        for (VehicleState<Loc> &vehicle : m_vehicles){
            const std::vector<StopEvent> newEvents = vehicle.fast_forward_time(t);
            // insertionsort events by timestamp
            for (const StopEvent &e : newEvents){
                // check if current event has to be appended or inserted
                if (e.timestamp > sortedEvents.back().timestamp){
                    sortedEvents.push_back(e);
                } else {
                    for (auto it = sortedEvents.begin(); it != sortedEvents.end(); ++it){
                        if (it->timestamp > e.timestamp){
                            sortedEvents.insert(it,e);
                            break;
                        }
                    }
                }
            }
        }

        // invalidate queries of travel requests
        m_last_request.request_id = -1;

        // return all sorted events as a vector
        return std::vector<StopEvent>(sortedEvents.begin(),sortedEvents.end());
    }


    /*!
     * \brief Sumits a transportation request to the fleet state and checks whether this request could be serviced or not
     * \param request The request to handle
     * \return An event, that states whether or not the request can be handled. If the request could be handled, it returns an estimate for the travel time (relative to pickup_timewindow.min), if the ride offer would be accepted
     */
    virtual RequestEvent submit_transportation_request(const TransportationRequest<Loc> &request){
        const int N = numVehicles();

        // reject trivial requests
        if (request.origin == request.destination)
            return RequestEvent(EventType::REQUESTREJECTION_EVENT,request,"Do not handle trivial requests");

        // get for each vehicle the cost for adding this request to its stoplist
        std::vector<SingleVehicleSolution> solutions;
        solutions.reserve(N);
        for (VehicleState<Loc> &vehicle : m_vehicles)
            solutions.push_back(vehicle.handle_transportation_request_single_vehicle(request));

        // choose vehicle with minimal cost
        double min_cost = INFINITY;
        int    opt_vehicle = -1;
        for (int i=0; i<N; i++){
            if (solutions.at(i).min_cost < min_cost){
                min_cost = solutions.at(i).min_cost;
                opt_vehicle = i;
            }
        }

        // if min_cost = INFINITY, the request can't be handled
        if (min_cost == INFINITY)
            return RequestEvent(EventType::REQUESTREJECTION_EVENT,request,"Can not handle request");

        // save request data in case the customer accepts the offer
        m_last_request = request;
        m_last_request_optimal_vehicle = opt_vehicle;

        // notify caller that the ride is possible and what would be the estimated invehicle time window for the ride
        return RequestEvent(EventType::REQUESTOFFERING_EVENT,request,m_vehicles.at(opt_vehicle).estimate_travel_time(request),"Offering a ride");
    }

    /*!
     * \brief Exectues a TransportationRequest that previously has been evaluated by calling submit_transportation_request()
     * \param request_id The id of the request to be executed
     * \return ...
     */
    virtual RequestEvent execute_transportation_request(const int request_id){
        if (m_last_request.request_id == -1)
            return RequestEvent(EventType::REQUESTREJECTION_EVENT,m_last_request,"Last request is invalid. Probably there was a fast_forward since the last request was submitted.");
        if (m_last_request.request_id != request_id)
            return RequestEvent(EventType::REQUESTREJECTION_EVENT,m_last_request,"The request doesn't match the last submitted request.");

        // tell the optimal vehicle to service this request
        m_vehicles.at(m_last_request_optimal_vehicle).select_new_stoplist();
        m_last_request.request_id = -1;
        std::stringstream s;
        s << "Serve request " << m_last_request.request_id << " with vehicle " << m_last_request_optimal_vehicle << ".";
        return RequestEvent(EventType::REQUESTOFFERING_EVENT,m_last_request,s.str());
    }

    std::vector<std::pair<double, double>> currentVehiclePositions() const{
        std::vector<std::pair<double, double>> locations;
        locations.reserve(m_vehicles.size());

        for (const VehicleState<Loc> &vehicle : m_vehicles)
            locations.push_back(vehicle.currentPosition());

        return locations;
    }

private:
    std::vector<VehicleState<Loc>> m_vehicles;

    TransportSpace<Loc>     *m_transportSpace;
    AbstractDispatcher<Loc> *m_dispatcher;

    // store informations on last request query, if m_last_request.request_id < 0, they are invalid
    Request m_last_request = {-1,0};
    int m_last_request_optimal_vehicle = 0;

};

} // namespace ridepy

#endif // FLEETSTATE_H
