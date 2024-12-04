#include "cspaces.h"

using namespace std;

namespace ridepy {

Euclidean2D::Euclidean2D(double velocity)
    : TransportSpace(), velocity(velocity) {}

double Euclidean2D::d(R2loc u, R2loc v) {
  return sqrt((u.first - v.first) * (u.first - v.first) +
              (u.second - v.second) * (u.second - v.second));
}

double Euclidean2D::t(R2loc u, R2loc v) {
  return this->d(u, v) / this->velocity;
}

pair<R2loc, double> Euclidean2D::interp_dist(R2loc u, R2loc v,
                                             double dist_to_dest) {
  double frac = dist_to_dest / this->d(u, v);
  return make_pair(R2loc{u.first * frac + (1 - frac) * v.first,
                         u.second * frac + (1 - frac) * v.second},
                   0);
}

pair<R2loc, double> Euclidean2D::interp_time(R2loc u, R2loc v,
                                             double time_to_dest) {
  double dist_to_dest = time_to_dest * (this->velocity);
  return this->interp_dist(u, v, dist_to_dest);
}

Euclidean2DPeriodicBoundaries::Euclidean2DPeriodicBoundaries(double velocity)
    : Euclidean2D(), velocity(velocity) {}

double Euclidean2DPeriodicBoundaries::d(R2loc u, R2loc v) {

  // stolen from <https://blog.demofox.org/2017/10/01/calculating-the-distance-
  //                 between-points-in-wrap-around-toroidal-space/>
  double dx = abs(v.first - u.first);
  double dy = abs(v.second - u.second);

  if (dx > 0.5)
    dx = 1.0 - dx;
  if (dy > 0.5)
    dy = 1.0 - dy;

  return sqrt(dx * dx + dy * dy);
}

double Euclidean2DPeriodicBoundaries::t(R2loc u, R2loc v) {
  return this->d(u, v) / this->velocity;
}

pair<R2loc, double>
Euclidean2DPeriodicBoundaries::interp_dist(R2loc u, R2loc v,
                                           double dist_to_dest) {

  double x1 = u.first;
  double y1 = u.second;

  double x2 = v.first;
  double y2 = v.second;

  double dx = v.first - u.first;
  double dy = v.second - u.second;

  if (dx > 0.5) {
    // Wrapping around in positive x direction
    dx = 1.0 - dx;
    x2 = x2 + 1.0;
  } else if (dx < -0.5) {
    // Wrapping around in negative x direction
    dx = 1.0 + dx;
    x2 = x2 - 1.0;
  }

  if (abs(dy) > 0.5) {
    // Wrapping around in positive y direction
    dy = 1.0 - dy;
    y2 = y2 + 1.0;
  } else if (dy < -0.5) {
    // Wrapping around in negative y direction
    dy = 1.0 + dy;
    y2 = y2 - 1.0;
  }

  double dist = sqrt(dx * dx + dy * dy);
  double frac = dist_to_dest / dist;

  double x_r = fmod(x1 * frac + (1 - frac) * x2, 1.0);
  double y_r = fmod(y1 * frac + (1 - frac) * y2, 1.0);

  return make_pair(R2loc{x_r, y_r}, 0);
}

pair<R2loc, double>
Euclidean2DPeriodicBoundaries::interp_time(R2loc u, R2loc v,
                                           double time_to_dest) {
  double dist_to_dest = time_to_dest * (this->velocity);
  return this->interp_dist(u, v, dist_to_dest);
}

Manhattan2D::Manhattan2D(double velocity)
    : TransportSpace(), velocity(velocity) {}

double Manhattan2D::d(R2loc u, R2loc v) {
  return abs(u.first - v.first) + abs(u.second - v.second);
}

double Manhattan2D::t(R2loc u, R2loc v) {
  return this->d(u, v) / this->velocity;
}

pair<R2loc, double> Manhattan2D::interp_dist(R2loc u, R2loc v,
                                             double dist_to_dest) {
  double frac = dist_to_dest / this->d(u, v);

  return make_pair(R2loc{u.first * frac + (1 - frac) * v.first,
                         u.second * frac + (1 - frac) * v.second},
                   0);
}

pair<R2loc, double> Manhattan2D::interp_time(R2loc u, R2loc v,
                                             double time_to_dest) {
  double dist_to_dest = time_to_dest * (this->velocity);
  return this->interp_dist(u, v, dist_to_dest);
}

} // namespace ridepy
