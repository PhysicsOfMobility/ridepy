#ifndef RIDEPY_TRANSPORTSPACE_H
#define RIDEPY_TRANSPORTSPACE_H

#include <utility>

namespace ridepy {

/*!
 * \ingroup RidePy
 * \brief The abtract template for a TransportSpace within which ridepooling
 * vehicles can move \tparam Loc The coordinate that identifies a location in
 * the transport space. This coordinate might for instance be a R2Loc to
 * identify a location in the 2D Euclidian plane.
 *
 * Custom transport spaces can be defined by inheriting this interface.
 *
 * The type template parameter \p Loc expresses the coordinate.
 * This might be for instance a R2Loc to identify a location by its position in
 * the 2D Euclidian plane or the unique id of a network node.
 */
template <typename Loc> class TransportSpace {
public:
  double velocity;

  /*!
   * \brief Returns the spacial distance between the locations \p u and \p v
   * inside this space \param u The starting point \param v The destination
   * \return The spacial distance between the locations \p u and \p v
   */
  virtual double d(Loc u, Loc v) = 0;

  /*!
   * \brief Returns the time needed to travel from location \p u to \p v inside
   * this space \param u The starting point \param v The destination \return The
   * time needed to travel from location \p u to \p v
   */
  virtual double t(Loc u, Loc v) = 0;

  /*!
   * \brief Calculates the current position of a vehicle on the way from \p u to
   * \p v at a distance \p dist_to_dest before reaching \p v \param u The origin
   * of the ride \param v The destination of the ride \param dist_to_dest The
   * remaining distance to reach the destination \p v \return A pair with
   * (first) the next location that will be reached and (second) the remaining
   * distance, until this intermediate node will be reached.
   */
  virtual std::pair<Loc, double> interp_dist(Loc u, Loc v,
                                             double dist_to_dest) = 0;

  /*!
   * \brief Calculates the current position of a vehicle on the way from \p u to
   * \p v at time \p time_to_dest before reaching \p v \param u The origin of
   * the ride \param v The destination of the ride \param time_to_dest The
   * remaining travel time to reach the destination \p v \return A pair with
   * (first) the next location that will be reached and (second) the remaining
   * travel time, until this intermediate node will be reached.
   */
  virtual std::pair<Loc, double> interp_time(Loc u, Loc v,
                                             double time_to_dest) = 0;
};

} // namespace ridepy

#endif // RIDEPY_TRANSPORTSPACE_H
