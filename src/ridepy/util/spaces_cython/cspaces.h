#ifndef RIDEPY_CSPACES_H
#define RIDEPY_CSPACES_H

#include <algorithm> // for max()
#include <chrono>    // for benchmarking
#include <cmath>
#include <iostream>
#include <random>
#include <tuple>
#include <utility> // for pair
#include <vector>

#include "ctransport_space.h"

using namespace std;

namespace ridepy {

/*!
 * \addtogroup RidePy
 * @{
 */

/*!
 * \brief A point in the 2D plane
 */
typedef pair<double, double> R2loc;

std::ostream &operator<<(std::ostream &stream, R2loc const &x) {
  return stream << "(" << x.first << "," << x.second << ")" << endl;
}

/*!
 * \brief The Euclidean2D class allows vehicles to drive anywhere on the 2D
 * plane.
 */
class Euclidean2D : public TransportSpace<R2loc> {
public:
  Euclidean2D(double velocity = 1.);

  double d(R2loc u, R2loc v) override;
  double t(R2loc u, R2loc v) override;
  pair<R2loc, double> interp_dist(R2loc u, R2loc v,
                                  double dist_to_dest) override;
  pair<R2loc, double> interp_time(R2loc u, R2loc v,
                                  double time_to_dest) override;

  double velocity;
};

/*!
 * \brief The Euclidean2D class allows vehicles to drive anywhere on the 2D
 * plane.
 */
class Manhattan2D : public TransportSpace<R2loc> {
public:
  Manhattan2D(double velocity = 1.);

  double d(R2loc u, R2loc v) override;
  double t(R2loc u, R2loc v) override;
  pair<R2loc, double> interp_dist(R2loc u, R2loc v,
                                  double dist_to_dest) override;
  pair<R2loc, double> interp_time(R2loc u, R2loc v,
                                  double time_to_dest) override;

  double velocity;
};

/*!
 * @}
 */

} // namespace ridepy

#endif
// RIDEPY_CSPACES_H
