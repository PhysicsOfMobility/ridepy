#include "cspaces.h"


using namespace std;

namespace cstuff{

TransportSpace::TransportSpace():velocity{1}{};
TransportSpace::TransportSpace(double velocity):velocity{velocity}{};


Euclidean2D::Euclidean2D():TransportSpace{}{};
Euclidean2D::Euclidean2D(double velocity):TransportSpace{velocity}{};

double Euclidean2D::d(pair<double, double> u, pair<double, double> v) const
{
    return sqrt((u.first-v.first)*(u.first-v.first) + (u.second-v.second)*(u.second-v.second));
}

double Euclidean2D::t(pair<double, double> u, pair<double, double> v) const
{
    return this->d(u,v)/this->velocity;
}

pair<pair<double, double>, double> Euclidean2D::interp_dist(pair<double, double> u, pair<double, double> v, double dist_to_dest) const
{
    double frac = dist_to_dest/this->d(u, v);
    return make_pair(
            pair<double, double>{u.first * frac + (1 - frac) * v.first, u.second * frac + (1 - frac) * v.second}, 0);
}

pair<pair<double, double>, double> Euclidean2D::interp_time(pair<double, double> u, pair<double, double> v, double time_to_dest) const
{
    double frac = time_to_dest/this->t(u, v);
    return make_pair(
            pair<double, double>{u.first * frac + (1 - frac) * v.first, u.second * frac + (1 - frac) * v.second}, 0);
}
}


