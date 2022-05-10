//
// Created by dmanik on 29.11.20.
//

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

/*!
 * \brief The abtract template for a TransportSpace within which ride-pooling vehicles can move
 * \tparam Loc The measure that allows to identify a location in the transport space.
 * This measure might for instance be a R2Loc to identify a location in the 2D Euclidian plane.
 *
 * Custom transport spaces can be defined by inheriting this interface.
 *
 * The type template parameter \p Loc expresses the measure, how to identify a location.
 * This might be for instance a R2Loc to identify a location by its position in the 2D Euclidian plane or
 * the unique id of a network node.
 */
template <typename Loc>
class TransportSpace {
public:
  double velocity;

  /*!
   * \brief Returns the spacial distance between the locations \p u and \p v inside this space
   * \param u The starting point
   * \param v The destination
   * \return The spacial distance between the locations \p u and \p v
   */
  virtual double d(Loc u, Loc v) = 0;

  /*!
   * \brief Returns the time needed to travel from location \p u to \p v inside this space
   * \param u The starting point
   * \param v The destination
   * \return The time needed to travel from location \p u to \p v
   */
  virtual double t(Loc u, Loc v) = 0;
  virtual pair<Loc, double> interp_dist(Loc u, Loc v, double dist_to_dest) = 0;
  virtual pair<Loc, double> interp_time(Loc u, Loc v, double time_to_dest) = 0;

  TransportSpace() : velocity{1} {};
  TransportSpace(double velocity) : velocity{velocity} {};
  virtual ~TransportSpace(){};
};

/*!
 * \brief The Euclidean2D class allows vehicles to drive anywhere on the 2D plane.
 */
class Euclidean2D : public TransportSpace<R2loc> {
public:
  double d(R2loc u, R2loc v) override;
  double t(R2loc u, R2loc v) override;
  pair<R2loc, double> interp_dist(R2loc u, R2loc v,
                                  double dist_to_dest) override;
  pair<R2loc, double> interp_time(R2loc u, R2loc v,
                                  double time_to_dest) override;

  Euclidean2D();
  Euclidean2D(double);
};

/*!
 * \brief The Euclidean2D class allows vehicles to drive anywhere on the 2D plane.
 */
class Manhattan2D : public TransportSpace<R2loc> {
public:
  double d(R2loc u, R2loc v) override;
  double t(R2loc u, R2loc v) override;
  pair<R2loc, double> interp_dist(R2loc u, R2loc v,
                                  double dist_to_dest) override;
  pair<R2loc, double> interp_time(R2loc u, R2loc v,
                                  double time_to_dest) override;

  Manhattan2D();
  Manhattan2D(double);
};

/*!
 * @}
 */

} // namespace ridepy

#endif
// RIDEPY_CSPACES_H
