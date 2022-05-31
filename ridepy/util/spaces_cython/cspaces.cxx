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

Manhattan2D::Manhattan2D(double velocity)
    : TransportSpace(), velocity(velocity) {}

double Manhattan2D::d(R2loc u, R2loc v) {
  return std::abs(u.first - v.first) + std::abs(u.second - v.second);
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

Grid::Grid(int n, int m, double dn, double dm, double velocity)
    : TransportSpace(), n(n), m(m), dn(dn), dm(dm), velocity(velocity) {}

double Grid::d(R2loc u, R2loc v) {
  return std::abs(u.first - v.first) + std::abs(u.second - v.second);
}

double Grid::t(R2loc u, R2loc v) { return this->d(u, v) / this->velocity; }

pair<R2loc, double> Grid::interp_dist(R2loc u, R2loc v, double dist_to_dest) {
  double frac = dist_to_dest / this->d(u, v);

  double x_prec = u.first * frac + (1 - frac) * v.first;
  double y_prec = u.second * frac + (1 - frac) * v.second;

  int x = ceil(x_rec / dm);
  int y = ceil(y_rec / dn);

  double jump_time = x_prec - x + y_prec - y;

  return make_pair(R2loc{x, y}, jump_time);
}

pair<R2loc, double> Grid::interp_time(R2loc u, R2loc v, double time_to_dest) {
  double dist_to_dest = time_to_dest * velocity;
  return interp_dist(u, v, dist_to_dest);
}

} // namespace ridepy
