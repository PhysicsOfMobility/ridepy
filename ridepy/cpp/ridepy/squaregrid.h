#ifndef SQUAREGRID_H
#define SQUAREGRID_H

#include <cmath>

#include "transportspace.h"
#include "i2loc.h"
#include "r2loc.h"

namespace ridepy {

class SquareGrid : public TransportSpace<I2loc>
{
public:
    inline SquareGrid(const double gridSize = 1., const double velocity = 1.)
        : m_gridSize(gridSize), m_velocity(velocity)
    {}

    inline double d(const I2loc &origin, const I2loc &destination){
        return m_gridSize*abs(origin-destination);
    }

    inline double t(const I2loc &origin, const I2loc &destination){
        return d(origin,destination) / m_velocity;
    }

    inline InterpolatedPosition<I2loc> interp_dist(const I2loc &origin, const I2loc &destination, const double dist_to_dest){
        // assume, vehicles first go along first dimension from origin.first to destination.first,
        // then along second dimension from origin.second to destination.second

        // get the number of full grid edges to go to reach destination and the distance to the next reached grid node
        const int    remaining_full_edges = floor(dist_to_dest/m_gridSize);
        const double dist_to_next_loc     = dist_to_dest - remaining_full_edges*m_gridSize;

        I2loc previous, next;

        // determine whether vehicle currently drives along first or second dimension
        const int second_dimension_dist = std::abs(destination.second - origin.second);
        if (remaining_full_edges < second_dimension_dist){
            // vehicle is already at destination.first axis driving into second direction
            previous.first = destination.first;
            previous.second = destination.second + (origin.second < destination.second ? -1 : +1) * (remaining_full_edges+1);

            next.first = destination.first;
            next.second = destination.second + (origin.second < destination.second ? -1 : +1) * remaining_full_edges;
        } else {
            // vehicle is still driving at origin.second into first direction
            const double remaining_full_edges_first_direction = remaining_full_edges - second_dimension_dist;
            previous.first  = destination.first + (origin.first < destination.first ? -1 : +1) * (remaining_full_edges_first_direction+1);
            previous.second = origin.second;

            next.first  = destination.first + (origin.first < destination.first ? -1 : +1) * remaining_full_edges_first_direction;
            next.second = origin.second;
        }

        return {previous,next,dist_to_next_loc};
    }

    inline InterpolatedPosition<I2loc> interp_time(const I2loc &origin, const I2loc &destination, const double time_to_dest){
        const double dist_to_dest = time_to_dest * m_velocity;
        InterpolatedPosition<I2loc> interp = interp_dist(origin,destination,dist_to_dest);
        // transport spacial distance into timelike distance
        interp.distance /= m_velocity;
        return interp;
    }

    inline std::pair<double, double> getCoordinates(const InterpolatedPosition<I2loc> &position){
        const R2loc nextPos = position.nextLocation * m_gridSize;
        const R2loc prevPos = position.previousLocation * m_gridSize;
        const R2loc normal = (nextPos-prevPos)/m_gridSize;
        return nextPos - normal * position.distance;
    }

private:
    double m_gridSize = 1;
    double m_velocity = 1;
};

} // namespace ridepy

#endif // SQUAREGRID_H
