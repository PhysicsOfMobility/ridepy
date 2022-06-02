#ifndef EUCLIDEAN2D_H
#define EUCLIDEAN2D_H

#include "transportspace.h"
#include "r2loc.h"

namespace ridepy {

/*!
 * \brief The Euclidean2D class allows vehicles to drive anywhere on the 2D
 * plane.
 */
class Euclidean2D : public TransportSpace<R2loc> {
public:
    inline Euclidean2D(double velocity = 1.)
        : TransportSpace<R2loc>(), m_velocity(velocity)
    {}

    inline double d(const R2loc &origin, const R2loc &destination){
        return abs(origin-destination);
    }
    inline double t(const R2loc &origin, const R2loc &destination){
        return abs(origin-destination)/m_velocity;
    }
    inline InterpolatedPosition<R2loc> interp_dist(const R2loc &origin, const R2loc &destination, const double dist_to_dest){
        const R2loc normal = (destination-origin)/(abs(origin-destination));
        const R2loc currentPostion = destination - dist_to_dest * normal;
        return {currentPostion,currentPostion,0};
    }
    inline InterpolatedPosition<R2loc> interp_time(const R2loc &origin, const R2loc &destination, const double time_to_dest){
        const R2loc normal = (destination-origin)/(abs(origin-destination)) * m_velocity;
        const R2loc currentPostion = destination - time_to_dest * normal;
        return {currentPostion,currentPostion,0};
    }

    inline std::pair<double, double> getCoordinates(const InterpolatedPosition<R2loc> &position){
        return position.previousLocation;
    }

private:
    double m_velocity;
};

} // namespace ridepy

#endif // EUCLIDEAN2D_H
