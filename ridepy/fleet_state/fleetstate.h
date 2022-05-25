#ifndef RIDEPY_FLEETSTATE_H
#define RIDEPY_FLEETSTATE_H

#include <vector>

#include "../vehicle_state_cython/cvehicle_state.h"

namespace ridepy {

/*!
 * \ingroup RidePy
 * \brief The FleetState class holds
 * \tparam Loc The type used to identify locations in the underlying TransportSpace
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
    FleetState(const int numVehicles, const int seatCapacity, TransportSpace<Loc> *transportSpace, AbstractDispatcher<Loc> *dispatcher)
        : m_transportSpace(transportSpace), m_dispatcher(dispatcher){

        m_vehicles.reserve(numVehicles);
        for (int i=0; i<numVehicles; i++)
            m_vehicles.push_back(VehicleState(i,seatCapacity,*m_transportSpace,*m_dispatcher));
    }

    /*!
     * \brief Returns the VehicleState of the vehicle with \p vehicleId
     * \param vehicleId The id of the vehicle that should be accessed
     * \return A reference to the requested vehicle
     * \throws std::out_of_range If \p vehicleId is not in [0, numVehicles()-1]
     */
    VehicleState<Loc> &vehicle(const int vehicleId){
        return m_vehicles[vehicleId];
    }

    /*!
     * \overload
     */
    const VehicleState<Loc> &vehicle(const int vehicleId) const{
        return m_vehicles[vehicleId];
    }

    /*!
     * \brief Returns the VehicleState of the vehicle with \p vehicleId. Equivalent to vehicle()
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

#endif // RIDEPY_FLEETSTATE_H
