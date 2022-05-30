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

    inline double d(R2loc u, R2loc v) override{
        return abs(u-v);
    }
    inline double t(R2loc u, R2loc v) override{
        return abs(u-v)/m_velocity;
    }
    inline NextLocationDistance interp_dist(R2loc u, R2loc v, double dist_to_dest) override{
        const R2loc normal = (v-u)/(abs(v-u));
        const R2loc currentPostion = v - dist_to_dest * normal;
        return {currentPostion,0};
    }
    inline NextLocationDistance interp_time(R2loc u, R2loc v, double time_to_dest) override{
        const R2loc normal = (v-u)/(abs(v-u))*m_velocity;
        const R2loc currentPostion = v - time_to_dest * normal;
        return {currentPostion,0};
    }

private:
    double m_velocity;
};

} // namespace ridepy

#endif // EUCLIDEAN2D_H
