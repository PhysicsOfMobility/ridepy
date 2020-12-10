#include "cspaces.h"


using namespace std;

namespace cstuff{

Euclidean2D::Euclidean2D():velocity{1}{};
Euclidean2D::Euclidean2D(double velocity):velocity{velocity}{};

double Euclidean2D::d(R2loc u, R2loc v) const
{
    return sqrt((u.first-v.first)*(u.first-v.first) + (u.second-v.second)*(u.second-v.second));
}

double Euclidean2D::t(R2loc u, R2loc v) const
{
    return this->d(u,v)/this->velocity;
}

pair<R2loc, double> Euclidean2D::interp_dist(R2loc u, R2loc v, double dist_to_dest) const
{
    double frac = dist_to_dest/this->d(u, v);
    return make_pair(
        R2loc {u.first*frac + (1-frac)*v.first, u.second*frac + (1-frac)*v.second}, 0);
}

pair<R2loc, double> Euclidean2D::interp_time(R2loc u, R2loc v, double time_to_dest) const
{
    double frac = time_to_dest/this->t(u, v);
    return make_pair(
        R2loc {u.first*frac + (1-frac)*v.first, u.second*frac + (1-frac)*v.second}, 0);
}
}
