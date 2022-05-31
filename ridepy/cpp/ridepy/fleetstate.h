#ifndef FLEETSTATE_H
#define FLEETSTATE_H

#include <vector>
#include <deque>
#include <list>

#include "vehiclestate.h"
#include "transportationrequest.h"

namespace ridepy {

/*!
 * \brief The FleetState class holds
 * \tparam Loc The type used to identify locations in the underlying TransportSpace
 *
 * The virtual functions fast_forward() and handle_transportation_request() can be overwritten in childclasses to implement e.g. paralellisation or other optimisations.
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
        std::deque<Stop<Loc>> initialStopList = {Stop<Loc>(startLocation,new Request(-1,startTime),StopAction::INTERNAL,startTime)};

        m_vehicles.reserve(numVehicles);
        for (int i=0; i<numVehicles; i++)
            m_vehicles.push_back(VehicleState<Loc>(i,seatCapacity,initialStopList,*m_dispatcher,*m_transportSpace));
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

private:
    std::vector<VehicleState<Loc>> m_vehicles;

    TransportSpace<Loc>     *m_transportSpace;
    AbstractDispatcher<Loc> *m_dispatcher;

};

} // namespace ridepy

#endif // FLEETSTATE_H
