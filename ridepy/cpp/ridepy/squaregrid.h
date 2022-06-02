#ifndef SQUAREGRID_H
#define SQUAREGRID_H

#include <cmath>

#include "transportspace.h"
#include "i2loc.h"

namespace ridepy {

class SquareGrid : public TransportSpace<I2loc>
{
public:
    inline SquareGrid(const double gridSize = 1., const double velocity = 1.)
        : m_gridSize(gridSize), m_velocity(velocity)
    {}

    inline double d(const I2loc &u, const I2loc &v){
        return abs(u-v);
    }

    inline double t(const I2loc &u, const I2loc &v){
        return d(u,v) / m_velocity;
    }

    inline NextLocationDistance interp_dist(const I2loc &u, const I2loc &v, const double dist_to_dest){
        // assume, vehicles first go along first dimension to v.first, then along second dimension to v.second
        const int remaining_full_edges = floor(dist_to_dest/m_gridSize);
        const int second_dimenstion_dist = std::abs(v.second - u.second);
        const double dist_to_next_loc = dist_to_dest - remaining_full_edges*m_gridSize;

        if (second_dimenstion_dist < remaining_full_edges){
            // vehicle is already a v.first axis driving into second direction
            const int pos_first  = v.first;
            const int pos_second = v.second + (u.second < v.second ? -1 : +1) * remaining_full_edges;
            return {{pos_first,pos_second},dist_to_next_loc};
        } else {
            // vehicle is still driving at u.second into first direction
            const int pos_first  = v.first + (u.first > v.first ? +1 : -1) * (remaining_full_edges-second_dimenstion_dist);
            const int pos_second = u.second;
            return {{pos_first,pos_second},dist_to_next_loc};
        }
    }

    inline NextLocationDistance interp_time(const I2loc &u, const I2loc &v, const double time_to_dest){
        const double dist_to_dest = time_to_dest * m_velocity;
        return interp_dist(u,v,dist_to_dest);
    }

private:
    double m_gridSize = 1;
    double m_velocity = 1;
};

} // namespace ridepy

#endif // SQUAREGRID_H
