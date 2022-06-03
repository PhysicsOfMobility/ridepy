#ifndef RIDEPY_TRANSPORTSPACE_H
#define RIDEPY_TRANSPORTSPACE_H

#include <utility>
#include <ostream>

namespace ridepy {

/*!
 * \brief The InterpolatedPosition allows to excatly locate a vehicle in the plane:
 *        The vehicle is on the edge from \p previousLocation to \p nextLocation at
 *        a distance \p distance befor reaching \p nextLocation
 * \tparam Loc The measure to identify locations in the choosen TransportSpace
 */
template <typename Loc>
struct InterpolatedPosition{
    /*!
     * \brief The last location, that the vehicle passed by
     */
    Loc previousLocation;

    /*!
     * \brief The next location that will be reached
     */
    Loc nextLocation;

    /*!
     * \brief The remaining (spacial or timelike) distance to \a nextLocation location
     */
    double distance;

    /*!
     * \brief Flag that states whether the value of \a distance is a spacial distance or not
     */
    bool distanceIsSpacial;
};

template <typename Loc>
inline std::ostream &operator<<(std::ostream &os, const InterpolatedPosition<Loc> &interp){
    return os << interp.previousLocation << " -> " << interp.nextLocation << ",   " << (interp.distanceIsSpacial ? "d" : "t") << "=" << interp.distance;
}

/*!
 * \brief The abtract template for a TransportSpace within which ridepooling vehicles can move
 * \tparam Loc The coordinate that identifies a location in the transport space.
 *         This coordinate might for instance be a R2Loc to identify a location
 *         in the 2D Euclidian plane.
 *
 * Custom transport spaces can be defined by inheriting this interface.
 *
 * The type template parameter \p Loc expresses the coordinate.
 * This might be for instance a R2Loc to identify a location by its position in
 * the 2D Euclidian plane or the unique id of a network node.
 */
template <typename Loc>
class TransportSpace
{
public:
    /*!
     * \brief Returns the spacial distance between the locations \p origin and \p destination
     * inside this space
     * \return The spacial distance between the locations \p origin and \p destination
     */
    virtual double d(const Loc &origin, const Loc &destination) = 0;

    /*!
     * \brief Returns the time needed to travel from location \p origin to \p destination inside
     * this space
     * \return The time needed to travel from location \p origin to \p destination
     */
    virtual double t(const Loc &origin, const Loc &destination) = 0;

    /*!
     * \brief Calculates the current position of a vehicle on the way from \p origin to \p destination at a distance \p dist_to_dest before reaching \p destination
     * \param dist_to_dest The remaining distance to reach \p destination
     * \return An instance of InterpolatedPosition, that contains the last location passed through and the next location
     *         that will be reached as well as the spacial distance to the latter location.
     *
     * Compared to the original RidePy implementation, also the last location is now returned to be able to determine the exact position in the plane
     */
    virtual InterpolatedPosition<Loc> interp_dist(const Loc &origin, const Loc &destination, const double dist_to_dest) = 0;

    /*!
     * \brief Calculates the current position of a vehicle on the way from \p origin to \p destination at time \p time_to_dest before reaching \p destination
     * \param time_to_dest The remaining travel time to reach the destination \p destination
     * \return An instance of InterpolatedPosition, that contains the last location passed through and the next location
     *         that will be reached as well as the remaining travel time to reach the latter location.
     *
     * Compared to the original RidePy implementation, also the last location is now returned to be able to determine the exact position in the plane
     */
    virtual InterpolatedPosition<Loc> interp_time(const Loc &origin, const Loc &destination, const double time_to_dest) = 0;

    /*!
     * \brief Returns the coordinates in the 2D plane that correspond to the InterpolatedPosition \p position
     */
    virtual std::pair<double,double> getCoordinates(const InterpolatedPosition<Loc> &position) = 0;
};

} // namespace ridepy

#endif // RIDEPY_TRANSPORTSPACE_H
