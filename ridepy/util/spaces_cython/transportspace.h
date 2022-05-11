#ifndef TRANSPORTSPACE_H
#define TRANSPORTSPACE_H

#include <utility>

namespace ridepy {

/*!
 * \ingroup RidePy
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
  virtual std::pair<Loc, double> interp_dist(Loc u, Loc v, double dist_to_dest) = 0;
  virtual std::pair<Loc, double> interp_time(Loc u, Loc v, double time_to_dest) = 0;

  TransportSpace() : velocity{1} {}
  TransportSpace(double velocity) : velocity{velocity} {}
  virtual ~TransportSpace(){}
};

} // namespace RidePy

#endif // TRANSPORTSPACE_H
